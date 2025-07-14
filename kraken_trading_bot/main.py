#!/usr/bin/env python3
"""
Main trading bot application for Kraken
"""
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import signal
import sys
from loguru import logger

from config import config, STRATEGY_WEIGHTS
from exchange.kraken_client import KrakenClient
from strategies.technical_strategies import (
    RSIStrategy, MACDStrategy, BollingerBandsStrategy, 
    VolumeStrategy, MovingAverageStrategy
)
from ml.models import MLTradingModel, EnsembleModel
from risk_management import RiskManager
from models.database import init_db

class KrakenTradingBot:
    """Main trading bot class"""
    
    def __init__(self):
        # Initialize components
        self.exchange = KrakenClient()
        self.risk_manager = RiskManager()
        
        # Initialize strategies
        self.strategies = {
            'rsi': RSIStrategy(config.rsi_period),
            'macd': MACDStrategy({
                'fast_period': config.macd_fast,
                'slow_period': config.macd_slow,
                'signal_period': config.macd_signal
            }),
            'bollinger': BollingerBandsStrategy({
                'period': config.bollinger_period,
                'std_dev': config.bollinger_std
            }),
            'volume': VolumeStrategy(),
            'moving_average': MovingAverageStrategy()
        }
        
        # Initialize ML models
        self.ml_models = {}
        if config.enable_machine_learning:
            self.ml_models = {
                'random_forest': MLTradingModel('random_forest', 'random_forest'),
                'gradient_boosting': MLTradingModel('gradient_boosting', 'gradient_boosting'),
                'logistic_regression': MLTradingModel('logistic_regression', 'logistic_regression')
            }
            
            # Create ensemble model
            if len(self.ml_models) > 1:
                self.ensemble_model = EnsembleModel(self.ml_models)
        
        # Trading state
        self.is_running = False
        self.trading_pairs = config.trading_pairs
        self.current_signals = {}
        
        # Performance tracking
        self.performance_metrics = {}
        
        # Setup logging
        logger.add(config.log_file, rotation="1 day", retention="30 days")
        
    async def initialize(self):
        """Initialize the trading bot"""
        logger.info("Initializing Kraken Trading Bot...")
        
        try:
            # Initialize database
            init_db()
            logger.info("Database initialized")
            
            # Test exchange connection
            server_time = self.exchange.get_server_time()
            if server_time:
                logger.info(f"Connected to Kraken API. Server time: {server_time}")
            else:
                logger.error("Failed to connect to Kraken API")
                return False
            
            # Get account balance
            balance = self.exchange.get_account_balance()
            if balance:
                logger.info(f"Account balance: {balance}")
                # Set initial peak balance for risk management
                total_balance = sum(balance.values())
                self.risk_manager.peak_balance = total_balance
            else:
                logger.warning("Could not retrieve account balance")
            
            # Train ML models if enabled
            if config.enable_machine_learning:
                await self.train_ml_models()
            
            logger.info("Trading bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing trading bot: {e}")
            return False
    
    async def train_ml_models(self):
        """Train machine learning models"""
        logger.info("Training ML models...")
        
        for symbol in self.trading_pairs:
            try:
                # Get historical data for training
                historical_data = self.exchange.get_ohlcv(symbol, interval=60, since=None)
                
                if len(historical_data) < 1000:
                    logger.warning(f"Insufficient data for {symbol}, skipping ML training")
                    continue
                
                # Train each model
                for name, model in self.ml_models.items():
                    try:
                        metrics = model.train(historical_data)
                        logger.info(f"Trained {name} model for {symbol}: {metrics}")
                        
                        # Save model
                        model_path = f"{config.ml_model_path}/{name}_{symbol}.pkl"
                        model.save_model(model_path)
                        
                    except Exception as e:
                        logger.error(f"Error training {name} model for {symbol}: {e}")
                
            except Exception as e:
                logger.error(f"Error training ML models for {symbol}: {e}")
    
    async def analyze_market(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze market and generate trading signals
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Get market data
            market_data = self.exchange.get_ohlcv(symbol, interval=5)
            
            if market_data.empty:
                return {'signal': 'hold', 'confidence': 0.0, 'reason': 'no_data'}
            
            # Generate signals from technical strategies
            strategy_signals = {}
            for name, strategy in self.strategies.items():
                try:
                    signal = strategy.generate_signal(market_data)
                    strategy_signals[name] = signal
                except Exception as e:
                    logger.error(f"Error in {name} strategy: {e}")
                    strategy_signals[name] = {'signal': 'hold', 'confidence': 0.0}
            
            # Generate ML signals if enabled
            ml_signals = {}
            if config.enable_machine_learning and self.ml_models:
                try:
                    if hasattr(self, 'ensemble_model'):
                        signal, confidence = self.ensemble_model.predict(market_data)
                        ml_signals['ensemble'] = {'signal': signal, 'confidence': confidence}
                    else:
                        for name, model in self.ml_models.items():
                            if model.is_trained:
                                signal, confidence = model.predict(market_data)
                                ml_signals[name] = {'signal': signal, 'confidence': confidence}
                except Exception as e:
                    logger.error(f"Error in ML prediction: {e}")
            
            # Combine signals using weighted voting
            final_signal = self.combine_signals(strategy_signals, ml_signals)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow(),
                'current_price': market_data['close'].iloc[-1],
                'final_signal': final_signal,
                'strategy_signals': strategy_signals,
                'ml_signals': ml_signals,
                'market_data': market_data.tail(1).to_dict('records')[0]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market for {symbol}: {e}")
            return {'signal': 'hold', 'confidence': 0.0, 'reason': f'error: {e}'}
    
    def combine_signals(self, strategy_signals: Dict, ml_signals: Dict) -> Dict[str, Any]:
        """
        Combine signals from multiple strategies using weighted voting
        
        Args:
            strategy_signals: Signals from technical strategies
            ml_signals: Signals from ML models
            
        Returns:
            Combined signal
        """
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        
        # Process strategy signals
        for name, signal in strategy_signals.items():
            weight = STRATEGY_WEIGHTS.get(name, 0.1)
            confidence = signal.get('confidence', 0.0)
            
            if signal.get('signal') == 'buy':
                buy_score += weight * confidence
            elif signal.get('signal') == 'sell':
                sell_score += weight * confidence
            
            total_weight += weight
        
        # Process ML signals
        for name, signal in ml_signals.items():
            weight = STRATEGY_WEIGHTS.get('machine_learning', 0.25) / len(ml_signals)
            confidence = signal.get('confidence', 0.0)
            
            if signal.get('signal') == 'buy':
                buy_score += weight * confidence
            elif signal.get('signal') == 'sell':
                sell_score += weight * confidence
            
            total_weight += weight
        
        # Normalize scores
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight
        
        # Determine final signal
        if buy_score > sell_score and buy_score > 0.6:
            final_signal = 'buy'
            confidence = buy_score
        elif sell_score > buy_score and sell_score > 0.6:
            final_signal = 'sell'
            confidence = sell_score
        else:
            final_signal = 'hold'
            confidence = max(buy_score, sell_score)
        
        return {
            'signal': final_signal,
            'confidence': confidence,
            'buy_score': buy_score,
            'sell_score': sell_score
        }
    
    async def execute_trade(self, symbol: str, signal: Dict[str, Any]):
        """
        Execute trade based on signal
        
        Args:
            symbol: Trading pair symbol
            signal: Trading signal
        """
        try:
            current_price = signal['current_price']
            signal_type = signal['final_signal']['signal']
            confidence = signal['final_signal']['confidence']
            
            # Check risk limits
            balance = self.exchange.get_account_balance()
            if not balance:
                logger.warning("Could not get account balance")
                return
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                sum(balance.values()), current_price
            )
            
            # Check if trade is allowed
            allowed, reason = self.risk_manager.check_risk_limits(
                symbol, signal_type, position_size, current_price
            )
            
            if not allowed:
                logger.info(f"Trade not allowed for {symbol}: {reason}")
                return
            
            # Execute trade
            if signal_type == 'buy':
                result = self.exchange.place_market_order(symbol, 'buy', position_size)
                if result['success']:
                    # Add position to risk manager
                    stop_loss = current_price * (1 - config.stop_loss_pct)
                    take_profit = current_price * (1 + config.take_profit_pct)
                    
                    self.risk_manager.add_position(
                        symbol, 'long', position_size, current_price,
                        stop_loss, take_profit
                    )
                    
                    logger.info(f"Buy order executed: {position_size} {symbol} @ {current_price}")
                else:
                    logger.error(f"Buy order failed: {result['error']}")
            
            elif signal_type == 'sell':
                # Check if we have a position to sell
                if symbol in self.risk_manager.positions:
                    position = self.risk_manager.positions[symbol]
                    if position.side == 'long':
                        result = self.exchange.place_market_order(symbol, 'sell', position.quantity)
                        if result['success']:
                            self.risk_manager.close_position(symbol, current_price, 'signal')
                            logger.info(f"Sell order executed: {position.quantity} {symbol} @ {current_price}")
                        else:
                            logger.error(f"Sell order failed: {result['error']}")
                    else:
                        logger.info(f"Cannot sell {symbol}: position is short")
                else:
                    logger.info(f"No position to sell for {symbol}")
            
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {e}")
    
    async def update_positions(self):
        """Update all open positions"""
        for symbol in list(self.risk_manager.positions.keys()):
            try:
                # Get current price
                ticker = self.exchange.get_ticker_info(symbol)
                if not ticker:
                    continue
                
                # Extract current price (this may need adjustment based on actual ticker structure)
                current_price = float(ticker.get('c', [0])[0])  # Close price
                
                # Update position
                self.risk_manager.update_position(symbol, current_price)
                
                # Check stop loss/take profit
                action = self.risk_manager.check_stop_loss_take_profit(symbol, current_price)
                if action:
                    if action == 'stop_loss':
                        result = self.exchange.place_market_order(symbol, 'sell', 
                                                                self.risk_manager.positions[symbol].quantity)
                        if result['success']:
                            self.risk_manager.close_position(symbol, current_price, 'stop_loss')
                    elif action == 'take_profit':
                        result = self.exchange.place_market_order(symbol, 'sell',
                                                                self.risk_manager.positions[symbol].quantity)
                        if result['success']:
                            self.risk_manager.close_position(symbol, current_price, 'take_profit')
                
            except Exception as e:
                logger.error(f"Error updating position for {symbol}: {e}")
    
    async def trading_cycle(self):
        """Main trading cycle"""
        logger.info("Starting trading cycle...")
        
        try:
            # Check if trading should be stopped
            should_stop, reason = self.risk_manager.should_stop_trading()
            if should_stop:
                logger.warning(f"Trading stopped: {reason}")
                return
            
            # Update existing positions
            await self.update_positions()
            
            # Analyze each trading pair
            for symbol in self.trading_pairs:
                try:
                    # Analyze market
                    analysis = await self.analyze_market(symbol)
                    
                    # Store current signal
                    self.current_signals[symbol] = analysis
                    
                    # Execute trade if signal is strong enough
                    if analysis['final_signal']['confidence'] > 0.7:
                        await self.execute_trade(symbol, analysis)
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in trading cycle for {symbol}: {e}")
            
            # Update performance metrics
            self.performance_metrics = self.risk_manager.calculate_risk_metrics()
            
            logger.info("Trading cycle completed")
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    async def run(self):
        """Run the trading bot"""
        logger.info("Starting Kraken Trading Bot...")
        
        # Initialize bot
        if not await self.initialize():
            logger.error("Failed to initialize trading bot")
            return
        
        self.is_running = True
        
        # Schedule trading cycles
        schedule.every(5).minutes.do(lambda: asyncio.create_task(self.trading_cycle()))
        schedule.every().day.at("00:00").do(self.risk_manager.reset_daily_metrics)
        
        # Schedule ML model retraining
        if config.enable_machine_learning:
            schedule.every(config.ml_retrain_interval).hours.do(
                lambda: asyncio.create_task(self.train_ml_models())
            )
        
        logger.info("Trading bot started successfully")
        
        # Main loop
        while self.is_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
        
        # Cleanup
        await self.shutdown()
    
    async def shutdown(self):
        """Shutdown the trading bot"""
        logger.info("Shutting down trading bot...")
        self.is_running = False
        
        # Close all positions if needed
        for symbol in list(self.risk_manager.positions.keys()):
            try:
                position = self.risk_manager.positions[symbol]
                if position.side == 'long':
                    self.exchange.place_market_order(symbol, 'sell', position.quantity)
                    logger.info(f"Closed position: {symbol}")
            except Exception as e:
                logger.error(f"Error closing position {symbol}: {e}")
        
        logger.info("Trading bot shutdown complete")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run trading bot
    bot = KrakenTradingBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())