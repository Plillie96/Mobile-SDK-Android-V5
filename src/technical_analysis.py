"""
Technical Analysis Module
Provides various technical indicators and analysis tools
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import ta
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice
from ta.others import DailyReturnIndicator
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """Advanced Technical Analysis Engine"""
    
    def __init__(self, config):
        self.config = config
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            rsi = RSIIndicator(close=prices, window=period)
            return rsi.rsi()
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series([np.nan] * len(prices))
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            macd = MACD(close=prices, window_fast=fast, window_slow=slow, window_sign=signal)
            return {
                'macd': macd.macd(),
                'macd_signal': macd.macd_signal(),
                'macd_histogram': macd.macd_diff()
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {
                'macd': pd.Series([np.nan] * len(prices)),
                'macd_signal': pd.Series([np.nan] * len(prices)),
                'macd_histogram': pd.Series([np.nan] * len(prices))
            }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2.0) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            bb = BollingerBands(close=prices, window=period, window_dev=std)
            return {
                'upper': bb.bollinger_hband(),
                'middle': bb.bollinger_mavg(),
                'lower': bb.bollinger_lband(),
                'width': bb.bollinger_wband(),
                'percent': bb.bollinger_pband()
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return {
                'upper': pd.Series([np.nan] * len(prices)),
                'middle': pd.Series([np.nan] * len(prices)),
                'lower': pd.Series([np.nan] * len(prices)),
                'width': pd.Series([np.nan] * len(prices)),
                'percent': pd.Series([np.nan] * len(prices))
            }
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        try:
            stoch = StochasticOscillator(high=high, low=low, close=close, 
                                       window=k_period, smooth_window=d_period)
            return {
                'k': stoch.stoch(),
                'd': stoch.stoch_signal()
            }
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {e}")
            return {
                'k': pd.Series([np.nan] * len(close)),
                'd': pd.Series([np.nan] * len(close))
            }
    
    def calculate_moving_averages(self, prices: pd.Series, periods: List[int] = [20, 50, 200]) -> Dict[str, pd.Series]:
        """Calculate multiple moving averages"""
        try:
            mas = {}
            for period in periods:
                sma = SMAIndicator(close=prices, window=period)
                ema = EMAIndicator(close=prices, window=period)
                mas[f'sma_{period}'] = sma.sma_indicator()
                mas[f'ema_{period}'] = ema.ema_indicator()
            return mas
        except Exception as e:
            logger.error(f"Error calculating Moving Averages: {e}")
            return {f'sma_{period}': pd.Series([np.nan] * len(prices)) for period in periods}
    
    def calculate_volume_indicators(self, high: pd.Series, low: pd.Series, 
                                  close: pd.Series, volume: pd.Series) -> Dict[str, pd.Series]:
        """Calculate volume-based indicators"""
        try:
            vwap = VolumeWeightedAveragePrice(high=high, low=low, close=close, volume=volume)
            return {
                'vwap': vwap.volume_weighted_average_price()
            }
        except Exception as e:
            logger.error(f"Error calculating Volume Indicators: {e}")
            return {'vwap': pd.Series([np.nan] * len(close))}
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            return ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=period).average_true_range()
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return pd.Series([np.nan] * len(close))
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """Calculate Average Directional Index"""
        try:
            adx = ta.trend.ADXIndicator(high=high, low=low, close=close, window=period)
            return {
                'adx': adx.adx(),
                'di_plus': adx.adx_pos(),
                'di_minus': adx.adx_neg()
            }
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            return {
                'adx': pd.Series([np.nan] * len(close)),
                'di_plus': pd.Series([np.nan] * len(close)),
                'di_minus': pd.Series([np.nan] * len(close))
            }
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        try:
            return ta.trend.CCIIndicator(high=high, low=low, close=close, window=period).cci()
        except Exception as e:
            logger.error(f"Error calculating CCI: {e}")
            return pd.Series([np.nan] * len(close))
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        try:
            return ta.momentum.WilliamsRIndicator(high=high, low=low, close=close, window=period).williams_r()
        except Exception as e:
            logger.error(f"Error calculating Williams %R: {e}")
            return pd.Series([np.nan] * len(close))
    
    def generate_signals(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Generate trading signals based on multiple indicators"""
        signals = {}
        
        try:
            # RSI signals
            if 'rsi' in df.columns:
                signals['rsi_buy'] = (df['rsi'] < self.config.rsi_oversold) & (df['rsi'].shift(1) >= self.config.rsi_oversold)
                signals['rsi_sell'] = (df['rsi'] > self.config.rsi_overbought) & (df['rsi'].shift(1) <= self.config.rsi_overbought)
            
            # MACD signals
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                signals['macd_buy'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
                signals['macd_sell'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
            
            # Bollinger Bands signals
            if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
                signals['bb_buy'] = df['close'] <= df['bb_lower']
                signals['bb_sell'] = df['close'] >= df['bb_upper']
            
            # Moving Average crossover signals
            if 'sma_20' in df.columns and 'sma_50' in df.columns:
                signals['ma_buy'] = (df['sma_20'] > df['sma_50']) & (df['sma_20'].shift(1) <= df['sma_50'].shift(1))
                signals['ma_sell'] = (df['sma_20'] < df['sma_50']) & (df['sma_20'].shift(1) >= df['sma_50'].shift(1))
            
            # Volume confirmation
            if 'volume' in df.columns:
                avg_volume = df['volume'].rolling(window=20).mean()
                signals['volume_confirmation'] = df['volume'] > avg_volume * 1.5
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
        
        return signals
    
    def calculate_support_resistance(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                                   window: int = 20) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        try:
            recent_high = high.rolling(window=window).max().iloc[-1]
            recent_low = low.rolling(window=window).min().iloc[-1]
            current_price = close.iloc[-1]
            
            return {
                'support': recent_low,
                'resistance': recent_high,
                'current_price': current_price,
                'distance_to_support': (current_price - recent_low) / current_price,
                'distance_to_resistance': (recent_high - current_price) / current_price
            }
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {}
    
    def calculate_volatility(self, close: pd.Series, window: int = 20) -> pd.Series:
        """Calculate price volatility"""
        try:
            returns = close.pct_change()
            volatility = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
            return volatility
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return pd.Series([np.nan] * len(close))
    
    def calculate_momentum(self, close: pd.Series, periods: List[int] = [5, 10, 20]) -> Dict[str, pd.Series]:
        """Calculate momentum indicators"""
        try:
            momentum = {}
            for period in periods:
                momentum[f'momentum_{period}'] = close / close.shift(period) - 1
            return momentum
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return {f'momentum_{period}': pd.Series([np.nan] * len(close)) for period in periods}
    
    def analyze_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform comprehensive technical analysis"""
        try:
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"DataFrame must contain columns: {required_cols}")
            
            # Calculate all indicators
            df['rsi'] = self.calculate_rsi(df['close'], self.config.rsi_period)
            
            macd_data = self.calculate_macd(df['close'], self.config.macd_fast, 
                                          self.config.macd_slow, self.config.macd_signal)
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['macd_signal']
            df['macd_histogram'] = macd_data['macd_histogram']
            
            bb_data = self.calculate_bollinger_bands(df['close'], self.config.bollinger_period, 
                                                   self.config.bollinger_std)
            df['bb_upper'] = bb_data['upper']
            df['bb_middle'] = bb_data['middle']
            df['bb_lower'] = bb_data['lower']
            df['bb_width'] = bb_data['width']
            df['bb_percent'] = bb_data['percent']
            
            # Moving averages
            ma_data = self.calculate_moving_averages(df['close'])
            for key, value in ma_data.items():
                df[key] = value
            
            # Volume indicators
            volume_data = self.calculate_volume_indicators(df['high'], df['low'], df['close'], df['volume'])
            df['vwap'] = volume_data['vwap']
            
            # Additional indicators
            df['atr'] = self.calculate_atr(df['high'], df['low'], df['close'])
            df['volatility'] = self.calculate_volatility(df['close'])
            
            adx_data = self.calculate_adx(df['high'], df['low'], df['close'])
            df['adx'] = adx_data['adx']
            df['di_plus'] = adx_data['di_plus']
            df['di_minus'] = adx_data['di_minus']
            
            # Generate signals
            signals = self.generate_signals(df)
            for key, value in signals.items():
                df[key] = value
            
            return df
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return df