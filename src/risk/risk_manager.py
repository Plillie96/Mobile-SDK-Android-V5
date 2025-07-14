"""
Risk Management System for the Kraken Trading Bot
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import sys
import os

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import config

@dataclass
class Position:
    """Position data structure"""
    symbol: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    current_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        if self.side == 'long':
            return (self.current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.current_price) * self.size
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Calculate unrealized P&L percentage"""
        if self.side == 'long':
            return (self.current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - self.current_price) / self.entry_price

@dataclass
class Trade:
    """Trade data structure"""
    symbol: str
    side: str
    size: float
    price: float
    timestamp: datetime
    order_id: str
    fees: float = 0.0
    
    @property
    def value(self) -> float:
        """Calculate trade value"""
        return self.size * self.price

class RiskManager:
    """Advanced risk management system"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.max_drawdown = 0.0
        self.peak_balance = 0.0
        self.current_balance = 0.0
        self.risk_metrics = {}
        
    def update_balance(self, balance: float):
        """Update current balance and calculate drawdown"""
        self.current_balance = balance
        if balance > self.peak_balance:
            self.peak_balance = balance
        
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - balance) / self.peak_balance
            self.max_drawdown = max(self.max_drawdown, drawdown)
    
    def calculate_position_size(self, signal: Dict[str, Any], balance: float, 
                              symbol: str, current_price: float) -> float:
        """Calculate optimal position size based on risk parameters"""
        
        # Base position size from signal strength
        base_size = balance * config.MAX_POSITION_SIZE
        
        # Adjust for signal strength and confidence
        strength_multiplier = signal.get('strength', 0) * signal.get('confidence', 0)
        adjusted_size = base_size * strength_multiplier
        
        # Risk-based position sizing using Kelly Criterion
        win_rate = self.get_historical_win_rate(symbol)
        avg_win = self.get_average_win(symbol)
        avg_loss = self.get_average_loss(symbol)
        
        if avg_loss > 0 and win_rate > 0:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            adjusted_size *= kelly_fraction
        
        # Volatility adjustment
        volatility = self.get_volatility(symbol)
        if volatility > 0:
            volatility_adjustment = 1 / (1 + volatility)
            adjusted_size *= volatility_adjustment
        
        # Correlation adjustment
        correlation_penalty = self.get_correlation_penalty(symbol)
        adjusted_size *= (1 - correlation_penalty)
        
        # Ensure minimum trade size
        if adjusted_size * current_price < config.MIN_TRADE_AMOUNT:
            return 0
        
        # Ensure maximum position size
        max_position_value = balance * 0.5  # Max 50% of balance in single position
        max_size = max_position_value / current_price
        
        return min(adjusted_size, max_size)
    
    def calculate_stop_loss(self, entry_price: float, side: str, atr: float) -> float:
        """Calculate dynamic stop loss based on ATR"""
        atr_multiplier = 2.0  # 2x ATR for stop loss
        
        if side == 'long':
            stop_loss = entry_price - (atr * atr_multiplier)
        else:
            stop_loss = entry_price + (atr * atr_multiplier)
        
        return stop_loss
    
    def calculate_take_profit(self, entry_price: float, side: str, 
                            risk_reward_ratio: float = 2.0) -> float:
        """Calculate take profit based on risk-reward ratio"""
        if side == 'long':
            take_profit = entry_price + (entry_price * config.TAKE_PROFIT_PERCENTAGE * risk_reward_ratio)
        else:
            take_profit = entry_price - (entry_price * config.TAKE_PROFIT_PERCENTAGE * risk_reward_ratio)
        
        return take_profit
    
    def update_trailing_stop(self, position: Position, current_price: float):
        """Update trailing stop for a position"""
        if not config.TRAILING_STOP:
            return
        
        if position.side == 'long':
            new_trailing_stop = current_price * (1 - config.TRAILING_STOP_PERCENTAGE)
            if position.trailing_stop is None or new_trailing_stop > position.trailing_stop:
                position.trailing_stop = new_trailing_stop
        else:
            new_trailing_stop = current_price * (1 + config.TRAILING_STOP_PERCENTAGE)
            if position.trailing_stop is None or new_trailing_stop < position.trailing_stop:
                position.trailing_stop = new_trailing_stop
    
    def check_stop_loss(self, position: Position, current_price: float) -> bool:
        """Check if stop loss has been triggered"""
        if position.stop_loss is None:
            return False
        
        if position.side == 'long':
            return current_price <= position.stop_loss
        else:
            return current_price >= position.stop_loss
    
    def check_take_profit(self, position: Position, current_price: float) -> bool:
        """Check if take profit has been triggered"""
        if position.take_profit is None:
            return False
        
        if position.side == 'long':
            return current_price >= position.take_profit
        else:
            return current_price <= position.take_profit
    
    def check_trailing_stop(self, position: Position, current_price: float) -> bool:
        """Check if trailing stop has been triggered"""
        if position.trailing_stop is None:
            return False
        
        if position.side == 'long':
            return current_price <= position.trailing_stop
        else:
            return current_price >= position.trailing_stop
    
    def can_open_position(self, symbol: str, side: str, size: float, 
                         current_price: float) -> Tuple[bool, str]:
        """Check if we can open a new position"""
        
        # Check daily loss limit
        if self.daily_pnl < -(self.current_balance * config.MAX_DAILY_LOSS):
            return False, "Daily loss limit exceeded"
        
        # Check daily trade limit
        if self.daily_trades >= config.MAX_DAILY_TRADES:
            return False, "Daily trade limit exceeded"
        
        # Check position concentration
        total_position_value = sum(
            pos.size * pos.current_price for pos in self.positions.values()
        )
        new_position_value = size * current_price
        
        if (total_position_value + new_position_value) > (self.current_balance * 0.8):
            return False, "Position concentration limit exceeded"
        
        # Check symbol-specific limits
        symbol_positions = [pos for pos in self.positions.values() if pos.symbol == symbol]
        symbol_value = sum(pos.size * pos.current_price for pos in symbol_positions)
        
        if (symbol_value + new_position_value) > (self.current_balance * 0.3):
            return False, "Symbol concentration limit exceeded"
        
        return True, "Position allowed"
    
    def add_position(self, symbol: str, side: str, size: float, 
                    entry_price: float, stop_loss: float = None, 
                    take_profit: float = None) -> Position:
        """Add a new position"""
        position = Position(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=entry_price,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        return position
    
    def close_position(self, symbol: str, exit_price: float, 
                      exit_time: datetime = None) -> Optional[Trade]:
        """Close a position and record the trade"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        exit_time = exit_time or datetime.now()
        
        # Calculate trade details
        trade = Trade(
            symbol=symbol,
            side='sell' if position.side == 'long' else 'buy',
            size=position.size,
            price=exit_price,
            timestamp=exit_time,
            order_id=f"close_{symbol}_{exit_time.timestamp()}"
        )
        
        # Calculate P&L
        pnl = position.unrealized_pnl
        self.daily_pnl += pnl
        self.daily_trades += 1
        
        # Update balance
        self.update_balance(self.current_balance + pnl)
        
        # Remove position
        del self.positions[symbol]
        
        # Add to trade history
        self.trades.append(trade)
        
        return trade
    
    def update_position_prices(self, price_updates: Dict[str, float]):
        """Update current prices for all positions"""
        for symbol, price in price_updates.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
                self.update_trailing_stop(self.positions[symbol], price)
    
    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        if not self.positions:
            return {}
        
        total_value = sum(pos.size * pos.current_price for pos in self.positions.values())
        total_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        # Calculate portfolio beta (simplified)
        portfolio_beta = 1.0  # Placeholder - would need market data
        
        # Calculate VaR (Value at Risk)
        returns = [pos.unrealized_pnl_percent for pos in self.positions.values()]
        if returns:
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
        else:
            var_95 = var_99 = 0
        
        return {
            'total_positions': len(self.positions),
            'total_value': total_value,
            'total_pnl': total_pnl,
            'portfolio_beta': portfolio_beta,
            'var_95': var_95,
            'var_99': var_99,
            'max_drawdown': self.max_drawdown,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades
        }
    
    def get_historical_win_rate(self, symbol: str) -> float:
        """Get historical win rate for a symbol"""
        symbol_trades = [t for t in self.trades if t.symbol == symbol]
        if not symbol_trades:
            return 0.5  # Default to 50%
        
        winning_trades = len([t for t in symbol_trades if t.value > 0])
        return winning_trades / len(symbol_trades)
    
    def get_average_win(self, symbol: str) -> float:
        """Get average winning trade size for a symbol"""
        symbol_trades = [t for t in self.trades if t.symbol == symbol and t.value > 0]
        if not symbol_trades:
            return 0.02  # Default 2% win
        
        return np.mean([t.value for t in symbol_trades])
    
    def get_average_loss(self, symbol: str) -> float:
        """Get average losing trade size for a symbol"""
        symbol_trades = [t for t in self.trades if t.symbol == symbol and t.value < 0]
        if not symbol_trades:
            return 0.01  # Default 1% loss
        
        return abs(np.mean([t.value for t in symbol_trades]))
    
    def get_volatility(self, symbol: str) -> float:
        """Get historical volatility for a symbol"""
        symbol_trades = [t for t in self.trades if t.symbol == symbol]
        if len(symbol_trades) < 2:
            return 0.02  # Default 2% volatility
        
        returns = [t.value for t in symbol_trades]
        return np.std(returns)
    
    def get_correlation_penalty(self, symbol: str) -> float:
        """Calculate correlation penalty for portfolio diversification"""
        if len(self.positions) < 2:
            return 0
        
        # Simplified correlation calculation
        # In a real implementation, you'd calculate actual correlations
        return 0.1  # 10% penalty for correlation
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of new day)"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        portfolio_metrics = self.get_portfolio_metrics()
        
        return {
            'portfolio_metrics': portfolio_metrics,
            'positions': {
                symbol: {
                    'side': pos.side,
                    'size': pos.size,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'unrealized_pnl_percent': pos.unrealized_pnl_percent,
                    'stop_loss': pos.stop_loss,
                    'take_profit': pos.take_profit,
                    'trailing_stop': pos.trailing_stop
                }
                for symbol, pos in self.positions.items()
            },
            'risk_limits': {
                'max_position_size': config.MAX_POSITION_SIZE,
                'max_daily_loss': config.MAX_DAILY_LOSS,
                'max_daily_trades': config.MAX_DAILY_TRADES,
                'stop_loss_percentage': config.STOP_LOSS_PERCENTAGE,
                'take_profit_percentage': config.TAKE_PROFIT_PERCENTAGE
            },
            'current_balance': self.current_balance,
            'peak_balance': self.peak_balance,
            'max_drawdown': self.max_drawdown
        }