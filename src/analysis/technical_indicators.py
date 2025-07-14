"""
Technical Analysis Indicators for Trading Bot
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import ta
from scipy import stats
from sklearn.preprocessing import StandardScaler
import sys
import os

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import config

class TechnicalIndicators:
    """Advanced technical analysis indicators for trading decisions"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        return ta.momentum.RSIIndicator(prices, window=period).rsi()
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        macd_indicator = ta.trend.MACD(prices, window_fast=fast, window_slow=slow, window_sign=signal)
        return {
            'macd': macd_indicator.macd(),
            'macd_signal': macd_indicator.macd_signal(),
            'macd_histogram': macd_indicator.macd_diff()
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2.0) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        bb_indicator = ta.volatility.BollingerBands(prices, window=period, window_dev=std)
        return {
            'upper': bb_indicator.bollinger_hband(),
            'middle': bb_indicator.bollinger_mavg(),
            'lower': bb_indicator.bollinger_lband(),
            'width': bb_indicator.bollinger_wband(),
            'percent': bb_indicator.bollinger_pband()
        }
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        stoch_indicator = ta.momentum.StochasticOscillator(high, low, close, window=k_period, smooth_window=d_period)
        return {
            'k': stoch_indicator.stoch(),
            'd': stoch_indicator.stoch_signal()
        }
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        return ta.volatility.AverageTrueRange(high, low, close, window=period).average_true_range()
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """Calculate Average Directional Index"""
        adx_indicator = ta.trend.ADXIndicator(high, low, close, window=period)
        return {
            'adx': adx_indicator.adx(),
            'plus_di': adx_indicator.adx_pos(),
            'minus_di': adx_indicator.adx_neg()
        }
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        return ta.trend.CCIIndicator(high, low, close, window=period).cci()
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        return ta.momentum.WilliamsRIndicator(high, low, close, window=period).williams_r()
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume"""
        return ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()
    
    def calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        return ta.volume.VolumeWeightedAveragePrice(high, low, close, volume).volume_weighted_average_price()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return ta.trend.EMAIndicator(prices, window=period).ema_indicator()
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return ta.trend.SMAIndicator(prices, window=period).sma_indicator()
    
    def calculate_ichimoku(self, high: pd.Series, low: pd.Series, 
                          tenkan: int = 9, kijun: int = 26, senkou: int = 52) -> Dict[str, pd.Series]:
        """Calculate Ichimoku Cloud"""
        ichimoku_indicator = ta.trend.IchimokuIndicator(high, low, window1=tenkan, window2=kijun, window3=senkou)
        return {
            'tenkan_sen': ichimoku_indicator.ichimoku_conversion_line(),
            'kijun_sen': ichimoku_indicator.ichimoku_base_line(),
            'senkou_span_a': ichimoku_indicator.ichimoku_a(),
            'senkou_span_b': ichimoku_indicator.ichimoku_b(),
            'chikou_span': ichimoku_indicator.ichimoku_span_b()
        }
    
    def calculate_fibonacci_retracements(self, high: float, low: float) -> Dict[str, float]:
        """Calculate Fibonacci Retracement Levels"""
        diff = high - low
        return {
            '0.0': low,
            '0.236': low + 0.236 * diff,
            '0.382': low + 0.382 * diff,
            '0.5': low + 0.5 * diff,
            '0.618': low + 0.618 * diff,
            '0.786': low + 0.786 * diff,
            '1.0': high
        }
    
    def calculate_pivot_points(self, high: float, low: float, close: float) -> Dict[str, float]:
        """Calculate Pivot Points"""
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }
    
    def calculate_volume_profile(self, prices: pd.Series, volume: pd.Series, bins: int = 50) -> Dict[str, np.ndarray]:
        """Calculate Volume Profile"""
        price_bins = np.linspace(prices.min(), prices.max(), bins)
        volume_profile = np.zeros(bins-1)
        
        for i in range(len(prices)):
            bin_idx = np.digitize(prices.iloc[i], price_bins) - 1
            if 0 <= bin_idx < len(volume_profile):
                volume_profile[bin_idx] += volume.iloc[i]
        
        return {
            'price_levels': price_bins[:-1],
            'volume_profile': volume_profile
        }
    
    def calculate_support_resistance(self, prices: pd.Series, window: int = 20, threshold: float = 0.02) -> Dict[str, List[float]]:
        """Calculate Support and Resistance Levels"""
        highs = prices.rolling(window=window, center=True).max()
        lows = prices.rolling(window=window, center=True).min()
        
        resistance_levels = []
        support_levels = []
        
        for i in range(window, len(prices) - window):
            if prices.iloc[i] == highs.iloc[i]:
                resistance_levels.append(prices.iloc[i])
            if prices.iloc[i] == lows.iloc[i]:
                support_levels.append(prices.iloc[i])
        
        # Cluster nearby levels
        resistance_levels = self._cluster_levels(resistance_levels, threshold)
        support_levels = self._cluster_levels(support_levels, threshold)
        
        return {
            'resistance': resistance_levels,
            'support': support_levels
        }
    
    def _cluster_levels(self, levels: List[float], threshold: float) -> List[float]:
        """Cluster nearby price levels"""
        if not levels:
            return []
        
        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] <= threshold:
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        clustered.append(np.mean(current_cluster))
        return clustered
    
    def calculate_momentum_indicators(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate multiple momentum indicators"""
        return {
            'roc': ta.momentum.ROCIndicator(prices).roc(),
            'mom': ta.momentum.MOMIndicator(prices).mom(),
            'ppo': ta.momentum.PercentagePriceOscillator(prices).ppo(),
            'ppo_signal': ta.momentum.PercentagePriceOscillator(prices).ppo_signal(),
            'ppo_hist': ta.momentum.PercentagePriceOscillator(prices).ppo_hist()
        }
    
    def calculate_volatility_indicators(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Calculate multiple volatility indicators"""
        return {
            'atr': self.calculate_atr(high, low, close),
            'bb_width': self.calculate_bollinger_bands(close)['width'],
            'bb_percent': self.calculate_bollinger_bands(close)['percent'],
            'natr': ta.volatility.AverageTrueRange(high, low, close).average_true_range() / close * 100
        }
    
    def calculate_trend_indicators(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Calculate multiple trend indicators"""
        return {
            'adx': self.calculate_adx(high, low, close)['adx'],
            'plus_di': self.calculate_adx(high, low, close)['plus_di'],
            'minus_di': self.calculate_adx(high, low, close)['minus_di'],
            'cci': self.calculate_cci(high, low, close),
            'aroon_up': ta.trend.AroonIndicator(close).aroon_up(),
            'aroon_down': ta.trend.AroonIndicator(close).aroon_down(),
            'aroon_ind': ta.trend.AroonIndicator(close).aroon_indicator()
        }
    
    def calculate_volume_indicators(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> Dict[str, pd.Series]:
        """Calculate multiple volume indicators"""
        return {
            'obv': self.calculate_obv(close, volume),
            'vwap': self.calculate_vwap(high, low, close, volume),
            'mfi': ta.volume.MFIIndicator(high, low, close, volume).money_flow_index(),
            'vwma': ta.volume.VolumeWeightedAveragePrice(high, low, close, volume).volume_weighted_average_price()
        }
    
    def get_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for a dataframe"""
        if df.empty:
            return df
        
        result = df.copy()
        
        # Basic indicators
        result['rsi'] = self.calculate_rsi(result['close'])
        result['sma_20'] = self.calculate_sma(result['close'], 20)
        result['sma_50'] = self.calculate_sma(result['close'], 50)
        result['ema_12'] = self.calculate_ema(result['close'], 12)
        result['ema_26'] = self.calculate_ema(result['close'], 26)
        
        # MACD
        macd_data = self.calculate_macd(result['close'])
        result['macd'] = macd_data['macd']
        result['macd_signal'] = macd_data['macd_signal']
        result['macd_histogram'] = macd_data['macd_histogram']
        
        # Bollinger Bands
        bb_data = self.calculate_bollinger_bands(result['close'])
        result['bb_upper'] = bb_data['upper']
        result['bb_middle'] = bb_data['middle']
        result['bb_lower'] = bb_data['lower']
        result['bb_width'] = bb_data['width']
        result['bb_percent'] = bb_data['percent']
        
        # Stochastic
        stoch_data = self.calculate_stochastic(result['high'], result['low'], result['close'])
        result['stoch_k'] = stoch_data['k']
        result['stoch_d'] = stoch_data['d']
        
        # Additional indicators
        result['atr'] = self.calculate_atr(result['high'], result['low'], result['close'])
        result['williams_r'] = self.calculate_williams_r(result['high'], result['low'], result['close'])
        
        # Volume indicators
        if 'volume' in result.columns:
            result['obv'] = self.calculate_obv(result['close'], result['volume'])
            result['vwap'] = self.calculate_vwap(result['high'], result['low'], result['close'], result['volume'])
        
        return result
    
    def generate_signals(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Generate trading signals based on technical indicators"""
        signals = {}
        
        # RSI signals
        signals['rsi_oversold'] = df['rsi'] < config.RSI_OVERSOLD
        signals['rsi_overbought'] = df['rsi'] > config.RSI_OVERBOUGHT
        
        # MACD signals
        signals['macd_bullish'] = (df['macd'] > df['macd_signal']) & (df['macd_histogram'] > 0)
        signals['macd_bearish'] = (df['macd'] < df['macd_signal']) & (df['macd_histogram'] < 0)
        
        # Bollinger Bands signals
        signals['bb_oversold'] = df['close'] < df['bb_lower']
        signals['bb_overbought'] = df['close'] > df['bb_upper']
        
        # Moving Average signals
        signals['ma_bullish'] = df['close'] > df['sma_20']
        signals['ma_bearish'] = df['close'] < df['sma_20']
        
        # Stochastic signals
        signals['stoch_oversold'] = df['stoch_k'] < 20
        signals['stoch_overbought'] = df['stoch_k'] > 80
        
        # Combined signals
        signals['strong_buy'] = (
            signals['rsi_oversold'] & 
            signals['macd_bullish'] & 
            signals['bb_oversold'] &
            signals['ma_bullish']
        )
        
        signals['strong_sell'] = (
            signals['rsi_overbought'] & 
            signals['macd_bearish'] & 
            signals['bb_overbought'] &
            signals['ma_bearish']
        )
        
        return signals