"""
Technical Analysis Module
Provides various technical indicators and analysis tools
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import ta
from scipy import stats
from loguru import logger

from config import config


@dataclass
class Signal:
    """Trading signal data structure"""
    symbol: str
    timestamp: int
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float  # 0.0 to 1.0
    indicator: str
    value: float
    threshold: float
    confidence: float


class TechnicalAnalysis:
    """Technical Analysis Engine"""
    
    def __init__(self):
        self.indicators = {}
        
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        return ta.momentum.RSIIndicator(prices, window=period).rsi()
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        macd_indicator = ta.trend.MACD(prices, window_fast=fast, window_slow=slow, window_sign=signal)
        return macd_indicator.macd(), macd_indicator.macd_signal(), macd_indicator.macd_diff()
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        bb_indicator = ta.volatility.BollingerBands(prices, window=period, window_dev=std)
        return bb_indicator.bollinger_hband(), bb_indicator.bollinger_lband(), bb_indicator.bollinger_mavg()
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        stoch_indicator = ta.momentum.StochasticOscillator(high, low, close, window=k_period, smooth_window=d_period)
        return stoch_indicator.stoch(), stoch_indicator.stoch_signal()
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        return ta.volatility.AverageTrueRange(high, low, close, window=period).average_true_range()
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index"""
        return ta.trend.ADXIndicator(high, low, close, window=period).adx()
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        return ta.trend.CCIIndicator(high, low, close, window=period).cci()
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        return ta.momentum.WilliamsRIndicator(high, low, close, lbp=period).williams_r()
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume"""
        return ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()
    
    def calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()
    
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
    
    def calculate_support_resistance(self, prices: pd.Series, window: int = 20) -> Tuple[List[float], List[float]]:
        """Calculate Support and Resistance Levels"""
        supports = []
        resistances = []
        
        for i in range(window, len(prices) - window):
            # Check for support
            if all(prices.iloc[i] <= prices.iloc[j] for j in range(i - window, i + window + 1)):
                supports.append(prices.iloc[i])
            
            # Check for resistance
            if all(prices.iloc[i] >= prices.iloc[j] for j in range(i - window, i + window + 1)):
                resistances.append(prices.iloc[i])
        
        return supports, resistances
    
    def calculate_momentum(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculate Momentum"""
        return prices.diff(period)
    
    def calculate_rate_of_change(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculate Rate of Change"""
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Volatility (Standard Deviation)"""
        return prices.rolling(window=period).std()
    
    def calculate_beta(self, asset_returns: pd.Series, market_returns: pd.Series) -> float:
        """Calculate Beta relative to market"""
        covariance = np.cov(asset_returns, market_returns)[0][1]
        market_variance = np.var(market_returns)
        return covariance / market_variance if market_variance != 0 else 0
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio"""
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) != 0 else 0
    
    def calculate_max_drawdown(self, prices: pd.Series) -> Tuple[float, int, int]:
        """Calculate Maximum Drawdown"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        peak_idx = prices[:max_dd_idx].idxmax()
        return max_dd, peak_idx, max_dd_idx
    
    def generate_signals(self, df: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate trading signals based on multiple indicators"""
        signals = []
        
        if len(df) < 50:  # Need minimum data
            return signals
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # RSI Signals
        rsi = self.calculate_rsi(close, config.RSI_PERIOD)
        if not rsi.empty and not pd.isna(rsi.iloc[-1]):
            rsi_value = rsi.iloc[-1]
            if rsi_value < config.RSI_OVERSOLD:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='buy',
                    strength=min(1.0, (config.RSI_OVERSOLD - rsi_value) / config.RSI_OVERSOLD),
                    indicator='RSI',
                    value=rsi_value,
                    threshold=config.RSI_OVERSOLD,
                    confidence=0.7
                ))
            elif rsi_value > config.RSI_OVERBOUGHT:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='sell',
                    strength=min(1.0, (rsi_value - config.RSI_OVERBOUGHT) / (100 - config.RSI_OVERBOUGHT)),
                    indicator='RSI',
                    value=rsi_value,
                    threshold=config.RSI_OVERBOUGHT,
                    confidence=0.7
                ))
        
        # MACD Signals
        macd, macd_signal, macd_diff = self.calculate_macd(close)
        if not macd.empty and not pd.isna(macd.iloc[-1]):
            if macd.iloc[-1] > macd_signal.iloc[-1] and macd.iloc[-2] <= macd_signal.iloc[-2]:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='buy',
                    strength=0.8,
                    indicator='MACD',
                    value=macd_diff.iloc[-1],
                    threshold=0,
                    confidence=0.8
                ))
            elif macd.iloc[-1] < macd_signal.iloc[-1] and macd.iloc[-2] >= macd_signal.iloc[-2]:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='sell',
                    strength=0.8,
                    indicator='MACD',
                    value=macd_diff.iloc[-1],
                    threshold=0,
                    confidence=0.8
                ))
        
        # Bollinger Bands Signals
        bb_upper, bb_lower, bb_middle = self.calculate_bollinger_bands(close, config.BOLLINGER_PERIOD, config.BOLLINGER_STD)
        if not bb_upper.empty and not pd.isna(bb_upper.iloc[-1]):
            current_price = close.iloc[-1]
            if current_price <= bb_lower.iloc[-1]:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='buy',
                    strength=0.9,
                    indicator='Bollinger_Bands',
                    value=current_price,
                    threshold=bb_lower.iloc[-1],
                    confidence=0.8
                ))
            elif current_price >= bb_upper.iloc[-1]:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='sell',
                    strength=0.9,
                    indicator='Bollinger_Bands',
                    value=current_price,
                    threshold=bb_upper.iloc[-1],
                    confidence=0.8
                ))
        
        # Moving Average Crossover
        sma_short = self.calculate_sma(close, config.SHORT_MA_PERIOD)
        sma_long = self.calculate_sma(close, config.LONG_MA_PERIOD)
        if not sma_short.empty and not sma_long.empty:
            if sma_short.iloc[-1] > sma_long.iloc[-1] and sma_short.iloc[-2] <= sma_long.iloc[-2]:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='buy',
                    strength=0.7,
                    indicator='MA_Crossover',
                    value=sma_short.iloc[-1] - sma_long.iloc[-1],
                    threshold=0,
                    confidence=0.6
                ))
            elif sma_short.iloc[-1] < sma_long.iloc[-1] and sma_short.iloc[-2] >= sma_long.iloc[-2]:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='sell',
                    strength=0.7,
                    indicator='MA_Crossover',
                    value=sma_short.iloc[-1] - sma_long.iloc[-1],
                    threshold=0,
                    confidence=0.6
                ))
        
        # Stochastic Signals
        stoch_k, stoch_d = self.calculate_stochastic(high, low, close)
        if not stoch_k.empty and not pd.isna(stoch_k.iloc[-1]):
            if stoch_k.iloc[-1] < 20 and stoch_d.iloc[-1] < 20:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='buy',
                    strength=0.8,
                    indicator='Stochastic',
                    value=stoch_k.iloc[-1],
                    threshold=20,
                    confidence=0.7
                ))
            elif stoch_k.iloc[-1] > 80 and stoch_d.iloc[-1] > 80:
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=df.index[-1],
                    signal_type='sell',
                    strength=0.8,
                    indicator='Stochastic',
                    value=stoch_k.iloc[-1],
                    threshold=80,
                    confidence=0.7
                ))
        
        return signals
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for a dataframe"""
        if len(df) < 50:
            return df
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # Moving Averages
        df['sma_10'] = self.calculate_sma(close, 10)
        df['sma_20'] = self.calculate_sma(close, 20)
        df['sma_50'] = self.calculate_sma(close, 50)
        df['sma_200'] = self.calculate_sma(close, 200)
        df['ema_12'] = self.calculate_ema(close, 12)
        df['ema_26'] = self.calculate_ema(close, 26)
        
        # Momentum Indicators
        df['rsi'] = self.calculate_rsi(close, 14)
        df['stoch_k'], df['stoch_d'] = self.calculate_stochastic(high, low, close)
        df['williams_r'] = self.calculate_williams_r(high, low, close)
        
        # Trend Indicators
        df['macd'], df['macd_signal'], df['macd_diff'] = self.calculate_macd(close)
        df['adx'] = self.calculate_adx(high, low, close)
        df['cci'] = self.calculate_cci(high, low, close)
        
        # Volatility Indicators
        df['bb_upper'], df['bb_lower'], df['bb_middle'] = self.calculate_bollinger_bands(close)
        df['atr'] = self.calculate_atr(high, low, close)
        
        # Volume Indicators
        df['obv'] = self.calculate_obv(close, volume)
        df['vwap'] = self.calculate_vwap(high, low, close, volume)
        
        # Additional Indicators
        df['momentum'] = self.calculate_momentum(close, 10)
        df['roc'] = self.calculate_rate_of_change(close, 10)
        df['volatility'] = self.calculate_volatility(close, 20)
        
        return df
    
    def get_signal_summary(self, signals: List[Signal]) -> Dict:
        """Get summary of all signals"""
        if not signals:
            return {'signal': 'hold', 'strength': 0.0, 'confidence': 0.0}
        
        buy_signals = [s for s in signals if s.signal_type == 'buy']
        sell_signals = [s for s in signals if s.signal_type == 'sell']
        
        buy_strength = sum(s.strength * s.confidence for s in buy_signals) if buy_signals else 0
        sell_strength = sum(s.strength * s.confidence for s in sell_signals) if sell_signals else 0
        
        if buy_strength > sell_strength and buy_strength > 0.5:
            return {
                'signal': 'buy',
                'strength': buy_strength,
                'confidence': np.mean([s.confidence for s in buy_signals]),
                'indicators': [s.indicator for s in buy_signals]
            }
        elif sell_strength > buy_strength and sell_strength > 0.5:
            return {
                'signal': 'sell',
                'strength': sell_strength,
                'confidence': np.mean([s.confidence for s in sell_signals]),
                'indicators': [s.indicator for s in sell_signals]
            }
        else:
            return {
                'signal': 'hold',
                'strength': max(buy_strength, sell_strength),
                'confidence': 0.0,
                'indicators': []
            }