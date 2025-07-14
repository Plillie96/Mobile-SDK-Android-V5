"""
Advanced Trading Strategies for the Kraken Bot
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import config, STRATEGY_CONFIGS

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.enabled = True
        self.last_signal = None
        self.performance_history = []
        
    @abstractmethod
    async def generate_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on strategy logic"""
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Dict[str, Any], balance: float) -> float:
        """Calculate position size based on signal strength and risk"""
        pass
    
    def update_performance(self, trade_result: Dict[str, Any]):
        """Update strategy performance metrics"""
        self.performance_history.append(trade_result)
        
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics for the strategy"""
        if not self.performance_history:
            return {}
        
        returns = [trade['return'] for trade in self.performance_history]
        return {
            'total_return': sum(returns),
            'avg_return': np.mean(returns),
            'std_return': np.std(returns),
            'sharpe_ratio': np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0,
            'win_rate': len([r for r in returns if r > 0]) / len(returns),
            'max_drawdown': min(returns),
            'total_trades': len(returns)
        }

class MeanReversionStrategy(BaseStrategy):
    """Mean Reversion Strategy based on Bollinger Bands and RSI"""
    
    def __init__(self, lookback_period: int = 20, threshold: float = 2.0):
        super().__init__("mean_reversion", STRATEGY_CONFIGS["mean_reversion"]["weight"])
        self.lookback_period = lookback_period
        self.threshold = threshold
        
    async def generate_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mean reversion signal"""
        df = data.get('ohlcv', pd.DataFrame())
        if df.empty or len(df) < self.lookback_period:
            return {'signal': 'hold', 'strength': 0, 'confidence': 0}
        
        # Calculate indicators
        close_prices = df['close']
        sma = close_prices.rolling(window=self.lookback_period).mean()
        std = close_prices.rolling(window=self.lookback_period).std()
        
        # Bollinger Bands
        upper_band = sma + (self.threshold * std)
        lower_band = sma - (self.threshold * std)
        
        current_price = close_prices.iloc[-1]
        
        # Generate signals
        if current_price < lower_band.iloc[-1]:
            signal = 'buy'
            strength = (lower_band.iloc[-1] - current_price) / current_price
            confidence = min(strength * 10, 1.0)
        elif current_price > upper_band.iloc[-1]:
            signal = 'sell'
            strength = (current_price - upper_band.iloc[-1]) / current_price
            confidence = min(strength * 10, 1.0)
        else:
            signal = 'hold'
            strength = 0
            confidence = 0
            
        return {
            'signal': signal,
            'strength': strength,
            'confidence': confidence,
            'price': current_price,
            'sma': sma.iloc[-1],
            'upper_band': upper_band.iloc[-1],
            'lower_band': lower_band.iloc[-1]
        }
    
    def calculate_position_size(self, signal: Dict[str, Any], balance: float) -> float:
        """Calculate position size based on signal strength"""
        if signal['signal'] == 'hold':
            return 0
        
        base_size = balance * config.MAX_POSITION_SIZE
        strength_multiplier = signal['strength'] * 2  # Scale strength to reasonable position size
        return min(base_size * strength_multiplier, balance * 0.5)  # Max 50% of balance

class MomentumStrategy(BaseStrategy):
    """Momentum Strategy based on price momentum and volume"""
    
    def __init__(self, lookback_period: int = 10, threshold: float = 0.02):
        super().__init__("momentum", STRATEGY_CONFIGS["momentum"]["weight"])
        self.lookback_period = lookback_period
        self.threshold = threshold
        
    async def generate_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate momentum signal"""
        df = data.get('ohlcv', pd.DataFrame())
        if df.empty or len(df) < self.lookback_period:
            return {'signal': 'hold', 'strength': 0, 'confidence': 0}
        
        # Calculate momentum indicators
        close_prices = df['close']
        returns = close_prices.pct_change()
        
        # Price momentum
        price_momentum = returns.rolling(window=self.lookback_period).mean()
        
        # Volume momentum
        volume = df.get('volume', pd.Series([1] * len(df)))
        volume_ma = volume.rolling(window=self.lookback_period).mean()
        volume_ratio = volume.iloc[-1] / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1
        
        current_momentum = price_momentum.iloc[-1]
        
        # Generate signals
        if current_momentum > self.threshold and volume_ratio > 1.2:
            signal = 'buy'
            strength = current_momentum / self.threshold
            confidence = min(strength * 0.5, 1.0)
        elif current_momentum < -self.threshold and volume_ratio > 1.2:
            signal = 'sell'
            strength = abs(current_momentum) / self.threshold
            confidence = min(strength * 0.5, 1.0)
        else:
            signal = 'hold'
            strength = 0
            confidence = 0
            
        return {
            'signal': signal,
            'strength': strength,
            'confidence': confidence,
            'momentum': current_momentum,
            'volume_ratio': volume_ratio,
            'price': close_prices.iloc[-1]
        }
    
    def calculate_position_size(self, signal: Dict[str, Any], balance: float) -> float:
        """Calculate position size based on momentum strength"""
        if signal['signal'] == 'hold':
            return 0
        
        base_size = balance * config.MAX_POSITION_SIZE
        strength_multiplier = signal['strength'] * 1.5
        return min(base_size * strength_multiplier, balance * 0.4)

class ArbitrageStrategy(BaseStrategy):
    """Arbitrage Strategy for price differences across exchanges"""
    
    def __init__(self, min_spread: float = 0.001):
        super().__init__("arbitrage", STRATEGY_CONFIGS["arbitrage"]["weight"])
        self.min_spread = min_spread
        self.exchanges = ['kraken', 'binance', 'coinbase']  # Add more exchanges as needed
        
    async def generate_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate arbitrage signal"""
        # This would require real-time data from multiple exchanges
        # For now, we'll simulate arbitrage opportunities
        
        current_price = data.get('current_price', 0)
        if current_price == 0:
            return {'signal': 'hold', 'strength': 0, 'confidence': 0}
        
        # Simulate price differences (in real implementation, fetch from multiple exchanges)
        price_variations = np.random.normal(0, 0.002, len(self.exchanges))
        prices = [current_price * (1 + var) for var in price_variations]
        
        min_price = min(prices)
        max_price = max(prices)
        spread = (max_price - min_price) / min_price
        
        if spread > self.min_spread:
            signal = 'arbitrage'
            strength = spread / self.min_spread
            confidence = min(strength * 0.3, 1.0)
        else:
            signal = 'hold'
            strength = 0
            confidence = 0
            
        return {
            'signal': signal,
            'strength': strength,
            'confidence': confidence,
            'spread': spread,
            'min_price': min_price,
            'max_price': max_price
        }
    
    def calculate_position_size(self, signal: Dict[str, Any], balance: float) -> float:
        """Calculate position size for arbitrage"""
        if signal['signal'] != 'arbitrage':
            return 0
        
        # Arbitrage positions can be larger due to lower risk
        base_size = balance * config.MAX_POSITION_SIZE * 2
        strength_multiplier = signal['strength'] * 0.5
        return min(base_size * strength_multiplier, balance * 0.3)

class SentimentStrategy(BaseStrategy):
    """Sentiment-based Strategy using news and social media"""
    
    def __init__(self, news_weight: float = 0.6, social_weight: float = 0.4):
        super().__init__("sentiment", STRATEGY_CONFIGS["sentiment"]["weight"])
        self.news_weight = news_weight
        self.social_weight = social_weight
        
    async def generate_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sentiment-based signal"""
        # Get sentiment data
        news_sentiment = data.get('news_sentiment', 0)
        social_sentiment = data.get('social_sentiment', 0)
        
        # Calculate weighted sentiment
        weighted_sentiment = (
            news_sentiment * self.news_weight +
            social_sentiment * self.social_weight
        )
        
        # Generate signals based on sentiment
        if weighted_sentiment > 0.3:
            signal = 'buy'
            strength = weighted_sentiment
            confidence = min(strength * 0.8, 1.0)
        elif weighted_sentiment < -0.3:
            signal = 'sell'
            strength = abs(weighted_sentiment)
            confidence = min(strength * 0.8, 1.0)
        else:
            signal = 'hold'
            strength = 0
            confidence = 0
            
        return {
            'signal': signal,
            'strength': strength,
            'confidence': confidence,
            'weighted_sentiment': weighted_sentiment,
            'news_sentiment': news_sentiment,
            'social_sentiment': social_sentiment
        }
    
    def calculate_position_size(self, signal: Dict[str, Any], balance: float) -> float:
        """Calculate position size based on sentiment strength"""
        if signal['signal'] == 'hold':
            return 0
        
        base_size = balance * config.MAX_POSITION_SIZE
        strength_multiplier = signal['strength'] * 1.2
        return min(base_size * strength_multiplier, balance * 0.3)

class GridTradingStrategy(BaseStrategy):
    """Grid Trading Strategy for range-bound markets"""
    
    def __init__(self, grid_levels: int = 10, grid_spacing: float = 0.02):
        super().__init__("grid_trading", 0.2)
        self.grid_levels = grid_levels
        self.grid_spacing = grid_spacing
        self.grid_orders = {}
        
    async def generate_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate grid trading signal"""
        current_price = data.get('current_price', 0)
        if current_price == 0:
            return {'signal': 'hold', 'strength': 0, 'confidence': 0}
        
        # Calculate grid levels
        grid_prices = []
        for i in range(-self.grid_levels//2, self.grid_levels//2 + 1):
            grid_price = current_price * (1 + i * self.grid_spacing)
            grid_prices.append(grid_price)
        
        # Find nearest grid levels
        nearest_buy = max([p for p in grid_prices if p < current_price], default=0)
        nearest_sell = min([p for p in grid_prices if p > current_price], default=0)
        
        # Calculate distance to nearest levels
        buy_distance = (current_price - nearest_buy) / current_price if nearest_buy > 0 else 1
        sell_distance = (nearest_sell - current_price) / current_price if nearest_sell > 0 else 1
        
        # Generate signals
        if buy_distance < self.grid_spacing * 0.5:
            signal = 'buy'
            strength = 1 - (buy_distance / self.grid_spacing)
            confidence = 0.7
        elif sell_distance < self.grid_spacing * 0.5:
            signal = 'sell'
            strength = 1 - (sell_distance / self.grid_spacing)
            confidence = 0.7
        else:
            signal = 'hold'
            strength = 0
            confidence = 0
            
        return {
            'signal': signal,
            'strength': strength,
            'confidence': confidence,
            'current_price': current_price,
            'nearest_buy': nearest_buy,
            'nearest_sell': nearest_sell,
            'grid_prices': grid_prices
        }
    
    def calculate_position_size(self, signal: Dict[str, Any], balance: float) -> float:
        """Calculate position size for grid trading"""
        if signal['signal'] == 'hold':
            return 0
        
        # Grid trading uses smaller, consistent position sizes
        base_size = balance * config.MAX_POSITION_SIZE * 0.5
        return base_size

class StrategyManager:
    """Manages multiple trading strategies and combines their signals"""
    
    def __init__(self):
        self.strategies = {
            'mean_reversion': MeanReversionStrategy(),
            'momentum': MomentumStrategy(),
            'arbitrage': ArbitrageStrategy(),
            'sentiment': SentimentStrategy(),
            'grid_trading': GridTradingStrategy()
        }
        
    async def get_combined_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine signals from all strategies"""
        signals = {}
        total_weight = 0
        
        for name, strategy in self.strategies.items():
            if strategy.enabled:
                try:
                    signal = await strategy.generate_signal(data)
                    signals[name] = signal
                    total_weight += strategy.weight
                except Exception as e:
                    print(f"Error in strategy {name}: {e}")
                    continue
        
        if not signals or total_weight == 0:
            return {'signal': 'hold', 'strength': 0, 'confidence': 0}
        
        # Combine signals weighted by strategy weights
        buy_strength = 0
        sell_strength = 0
        total_confidence = 0
        
        for name, signal in signals.items():
            weight = self.strategies[name].weight / total_weight
            
            if signal['signal'] == 'buy':
                buy_strength += signal['strength'] * weight * signal['confidence']
            elif signal['signal'] == 'sell':
                sell_strength += signal['strength'] * weight * signal['confidence']
            
            total_confidence += signal['confidence'] * weight
        
        # Determine final signal
        if buy_strength > sell_strength and buy_strength > 0.1:
            final_signal = 'buy'
            final_strength = buy_strength
        elif sell_strength > buy_strength and sell_strength > 0.1:
            final_signal = 'sell'
            final_strength = sell_strength
        else:
            final_signal = 'hold'
            final_strength = 0
        
        return {
            'signal': final_signal,
            'strength': final_strength,
            'confidence': total_confidence,
            'strategy_signals': signals,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all strategies"""
        performance = {}
        for name, strategy in self.strategies.items():
            performance[name] = strategy.get_performance_metrics()
        return performance
    
    def enable_strategy(self, strategy_name: str):
        """Enable a specific strategy"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].enabled = True
    
    def disable_strategy(self, strategy_name: str):
        """Disable a specific strategy"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].enabled = False