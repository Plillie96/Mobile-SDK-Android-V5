"""
Machine Learning Module for Trading Bot
Provides ML-based price prediction and pattern recognition
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MLPredictor:
    """Machine Learning Price Predictor"""
    
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.target_column = 'target'
        self.model_path = config.ml_model_path
        
        # Ensure model directory exists
        os.makedirs(self.model_path, exist_ok=True)
        
    def prepare_features(self, df: pd.DataFrame, prediction_horizon: int = 1) -> pd.DataFrame:
        """Prepare features for ML model"""
        try:
            # Create target variable (future price)
            df[self.target_column] = df['close'].shift(-prediction_horizon)
            
            # Technical indicators as features
            feature_cols = [
                'rsi', 'macd', 'macd_signal', 'macd_histogram',
                'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_percent',
                'sma_20', 'sma_50', 'ema_20', 'ema_50',
                'vwap', 'atr', 'volatility', 'adx', 'di_plus', 'di_minus'
            ]
            
            # Price-based features
            df['price_change'] = df['close'].pct_change()
            df['price_change_5'] = df['close'].pct_change(5)
            df['price_change_10'] = df['close'].pct_change(10)
            df['high_low_ratio'] = df['high'] / df['low']
            df['close_open_ratio'] = df['close'] / df['open']
            
            # Volume features
            df['volume_change'] = df['volume'].pct_change()
            df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            
            # Momentum features
            df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
            df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
            df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
            
            # Volatility features
            df['volatility_5'] = df['price_change'].rolling(5).std()
            df['volatility_10'] = df['price_change'].rolling(10).std()
            
            # Time-based features
            df['hour'] = pd.to_datetime(df['timestamp'], unit='ms').dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp'], unit='ms').dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # Add to feature columns
            additional_features = [
                'price_change', 'price_change_5', 'price_change_10',
                'high_low_ratio', 'close_open_ratio', 'volume_change',
                'volume_ma_ratio', 'momentum_5', 'momentum_10', 'momentum_20',
                'volatility_5', 'volatility_10', 'hour', 'day_of_week', 'is_weekend'
            ]
            
            self.feature_columns = feature_cols + additional_features
            
            # Remove rows with NaN values
            df = df.dropna()
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return df
    
    def train_models(self, df: pd.DataFrame, symbol: str) -> Dict[str, float]:
        """Train multiple ML models"""
        try:
            # Prepare features
            df = self.prepare_features(df)
            
            if len(df) < 100:
                logger.warning(f"Insufficient data for training: {len(df)} samples")
                return {}
            
            # Split features and target
            X = df[self.feature_columns]
            y = df[self.target_column]
            
            # Remove any remaining NaN values
            mask = ~(X.isna().any(axis=1) | y.isna())
            X = X[mask]
            y = y[mask]
            
            if len(X) < 50:
                logger.warning(f"Insufficient clean data for training: {len(X)} samples")
                return {}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            self.scalers[symbol] = scaler
            
            # Define models
            models = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100, max_depth=10, random_state=42
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=100, max_depth=5, random_state=42
                ),
                'linear_regression': LinearRegression(),
                'ridge': Ridge(alpha=1.0)
            }
            
            scores = {}
            
            # Train each model
            for name, model in models.items():
                try:
                    # Train model
                    model.fit(X_train_scaled, y_train)
                    
                    # Make predictions
                    y_pred = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    mse = mean_squared_error(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    scores[name] = {
                        'mse': mse,
                        'mae': mae,
                        'r2': r2,
                        'rmse': np.sqrt(mse)
                    }
                    
                    # Store model
                    self.models[f"{symbol}_{name}"] = model
                    
                    # Save model
                    model_file = os.path.join(self.model_path, f"{symbol}_{name}.joblib")
                    scaler_file = os.path.join(self.model_path, f"{symbol}_{name}_scaler.joblib")
                    
                    joblib.dump(model, model_file)
                    joblib.dump(scaler, scaler_file)
                    
                    logger.info(f"Trained {name} for {symbol}: R²={r2:.4f}, RMSE={np.sqrt(mse):.4f}")
                    
                except Exception as e:
                    logger.error(f"Error training {name} model: {e}")
                    continue
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in train_models: {e}")
            return {}
    
    def load_models(self, symbol: str) -> bool:
        """Load trained models from disk"""
        try:
            model_names = ['random_forest', 'gradient_boosting', 'linear_regression', 'ridge']
            
            for name in model_names:
                model_file = os.path.join(self.model_path, f"{symbol}_{name}.joblib")
                scaler_file = os.path.join(self.model_path, f"{symbol}_{name}_scaler.joblib")
                
                if os.path.exists(model_file) and os.path.exists(scaler_file):
                    self.models[f"{symbol}_{name}"] = joblib.load(model_file)
                    self.scalers[f"{symbol}_{name}"] = joblib.load(scaler_file)
                    logger.info(f"Loaded {name} model for {symbol}")
                else:
                    logger.warning(f"Model files not found for {symbol}_{name}")
            
            return len([k for k in self.models.keys() if k.startswith(symbol)]) > 0
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def predict(self, df: pd.DataFrame, symbol: str) -> Dict[str, float]:
        """Make price predictions using ensemble of models"""
        try:
            if not self.feature_columns:
                logger.error("No feature columns defined. Train models first.")
                return {}
            
            # Prepare features
            df = self.prepare_features(df)
            
            if len(df) == 0:
                logger.warning("No data available for prediction")
                return {}
            
            # Get latest data point
            latest_data = df[self.feature_columns].iloc[-1:]
            
            predictions = {}
            weights = {
                'random_forest': 0.3,
                'gradient_boosting': 0.3,
                'linear_regression': 0.2,
                'ridge': 0.2
            }
            
            # Make predictions with each model
            for name in weights.keys():
                model_key = f"{symbol}_{name}"
                scaler_key = f"{symbol}_{name}"
                
                if model_key in self.models and scaler_key in self.scalers:
                    try:
                        # Scale features
                        scaled_data = self.scalers[scaler_key].transform(latest_data)
                        
                        # Make prediction
                        pred = self.models[model_key].predict(scaled_data)[0]
                        predictions[name] = pred
                        
                    except Exception as e:
                        logger.error(f"Error making prediction with {name}: {e}")
                        continue
            
            if not predictions:
                logger.warning("No models available for prediction")
                return {}
            
            # Calculate weighted ensemble prediction
            weighted_pred = 0
            total_weight = 0
            
            for name, pred in predictions.items():
                weight = weights[name]
                weighted_pred += pred * weight
                total_weight += weight
            
            if total_weight > 0:
                ensemble_pred = weighted_pred / total_weight
            else:
                ensemble_pred = np.mean(list(predictions.values()))
            
            # Calculate prediction confidence
            if len(predictions) > 1:
                confidence = 1 - np.std(list(predictions.values())) / np.mean(list(predictions.values()))
                confidence = max(0, min(1, confidence))  # Clamp between 0 and 1
            else:
                confidence = 0.5
            
            return {
                'ensemble_prediction': ensemble_pred,
                'individual_predictions': predictions,
                'confidence': confidence,
                'current_price': df['close'].iloc[-1],
                'predicted_change': (ensemble_pred - df['close'].iloc[-1]) / df['close'].iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            return {}
    
    def get_prediction_signal(self, prediction_data: Dict[str, float], 
                            threshold: float = 0.02) -> Dict[str, Any]:
        """Convert prediction to trading signal"""
        try:
            if not prediction_data:
                return {'signal': 'hold', 'confidence': 0, 'reason': 'No prediction data'}
            
            predicted_change = prediction_data.get('predicted_change', 0)
            confidence = prediction_data.get('confidence', 0)
            
            # Define signal thresholds
            buy_threshold = threshold
            sell_threshold = -threshold
            
            signal = 'hold'
            reason = 'Prediction within threshold'
            
            if predicted_change > buy_threshold and confidence > 0.6:
                signal = 'buy'
                reason = f'Predicted {predicted_change:.2%} increase with {confidence:.2%} confidence'
            elif predicted_change < sell_threshold and confidence > 0.6:
                signal = 'sell'
                reason = f'Predicted {predicted_change:.2%} decrease with {confidence:.2%} confidence'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'predicted_change': predicted_change,
                'reason': reason,
                'threshold': threshold
            }
            
        except Exception as e:
            logger.error(f"Error getting prediction signal: {e}")
            return {'signal': 'hold', 'confidence': 0, 'reason': f'Error: {e}'}
    
    def retrain_if_needed(self, symbol: str, last_training_time: Optional[datetime] = None) -> bool:
        """Check if models need retraining"""
        try:
            if last_training_time is None:
                return True
            
            hours_since_training = (datetime.now() - last_training_time).total_seconds() / 3600
            
            if hours_since_training >= self.config.retrain_interval_hours:
                logger.info(f"Models for {symbol} need retraining (last trained {hours_since_training:.1f} hours ago)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking retrain status: {e}")
            return True
    
    def get_model_performance(self, symbol: str) -> Dict[str, Any]:
        """Get performance metrics for trained models"""
        try:
            performance = {}
            
            for key in self.models.keys():
                if key.startswith(symbol):
                    model_name = key.replace(f"{symbol}_", "")
                    performance[model_name] = {
                        'loaded': True,
                        'last_updated': datetime.now().isoformat()
                    }
            
            return performance
            
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {}