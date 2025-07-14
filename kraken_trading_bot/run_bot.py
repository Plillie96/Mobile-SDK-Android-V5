#!/usr/bin/env python3
"""
Simple script to run the Kraken Trading Bot
"""
import asyncio
import sys
import os
from pathlib import Path
from loguru import logger

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        logs_dir / "trading_bot.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        "KRAKEN_API_KEY",
        "KRAKEN_SECRET_KEY",
        "DATABASE_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import krakenex
        import ccxt
        import pandas
        import numpy
        import sklearn
        import ta
        import fastapi
        import uvicorn
        import plotly
        import redis
        import sqlalchemy
        import psycopg2
        logger.info("All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please install all dependencies with: pip install -r requirements.txt")
        return False

async def main():
    """Main function to run the trading bot"""
    logger.info("Starting Kraken Trading Bot...")
    
    # Setup logging
    setup_logging()
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Exiting.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Exiting.")
        sys.exit(1)
    
    try:
        # Import and run the bot
        from main import KrakenTradingBot
        
        bot = KrakenTradingBot()
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())