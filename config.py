"""
Configuration settings for the Kraken Trading Bot
"""
import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()

class TradingConfig(BaseSettings):
    """Trading configuration settings"""
    
    # Kraken API Configuration
    KRAKEN_API_KEY: str = Field(default="", env="KRAKEN_API_KEY")
    KRAKEN_SECRET_KEY: str = Field(default="", env="KRAKEN_SECRET_KEY")
    KRAKEN_SANDBOX: bool = Field(default=True, env="KRAKEN_SANDBOX")
    
    # Trading Parameters
    TRADING_PAIRS: List[str] = Field(default=["XBT/USD", "ETH/USD", "ADA/USD"], env="TRADING_PAIRS")
    BASE_CURRENCY: str = Field(default="USD", env="BASE_CURRENCY")
    MAX_POSITION_SIZE: float = Field(default=0.1, env="MAX_POSITION_SIZE")  # 10% of portfolio
    MAX_DAILY_LOSS: float = Field(default=0.02, env="MAX_DAILY_LOSS")  # 2% daily loss limit
    MAX_DAILY_TRADES: int = Field(default=50, env="MAX_DAILY_TRADES")
    MIN_TRADE_AMOUNT: float = Field(default=10.0, env="MIN_TRADE_AMOUNT")
    
    # Risk Management
    STOP_LOSS_PERCENTAGE: float = Field(default=0.02, env="STOP_LOSS_PERCENTAGE")  # 2%
    TAKE_PROFIT_PERCENTAGE: float = Field(default=0.04, env="TAKE_PROFIT_PERCENTAGE")  # 4%
    TRAILING_STOP: bool = Field(default=True, env="TRAILING_STOP")
    TRAILING_STOP_PERCENTAGE: float = Field(default=0.01, env="TRAILING_STOP_PERCENTAGE")  # 1%
    
    # Technical Analysis
    RSI_PERIOD: int = Field(default=14, env="RSI_PERIOD")
    RSI_OVERBOUGHT: int = Field(default=70, env="RSI_OVERBOUGHT")
    RSI_OVERSOLD: int = Field(default=30, env="RSI_OVERSOLD")
    MACD_FAST: int = Field(default=12, env="MACD_FAST")
    MACD_SLOW: int = Field(default=26, env="MACD_SLOW")
    MACD_SIGNAL: int = Field(default=9, env="MACD_SIGNAL")
    BOLLINGER_PERIOD: int = Field(default=20, env="BOLLINGER_PERIOD")
    BOLLINGER_STD: float = Field(default=2.0, env="BOLLINGER_STD")
    
    # Database Configuration
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost/kraken_bot", env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/trading_bot.log", env="LOG_FILE")
    
    # Monitoring
    PROMETHEUS_PORT: int = Field(default=8000, env="PROMETHEUS_PORT")
    GRAFANA_URL: str = Field(default="http://localhost:3000", env="GRAFANA_URL")
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: str = Field(default="", env="ALPHA_VANTAGE_API_KEY")
    NEWS_API_KEY: str = Field(default="", env="NEWS_API_KEY")
    
    # Machine Learning
    MODEL_PATH: str = Field(default="models/", env="MODEL_PATH")
    RETRAIN_INTERVAL_HOURS: int = Field(default=24, env="RETRAIN_INTERVAL_HOURS")
    
    # Web Interface
    WEB_PORT: int = Field(default=8080, env="WEB_PORT")
    WEB_HOST: str = Field(default="0.0.0.0", env="WEB_HOST")
    
    # Notification
    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(default="", env="TELEGRAM_CHAT_ID")
    EMAIL_SMTP_SERVER: str = Field(default="", env="EMAIL_SMTP_SERVER")
    EMAIL_USERNAME: str = Field(default="", env="EMAIL_USERNAME")
    EMAIL_PASSWORD: str = Field(default="", env="EMAIL_PASSWORD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global configuration instance
config = TradingConfig()

# Strategy configurations
STRATEGY_CONFIGS = {
    "mean_reversion": {
        "enabled": True,
        "weight": 0.3,
        "lookback_period": 20,
        "threshold": 2.0
    },
    "momentum": {
        "enabled": True,
        "weight": 0.3,
        "lookback_period": 10,
        "threshold": 0.02
    },
    "arbitrage": {
        "enabled": True,
        "weight": 0.2,
        "min_spread": 0.001
    },
    "sentiment": {
        "enabled": True,
        "weight": 0.2,
        "news_weight": 0.6,
        "social_weight": 0.4
    }
}

# Time intervals for different operations
TIME_INTERVALS = {
    "market_data": "1m",
    "analysis": "5m",
    "trading": "1m",
    "risk_check": "30s",
    "performance_report": "1h"
}