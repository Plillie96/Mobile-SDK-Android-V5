"""
Machine Learning Module
Provides ML models for price prediction and sentiment analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import pickle
import os
from datetime import datetime, timedelta
from loguru import logger

# ML imports
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    import torch
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from sentence_transformers import SentenceTransformer
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. ML features will be disabled.")

from config import config


@dataclass
class Prediction:
    """Prediction data structure"""
    symbol: str
    timestamp: datetime
    predicted_price: float
    confidence: float
    direction: str  # 'up', 'down', 'sideways'
    timeframe: str  # '1h', '4h', '1d'
    features_used: List[str]


@dataclass
class SentimentScore:
    """Sentiment analysis result"""
    text: str
    sentiment: str  # 'positive', 'negative', 'neutral'
    score: float
    confidence: float
    source: str
    timestamp: datetime


class PricePredictor:
    """LSTM-based price prediction model"""
    
    def __init__(self, symbol: str, sequence_length: int = 60):
        self.symbol = symbol
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        self.is_trained = False
        
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available. Price prediction disabled.")
            return
        
        self._build_model()
    
    def _build_model(self):
        """Build LSTM model architecture"""
        if not TENSORFLOW_AVAILABLE:
            return
        
        self.model = Sequential([
            Bidirectional(LSTM(100, return_sequences=True, input_shape=(self.sequence_length, 1))),
            Dropout(0.2),
            Bidirectional(LSTM(100, return_sequences=True)),
            Dropout(0.2),
            Bidirectional(LSTM(50, return_sequences=False)),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1, activation='linear')
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM model"""
        # Use close prices
        data = df['close'].values.reshape(-1, 1)
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y)
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for enhanced prediction"""
        # Select features
        feature_columns = ['close', 'volume', 'rsi', 'macd', 'bb_upper', 'bb_lower']
        available_features = [col for col in feature_columns if col in df.columns]
        
        if not available_features:
            # Fallback to just close prices
            return self.prepare_data(df)
        
        # Prepare feature data
        feature_data = df[available_features].values
        
        # Handle NaN values
        feature_data = np.nan_to_num(feature_data, nan=0.0)
        
        # Scale features
        scaled_features = self.feature_scaler.fit_transform(feature_data)
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_features)):
            X.append(scaled_features[i-self.sequence_length:i])
            y.append(scaled_features[i, 0])  # Predict close price
        
        return np.array(X), np.array(y)
    
    def train(self, df: pd.DataFrame, epochs: int = 100, batch_size: int = 32):
        """Train the LSTM model"""
        if not TENSORFLOW_AVAILABLE or self.model is None:
            logger.warning("TensorFlow not available for training")
            return
        
        logger.info(f"Training LSTM model for {self.symbol}")
        
        # Prepare data
        X, y = self.prepare_features(df)
        
        if len(X) < 100:
            logger.warning(f"Insufficient data for training: {len(X)} samples")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ModelCheckpoint(
                f'models/{self.symbol}_lstm_best.h5',
                monitor='val_loss',
                save_best_only=True
            )
        ]
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        logger.info(f"Model trained. MSE: {mse:.6f}, MAE: {mae:.6f}")
        self.is_trained = True
        
        return history
    
    def predict(self, df: pd.DataFrame) -> Optional[Prediction]:
        """Make price prediction"""
        if not TENSORFLOW_AVAILABLE or not self.is_trained or self.model is None:
            return None
        
        try:
            # Prepare latest data
            X, _ = self.prepare_features(df)
            
            if len(X) == 0:
                return None
            
            # Get latest sequence
            latest_sequence = X[-1:]
            
            # Make prediction
            scaled_prediction = self.model.predict(latest_sequence)[0, 0]
            
            # Inverse transform
            prediction = self.scaler.inverse_transform([[scaled_prediction]])[0, 0]
            
            # Calculate confidence based on recent prediction accuracy
            confidence = self._calculate_confidence(df)
            
            # Determine direction
            current_price = df['close'].iloc[-1]
            direction = 'up' if prediction > current_price else 'down'
            
            return Prediction(
                symbol=self.symbol,
                timestamp=datetime.now(),
                predicted_price=prediction,
                confidence=confidence,
                direction=direction,
                timeframe='1h',
                features_used=['close', 'volume', 'rsi', 'macd', 'bb_upper', 'bb_lower']
            )
            
        except Exception as e:
            logger.error(f"Error making prediction for {self.symbol}: {e}")
            return None
    
    def _calculate_confidence(self, df: pd.DataFrame) -> float:
        """Calculate prediction confidence based on recent accuracy"""
        if len(df) < self.sequence_length + 10:
            return 0.5
        
        # Make predictions for recent data and compare with actual
        recent_data = df.tail(10)
        actual_prices = recent_data['close'].values
        
        predictions = []
        for i in range(len(recent_data) - self.sequence_length):
            sequence_data = df.iloc[i:i+self.sequence_length]
            X, _ = self.prepare_features(sequence_data)
            if len(X) > 0:
                pred = self.model.predict(X[-1:])[0, 0]
                pred_price = self.scaler.inverse_transform([[pred]])[0, 0]
                predictions.append(pred_price)
        
        if not predictions:
            return 0.5
        
        # Calculate accuracy
        actual_prices = actual_prices[-len(predictions):]
        errors = np.abs(np.array(predictions) - np.array(actual_prices)) / np.array(actual_prices)
        accuracy = 1 - np.mean(errors)
        
        return max(0.1, min(0.9, accuracy))
    
    def save_model(self, filepath: str):
        """Save trained model"""
        if self.model and self.is_trained:
            self.model.save(filepath)
            logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        if TENSORFLOW_AVAILABLE and os.path.exists(filepath):
            self.model = load_model(filepath)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")


class SentimentAnalyzer:
    """Sentiment analysis for news and social media"""
    
    def __init__(self):
        self.sentiment_pipeline = None
        self.sentence_transformer = None
        
        if TENSORFLOW_AVAILABLE:
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize sentiment analysis models"""
        try:
            # Initialize sentiment pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
            
            # Initialize sentence transformer for similarity
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("Sentiment analysis models initialized")
        except Exception as e:
            logger.error(f"Error initializing sentiment models: {e}")
    
    def analyze_sentiment(self, text: str, source: str = "unknown") -> Optional[SentimentScore]:
        """Analyze sentiment of text"""
        if not self.sentiment_pipeline:
            return None
        
        try:
            # Clean text
            cleaned_text = self._clean_text(text)
            
            if len(cleaned_text) < 10:
                return None
            
            # Analyze sentiment
            result = self.sentiment_pipeline(cleaned_text)[0]
            
            # Map labels to standard format
            label_mapping = {
                'LABEL_0': 'negative',
                'LABEL_1': 'neutral',
                'LABEL_2': 'positive'
            }
            
            sentiment = label_mapping.get(result['label'], 'neutral')
            score = result['score']
            
            return SentimentScore(
                text=cleaned_text,
                sentiment=sentiment,
                score=score,
                confidence=score,
                source=source,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return None
    
    def analyze_batch_sentiment(self, texts: List[str], source: str = "unknown") -> List[SentimentScore]:
        """Analyze sentiment for multiple texts"""
        results = []
        
        for text in texts:
            sentiment = self.analyze_sentiment(text, source)
            if sentiment:
                results.append(sentiment)
        
        return results
    
    def calculate_market_sentiment(self, sentiments: List[SentimentScore]) -> Dict:
        """Calculate overall market sentiment"""
        if not sentiments:
            return {
                'overall_sentiment': 'neutral',
                'sentiment_score': 0.0,
                'confidence': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0
            }
        
        # Calculate sentiment scores
        positive_scores = [s.score for s in sentiments if s.sentiment == 'positive']
        negative_scores = [s.score for s in sentiments if s.sentiment == 'negative']
        neutral_scores = [s.score for s in sentiments if s.sentiment == 'neutral']
        
        # Calculate ratios
        total = len(sentiments)
        positive_ratio = len(positive_scores) / total
        negative_ratio = len(negative_scores) / total
        neutral_ratio = len(neutral_scores) / total
        
        # Calculate overall sentiment score
        sentiment_score = (positive_ratio - negative_ratio) * 100
        
        # Determine overall sentiment
        if sentiment_score > 10:
            overall_sentiment = 'positive'
        elif sentiment_score < -10:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        # Calculate confidence
        avg_confidence = np.mean([s.confidence for s in sentiments])
        
        return {
            'overall_sentiment': overall_sentiment,
            'sentiment_score': sentiment_score,
            'confidence': avg_confidence,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'neutral_ratio': neutral_ratio
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        import re
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()


class EnsemblePredictor:
    """Ensemble of multiple prediction models"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.models = {}
        self.weights = {}
        
    def add_model(self, name: str, model, weight: float = 1.0):
        """Add a model to the ensemble"""
        self.models[name] = model
        self.weights[name] = weight
    
    def predict(self, df: pd.DataFrame) -> Optional[Prediction]:
        """Make ensemble prediction"""
        predictions = []
        weights = []
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict'):
                    pred = model.predict(df)
                    if pred:
                        predictions.append(pred)
                        weights.append(self.weights[name])
            except Exception as e:
                logger.error(f"Error with model {name}: {e}")
        
        if not predictions:
            return None
        
        # Weighted average of predictions
        total_weight = sum(weights)
        if total_weight == 0:
            return None
        
        weighted_price = sum(p.predicted_price * w for p, w in zip(predictions, weights)) / total_weight
        weighted_confidence = sum(p.confidence * w for p, w in zip(predictions, weights)) / total_weight
        
        # Determine direction
        current_price = df['close'].iloc[-1]
        direction = 'up' if weighted_price > current_price else 'down'
        
        return Prediction(
            symbol=self.symbol,
            timestamp=datetime.now(),
            predicted_price=weighted_price,
            confidence=weighted_confidence,
            direction=direction,
            timeframe='1h',
            features_used=['ensemble']
        )


class MLManager:
    """Manager for all ML components"""
    
    def __init__(self):
        self.price_predictors = {}
        self.sentiment_analyzer = SentimentAnalyzer()
        self.ensemble_predictors = {}
        
    def get_price_predictor(self, symbol: str) -> PricePredictor:
        """Get or create price predictor for symbol"""
        if symbol not in self.price_predictors:
            self.price_predictors[symbol] = PricePredictor(symbol)
        return self.price_predictors[symbol]
    
    def train_price_predictor(self, symbol: str, df: pd.DataFrame):
        """Train price predictor for symbol"""
        predictor = self.get_price_predictor(symbol)
        return predictor.train(df)
    
    def predict_price(self, symbol: str, df: pd.DataFrame) -> Optional[Prediction]:
        """Make price prediction for symbol"""
        predictor = self.get_price_predictor(symbol)
        return predictor.predict(df)
    
    def analyze_sentiment(self, text: str, source: str = "unknown") -> Optional[SentimentScore]:
        """Analyze sentiment of text"""
        return self.sentiment_analyzer.analyze_sentiment(text, source)
    
    def get_ensemble_predictor(self, symbol: str) -> EnsemblePredictor:
        """Get or create ensemble predictor for symbol"""
        if symbol not in self.ensemble_predictors:
            self.ensemble_predictors[symbol] = EnsemblePredictor(symbol)
        return self.ensemble_predictors[symbol]
    
    def save_models(self, directory: str = "models"):
        """Save all trained models"""
        os.makedirs(directory, exist_ok=True)
        
        for symbol, predictor in self.price_predictors.items():
            if predictor.is_trained:
                filepath = os.path.join(directory, f"{symbol}_lstm.h5")
                predictor.save_model(filepath)
    
    def load_models(self, directory: str = "models"):
        """Load all trained models"""
        for filename in os.listdir(directory):
            if filename.endswith('_lstm.h5'):
                symbol = filename.replace('_lstm.h5', '')
                predictor = self.get_price_predictor(symbol)
                filepath = os.path.join(directory, filename)
                predictor.load_model(filepath)