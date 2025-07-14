"""
Main Trading Bot for Kraken
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from loguru import logger
import sys
import os

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import config, TIME_INTERVALS

# Import our modules
from exchange.kraken_client import KrakenClient
from analysis.technical_indicators import TechnicalIndicators
from strategies.trading_strategies import StrategyManager
from risk.risk_manager import RiskManager

class KrakenTradingBot:
    """Main trading bot class"""
    
    def __init__(self):
        self.client = None
        self.indicators = TechnicalIndicators()
        self.strategy_manager = StrategyManager()
        self.risk_manager = RiskManager()
        self.is_running = False
        self.market_data = {}
        self.last_analysis = {}
        self.performance_metrics = {}
        
    async def initialize(self):
        """Initialize the trading bot"""
        logger.info("Initializing Kraken Trading Bot...")
        
        # Initialize Kraken client
        self.client = KrakenClient()
        await self.client.__aenter__()
        
        # Get initial balance
        balance = await self.client.get_account_balance()
        total_balance = sum(balance.values())
        self.risk_manager.update_balance(total_balance)
        
        logger.info(f"Initial balance: {total_balance}")
        logger.info("Trading bot initialized successfully")
        
    async def shutdown(self):
        """Shutdown the trading bot"""
        logger.info("Shutting down trading bot...")
        self.is_running = False
        
        if self.client:
            await self.client.__aexit__(None, None, None)
        
        logger.info("Trading bot shutdown complete")
    
    async def fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch market data for a symbol"""
        try:
            # Get OHLCV data
            ohlcv = await self.client.get_ohlcv(symbol, '1m', 100)
            df = pd.DataFrame(ohlcv)
            
            if df.empty:
                return {}
            
            # Get current ticker
            ticker = await self.client.get_ticker(symbol)
            
            # Get order book
            orderbook = await self.client.get_order_book(symbol, 20)
            
            return {
                'symbol': symbol,
                'ohlcv': df,
                'ticker': ticker,
                'orderbook': orderbook,
                'current_price': ticker.get('last', 0),
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return {}
    
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform technical analysis on market data"""
        try:
            df = market_data.get('ohlcv', pd.DataFrame())
            if df.empty:
                return {}
            
            # Calculate technical indicators
            df_with_indicators = self.indicators.get_all_indicators(df)
            
            # Generate signals
            signals = self.indicators.generate_signals(df_with_indicators)
            
            # Get latest values
            latest = df_with_indicators.iloc[-1] if not df_with_indicators.empty else {}
            
            return {
                'symbol': market_data['symbol'],
                'indicators': latest.to_dict(),
                'signals': {k: v.iloc[-1] if hasattr(v, 'iloc') else v for k, v in signals.items()},
                'current_price': market_data['current_price'],
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error analyzing market data: {e}")
            return {}
    
    async def execute_trade(self, signal: Dict[str, Any], market_data: Dict[str, Any]) -> bool:
        """Execute a trade based on the signal"""
        try:
            symbol = market_data['symbol']
            current_price = market_data['current_price']
            side = signal['signal']
            
            if side == 'hold':
                return False
            
            # Calculate position size
            balance = self.risk_manager.current_balance
            position_size = self.risk_manager.calculate_position_size(
                signal, balance, symbol, current_price
            )
            
            if position_size <= 0:
                logger.info(f"Position size too small for {symbol}")
                return False
            
            # Check if we can open position
            can_open, reason = self.risk_manager.can_open_position(
                symbol, side, position_size, current_price
            )
            
            if not can_open:
                logger.warning(f"Cannot open position for {symbol}: {reason}")
                return False
            
            # Execute the trade
            if side == 'buy':
                order = await self.client.place_market_order(symbol, 'buy', position_size)
            else:
                order = await self.client.place_market_order(symbol, 'sell', position_size)
            
            if order:
                # Add position to risk manager
                stop_loss = None
                take_profit = None
                
                # Calculate stop loss and take profit if we have ATR data
                if 'atr' in signal.get('indicators', {}):
                    atr = signal['indicators']['atr']
                    stop_loss = self.risk_manager.calculate_stop_loss(current_price, side, atr)
                    take_profit = self.risk_manager.calculate_take_profit(current_price, side)
                
                position = self.risk_manager.add_position(
                    symbol, side, position_size, current_price, stop_loss, take_profit
                )
                
                logger.info(f"Trade executed: {side} {position_size} {symbol} at {current_price}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False
    
    async def check_exit_conditions(self, market_data: Dict[str, Any]) -> List[str]:
        """Check if any positions should be closed"""
        positions_to_close = []
        
        try:
            symbol = market_data['symbol']
            current_price = market_data['current_price']
            
            if symbol not in self.risk_manager.positions:
                return positions_to_close
            
            position = self.risk_manager.positions[symbol]
            
            # Check stop loss
            if self.risk_manager.check_stop_loss(position, current_price):
                positions_to_close.append(f"{symbol}_stop_loss")
            
            # Check take profit
            if self.risk_manager.check_take_profit(position, current_price):
                positions_to_close.append(f"{symbol}_take_profit")
            
            # Check trailing stop
            if self.risk_manager.check_trailing_stop(position, current_price):
                positions_to_close.append(f"{symbol}_trailing_stop")
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
        
        return positions_to_close
    
    async def close_position(self, symbol: str, reason: str) -> bool:
        """Close a position"""
        try:
            position = self.risk_manager.positions.get(symbol)
            if not position:
                return False
            
            # Get current price
            ticker = await self.client.get_ticker(symbol)
            current_price = ticker.get('last', position.current_price)
            
            # Close position
            trade = self.risk_manager.close_position(symbol, current_price)
            
            if trade:
                logger.info(f"Position closed: {symbol} at {current_price} (reason: {reason})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error closing position {symbol}: {e}")
            return False
    
    async def update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Get portfolio metrics
            portfolio_metrics = self.risk_manager.get_portfolio_metrics()
            
            # Get strategy performance
            strategy_performance = self.strategy_manager.get_strategy_performance()
            
            # Calculate overall performance
            total_return = portfolio_metrics.get('total_pnl', 0)
            total_value = portfolio_metrics.get('total_value', 0)
            
            if self.risk_manager.current_balance > 0:
                return_rate = total_return / self.risk_manager.current_balance
            else:
                return_rate = 0
            
            self.performance_metrics = {
                'total_return': total_return,
                'return_rate': return_rate,
                'total_value': total_value,
                'max_drawdown': self.risk_manager.max_drawdown,
                'daily_pnl': self.risk_manager.daily_pnl,
                'daily_trades': self.risk_manager.daily_trades,
                'portfolio_metrics': portfolio_metrics,
                'strategy_performance': strategy_performance,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def trading_cycle(self):
        """Main trading cycle"""
        try:
            for symbol in config.TRADING_PAIRS:
                # Fetch market data
                market_data = await self.fetch_market_data(symbol)
                if not market_data:
                    continue
                
                # Store market data
                self.market_data[symbol] = market_data
                
                # Analyze market
                analysis = await self.analyze_market(market_data)
                if not analysis:
                    continue
                
                self.last_analysis[symbol] = analysis
                
                # Check exit conditions first
                positions_to_close = await self.check_exit_conditions(market_data)
                for position_reason in positions_to_close:
                    symbol_to_close = position_reason.split('_')[0]
                    reason = '_'.join(position_reason.split('_')[1:])
                    await self.close_position(symbol_to_close, reason)
                
                # Generate trading signal
                signal = await self.strategy_manager.get_combined_signal({
                    'ohlcv': market_data['ohlcv'],
                    'current_price': market_data['current_price'],
                    'indicators': analysis.get('indicators', {}),
                    'signals': analysis.get('signals', {}),
                    'news_sentiment': 0,  # Placeholder - would integrate with news API
                    'social_sentiment': 0  # Placeholder - would integrate with social media
                })
                
                # Execute trade if signal is strong enough
                if signal['confidence'] > 0.6 and signal['strength'] > 0.3:
                    await self.execute_trade(signal, market_data)
                
                # Update position prices
                price_updates = {symbol: market_data['current_price']}
                self.risk_manager.update_position_prices(price_updates)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
            
            # Update performance metrics
            await self.update_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    async def run(self):
        """Main run loop"""
        logger.info("Starting trading bot...")
        self.is_running = True
        
        try:
            while self.is_running:
                await self.trading_cycle()
                
                # Wait for next cycle
                await asyncio.sleep(60)  # 1 minute cycle
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error in main run loop: {e}")
        finally:
            await self.shutdown()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        return {
            'is_running': self.is_running,
            'performance_metrics': self.performance_metrics,
            'risk_report': self.risk_manager.get_risk_report(),
            'market_data_symbols': list(self.market_data.keys()),
            'last_analysis_symbols': list(self.last_analysis.keys())
        }
    
    async def backtest(self, start_date: str, end_date: str, initial_balance: float = 10000) -> Dict[str, Any]:
        """Run backtest with historical data"""
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # This is a simplified backtest - in a real implementation,
        # you would fetch historical data and simulate trading
        
        results = {
            'initial_balance': initial_balance,
            'final_balance': initial_balance,
            'total_return': 0,
            'total_trades': 0,
            'win_rate': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0
        }
        
        logger.info("Backtest completed")
        return results

async def main():
    """Main entry point"""
    bot = KrakenTradingBot()
    
    try:
        await bot.initialize()
        await bot.run()
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    # Configure logging
    logger.add(
        config.LOG_FILE,
        rotation="1 day",
        retention="30 days",
        level=config.LOG_LEVEL
    )
    
    # Run the bot
    asyncio.run(main())