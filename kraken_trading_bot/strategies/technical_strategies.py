"""
Technical analysis-based trading strategies
"""
import pandas as pd
import numpy as np
import ta
from typing import Dict, Any
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """RSI-based trading strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'period': 14,
            'oversold': 30,
            'overbought': 70,
            'rsi_threshold': 0.1
        }
        if parameters:
            default_params.update(parameters)
        super().__init__('RSI', default_params)
    
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(data):
            return {'signal': 'hold', 'confidence': 0.0, 'reason': 'insufficient_data'}
        
        # Calculate RSI
        rsi = ta.momentum.RSIIndicator(
            close=data['close'], 
            window=self.parameters['period']
        ).rsi()
        
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
        
        # Generate signal
        if current_rsi < self.parameters['oversold'] and prev_rsi >= self.parameters['oversold']:
            signal = 'buy'
            confidence = min(1.0, (self.parameters['oversold'] - current_rsi) / self.parameters['oversold'])
        elif current_rsi > self.parameters['overbought'] and prev_rsi <= self.parameters['overbought']:
            signal = 'sell'
            confidence = min(1.0, (current_rsi - self.parameters['overbought']) / (100 - self.parameters['overbought']))
        else:
            signal = 'hold'
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'rsi_value': current_rsi,
            'reason': f'RSI: {current_rsi:.2f}'
        }
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        signal = self.generate_signal(data)
        return signal['confidence']

class MACDStrategy(BaseStrategy):
    """MACD-based trading strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'threshold': 0.0001
        }
        if parameters:
            default_params.update(parameters)
        super().__init__('MACD', default_params)
    
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(data):
            return {'signal': 'hold', 'confidence': 0.0, 'reason': 'insufficient_data'}
        
        # Calculate MACD
        macd = ta.trend.MACD(
            close=data['close'],
            window_fast=self.parameters['fast_period'],
            window_slow=self.parameters['slow_period'],
            window_sign=self.parameters['signal_period']
        )
        
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        histogram = macd.macd_diff()
        
        current_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2] if len(histogram) > 1 else current_hist
        
        # Generate signal
        if current_hist > self.parameters['threshold'] and prev_hist <= self.parameters['threshold']:
            signal = 'buy'
            confidence = min(1.0, abs(current_hist) / abs(current_hist) + 0.001)
        elif current_hist < -self.parameters['threshold'] and prev_hist >= -self.parameters['threshold']:
            signal = 'sell'
            confidence = min(1.0, abs(current_hist) / abs(current_hist) + 0.001)
        else:
            signal = 'hold'
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'macd_value': macd_line.iloc[-1],
            'signal_value': signal_line.iloc[-1],
            'histogram': current_hist,
            'reason': f'MACD Histogram: {current_hist:.6f}'
        }
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        signal = self.generate_signal(data)
        return signal['confidence']

class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands-based trading strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'period': 20,
            'std_dev': 2.0,
            'threshold': 0.02
        }
        if parameters:
            default_params.update(parameters)
        super().__init__('BollingerBands', default_params)
    
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(data):
            return {'signal': 'hold', 'confidence': 0.0, 'reason': 'insufficient_data'}
        
        # Calculate Bollinger Bands
        bb = ta.volatility.BollingerBands(
            close=data['close'],
            window=self.parameters['period'],
            window_dev=self.parameters['std_dev']
        )
        
        upper_band = bb.bollinger_hband()
        lower_band = bb.bollinger_lband()
        middle_band = bb.bollinger_mavg()
        
        current_price = data['close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # Calculate position within bands
        band_width = current_upper - current_lower
        position = (current_price - current_lower) / band_width if band_width > 0 else 0.5
        
        # Generate signal
        if current_price <= current_lower * (1 + self.parameters['threshold']):
            signal = 'buy'
            confidence = min(1.0, (current_lower - current_price) / current_lower)
        elif current_price >= current_upper * (1 - self.parameters['threshold']):
            signal = 'sell'
            confidence = min(1.0, (current_price - current_upper) / current_upper)
        else:
            signal = 'hold'
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'position_in_bands': position,
            'upper_band': current_upper,
            'lower_band': current_lower,
            'middle_band': middle_band.iloc[-1],
            'reason': f'Price position in BB: {position:.2f}'
        }
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        signal = self.generate_signal(data)
        return signal['confidence']

class VolumeStrategy(BaseStrategy):
    """Volume-based trading strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'period': 20,
            'volume_threshold': 1.5,
            'price_change_threshold': 0.01
        }
        if parameters:
            default_params.update(parameters)
        super().__init__('Volume', default_params)
    
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(data):
            return {'signal': 'hold', 'confidence': 0.0, 'reason': 'insufficient_data'}
        
        # Calculate volume metrics
        avg_volume = data['volume'].rolling(window=self.parameters['period']).mean()
        current_volume = data['volume'].iloc[-1]
        current_avg_volume = avg_volume.iloc[-1]
        
        # Calculate price change
        price_change = data['close'].pct_change().iloc[-1]
        
        # Volume ratio
        volume_ratio = current_volume / current_avg_volume if current_avg_volume > 0 else 1.0
        
        # Generate signal
        if (volume_ratio > self.parameters['volume_threshold'] and 
            abs(price_change) > self.parameters['price_change_threshold']):
            
            if price_change > 0:
                signal = 'buy'
                confidence = min(1.0, volume_ratio / (volume_ratio + 1))
            else:
                signal = 'sell'
                confidence = min(1.0, volume_ratio / (volume_ratio + 1))
        else:
            signal = 'hold'
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'volume_ratio': volume_ratio,
            'price_change': price_change,
            'current_volume': current_volume,
            'avg_volume': current_avg_volume,
            'reason': f'Volume ratio: {volume_ratio:.2f}, Price change: {price_change:.2%}'
        }
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        signal = self.generate_signal(data)
        return signal['confidence']

class MovingAverageStrategy(BaseStrategy):
    """Moving Average crossover strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'fast_period': 10,
            'slow_period': 30,
            'ma_type': 'sma'  # 'sma', 'ema'
        }
        if parameters:
            default_params.update(parameters)
        super().__init__('MovingAverage', default_params)
    
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(data):
            return {'signal': 'hold', 'confidence': 0.0, 'reason': 'insufficient_data'}
        
        # Calculate moving averages
        if self.parameters['ma_type'] == 'ema':
            fast_ma = ta.trend.EMAIndicator(close=data['close'], window=self.parameters['fast_period']).ema_indicator()
            slow_ma = ta.trend.EMAIndicator(close=data['close'], window=self.parameters['slow_period']).ema_indicator()
        else:
            fast_ma = ta.trend.SMAIndicator(close=data['close'], window=self.parameters['fast_period']).sma_indicator()
            slow_ma = ta.trend.SMAIndicator(close=data['close'], window=self.parameters['slow_period']).sma_indicator()
        
        current_fast = fast_ma.iloc[-1]
        current_slow = slow_ma.iloc[-1]
        prev_fast = fast_ma.iloc[-2] if len(fast_ma) > 1 else current_fast
        prev_slow = slow_ma.iloc[-2] if len(slow_ma) > 1 else current_slow
        
        # Check for crossover
        crossover_up = prev_fast <= prev_slow and current_fast > current_slow
        crossover_down = prev_fast >= prev_slow and current_fast < current_slow
        
        # Calculate confidence based on distance between MAs
        ma_distance = abs(current_fast - current_slow) / current_slow if current_slow > 0 else 0
        
        if crossover_up:
            signal = 'buy'
            confidence = min(1.0, ma_distance * 10)  # Scale up the distance
        elif crossover_down:
            signal = 'sell'
            confidence = min(1.0, ma_distance * 10)
        else:
            signal = 'hold'
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'fast_ma': current_fast,
            'slow_ma': current_slow,
            'ma_distance': ma_distance,
            'reason': f'{self.parameters["ma_type"].upper()} Crossover - Fast: {current_fast:.2f}, Slow: {current_slow:.2f}'
        }
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        signal = self.generate_signal(data)
        return signal['confidence']