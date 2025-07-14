#!/usr/bin/env python3
"""
Kraken Trading Bot - Main Entry Point
A sophisticated algorithmic trading bot for Kraken exchange
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from config import config
from src.trading_bot import TradingBot
from src.dashboard import TradingDashboard, create_dash_app

def setup_logging():
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=log_format,
        handlers=[
            logging.FileHandler('logs/trading_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_env_template():
    """Create .env template file"""
    env_template = """# Kraken API Configuration
KRAKEN_API_KEY=your_api_key_here
KRAKEN_SECRET_KEY=your_secret_key_here

# Trading Configuration
TRADING_PAIRS=["XBT/USD", "ETH/USD", "ADA/USD", "DOT/USD", "LINK/USD"]
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.04

# Technical Analysis Parameters
RSI_PERIOD=14
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
BOLLINGER_PERIOD=20
BOLLINGER_STD=2.0

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/kraken_bot
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
LOG_FILE=trading_bot.log

# Machine Learning
ML_MODEL_PATH=models/
RETRAIN_INTERVAL_HOURS=24
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("Created .env.template file. Please copy it to .env and configure your settings.")

async def run_bot_only():
    """Run only the trading bot without dashboard"""
    print("Starting Kraken Trading Bot...")
    
    bot = TradingBot()
    
    if await bot.initialize():
        print("Bot initialized successfully. Starting trading...")
        await bot.run()
    else:
        print("Failed to initialize bot. Check your configuration and API credentials.")
        sys.exit(1)

async def run_with_dashboard():
    """Run trading bot with web dashboard"""
    print("Starting Kraken Trading Bot with Dashboard...")
    
    bot = TradingBot()
    
    if await bot.initialize():
        print("Bot initialized successfully.")
        
        # Create and start dashboard
        dashboard = TradingDashboard(bot)
        
        # Start dashboard in background
        import threading
        dashboard_thread = threading.Thread(
            target=dashboard.run,
            kwargs={'host': '0.0.0.0', 'port': 8000}
        )
        dashboard_thread.daemon = True
        dashboard_thread.start()
        
        print("Dashboard started at http://localhost:8000")
        print("Starting trading bot...")
        
        # Run the bot
        await bot.run()
    else:
        print("Failed to initialize bot. Check your configuration and API credentials.")
        sys.exit(1)

def run_backtest():
    """Run backtesting (placeholder for future implementation)"""
    print("Backtesting feature coming soon!")
    print("For now, you can use the live trading mode with paper trading enabled.")

def show_status():
    """Show current bot status"""
    print("Bot Status Check")
    print("================")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✓ Configuration file (.env) found")
    else:
        print("✗ Configuration file (.env) not found")
        print("  Run 'python main.py --setup' to create template")
    
    # Check if models directory exists
    if os.path.exists('models'):
        print("✓ Models directory found")
    else:
        print("✗ Models directory not found")
        print("  Will be created automatically on first run")
    
    # Check if logs directory exists
    if os.path.exists('logs'):
        print("✓ Logs directory found")
    else:
        print("✗ Logs directory not found")
        print("  Will be created automatically on first run")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Kraken Trading Bot - Advanced Algorithmic Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --bot-only          # Run trading bot only
  python main.py --with-dashboard    # Run bot with web dashboard
  python main.py --setup             # Create configuration template
  python main.py --status            # Check bot status
  python main.py --backtest          # Run backtesting (coming soon)
        """
    )
    
    parser.add_argument(
        '--bot-only',
        action='store_true',
        help='Run only the trading bot without dashboard'
    )
    
    parser.add_argument(
        '--with-dashboard',
        action='store_true',
        help='Run trading bot with web dashboard'
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Create configuration template'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current bot status'
    )
    
    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Run backtesting (coming soon)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Handle different modes
    if args.setup:
        create_env_template()
        return
    
    if args.status:
        show_status()
        return
    
    if args.backtest:
        run_backtest()
        return
    
    # Default behavior: run with dashboard
    if args.bot_only:
        asyncio.run(run_bot_only())
    else:
        asyncio.run(run_with_dashboard())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}")
        sys.exit(1)