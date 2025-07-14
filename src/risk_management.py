"""
Risk Management Module
Handles position sizing, stop losses, and portfolio protection
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

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
    pnl: float = 0.0
    pnl_percentage: float = 0.0

@dataclass
class RiskMetrics:
    """Risk metrics data structure"""
    total_pnl: float
    total_pnl_percentage: float
    daily_pnl: float
    daily_pnl_percentage: float
    max_drawdown: float
    sharpe_ratio: float
    volatility: float
    var_95: float  # Value at Risk (95%)
    position_count: int
    open_positions: int

class RiskManager:
    """Advanced Risk Management System"""
    
    def __init__(self, config):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.daily_pnl_history: List[float] = []
        self.max_daily_loss = config.max_daily_loss
        self.max_position_size = config.max_position_size
        self.stop_loss_percentage = config.stop_loss_percentage
        self.take_profit_percentage = config.take_profit_percentage
        
    def calculate_position_size(self, portfolio_value: float, symbol: str, 
                              signal_strength: float, volatility: float) -> float:
        """Calculate optimal position size using Kelly Criterion and risk management"""
        try:
            # Base position size from config
            base_size = portfolio_value * self.max_position_size
            
            # Adjust for signal strength (0-1)
            signal_adjustment = min(1.0, max(0.1, signal_strength))
            
            # Adjust for volatility (higher volatility = smaller position)
            volatility_adjustment = max(0.1, 1 - volatility)
            
            # Kelly Criterion adjustment
            win_rate = 0.55  # Estimated win rate
            avg_win = 0.04   # Average win percentage
            avg_loss = 0.02  # Average loss percentage
            
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly_fraction = max(0, min(0.25, kelly_fraction))  # Cap at 25%
            
            # Calculate final position size
            position_size = base_size * signal_adjustment * volatility_adjustment * kelly_fraction
            
            # Ensure minimum and maximum limits
            min_position = portfolio_value * 0.01  # 1% minimum
            max_position = portfolio_value * self.max_position_size
            
            position_size = max(min_position, min(max_position, position_size))
            
            logger.info(f"Position size for {symbol}: {position_size:.2f} "
                       f"(signal: {signal_strength:.2f}, vol: {volatility:.2f})")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return portfolio_value * 0.01  # Default to 1%
    
    def calculate_stop_loss(self, entry_price: float, side: str, 
                          atr: float, volatility: float) -> float:
        """Calculate dynamic stop loss based on ATR and volatility"""
        try:
            # Base stop loss from config
            base_stop_distance = entry_price * self.stop_loss_percentage
            
            # ATR-based stop loss (2x ATR)
            atr_stop_distance = atr * 2
            
            # Volatility-based stop loss
            vol_stop_distance = entry_price * volatility * 1.5
            
            # Use the most conservative stop loss
            stop_distance = max(base_stop_distance, atr_stop_distance, vol_stop_distance)
            
            if side == 'long':
                stop_loss = entry_price - stop_distance
            else:  # short
                stop_loss = entry_price + stop_distance
            
            logger.info(f"Stop loss for {side} position: {stop_loss:.4f} "
                       f"(distance: {stop_distance:.4f})")
            
            return stop_loss
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            # Fallback to simple percentage-based stop loss
            if side == 'long':
                return entry_price * (1 - self.stop_loss_percentage)
            else:
                return entry_price * (1 + self.stop_loss_percentage)
    
    def calculate_take_profit(self, entry_price: float, side: str, 
                            risk_reward_ratio: float = 2.0) -> float:
        """Calculate take profit based on risk-reward ratio"""
        try:
            # Calculate stop loss distance
            stop_distance = abs(entry_price - self.calculate_stop_loss(entry_price, side, 0, 0.02))
            
            # Take profit distance = stop distance * risk-reward ratio
            profit_distance = stop_distance * risk_reward_ratio
            
            if side == 'long':
                take_profit = entry_price + profit_distance
            else:  # short
                take_profit = entry_price - profit_distance
            
            logger.info(f"Take profit for {side} position: {take_profit:.4f} "
                       f"(distance: {profit_distance:.4f})")
            
            return take_profit
            
        except Exception as e:
            logger.error(f"Error calculating take profit: {e}")
            # Fallback to simple percentage-based take profit
            if side == 'long':
                return entry_price * (1 + self.take_profit_percentage)
            else:
                return entry_price * (1 - self.take_profit_percentage)
    
    def check_risk_limits(self, portfolio_value: float, new_position_value: float) -> Dict[str, Any]:
        """Check if new position violates risk limits"""
        try:
            # Calculate current portfolio exposure
            total_exposure = sum(pos.size * pos.current_price for pos in self.positions.values())
            new_total_exposure = total_exposure + new_position_value
            
            # Check position size limit
            position_size_limit = portfolio_value * self.max_position_size
            position_size_ok = new_position_value <= position_size_limit
            
            # Check total exposure limit (max 50% of portfolio)
            exposure_limit = portfolio_value * 0.5
            exposure_ok = new_total_exposure <= exposure_limit
            
            # Check daily loss limit
            daily_pnl = self.calculate_daily_pnl()
            daily_loss_ok = daily_pnl >= -(portfolio_value * self.max_daily_loss)
            
            # Check correlation limits (simplified)
            correlation_ok = self.check_correlation_limits()
            
            risk_check = {
                'position_size_ok': position_size_ok,
                'exposure_ok': exposure_ok,
                'daily_loss_ok': daily_loss_ok,
                'correlation_ok': correlation_ok,
                'overall_ok': position_size_ok and exposure_ok and daily_loss_ok and correlation_ok,
                'reasons': []
            }
            
            if not position_size_ok:
                risk_check['reasons'].append(f"Position size {new_position_value:.2f} exceeds limit {position_size_limit:.2f}")
            if not exposure_ok:
                risk_check['reasons'].append(f"Total exposure {new_total_exposure:.2f} exceeds limit {exposure_limit:.2f}")
            if not daily_loss_ok:
                risk_check['reasons'].append(f"Daily loss {daily_pnl:.2f} exceeds limit {portfolio_value * self.max_daily_loss:.2f}")
            if not correlation_ok:
                risk_check['reasons'].append("Correlation limits exceeded")
            
            return risk_check
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return {'overall_ok': False, 'reasons': [f"Error: {e}"]}
    
    def check_correlation_limits(self) -> bool:
        """Check if positions are too correlated (simplified)"""
        try:
            # For now, just check if we have too many positions in the same asset class
            crypto_positions = sum(1 for pos in self.positions.values() if 'USD' in pos.symbol)
            
            # Limit to 3 crypto positions
            return crypto_positions < 3
            
        except Exception as e:
            logger.error(f"Error checking correlation limits: {e}")
            return True
    
    def update_position(self, symbol: str, current_price: float, timestamp: datetime) -> Dict[str, Any]:
        """Update position with current market data"""
        try:
            if symbol not in self.positions:
                return {'action': 'none', 'reason': 'Position not found'}
            
            position = self.positions[symbol]
            position.current_price = current_price
            
            # Calculate P&L
            if position.side == 'long':
                position.pnl = (current_price - position.entry_price) * position.size
                position.pnl_percentage = (current_price - position.entry_price) / position.entry_price
            else:  # short
                position.pnl = (position.entry_price - current_price) * position.size
                position.pnl_percentage = (position.entry_price - current_price) / position.entry_price
            
            # Check stop loss
            if position.stop_loss:
                if (position.side == 'long' and current_price <= position.stop_loss) or \
                   (position.side == 'short' and current_price >= position.stop_loss):
                    return {
                        'action': 'close',
                        'reason': 'Stop loss triggered',
                        'pnl': position.pnl,
                        'pnl_percentage': position.pnl_percentage
                    }
            
            # Check take profit
            if position.take_profit:
                if (position.side == 'long' and current_price >= position.take_profit) or \
                   (position.side == 'short' and current_price <= position.take_profit):
                    return {
                        'action': 'close',
                        'reason': 'Take profit triggered',
                        'pnl': position.pnl,
                        'pnl_percentage': position.pnl_percentage
                    }
            
            # Check trailing stop (if implemented)
            trailing_action = self.check_trailing_stop(position, current_price)
            if trailing_action['action'] == 'close':
                return trailing_action
            
            return {'action': 'hold', 'pnl': position.pnl, 'pnl_percentage': position.pnl_percentage}
            
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            return {'action': 'none', 'reason': f'Error: {e}'}
    
    def check_trailing_stop(self, position: Position, current_price: float) -> Dict[str, Any]:
        """Check trailing stop loss (simplified implementation)"""
        try:
            # Simple trailing stop: if profit > 2%, move stop loss to breakeven
            if position.pnl_percentage > 0.02:
                if position.side == 'long':
                    new_stop = max(position.stop_loss or 0, position.entry_price)
                else:
                    new_stop = min(position.stop_loss or float('inf'), position.entry_price)
                
                if new_stop != position.stop_loss:
                    position.stop_loss = new_stop
                    logger.info(f"Updated trailing stop for {position.symbol} to {new_stop:.4f}")
            
            return {'action': 'hold'}
            
        except Exception as e:
            logger.error(f"Error checking trailing stop: {e}")
            return {'action': 'hold'}
    
    def add_position(self, symbol: str, side: str, size: float, entry_price: float,
                    stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> bool:
        """Add new position to tracking"""
        try:
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
            logger.info(f"Added {side} position for {symbol}: size={size:.4f}, price={entry_price:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding position: {e}")
            return False
    
    def close_position(self, symbol: str, close_price: float) -> Dict[str, Any]:
        """Close position and return P&L"""
        try:
            if symbol not in self.positions:
                return {'success': False, 'reason': 'Position not found'}
            
            position = self.positions[symbol]
            
            # Calculate final P&L
            if position.side == 'long':
                pnl = (close_price - position.entry_price) * position.size
                pnl_percentage = (close_price - position.entry_price) / position.entry_price
            else:  # short
                pnl = (position.entry_price - close_price) * position.size
                pnl_percentage = (position.entry_price - close_price) / position.entry_price
            
            # Remove position
            del self.positions[symbol]
            
            # Add to daily P&L history
            self.daily_pnl_history.append(pnl)
            
            logger.info(f"Closed {position.side} position for {symbol}: "
                       f"P&L={pnl:.2f} ({pnl_percentage:.2%})")
            
            return {
                'success': True,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage,
                'duration': datetime.now() - position.entry_time
            }
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {'success': False, 'reason': f'Error: {e}'}
    
    def calculate_daily_pnl(self) -> float:
        """Calculate today's P&L"""
        try:
            today = datetime.now().date()
            today_pnl = 0.0
            
            # P&L from closed positions today
            for pnl in self.daily_pnl_history[-100:]:  # Last 100 trades
                today_pnl += pnl
            
            # P&L from open positions
            for position in self.positions.values():
                today_pnl += position.pnl
            
            return today_pnl
            
        except Exception as e:
            logger.error(f"Error calculating daily P&L: {e}")
            return 0.0
    
    def get_risk_metrics(self, portfolio_value: float) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        try:
            # Calculate total P&L
            total_pnl = sum(pos.pnl for pos in self.positions.values())
            total_pnl_percentage = total_pnl / portfolio_value if portfolio_value > 0 else 0
            
            # Daily P&L
            daily_pnl = self.calculate_daily_pnl()
            daily_pnl_percentage = daily_pnl / portfolio_value if portfolio_value > 0 else 0
            
            # Calculate volatility from P&L history
            if len(self.daily_pnl_history) > 1:
                volatility = np.std(self.daily_pnl_history) / portfolio_value
            else:
                volatility = 0.0
            
            # Calculate Sharpe ratio (simplified)
            if volatility > 0:
                sharpe_ratio = (total_pnl_percentage - 0.02) / volatility  # Assuming 2% risk-free rate
            else:
                sharpe_ratio = 0.0
            
            # Calculate Value at Risk (95%)
            if len(self.daily_pnl_history) > 10:
                var_95 = np.percentile(self.daily_pnl_history, 5)
            else:
                var_95 = -portfolio_value * 0.05  # Conservative estimate
            
            # Calculate max drawdown
            max_drawdown = self.calculate_max_drawdown()
            
            return RiskMetrics(
                total_pnl=total_pnl,
                total_pnl_percentage=total_pnl_percentage,
                daily_pnl=daily_pnl,
                daily_pnl_percentage=daily_pnl_percentage,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                volatility=volatility,
                var_95=var_95,
                position_count=len(self.positions),
                open_positions=len([p for p in self.positions.values() if p.pnl != 0])
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from P&L history"""
        try:
            if not self.daily_pnl_history:
                return 0.0
            
            cumulative_pnl = np.cumsum(self.daily_pnl_history)
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdown = cumulative_pnl - running_max
            
            return float(np.min(drawdown))
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def emergency_stop(self) -> List[str]:
        """Emergency stop - close all positions"""
        try:
            symbols_to_close = list(self.positions.keys())
            logger.warning(f"Emergency stop triggered. Closing {len(symbols_to_close)} positions.")
            return symbols_to_close
            
        except Exception as e:
            logger.error(f"Error in emergency stop: {e}")
            return []