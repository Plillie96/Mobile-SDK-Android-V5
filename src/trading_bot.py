"""
Main Trading Bot
Orchestrates all components and implements trading strategies
"""
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import time
import signal
import sys

from config import config, STRATEGY_WEIGHTS
from src.exchange import KrakenExchange
from src.technical_analysis import TechnicalAnalyzer
from src.machine_learning import MLPredictor
from src.risk_management import RiskManager

logger = logging.getLogger(__name__)

class TradingBot:
    """Advanced Kraken Trading Bot"""
    
    def __init__(self):
        self.config = config
        self.exchange = None
        self.technical_analyzer = TechnicalAnalyzer(config)
        self.ml_predictor = MLPredictor(config)
        self.risk_manager = RiskManager(config)
        
        # State management
        self.is_running = False
        self.portfolio_value = 0.0
        self.last_balance_check = None
        self.last_training_time = {}
        self.emergency_stop_triggered = False
        
        # Performance tracking
        self.trade_history = []
        self.daily_stats = {}
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler()
            ]
        )
    
    async def initialize(self):
        """Initialize the trading bot"""
        try:
            logger.info("Initializing Trading Bot...")
            
            # Initialize exchange connection
            self.exchange = KrakenExchange()
            
            # Test connection
            await self.test_connection()
            
            # Load ML models
            await self.load_ml_models()
            
            # Get initial portfolio value
            await self.update_portfolio_value()
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            logger.info("Trading Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing trading bot: {e}")
            return False
    
    async def test_connection(self):
        """Test exchange connection"""
        try:
            # Test public API
            ticker = await self.exchange.get_ticker("XBT/USD")
            logger.info(f"Connection test successful. BTC price: ${ticker['last']:,.2f}")
            
            # Test private API if credentials are available
            if self.config.kraken_api_key and self.config.kraken_secret_key:
                balance = await self.exchange.get_balance()
                logger.info(f"Account balance retrieved. {len(balance)} currencies found.")
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    async def load_ml_models(self):
        """Load or train ML models for all trading pairs"""
        try:
            for symbol in self.config.trading_pairs:
                logger.info(f"Loading ML models for {symbol}...")
                
                # Try to load existing models
                models_loaded = self.ml_predictor.load_models(symbol)
                
                if not models_loaded:
                    logger.info(f"No existing models found for {symbol}. Training new models...")
                    await self.train_models_for_symbol(symbol)
                else:
                    logger.info(f"ML models loaded for {symbol}")
                    
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
    
    async def train_models_for_symbol(self, symbol: str):
        """Train ML models for a specific symbol"""
        try:
            # Get historical data for training
            historical_data = await self.get_historical_data(symbol, limit=1000)
            
            if len(historical_data) < 100:
                logger.warning(f"Insufficient historical data for {symbol}: {len(historical_data)} samples")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            
            # Perform technical analysis
            df = self.technical_analyzer.analyze_all(df)
            
            # Train models
            scores = self.ml_predictor.train_models(df, symbol)
            
            if scores:
                logger.info(f"Models trained for {symbol}: {scores}")
                self.last_training_time[symbol] = datetime.now()
            else:
                logger.warning(f"Failed to train models for {symbol}")
                
        except Exception as e:
            logger.error(f"Error training models for {symbol}: {e}")
    
    async def get_historical_data(self, symbol: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get historical OHLCV data"""
        try:
            # Get data from multiple timeframes
            all_data = []
            
            for timeframe in self.config.timeframes:
                data = await self.exchange.get_ohlcv(symbol, timeframe, limit)
                all_data.extend(data)
            
            # Remove duplicates and sort by timestamp
            df = pd.DataFrame(all_data)
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []
    
    async def update_portfolio_value(self):
        """Update current portfolio value"""
        try:
            balance = await self.exchange.get_balance()
            
            # Calculate total portfolio value in USD
            total_value = 0.0
            
            for bal in balance:
                if bal.currency == 'USD':
                    total_value += bal.total
                elif bal.currency in ['XBT', 'ETH', 'ADA', 'DOT', 'LINK']:
                    # Get current price and convert to USD
                    try:
                        ticker = await self.exchange.get_ticker(f"{bal.currency}/USD")
                        total_value += bal.total * ticker['last']
                    except:
                        # Use approximate values if ticker fails
                        approx_prices = {'XBT': 40000, 'ETH': 2500, 'ADA': 0.5, 'DOT': 7, 'LINK': 15}
                        total_value += bal.total * approx_prices.get(bal.currency, 0)
            
            self.portfolio_value = total_value
            self.last_balance_check = datetime.now()
            
            logger.info(f"Portfolio value updated: ${total_value:,.2f}")
            
        except Exception as e:
            logger.error(f"Error updating portfolio value: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal. Stopping bot...")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Main trading loop"""
        try:
            logger.info("Starting Trading Bot...")
            self.is_running = True
            
            while self.is_running and not self.emergency_stop_triggered:
                try:
                    # Update portfolio value
                    await self.update_portfolio_value()
                    
                    # Process each trading pair
                    for symbol in self.config.trading_pairs:
                        await self.process_symbol(symbol)
                    
                    # Check for emergency stop conditions
                    await self.check_emergency_stop()
                    
                    # Retrain models if needed
                    await self.retrain_models_if_needed()
                    
                    # Wait before next iteration
                    await asyncio.sleep(60)  # 1 minute intervals
                    
                except Exception as e:
                    logger.error(f"Error in main trading loop: {e}")
                    await asyncio.sleep(30)  # Wait 30 seconds on error
            
            logger.info("Trading Bot stopped")
            
        except Exception as e:
            logger.error(f"Fatal error in trading bot: {e}")
            self.emergency_stop_triggered = True
    
    async def process_symbol(self, symbol: str):
        """Process a single trading symbol"""
        try:
            # Get current market data
            market_data = await self.get_market_data(symbol)
            
            if not market_data:
                return
            
            # Perform technical analysis
            df = self.technical_analyzer.analyze_all(market_data)
            
            # Get ML predictions
            ml_prediction = self.ml_predictor.predict(df, symbol)
            
            # Generate trading signals
            signals = self.generate_trading_signals(df, ml_prediction)
            
            # Execute trades based on signals
            await self.execute_trades(symbol, signals, df)
            
            # Update positions
            await self.update_positions(symbol, df['close'].iloc[-1])
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {e}")
    
    async def get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get current market data for analysis"""
        try:
            # Get recent OHLCV data
            ohlcv_data = await self.exchange.get_ohlcv(symbol, '1m', limit=200)
            
            if not ohlcv_data:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data)
            
            # Add timestamp column if not present
            if 'timestamp' not in df.columns:
                df['timestamp'] = pd.to_datetime(df.index, unit='ms')
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def generate_trading_signals(self, df: pd.DataFrame, ml_prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive trading signals"""
        try:
            signals = {
                'rsi_signal': self.get_rsi_signal(df),
                'macd_signal': self.get_macd_signal(df),
                'bollinger_signal': self.get_bollinger_signal(df),
                'volume_signal': self.get_volume_signal(df),
                'ml_signal': self.ml_predictor.get_prediction_signal(ml_prediction),
                'ensemble_signal': None,
                'signal_strength': 0.0
            }
            
            # Calculate ensemble signal
            ensemble_signal = self.calculate_ensemble_signal(signals)
            signals['ensemble_signal'] = ensemble_signal
            
            # Calculate overall signal strength
            signals['signal_strength'] = self.calculate_signal_strength(signals)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
            return {'ensemble_signal': 'hold', 'signal_strength': 0.0}
    
    def get_rsi_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get RSI-based trading signal"""
        try:
            if 'rsi' not in df.columns or df['rsi'].isna().all():
                return {'signal': 'hold', 'value': 50}
            
            current_rsi = df['rsi'].iloc[-1]
            
            if current_rsi < self.config.rsi_oversold:
                return {'signal': 'buy', 'value': current_rsi, 'strength': (30 - current_rsi) / 30}
            elif current_rsi > self.config.rsi_overbought:
                return {'signal': 'sell', 'value': current_rsi, 'strength': (current_rsi - 70) / 30}
            else:
                return {'signal': 'hold', 'value': current_rsi, 'strength': 0}
                
        except Exception as e:
            logger.error(f"Error getting RSI signal: {e}")
            return {'signal': 'hold', 'value': 50, 'strength': 0}
    
    def get_macd_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get MACD-based trading signal"""
        try:
            if 'macd' not in df.columns or 'macd_signal' not in df.columns:
                return {'signal': 'hold', 'value': 0}
            
            current_macd = df['macd'].iloc[-1]
            current_signal = df['macd_signal'].iloc[-1]
            prev_macd = df['macd'].iloc[-2]
            prev_signal = df['macd_signal'].iloc[-2]
            
            # MACD crossover signals
            if current_macd > current_signal and prev_macd <= prev_signal:
                return {'signal': 'buy', 'value': current_macd - current_signal, 'strength': 0.8}
            elif current_macd < current_signal and prev_macd >= prev_signal:
                return {'signal': 'sell', 'value': current_signal - current_macd, 'strength': 0.8}
            else:
                return {'signal': 'hold', 'value': current_macd - current_signal, 'strength': 0}
                
        except Exception as e:
            logger.error(f"Error getting MACD signal: {e}")
            return {'signal': 'hold', 'value': 0, 'strength': 0}
    
    def get_bollinger_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get Bollinger Bands-based trading signal"""
        try:
            if 'bb_upper' not in df.columns or 'bb_lower' not in df.columns:
                return {'signal': 'hold', 'value': 0}
            
            current_price = df['close'].iloc[-1]
            bb_upper = df['bb_upper'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]
            bb_middle = df['bb_middle'].iloc[-1]
            
            # Calculate position within bands
            if bb_upper != bb_lower:
                position = (current_price - bb_lower) / (bb_upper - bb_lower)
            else:
                position = 0.5
            
            if current_price <= bb_lower:
                return {'signal': 'buy', 'value': position, 'strength': 0.9}
            elif current_price >= bb_upper:
                return {'signal': 'sell', 'value': position, 'strength': 0.9}
            else:
                return {'signal': 'hold', 'value': position, 'strength': 0}
                
        except Exception as e:
            logger.error(f"Error getting Bollinger signal: {e}")
            return {'signal': 'hold', 'value': 0.5, 'strength': 0}
    
    def get_volume_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get volume-based trading signal"""
        try:
            if 'volume' not in df.columns:
                return {'signal': 'hold', 'value': 1.0}
            
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
            else:
                volume_ratio = 1.0
            
            # High volume can confirm other signals
            if volume_ratio > 1.5:
                return {'signal': 'confirm', 'value': volume_ratio, 'strength': min(0.5, volume_ratio - 1)}
            else:
                return {'signal': 'hold', 'value': volume_ratio, 'strength': 0}
                
        except Exception as e:
            logger.error(f"Error getting volume signal: {e}")
            return {'signal': 'hold', 'value': 1.0, 'strength': 0}
    
    def calculate_ensemble_signal(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate ensemble signal from all indicators"""
        try:
            buy_strength = 0.0
            sell_strength = 0.0
            
            # RSI signal
            if signals['rsi_signal']['signal'] == 'buy':
                buy_strength += signals['rsi_signal']['strength'] * STRATEGY_WEIGHTS['rsi']
            elif signals['rsi_signal']['signal'] == 'sell':
                sell_strength += signals['rsi_signal']['strength'] * STRATEGY_WEIGHTS['rsi']
            
            # MACD signal
            if signals['macd_signal']['signal'] == 'buy':
                buy_strength += signals['macd_signal']['strength'] * STRATEGY_WEIGHTS['macd']
            elif signals['macd_signal']['signal'] == 'sell':
                sell_strength += signals['macd_signal']['strength'] * STRATEGY_WEIGHTS['macd']
            
            # Bollinger signal
            if signals['bollinger_signal']['signal'] == 'buy':
                buy_strength += signals['bollinger_signal']['strength'] * STRATEGY_WEIGHTS['bollinger']
            elif signals['bollinger_signal']['signal'] == 'sell':
                sell_strength += signals['bollinger_signal']['strength'] * STRATEGY_WEIGHTS['bollinger']
            
            # Volume confirmation
            if signals['volume_signal']['signal'] == 'confirm':
                buy_strength *= (1 + signals['volume_signal']['strength'])
                sell_strength *= (1 + signals['volume_signal']['strength'])
            
            # ML signal
            ml_signal = signals['ml_signal']
            if ml_signal['signal'] == 'buy':
                buy_strength += ml_signal['confidence'] * STRATEGY_WEIGHTS['ml_prediction']
            elif ml_signal['signal'] == 'sell':
                sell_strength += ml_signal['confidence'] * STRATEGY_WEIGHTS['ml_prediction']
            
            # Determine final signal
            signal_threshold = 0.3
            
            if buy_strength > sell_strength and buy_strength > signal_threshold:
                return {'signal': 'buy', 'strength': buy_strength, 'confidence': buy_strength}
            elif sell_strength > buy_strength and sell_strength > signal_threshold:
                return {'signal': 'sell', 'strength': sell_strength, 'confidence': sell_strength}
            else:
                return {'signal': 'hold', 'strength': max(buy_strength, sell_strength), 'confidence': 0}
                
        except Exception as e:
            logger.error(f"Error calculating ensemble signal: {e}")
            return {'signal': 'hold', 'strength': 0, 'confidence': 0}
    
    def calculate_signal_strength(self, signals: Dict[str, Any]) -> float:
        """Calculate overall signal strength"""
        try:
            ensemble = signals['ensemble_signal']
            return ensemble.get('strength', 0.0)
        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return 0.0
    
    async def execute_trades(self, symbol: str, signals: Dict[str, Any], df: pd.DataFrame):
        """Execute trades based on signals"""
        try:
            ensemble_signal = signals['ensemble_signal']
            signal_strength = signals['signal_strength']
            
            if not ensemble_signal or signal_strength < 0.3:
                return
            
            current_price = df['close'].iloc[-1]
            
            # Check if we already have a position
            if symbol in self.risk_manager.positions:
                # Check if we should close existing position
                if ensemble_signal['signal'] == 'sell' and self.risk_manager.positions[symbol].side == 'long':
                    await self.close_position(symbol, current_price, "Signal reversal")
                elif ensemble_signal['signal'] == 'buy' and self.risk_manager.positions[symbol].side == 'short':
                    await self.close_position(symbol, current_price, "Signal reversal")
            else:
                # Open new position
                if ensemble_signal['signal'] in ['buy', 'sell']:
                    await self.open_position(symbol, ensemble_signal['signal'], signal_strength, current_price, df)
                    
        except Exception as e:
            logger.error(f"Error executing trades for {symbol}: {e}")
    
    async def open_position(self, symbol: str, side: str, signal_strength: float, 
                          current_price: float, df: pd.DataFrame):
        """Open a new trading position"""
        try:
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                self.portfolio_value, symbol, signal_strength, 
                df['volatility'].iloc[-1] if 'volatility' in df.columns else 0.02
            )
            
            # Check risk limits
            position_value = position_size * current_price
            risk_check = self.risk_manager.check_risk_limits(self.portfolio_value, position_value)
            
            if not risk_check['overall_ok']:
                logger.warning(f"Risk limits exceeded for {symbol}: {risk_check['reasons']}")
                return
            
            # Calculate stop loss and take profit
            atr = df['atr'].iloc[-1] if 'atr' in df.columns else current_price * 0.02
            volatility = df['volatility'].iloc[-1] if 'volatility' in df.columns else 0.02
            
            stop_loss = self.risk_manager.calculate_stop_loss(current_price, side, atr, volatility)
            take_profit = self.risk_manager.calculate_take_profit(current_price, side)
            
            # Place order
            order = await self.exchange.place_order(
                symbol=symbol,
                side=side,
                order_type='market',
                amount=position_size
            )
            
            if order and order.status == 'closed':
                # Add position to risk manager
                self.risk_manager.add_position(
                    symbol=symbol,
                    side=side,
                    size=position_size,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                logger.info(f"Opened {side} position for {symbol}: "
                           f"size={position_size:.4f}, price={current_price:.4f}")
                
                # Record trade
                self.record_trade(symbol, side, 'open', current_price, position_size, signal_strength)
            
        except Exception as e:
            logger.error(f"Error opening position for {symbol}: {e}")
    
    async def close_position(self, symbol: str, current_price: float, reason: str):
        """Close an existing position"""
        try:
            position = self.risk_manager.positions.get(symbol)
            if not position:
                return
            
            # Place closing order
            close_side = 'sell' if position.side == 'long' else 'buy'
            
            order = await self.exchange.place_order(
                symbol=symbol,
                side=close_side,
                order_type='market',
                amount=position.size
            )
            
            if order and order.status == 'closed':
                # Close position in risk manager
                result = self.risk_manager.close_position(symbol, current_price)
                
                if result['success']:
                    logger.info(f"Closed {position.side} position for {symbol}: "
                               f"P&L={result['pnl']:.2f} ({result['pnl_percentage']:.2%}) - {reason}")
                    
                    # Record trade
                    self.record_trade(symbol, position.side, 'close', current_price, 
                                    position.size, 0, result['pnl'])
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
    
    async def update_positions(self, symbol: str, current_price: float):
        """Update existing positions and check stop losses"""
        try:
            if symbol not in self.risk_manager.positions:
                return
            
            # Update position
            action = self.risk_manager.update_position(symbol, current_price, datetime.now())
            
            if action['action'] == 'close':
                await self.close_position(symbol, current_price, action['reason'])
                
        except Exception as e:
            logger.error(f"Error updating position for {symbol}: {e}")
    
    async def check_emergency_stop(self):
        """Check for emergency stop conditions"""
        try:
            # Get risk metrics
            risk_metrics = self.risk_manager.get_risk_metrics(self.portfolio_value)
            
            # Check daily loss limit
            if risk_metrics.daily_pnl_percentage < -self.config.max_daily_loss:
                logger.warning(f"Daily loss limit exceeded: {risk_metrics.daily_pnl_percentage:.2%}")
                await self.emergency_stop()
                return
            
            # Check max drawdown
            if risk_metrics.max_drawdown < -0.2:  # 20% max drawdown
                logger.warning(f"Maximum drawdown exceeded: {risk_metrics.max_drawdown:.2%}")
                await self.emergency_stop()
                return
            
            # Check volatility
            if risk_metrics.volatility > 0.5:  # 50% volatility
                logger.warning(f"High volatility detected: {risk_metrics.volatility:.2%}")
                # Consider reducing position sizes or stopping trading
                
        except Exception as e:
            logger.error(f"Error checking emergency stop: {e}")
    
    async def emergency_stop(self):
        """Execute emergency stop"""
        try:
            logger.warning("EMERGENCY STOP TRIGGERED - Closing all positions")
            self.emergency_stop_triggered = True
            
            # Close all positions
            symbols_to_close = self.risk_manager.emergency_stop()
            
            for symbol in symbols_to_close:
                try:
                    ticker = await self.exchange.get_ticker(symbol)
                    await self.close_position(symbol, ticker['last'], "Emergency stop")
                except Exception as e:
                    logger.error(f"Error closing position during emergency stop: {e}")
            
            logger.info("Emergency stop completed")
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
    
    async def retrain_models_if_needed(self):
        """Retrain ML models if needed"""
        try:
            for symbol in self.config.trading_pairs:
                last_training = self.last_training_time.get(symbol)
                
                if self.ml_predictor.retrain_if_needed(symbol, last_training):
                    logger.info(f"Retraining models for {symbol}...")
                    await self.train_models_for_symbol(symbol)
                    
        except Exception as e:
            logger.error(f"Error retraining models: {e}")
    
    def record_trade(self, symbol: str, side: str, action: str, price: float, 
                    size: float, signal_strength: float = 0, pnl: float = 0):
        """Record trade for performance tracking"""
        try:
            trade = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'side': side,
                'action': action,
                'price': price,
                'size': size,
                'signal_strength': signal_strength,
                'pnl': pnl,
                'portfolio_value': self.portfolio_value
            }
            
            self.trade_history.append(trade)
            
            # Keep only last 1000 trades
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]
                
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            if not self.trade_history:
                return {'message': 'No trades recorded yet'}
            
            # Calculate basic stats
            total_trades = len(self.trade_history)
            winning_trades = len([t for t in self.trade_history if t['pnl'] > 0])
            losing_trades = len([t for t in self.trade_history if t['pnl'] < 0])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Calculate P&L stats
            total_pnl = sum(t['pnl'] for t in self.trade_history)
            avg_win = np.mean([t['pnl'] for t in self.trade_history if t['pnl'] > 0]) if winning_trades > 0 else 0
            avg_loss = np.mean([t['pnl'] for t in self.trade_history if t['pnl'] < 0]) if losing_trades > 0 else 0
            
            # Calculate Sharpe ratio
            returns = [t['pnl'] / t['portfolio_value'] for t in self.trade_history if t['portfolio_value'] > 0]
            sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else float('inf'),
                'sharpe_ratio': sharpe_ratio,
                'current_portfolio_value': self.portfolio_value,
                'open_positions': len(self.risk_manager.positions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance stats: {e}")
            return {'error': str(e)}

async def main():
    """Main entry point"""
    bot = TradingBot()
    
    if await bot.initialize():
        await bot.run()
    else:
        logger.error("Failed to initialize trading bot")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())