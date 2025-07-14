"""
Risk management system for the Kraken Trading Bot
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from config import config

@dataclass
class Position:
    """Position data class"""
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    current_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0

@dataclass
class RiskMetrics:
    """Risk metrics data class"""
    total_pnl: float
    daily_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int
    volatility: float
    var_95: float  # 95% Value at Risk

class RiskManager:
    """Advanced risk management system"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_balance = 0.0
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        
        # Risk limits
        self.max_position_size = config.max_position_size
        self.max_daily_loss = config.max_daily_loss
        self.stop_loss_pct = config.stop_loss_pct
        self.take_profit_pct = config.take_profit_pct
        
        # Emergency stop conditions
        self.emergency_stop_conditions = EMERGENCY_STOP_CONDITIONS
        
    def calculate_position_size(self, balance: float, price: float, risk_pct: float = None) -> float:
        """
        Calculate position size based on risk management rules
        
        Args:
            balance: Available balance
            price: Current asset price
            risk_pct: Risk percentage (optional)
            
        Returns:
            Position size in asset units
        """
        if risk_pct is None:
            risk_pct = self.max_position_size
        
        # Calculate position size based on risk
        position_value = balance * risk_pct
        position_size = position_value / price
        
        # Apply additional risk checks
        if self.daily_pnl < -balance * self.max_daily_loss:
            logger.warning("Daily loss limit reached, reducing position size")
            position_size *= 0.5
        
        if self.consecutive_losses >= 3:
            logger.warning("Consecutive losses detected, reducing position size")
            position_size *= 0.7
        
        return position_size
    
    def check_risk_limits(self, symbol: str, side: str, quantity: float, price: float) -> Tuple[bool, str]:
        """
        Check if trade meets risk management criteria
        
        Args:
            symbol: Trading symbol
            side: Trade side ('buy' or 'sell')
            quantity: Trade quantity
            price: Trade price
            
        Returns:
            Tuple of (allowed, reason)
        """
        # Check daily loss limit
        if self.daily_pnl < -self.peak_balance * self.max_daily_loss:
            return False, "Daily loss limit exceeded"
        
        # Check consecutive losses
        if self.consecutive_losses >= self.emergency_stop_conditions['max_consecutive_losses']:
            return False, "Maximum consecutive losses reached"
        
        # Check maximum drawdown
        current_drawdown = (self.peak_balance - (self.peak_balance + self.total_pnl)) / self.peak_balance
        if current_drawdown > self.emergency_stop_conditions['max_drawdown']:
            return False, "Maximum drawdown exceeded"
        
        # Check position size limit
        position_value = quantity * price
        if position_value > self.peak_balance * self.max_position_size:
            return False, "Position size exceeds limit"
        
        # Check if we already have a position in this symbol
        if symbol in self.positions:
            current_position = self.positions[symbol]
            if current_position.side == side:
                return False, "Already have position in same direction"
        
        return True, "Trade allowed"
    
    def add_position(self, symbol: str, side: str, quantity: float, price: float,
                    stop_loss: float = None, take_profit: float = None):
        """
        Add a new position
        
        Args:
            symbol: Trading symbol
            side: Position side ('long' or 'short')
            quantity: Position quantity
            price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=price,
            current_price=price,
            entry_time=datetime.utcnow(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        logger.info(f"Position opened: {side} {quantity} {symbol} @ {price}")
    
    def update_position(self, symbol: str, current_price: float):
        """
        Update position with current price
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
        """
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position.current_price = current_price
        
        # Calculate PnL
        if position.side == 'long':
            position.pnl = (current_price - position.entry_price) * position.quantity
            position.pnl_pct = (current_price - position.entry_price) / position.entry_price
        else:  # short
            position.pnl = (position.entry_price - current_price) * position.quantity
            position.pnl_pct = (position.entry_price - current_price) / position.entry_price
    
    def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> Optional[str]:
        """
        Check if stop loss or take profit should be triggered
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            Action to take ('close', 'stop_loss', 'take_profit') or None
        """
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        # Check stop loss
        if position.stop_loss:
            if (position.side == 'long' and current_price <= position.stop_loss) or \
               (position.side == 'short' and current_price >= position.stop_loss):
                return 'stop_loss'
        
        # Check take profit
        if position.take_profit:
            if (position.side == 'long' and current_price >= position.take_profit) or \
               (position.side == 'short' and current_price <= position.take_profit):
                return 'take_profit'
        
        # Check percentage-based stops
        if abs(position.pnl_pct) >= self.stop_loss_pct:
            return 'stop_loss'
        
        if position.pnl_pct >= self.take_profit_pct:
            return 'take_profit'
        
        return None
    
    def close_position(self, symbol: str, price: float, reason: str = "manual"):
        """
        Close a position
        
        Args:
            symbol: Trading symbol
            price: Closing price
            reason: Reason for closing
        """
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculate final PnL
        if position.side == 'long':
            pnl = (price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - price) * position.quantity
        
        # Update metrics
        self.total_pnl += pnl
        self.daily_pnl += pnl
        
        if pnl > 0:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
        
        # Update peak balance
        current_balance = self.peak_balance + self.total_pnl
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        # Calculate drawdown
        current_drawdown = (self.peak_balance - current_balance) / self.peak_balance
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # Record trade
        trade_record = {
            'symbol': symbol,
            'side': position.side,
            'entry_price': position.entry_price,
            'exit_price': price,
            'quantity': position.quantity,
            'pnl': pnl,
            'pnl_pct': pnl / (position.entry_price * position.quantity),
            'entry_time': position.entry_time,
            'exit_time': datetime.utcnow(),
            'reason': reason
        }
        
        self.trade_history.append(trade_record)
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"Position closed: {position.side} {position.quantity} {symbol} @ {price}, PnL: {pnl:.2f}")
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics
        
        Returns:
            RiskMetrics object
        """
        if not self.trade_history:
            return RiskMetrics(
                total_pnl=0.0, daily_pnl=0.0, max_drawdown=0.0, sharpe_ratio=0.0,
                win_rate=0.0, profit_factor=0.0, total_trades=0, winning_trades=0,
                losing_trades=0, avg_win=0.0, avg_loss=0.0, largest_win=0.0,
                largest_loss=0.0, consecutive_wins=0, consecutive_losses=0,
                volatility=0.0, var_95=0.0
            )
        
        # Calculate basic metrics
        total_trades = len(self.trade_history)
        winning_trades = len([t for t in self.trade_history if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Calculate profit/loss metrics
        wins = [t['pnl'] for t in self.trade_history if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trade_history if t['pnl'] < 0]
        
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0
        
        profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else float('inf')
        
        # Calculate Sharpe ratio
        returns = [t['pnl_pct'] for t in self.trade_history]
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0
            volatility = std_return
            var_95 = np.percentile(returns, 5)
        else:
            sharpe_ratio = 0.0
            volatility = 0.0
            var_95 = 0.0
        
        return RiskMetrics(
            total_pnl=self.total_pnl,
            daily_pnl=self.daily_pnl,
            max_drawdown=self.max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            consecutive_wins=self.consecutive_wins,
            consecutive_losses=self.consecutive_losses,
            volatility=volatility,
            var_95=var_95
        )
    
    def should_stop_trading(self) -> Tuple[bool, str]:
        """
        Check if trading should be stopped due to risk conditions
        
        Returns:
            Tuple of (should_stop, reason)
        """
        # Check daily loss limit
        if self.daily_pnl < -self.peak_balance * self.emergency_stop_conditions['max_daily_loss']:
            return True, "Daily loss limit exceeded"
        
        # Check consecutive losses
        if self.consecutive_losses >= self.emergency_stop_conditions['max_consecutive_losses']:
            return True, "Maximum consecutive losses reached"
        
        # Check maximum drawdown
        current_drawdown = (self.peak_balance - (self.peak_balance + self.total_pnl)) / self.peak_balance
        if current_drawdown > self.emergency_stop_conditions['max_drawdown']:
            return True, "Maximum drawdown exceeded"
        
        return False, "Trading allowed"
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of new day)"""
        self.daily_pnl = 0.0
        logger.info("Daily metrics reset")
    
    def get_position_summary(self) -> Dict[str, Any]:
        """
        Get summary of current positions
        
        Returns:
            Dictionary with position summary
        """
        summary = {
            'total_positions': len(self.positions),
            'total_value': 0.0,
            'total_pnl': 0.0,
            'positions': {}
        }
        
        for symbol, position in self.positions.items():
            position_value = position.quantity * position.current_price
            summary['total_value'] += position_value
            summary['total_pnl'] += position.pnl
            
            summary['positions'][symbol] = {
                'side': position.side,
                'quantity': position.quantity,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'pnl': position.pnl,
                'pnl_pct': position.pnl_pct,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit
            }
        
        return summary
    
    def get_trade_history_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get trade history summary for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with trade history summary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_trades = [t for t in self.trade_history if t['exit_time'] >= cutoff_date]
        
        if not recent_trades:
            return {'total_trades': 0, 'total_pnl': 0.0, 'win_rate': 0.0}
        
        total_trades = len(recent_trades)
        total_pnl = sum(t['pnl'] for t in recent_trades)
        winning_trades = len([t for t in recent_trades if t['pnl'] > 0])
        win_rate = winning_trades / total_trades
        
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_pnl_per_trade': total_pnl / total_trades
        }