#!/usr/bin/env python3
"""
Kraken Trading Bot - Main Entry Point
A sophisticated algorithmic trading bot for Kraken exchange
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from loguru import logger
import signal

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.trading_bot import TradingBot
from src.dashboard import create_dashboard
from config import config


def setup_logging():
    """Setup logging configuration"""
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Configure loguru
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.LOG_LEVEL
    )
    
    # Add file handler
    logger.add(
        config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.LOG_LEVEL,
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


async def run_bot():
    """Run the trading bot"""
    bot = TradingBot()
    
    try:
        logger.info("Starting Kraken Trading Bot...")
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping bot...")
    except Exception as e:
        logger.error(f"Error running trading bot: {e}")
    finally:
        await bot.stop()


async def run_dashboard():
    """Run the dashboard"""
    bot = TradingBot()
    
    try:
        # Initialize bot
        await bot.initialize()
        
        # Create and run dashboard
        dashboard = create_dashboard(bot)
        logger.info(f"Starting dashboard on http://localhost:{config.DASHBOARD_PORT}")
        dashboard.run(port=config.DASHBOARD_PORT)
        
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")


async def run_backtest():
    """Run backtest simulation"""
    bot = TradingBot()
    
    try:
        logger.info("Starting backtest...")
        results = await bot.backtest(
            start_date=config.BACKTEST_START_DATE,
            end_date=config.BACKTEST_END_DATE,
            initial_balance=config.BACKTEST_INITIAL_BALANCE
        )
        
        logger.info("Backtest Results:")
        logger.info(f"Initial Balance: ${results['initial_balance']:,.2f}")
        logger.info(f"Final Balance: ${results['final_balance']:,.2f}")
        logger.info(f"Total Return: {results['total_return']*100:.2f}%")
        logger.info(f"Max Drawdown: {results['max_drawdown']*100:.2f}%")
        logger.info(f"Sharpe Ratio: {results['sharpe_ratio']:.3f}")
        logger.info(f"Total Trades: {results['total_trades']}")
        logger.info(f"Win Rate: {results['win_rate']*100:.2f}%")
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")


def check_configuration():
    """Check if configuration is valid"""
    errors = []
    
    # Check API keys
    if not config.KRAKEN_API_KEY:
        errors.append("KRAKEN_API_KEY is not set")
    if not config.KRAKEN_SECRET_KEY:
        errors.append("KRAKEN_SECRET_KEY is not set")
    
    # Check trading pairs
    if not config.TRADING_PAIRS:
        errors.append("No trading pairs configured")
    
    # Check risk parameters
    if config.MAX_POSITION_SIZE <= 0 or config.MAX_POSITION_SIZE > 1:
        errors.append("MAX_POSITION_SIZE must be between 0 and 1")
    
    if config.STOP_LOSS_PERCENTAGE <= 0:
        errors.append("STOP_LOSS_PERCENTAGE must be positive")
    
    if config.TAKE_PROFIT_PERCENTAGE <= 0:
        errors.append("TAKE_PROFIT_PERCENTAGE must be positive")
    
    if errors:
        logger.error("Configuration errors found:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Kraken Trading Bot")
    parser.add_argument(
        "--mode",
        choices=["bot", "dashboard", "backtest"],
        default="bot",
        help="Run mode: bot (default), dashboard, or backtest"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Use sandbox mode for testing"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check configuration
    if not check_configuration():
        sys.exit(1)
    
    # Override sandbox setting if specified
    if args.sandbox:
        config.KRAKEN_SANDBOX = True
    
    # Set debug level
    if args.debug:
        config.LOG_LEVEL = "DEBUG"
    
    logger.info("Kraken Trading Bot v1.0.0")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Sandbox: {config.KRAKEN_SANDBOX}")
    logger.info(f"Trading Pairs: {config.TRADING_PAIRS}")
    
    try:
        if args.mode == "bot":
            asyncio.run(run_bot())
        elif args.mode == "dashboard":
            asyncio.run(run_dashboard())
        elif args.mode == "backtest":
            asyncio.run(run_backtest())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()