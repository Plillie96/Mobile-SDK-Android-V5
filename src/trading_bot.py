"""
Main Trading Bot
Orchestrates all components and implements trading strategies
"""
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from config import config, STRATEGIES_CONFIG
from src.exchange import KrakenExchange, Order, Trade, Balance
from src.technical_analysis import TechnicalAnalysis, Signal
from src.risk_management import RiskManager, Position, RiskMetrics


class TradingBot:
    """Main Trading Bot Class"""
    
    def __init__(self):
        self.exchange = KrakenExchange()
        self.technical_analysis = TechnicalAnalysis()
        self.risk_manager = RiskManager()
        
        self.is_running = False
        self.account_value = 0.0
        self.market_data = {}
        self.signals = {}
        self.last_update = datetime.now()
        
        # Performance tracking
        self.trade_history = []
        self.performance_metrics = {}
        
        # Strategy weights
        self.strategy_weights = STRATEGIES_CONFIG
        
    async def initialize(self):
        """Initialize the trading bot"""
        logger.info("Initializing Trading Bot...")
        
        # Test connection
        if not await self.exchange.test_connection():
            raise ConnectionError("Failed to connect to Kraken API")
        
        # Get initial account value
        balances = await self.exchange.get_balance()
        self.account_value = sum(bal.total for bal in balances if bal.currency == config.BASE_CURRENCY)
        
        logger.info(f"Initial account value: {self.account_value} {config.BASE_CURRENCY}")
        
        # Initialize market data
        await self.update_market_data()
        
        logger.info("Trading Bot initialized successfully")
    
    async def update_market_data(self):
        """Update market data for all trading pairs"""
        logger.debug("Updating market data...")
        
        for symbol in config.TRADING_PAIRS:
            try:
                # Get OHLCV data
                ohlcv_data = await self.exchange.get_ohlcv(symbol, '1h', 200)
                
                if ohlcv_data:
                    # Convert to DataFrame
                    df = pd.DataFrame(ohlcv_data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # Calculate technical indicators
                    df = self.technical_analysis.calculate_all_indicators(df)
                    
                    # Store market data
                    self.market_data[symbol] = df
                    
                    # Get current price
                    ticker = await self.exchange.get_ticker(symbol)
                    self.market_data[f"{symbol}_current"] = ticker['last']
                    
            except Exception as e:
                logger.error(f"Error updating market data for {symbol}: {e}")
        
        self.last_update = datetime.now()
        logger.debug("Market data updated")
    
    async def generate_signals(self) -> Dict[str, Dict]:
        """Generate trading signals for all symbols"""
        signals = {}
        
        for symbol in config.TRADING_PAIRS:
            if symbol in self.market_data:
                try:
                    # Generate technical signals
                    technical_signals = self.technical_analysis.generate_signals(
                        self.market_data[symbol], symbol
                    )
                    
                    # Get signal summary
                    signal_summary = self.technical_analysis.get_signal_summary(technical_signals)
                    
                    # Apply strategy weights
                    weighted_signal = self.apply_strategy_weights(signal_summary, symbol)
                    
                    signals[symbol] = weighted_signal
                    
                except Exception as e:
                    logger.error(f"Error generating signals for {symbol}: {e}")
        
        return signals
    
    def apply_strategy_weights(self, signal_summary: Dict, symbol: str) -> Dict:
        """Apply strategy weights to signals"""
        weighted_signal = {
            'signal': signal_summary['signal'],
            'strength': signal_summary['strength'],
            'confidence': signal_summary['confidence'],
            'indicators': signal_summary['indicators'],
            'timestamp': datetime.now()
        }
        
        # Apply momentum strategy
        if self.strategy_weights['momentum']['enabled']:
            momentum_weight = self.strategy_weights['momentum']['weight']
            weighted_signal['strength'] *= momentum_weight
        
        # Apply mean reversion strategy
        if self.strategy_weights['mean_reversion']['enabled']:
            mean_rev_weight = self.strategy_weights['mean_reversion']['weight']
            weighted_signal['strength'] *= mean_rev_weight
        
        # Apply trend following strategy
        if self.strategy_weights['trend_following']['enabled']:
            trend_weight = self.strategy_weights['trend_following']['weight']
            weighted_signal['strength'] *= trend_weight
        
        # Apply ML prediction strategy
        if self.strategy_weights['ml_prediction']['enabled']:
            ml_weight = self.strategy_weights['ml_prediction']['weight']
            weighted_signal['strength'] *= ml_weight
        
        return weighted_signal
    
    async def execute_trades(self, signals: Dict[str, Dict]):
        """Execute trades based on signals"""
        for symbol, signal in signals.items():
            if signal['signal'] == 'hold' or signal['strength'] < config.PREDICTION_THRESHOLD:
                continue
            
            try:
                current_price = self.market_data.get(f"{symbol}_current")
                if not current_price:
                    continue
                
                # Check if we already have a position
                existing_position = self.risk_manager.positions.get(symbol)
                
                if signal['signal'] == 'buy' and not existing_position:
                    await self.place_buy_order(symbol, current_price, signal)
                elif signal['signal'] == 'sell' and existing_position:
                    await self.place_sell_order(symbol, current_price, signal)
                    
            except Exception as e:
                logger.error(f"Error executing trade for {symbol}: {e}")
    
    async def place_buy_order(self, symbol: str, current_price: float, signal: Dict):
        """Place a buy order"""
        try:
            # Calculate position size
            stop_loss = current_price * (1 - config.STOP_LOSS_PERCENTAGE)
            position_size = self.risk_manager.calculate_position_size(
                self.account_value, 0.02, current_price, stop_loss
            )
            
            if position_size <= 0:
                return
            
            # Check risk limits
            position_value = position_size * current_price
            if not self.risk_manager.check_risk_limits(self.account_value, position_value):
                logger.warning(f"Risk limits exceeded for {symbol}")
                return
            
            # Place order
            order = await self.exchange.place_order(
                symbol=symbol,
                side='buy',
                order_type='market',
                amount=position_size,
                stop_loss=stop_loss,
                take_profit=current_price * (1 + config.TAKE_PROFIT_PERCENTAGE)
            )
            
            # Update position
            self.risk_manager.update_position(
                symbol=symbol,
                side='long',
                size=position_size,
                entry_price=current_price,
                current_price=current_price,
                stop_loss=stop_loss,
                take_profit=current_price * (1 + config.TAKE_PROFIT_PERCENTAGE)
            )
            
            logger.info(f"Buy order placed for {symbol}: {position_size} @ {current_price}")
            
        except Exception as e:
            logger.error(f"Error placing buy order for {symbol}: {e}")
    
    async def place_sell_order(self, symbol: str, current_price: float, signal: Dict):
        """Place a sell order"""
        try:
            position = self.risk_manager.positions.get(symbol)
            if not position:
                return
            
            # Place order to close position
            order = await self.exchange.place_order(
                symbol=symbol,
                side='sell',
                order_type='market',
                amount=position.size
            )
            
            # Calculate realized P&L
            realized_pnl = self.risk_manager.calculate_unrealized_pnl(
                position.side, position.size, position.entry_price, current_price
            )
            
            # Remove position
            del self.risk_manager.positions[symbol]
            
            # Update trade history
            self.trade_history.append({
                'symbol': symbol,
                'side': 'sell',
                'entry_price': position.entry_price,
                'exit_price': current_price,
                'size': position.size,
                'pnl': realized_pnl,
                'timestamp': datetime.now()
            })
            
            logger.info(f"Sell order placed for {symbol}: {position.size} @ {current_price}, P&L: {realized_pnl}")
            
        except Exception as e:
            logger.error(f"Error placing sell order for {symbol}: {e}")
    
    async def check_stop_losses(self):
        """Check and execute stop losses"""
        for symbol, position in list(self.risk_manager.positions.items()):
            current_price = self.market_data.get(f"{symbol}_current")
            if not current_price:
                continue
            
            # Check stop loss
            if self.risk_manager.check_stop_loss(symbol, current_price):
                await self.place_sell_order(symbol, current_price, {'signal': 'sell', 'strength': 1.0})
            
            # Check take profit
            elif self.risk_manager.check_take_profit(symbol, current_price):
                await self.place_sell_order(symbol, current_price, {'signal': 'sell', 'strength': 1.0})
    
    async def update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Get current market data
            current_prices = {}
            for symbol in config.TRADING_PAIRS:
                current_prices[symbol] = self.market_data.get(f"{symbol}_current", 0)
            
            # Calculate risk metrics
            risk_metrics = self.risk_manager.calculate_portfolio_metrics(
                self.account_value, current_prices
            )
            
            # Update account value
            self.account_value = risk_metrics.total_value
            
            # Store performance metrics
            self.performance_metrics = {
                'total_value': risk_metrics.total_value,
                'total_pnl': risk_metrics.total_pnl,
                'daily_pnl': risk_metrics.daily_pnl,
                'max_drawdown': risk_metrics.max_drawdown,
                'sharpe_ratio': risk_metrics.sharpe_ratio,
                'volatility': risk_metrics.volatility,
                'var_95': risk_metrics.var_95,
                'var_99': risk_metrics.var_99,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def run_trading_cycle(self):
        """Run one complete trading cycle"""
        try:
            # Update market data
            await self.update_market_data()
            
            # Generate signals
            signals = await self.generate_signals()
            
            # Check stop losses and take profits
            await self.check_stop_losses()
            
            # Execute trades
            await self.execute_trades(signals)
            
            # Update performance metrics
            await self.update_performance_metrics()
            
            # Log status
            logger.info(f"Trading cycle completed. Account value: {self.account_value:.2f}")
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    async def start(self):
        """Start the trading bot"""
        logger.info("Starting Trading Bot...")
        
        await self.initialize()
        self.is_running = True
        
        while self.is_running:
            try:
                await self.run_trading_cycle()
                
                # Wait before next cycle
                await asyncio.sleep(60)  # 1 minute cycle
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping bot...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
        
        await self.stop()
    
    async def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping Trading Bot...")
        self.is_running = False
        
        # Close all positions if needed
        # await self.close_all_positions()
        
        logger.info("Trading Bot stopped")
    
    async def close_all_positions(self):
        """Close all open positions"""
        logger.info("Closing all positions...")
        
        for symbol, position in list(self.risk_manager.positions.items()):
            try:
                current_price = self.market_data.get(f"{symbol}_current")
                if current_price:
                    await self.place_sell_order(symbol, current_price, {'signal': 'sell', 'strength': 1.0})
            except Exception as e:
                logger.error(f"Error closing position for {symbol}: {e}")
    
    def get_status(self) -> Dict:
        """Get current bot status"""
        return {
            'is_running': self.is_running,
            'account_value': self.account_value,
            'positions': len(self.risk_manager.positions),
            'last_update': self.last_update,
            'performance_metrics': self.performance_metrics,
            'trade_count': len(self.trade_history)
        }
    
    def get_risk_report(self) -> Dict:
        """Get comprehensive risk report"""
        current_prices = {}
        for symbol in config.TRADING_PAIRS:
            current_prices[symbol] = self.market_data.get(f"{symbol}_current", 0)
        
        return self.risk_manager.get_risk_report(self.account_value, current_prices)
    
    async def backtest(self, start_date: str, end_date: str, initial_balance: float) -> Dict:
        """Run backtest simulation"""
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # This is a simplified backtest
        # In a real implementation, you would load historical data and simulate trades
        
        results = {
            'initial_balance': initial_balance,
            'final_balance': initial_balance,
            'total_return': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0
        }
        
        logger.info("Backtest completed")
        return results


async def main():
    """Main function to run the trading bot"""
    bot = TradingBot()
    
    try:
        await bot.start()
    except Exception as e:
        logger.error(f"Error running trading bot: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())