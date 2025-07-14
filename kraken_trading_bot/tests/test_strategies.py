"""
Unit tests for trading strategies
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import strategies
from strategies.technical_strategies import (
    RSIStrategy, MACDStrategy, BollingerBandsStrategy,
    VolumeStrategy, MovingAverageStrategy
)

class TestRSIStrategy:
    """Test RSI strategy"""
    
    def setup_method(self):
        """Setup test data"""
        # Create sample OHLCV data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        np.random.seed(42)
        
        # Generate realistic price data
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        self.test_data = pd.DataFrame({
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        self.strategy = RSIStrategy()
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        signal = self.strategy.generate_signal(self.test_data)
        
        assert 'signal' in signal
        assert 'confidence' in signal
        assert 'rsi_value' in signal
        assert signal['signal'] in ['buy', 'sell', 'hold']
        assert 0 <= signal['confidence'] <= 1
        assert 0 <= signal['rsi_value'] <= 100
    
    def test_rsi_oversold_signal(self):
        """Test RSI oversold signal generation"""
        # Create data with declining prices to trigger oversold
        declining_data = self.test_data.copy()
        declining_data['close'] = declining_data['close'] * 0.8  # 20% decline
        
        signal = self.strategy.generate_signal(declining_data)
        
        # Should generate buy signal when RSI is oversold
        if signal['rsi_value'] < self.strategy.parameters['oversold']:
            assert signal['signal'] in ['buy', 'hold']
    
    def test_rsi_overbought_signal(self):
        """Test RSI overbought signal generation"""
        # Create data with rising prices to trigger overbought
        rising_data = self.test_data.copy()
        rising_data['close'] = rising_data['close'] * 1.2  # 20% increase
        
        signal = self.strategy.generate_signal(rising_data)
        
        # Should generate sell signal when RSI is overbought
        if signal['rsi_value'] > self.strategy.parameters['overbought']:
            assert signal['signal'] in ['sell', 'hold']

class TestMACDStrategy:
    """Test MACD strategy"""
    
    def setup_method(self):
        """Setup test data"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        np.random.seed(42)
        
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        self.test_data = pd.DataFrame({
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        self.strategy = MACDStrategy()
    
    def test_macd_signal_generation(self):
        """Test MACD signal generation"""
        signal = self.strategy.generate_signal(self.test_data)
        
        assert 'signal' in signal
        assert 'confidence' in signal
        assert 'macd_value' in signal
        assert 'signal_value' in signal
        assert 'histogram' in signal
        assert signal['signal'] in ['buy', 'sell', 'hold']
        assert 0 <= signal['confidence'] <= 1
    
    def test_macd_histogram_crossover(self):
        """Test MACD histogram crossover detection"""
        # Create data with clear trend
        trend_data = self.test_data.copy()
        trend_data['close'] = trend_data['close'] * (1 + np.linspace(0, 0.1, 100))
        
        signal = self.strategy.generate_signal(trend_data)
        
        # Should detect trend and generate appropriate signal
        assert signal['signal'] in ['buy', 'sell', 'hold']

class TestBollingerBandsStrategy:
    """Test Bollinger Bands strategy"""
    
    def setup_method(self):
        """Setup test data"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        np.random.seed(42)
        
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        self.test_data = pd.DataFrame({
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        self.strategy = BollingerBandsStrategy()
    
    def test_bollinger_bands_signal(self):
        """Test Bollinger Bands signal generation"""
        signal = self.strategy.generate_signal(self.test_data)
        
        assert 'signal' in signal
        assert 'confidence' in signal
        assert 'position_in_bands' in signal
        assert 'upper_band' in signal
        assert 'lower_band' in signal
        assert 'middle_band' in signal
        assert signal['signal'] in ['buy', 'sell', 'hold']
        assert 0 <= signal['confidence'] <= 1
        assert 0 <= signal['position_in_bands'] <= 1
    
    def test_bollinger_bands_extremes(self):
        """Test Bollinger Bands at extreme positions"""
        # Test price at lower band
        lower_band_data = self.test_data.copy()
        lower_band_data['close'] = lower_band_data['close'] * 0.9  # 10% decline
        
        signal = self.strategy.generate_signal(lower_band_data)
        
        # Should generate buy signal when price is near lower band
        if signal['position_in_bands'] < 0.2:
            assert signal['signal'] in ['buy', 'hold']

class TestVolumeStrategy:
    """Test Volume strategy"""
    
    def setup_method(self):
        """Setup test data"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        np.random.seed(42)
        
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        self.test_data = pd.DataFrame({
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        self.strategy = VolumeStrategy()
    
    def test_volume_signal_generation(self):
        """Test Volume signal generation"""
        signal = self.strategy.generate_signal(self.test_data)
        
        assert 'signal' in signal
        assert 'confidence' in signal
        assert 'volume_ratio' in signal
        assert 'price_change' in signal
        assert 'current_volume' in signal
        assert 'avg_volume' in signal
        assert signal['signal'] in ['buy', 'sell', 'hold']
        assert 0 <= signal['confidence'] <= 1
    
    def test_high_volume_signal(self):
        """Test high volume signal detection"""
        # Create data with high volume
        high_volume_data = self.test_data.copy()
        high_volume_data['volume'] = high_volume_data['volume'] * 2  # Double volume
        
        signal = self.strategy.generate_signal(high_volume_data)
        
        # Should detect high volume
        assert signal['volume_ratio'] > 1.0

class TestMovingAverageStrategy:
    """Test Moving Average strategy"""
    
    def setup_method(self):
        """Setup test data"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        np.random.seed(42)
        
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        self.test_data = pd.DataFrame({
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        self.strategy = MovingAverageStrategy()
    
    def test_moving_average_signal(self):
        """Test Moving Average signal generation"""
        signal = self.strategy.generate_signal(self.test_data)
        
        assert 'signal' in signal
        assert 'confidence' in signal
        assert 'fast_ma' in signal
        assert 'slow_ma' in signal
        assert 'ma_distance' in signal
        assert signal['signal'] in ['buy', 'sell', 'hold']
        assert 0 <= signal['confidence'] <= 1
    
    def test_moving_average_crossover(self):
        """Test Moving Average crossover detection"""
        # Create data with clear trend for crossover
        trend_data = self.test_data.copy()
        trend_data['close'] = trend_data['close'] * (1 + np.linspace(0, 0.15, 100))
        
        signal = self.strategy.generate_signal(trend_data)
        
        # Should detect trend and generate appropriate signal
        assert signal['signal'] in ['buy', 'sell', 'hold']

class TestStrategyValidation:
    """Test strategy data validation"""
    
    def test_empty_data(self):
        """Test strategy with empty data"""
        strategy = RSIStrategy()
        empty_data = pd.DataFrame()
        
        signal = strategy.generate_signal(empty_data)
        assert signal['signal'] == 'hold'
        assert signal['reason'] == 'insufficient_data'
    
    def test_insufficient_data(self):
        """Test strategy with insufficient data"""
        strategy = RSIStrategy()
        insufficient_data = pd.DataFrame({
            'open': [100] * 10,
            'high': [101] * 10,
            'low': [99] * 10,
            'close': [100] * 10,
            'volume': [1000] * 10
        })
        
        signal = strategy.generate_signal(insufficient_data)
        assert signal['signal'] == 'hold'
        assert signal['reason'] == 'insufficient_data'
    
    def test_missing_columns(self):
        """Test strategy with missing columns"""
        strategy = RSIStrategy()
        incomplete_data = pd.DataFrame({
            'open': [100] * 50,
            'close': [100] * 50
        })
        
        signal = strategy.generate_signal(incomplete_data)
        assert signal['signal'] == 'hold'
        assert signal['reason'] == 'insufficient_data'

if __name__ == "__main__":
    pytest.main([__file__])