"""
Machine learning models for trading signal generation
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

class MLTradingModel:
    """Base class for machine learning trading models"""
    
    def __init__(self, model_name: str, model_type: str = 'random_forest'):
        self.model_name = model_name
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_trained = False
        self.last_training_date = None
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for machine learning model
        
        Args:
            data: OHLCV market data
            
        Returns:
            DataFrame with engineered features
        """
        df = data.copy()
        
        # Technical indicators
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # Price momentum
        df['price_momentum'] = df['close'] / df['close'].shift(5) - 1
        df['volume_momentum'] = df['volume'] / df['volume'].rolling(window=5).mean()
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['high_low_ratio'] = df['high'] / df['low']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Target variable (1 for price increase, 0 for decrease)
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        # Drop NaN values
        df = df.dropna()
        
        return df
    
    def select_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Select relevant features for the model
        
        Args:
            df: DataFrame with all features
            
        Returns:
            DataFrame with selected features
        """
        feature_columns = [
            'returns', 'log_returns', 'sma_5', 'sma_20', 'ema_12', 'ema_26',
            'price_momentum', 'volume_momentum', 'volatility', 'high_low_ratio',
            'rsi', 'macd', 'macd_signal', 'macd_histogram', 'bb_position'
        ]
        
        self.feature_columns = feature_columns
        return df[feature_columns + ['target']]
    
    def create_model(self):
        """Create the machine learning model"""
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
        elif self.model_type == 'logistic_regression':
            self.model = LogisticRegression(random_state=42, max_iter=1000)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def train(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Train the machine learning model
        
        Args:
            data: OHLCV market data
            
        Returns:
            Dictionary with training metrics
        """
        # Prepare features
        df = self.prepare_features(data)
        df = self.select_features(df)
        
        # Split features and target
        X = df[self.feature_columns]
        y = df['target']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create and train model
        self.create_model()
        self.model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        metrics = {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        self.is_trained = True
        self.last_training_date = datetime.utcnow()
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> Tuple[str, float]:
        """
        Make prediction on new data
        
        Args:
            data: OHLCV market data
            
        Returns:
            Tuple of (signal, confidence)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features
        df = self.prepare_features(data)
        df = self.select_features(df)
        
        if df.empty:
            return 'hold', 0.0
        
        # Get latest features
        latest_features = df[self.feature_columns].iloc[-1:].values
        latest_features_scaled = self.scaler.transform(latest_features)
        
        # Make prediction
        prediction = self.model.predict(latest_features_scaled)[0]
        confidence = self.model.predict_proba(latest_features_scaled)[0][1]
        
        # Convert to signal
        if prediction == 1:
            signal = 'buy'
        else:
            signal = 'sell'
            confidence = 1 - confidence
        
        return signal, confidence
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type,
            'training_date': self.last_training_date
        }
        
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.model_type = model_data['model_type']
        self.last_training_date = model_data['training_date']
        self.is_trained = True

class EnsembleModel:
    """Ensemble of multiple ML models"""
    
    def __init__(self, models: Dict[str, MLTradingModel]):
        self.models = models
        self.weights = {name: 1.0 / len(models) for name in models.keys()}
    
    def predict(self, data: pd.DataFrame) -> Tuple[str, float]:
        """
        Make ensemble prediction
        
        Args:
            data: OHLCV market data
            
        Returns:
            Tuple of (signal, confidence)
        """
        predictions = {}
        confidences = {}
        
        for name, model in self.models.items():
            try:
                signal, confidence = model.predict(data)
                predictions[name] = signal
                confidences[name] = confidence
            except Exception as e:
                print(f"Error in model {name}: {e}")
                continue
        
        if not predictions:
            return 'hold', 0.0
        
        # Weighted voting
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        
        for name, signal in predictions.items():
            weight = self.weights.get(name, 1.0)
            confidence = confidences[name]
            
            if signal == 'buy':
                buy_score += weight * confidence
            else:
                sell_score += weight * confidence
            
            total_weight += weight
        
        if total_weight == 0:
            return 'hold', 0.0
        
        # Normalize scores
        buy_score /= total_weight
        sell_score /= total_weight
        
        # Determine final signal
        if buy_score > sell_score and buy_score > 0.6:
            return 'buy', buy_score
        elif sell_score > buy_score and sell_score > 0.6:
            return 'sell', sell_score
        else:
            return 'hold', max(buy_score, sell_score)
    
    def update_weights(self, performance: Dict[str, float]):
        """
        Update model weights based on performance
        
        Args:
            performance: Dictionary of model performance metrics
        """
        total_performance = sum(performance.values())
        
        if total_performance > 0:
            for name in self.models.keys():
                if name in performance:
                    self.weights[name] = performance[name] / total_performance
                else:
                    self.weights[name] = 0.0