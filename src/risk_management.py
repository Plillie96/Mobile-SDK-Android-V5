"""
Risk Management Module
Handles position sizing, stop losses, and portfolio protection
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger

from config import config


@dataclass
class Position:
    """Position data structure"""
    symbol: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class RiskMetrics:
    """Risk metrics data structure"""
    total_value: float
    total_pnl: float
    daily_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    volatility: float
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    beta: float
    correlation: float


class RiskManager:
    """Risk Management Engine"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.daily_pnl_history: List[float] = []
        self.max_drawdown = 0.0
        self.peak_value = 0.0
        self.daily_loss = 0.0
        self.trade_count = 0
        
    def calculate_position_size(self, account_value: float, risk_per_trade: float, 
                              entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk management rules"""
        if stop_loss is None or stop_loss == entry_price:
            return 0.0
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            return 0.0
        
        # Calculate dollar risk
        dollar_risk = account_value * risk_per_trade
        
        # Calculate position size
        position_size = dollar_risk / risk_per_share
        
        # Apply maximum position size limit
        max_position_value = account_value * config.MAX_POSITION_SIZE
        max_position_size = max_position_value / entry_price
        
        return min(position_size, max_position_size)
    
    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly Criterion for position sizing"""
        if avg_loss == 0:
            return 0.0
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        return max(0.0, min(kelly_fraction, 0.25))  # Cap at 25%
    
    def calculate_stop_loss(self, entry_price: float, side: str, atr: float, 
                           atr_multiplier: float = 2.0) -> float:
        """Calculate dynamic stop loss based on ATR"""
        if side == 'long':
            return entry_price - (atr * atr_multiplier)
        else:
            return entry_price + (atr * atr_multiplier)
    
    def calculate_take_profit(self, entry_price: float, side: str, 
                            risk_reward_ratio: float, stop_loss: float) -> float:
        """Calculate take profit based on risk-reward ratio"""
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        if side == 'long':
            return entry_price + reward
        else:
            return entry_price - reward
    
    def check_risk_limits(self, account_value: float, new_position_value: float) -> bool:
        """Check if new position violates risk limits"""
        # Check maximum position size
        if new_position_value > account_value * config.MAX_POSITION_SIZE:
            logger.warning(f"Position size {new_position_value} exceeds maximum {account_value * config.MAX_POSITION_SIZE}")
            return False
        
        # Check maximum daily trades
        if self.trade_count >= config.MAX_DAILY_TRADES:
            logger.warning(f"Daily trade limit {config.MAX_DAILY_TRADES} reached")
            return False
        
        # Check daily loss limit
        if self.daily_loss < -(account_value * config.DAILY_LOSS_LIMIT):
            logger.warning(f"Daily loss limit {config.DAILY_LOSS_LIMIT} exceeded")
            return False
        
        # Check maximum drawdown
        if self.max_drawdown > config.MAX_DRAWDOWN:
            logger.warning(f"Maximum drawdown {config.MAX_DRAWDOWN} exceeded")
            return False
        
        return True
    
    def update_position(self, symbol: str, side: str, size: float, 
                       entry_price: float, current_price: float,
                       stop_loss: Optional[float] = None, 
                       take_profit: Optional[float] = None):
        """Update position information"""
        unrealized_pnl = self.calculate_unrealized_pnl(side, size, entry_price, current_price)
        
        self.positions[symbol] = Position(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=0.0,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now()
        )
    
    def calculate_unrealized_pnl(self, side: str, size: float, 
                                entry_price: float, current_price: float) -> float:
        """Calculate unrealized P&L"""
        if side == 'long':
            return (current_price - entry_price) * size
        else:
            return (entry_price - current_price) * size
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """Check if stop loss has been triggered"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        if position.stop_loss is None:
            return False
        
        if position.side == 'long' and current_price <= position.stop_loss:
            logger.info(f"Stop loss triggered for {symbol} at {current_price}")
            return True
        elif position.side == 'short' and current_price >= position.stop_loss:
            logger.info(f"Stop loss triggered for {symbol} at {current_price}")
            return True
        
        return False
    
    def check_take_profit(self, symbol: str, current_price: float) -> bool:
        """Check if take profit has been triggered"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        if position.take_profit is None:
            return False
        
        if position.side == 'long' and current_price >= position.take_profit:
            logger.info(f"Take profit triggered for {symbol} at {current_price}")
            return True
        elif position.side == 'short' and current_price <= position.take_profit:
            logger.info(f"Take profit triggered for {symbol} at {current_price}")
            return True
        
        return False
    
    def calculate_portfolio_metrics(self, account_value: float, 
                                  market_data: Dict[str, float]) -> RiskMetrics:
        """Calculate comprehensive portfolio risk metrics"""
        # Update positions with current prices
        total_pnl = 0.0
        for symbol, position in self.positions.items():
            if symbol in market_data:
                current_price = market_data[symbol]
                position.current_price = current_price
                position.unrealized_pnl = self.calculate_unrealized_pnl(
                    position.side, position.size, position.entry_price, current_price
                )
                total_pnl += position.unrealized_pnl
        
        # Calculate daily P&L
        daily_pnl = total_pnl - sum(self.daily_pnl_history[-1:]) if self.daily_pnl_history else total_pnl
        self.daily_pnl_history.append(daily_pnl)
        
        # Update drawdown
        current_value = account_value + total_pnl
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        drawdown = (self.peak_value - current_value) / self.peak_value if self.peak_value > 0 else 0
        self.max_drawdown = max(self.max_drawdown, drawdown)
        
        # Calculate volatility
        if len(self.daily_pnl_history) > 1:
            volatility = np.std(self.daily_pnl_history)
        else:
            volatility = 0.0
        
        # Calculate Sharpe ratio (simplified)
        if volatility > 0:
            sharpe_ratio = np.mean(self.daily_pnl_history) / volatility
        else:
            sharpe_ratio = 0.0
        
        # Calculate Value at Risk
        if len(self.daily_pnl_history) > 10:
            var_95 = np.percentile(self.daily_pnl_history, 5)
            var_99 = np.percentile(self.daily_pnl_history, 1)
        else:
            var_95 = 0.0
            var_99 = 0.0
        
        return RiskMetrics(
            total_value=current_value,
            total_pnl=total_pnl,
            daily_pnl=daily_pnl,
            max_drawdown=self.max_drawdown,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            var_95=var_95,
            var_99=var_99,
            beta=0.0,  # Would need market data to calculate
            correlation=0.0  # Would need market data to calculate
        )
    
    def calculate_correlation_matrix(self, price_data: Dict[str, pd.Series]) -> pd.DataFrame:
        """Calculate correlation matrix for portfolio assets"""
        if not price_data:
            return pd.DataFrame()
        
        # Convert price data to returns
        returns_data = {}
        for symbol, prices in price_data.items():
            if len(prices) > 1:
                returns_data[symbol] = prices.pct_change().dropna()
        
        if not returns_data:
            return pd.DataFrame()
        
        # Create correlation matrix
        returns_df = pd.DataFrame(returns_data)
        return returns_df.corr()
    
    def calculate_portfolio_beta(self, portfolio_returns: pd.Series, 
                               market_returns: pd.Series) -> float:
        """Calculate portfolio beta relative to market"""
        if len(portfolio_returns) < 2 or len(market_returns) < 2:
            return 0.0
        
        # Align the series
        aligned_data = pd.concat([portfolio_returns, market_returns], axis=1).dropna()
        if len(aligned_data) < 2:
            return 0.0
        
        portfolio_ret = aligned_data.iloc[:, 0]
        market_ret = aligned_data.iloc[:, 1]
        
        # Calculate beta
        covariance = np.cov(portfolio_ret, market_ret)[0][1]
        market_variance = np.var(market_ret)
        
        return covariance / market_variance if market_variance != 0 else 0.0
    
    def calculate_optimal_position_sizes(self, account_value: float, 
                                       signals: Dict[str, Dict],
                                       price_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """Calculate optimal position sizes using modern portfolio theory"""
        if not signals or not price_data:
            return {}
        
        # Calculate expected returns and volatility
        expected_returns = {}
        volatilities = {}
        
        for symbol in signals.keys():
            if symbol in price_data and len(price_data[symbol]) > 20:
                returns = price_data[symbol].pct_change().dropna()
                expected_returns[symbol] = returns.mean() * 252  # Annualized
                volatilities[symbol] = returns.std() * np.sqrt(252)  # Annualized
        
        if not expected_returns:
            return {}
        
        # Calculate correlation matrix
        correlation_matrix = self.calculate_correlation_matrix(price_data)
        
        # Simple equal weight allocation for now
        # In a more sophisticated implementation, you would use optimization
        num_assets = len(expected_returns)
        equal_weight = 1.0 / num_assets
        
        position_sizes = {}
        for symbol in expected_returns.keys():
            # Adjust weight based on signal strength
            signal_strength = signals[symbol].get('strength', 0.5)
            adjusted_weight = equal_weight * signal_strength
            
            # Calculate position size in currency terms
            position_value = account_value * adjusted_weight * config.MAX_POSITION_SIZE
            
            # Convert to asset units
            current_price = price_data[symbol].iloc[-1]
            position_sizes[symbol] = position_value / current_price
        
        return position_sizes
    
    def apply_risk_parity(self, account_value: float, 
                         price_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """Apply risk parity allocation"""
        if not price_data:
            return {}
        
        # Calculate volatilities
        volatilities = {}
        for symbol, prices in price_data.items():
            if len(prices) > 20:
                returns = prices.pct_change().dropna()
                volatilities[symbol] = returns.std() * np.sqrt(252)
        
        if not volatilities:
            return {}
        
        # Calculate risk parity weights
        total_risk = sum(1 / vol for vol in volatilities.values())
        risk_weights = {symbol: (1 / vol) / total_risk for symbol, vol in volatilities.items()}
        
        # Calculate position sizes
        position_sizes = {}
        for symbol, weight in risk_weights.items():
            position_value = account_value * weight
            current_price = price_data[symbol].iloc[-1]
            position_sizes[symbol] = position_value / current_price
        
        return position_sizes
    
    def calculate_margin_requirements(self, positions: Dict[str, Position], 
                                    leverage: float = 1.0) -> float:
        """Calculate margin requirements for positions"""
        total_margin = 0.0
        
        for position in positions.values():
            position_value = position.size * position.current_price
            margin_required = position_value / leverage
            total_margin += margin_required
        
        return total_margin
    
    def check_margin_call(self, account_value: float, margin_required: float, 
                         margin_buffer: float = 0.1) -> bool:
        """Check if margin call is needed"""
        available_margin = account_value * (1 - margin_buffer)
        return margin_required > available_margin
    
    def get_risk_report(self, account_value: float, 
                       market_data: Dict[str, float]) -> Dict:
        """Generate comprehensive risk report"""
        metrics = self.calculate_portfolio_metrics(account_value, market_data)
        
        # Calculate position concentration
        total_position_value = sum(
            pos.size * pos.current_price for pos in self.positions.values()
        )
        
        concentration_risk = {}
        for symbol, position in self.positions.items():
            position_value = position.size * position.current_price
            concentration_risk[symbol] = position_value / total_position_value if total_position_value > 0 else 0
        
        return {
            'metrics': {
                'total_value': metrics.total_value,
                'total_pnl': metrics.total_pnl,
                'daily_pnl': metrics.daily_pnl,
                'max_drawdown': metrics.max_drawdown,
                'sharpe_ratio': metrics.sharpe_ratio,
                'volatility': metrics.volatility,
                'var_95': metrics.var_95,
                'var_99': metrics.var_99
            },
            'positions': {
                symbol: {
                    'size': pos.size,
                    'value': pos.size * pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'stop_loss': pos.stop_loss,
                    'take_profit': pos.take_profit
                }
                for symbol, pos in self.positions.items()
            },
            'concentration_risk': concentration_risk,
            'risk_limits': {
                'max_position_size': config.MAX_POSITION_SIZE,
                'max_drawdown': config.MAX_DRAWDOWN,
                'daily_loss_limit': config.DAILY_LOSS_LIMIT,
                'max_daily_trades': config.MAX_DAILY_TRADES
            },
            'current_limits': {
                'current_drawdown': metrics.max_drawdown,
                'daily_loss': metrics.daily_pnl,
                'trade_count': self.trade_count
            }
        }