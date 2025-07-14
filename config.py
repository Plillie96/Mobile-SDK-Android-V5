"""
Configuration file for the Kraken Trading Bot
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
    MAX_DAILY_TRADES: int = Field(default=50, env="MAX_DAILY_TRADES")
    MIN_TRADE_AMOUNT: float = Field(default=10.0, env="MIN_TRADE_AMOUNT")
    
    # Risk Management
    STOP_LOSS_PERCENTAGE: float = Field(default=0.02, env="STOP_LOSS_PERCENTAGE")  # 2%
    TAKE_PROFIT_PERCENTAGE: float = Field(default=0.04, env="TAKE_PROFIT_PERCENTAGE")  # 4%
    MAX_DRAWDOWN: float = Field(default=0.15, env="MAX_DRAWDOWN")  # 15%
    DAILY_LOSS_LIMIT: float = Field(default=0.05, env="DAILY_LOSS_LIMIT")  # 5%
    
    # Technical Analysis
    SHORT_MA_PERIOD: int = Field(default=10, env="SHORT_MA_PERIOD")
    LONG_MA_PERIOD: int = Field(default=50, env="LONG_MA_PERIOD")
    RSI_PERIOD: int = Field(default=14, env="RSI_PERIOD")
    RSI_OVERBOUGHT: int = Field(default=70, env="RSI_OVERBOUGHT")
    RSI_OVERSOLD: int = Field(default=30, env="RSI_OVERSOLD")
    BOLLINGER_PERIOD: int = Field(default=20, env="BOLLINGER_PERIOD")
    BOLLINGER_STD: float = Field(default=2.0, env="BOLLINGER_STD")
    
    # Machine Learning
    ML_MODEL_PATH: str = Field(default="models/", env="ML_MODEL_PATH")
    FEATURE_WINDOW: int = Field(default=100, env="FEATURE_WINDOW")
    PREDICTION_THRESHOLD: float = Field(default=0.6, env="PREDICTION_THRESHOLD")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///trading_bot.db", env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/trading_bot.log", env="LOG_FILE")
    
    # Monitoring
    METRICS_PORT: int = Field(default=8000, env="METRICS_PORT")
    DASHBOARD_PORT: int = Field(default=8050, env="DASHBOARD_PORT")
    
    # News and Sentiment
    NEWS_API_KEY: str = Field(default="", env="NEWS_API_KEY")
    TWITTER_API_KEY: str = Field(default="", env="TWITTER_API_KEY")
    TWITTER_API_SECRET: str = Field(default="", env="TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN: str = Field(default="", env="TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_SECRET: str = Field(default="", env="TWITTER_ACCESS_SECRET")
    
    # Backtesting
    BACKTEST_START_DATE: str = Field(default="2023-01-01", env="BACKTEST_START_DATE")
    BACKTEST_END_DATE: str = Field(default="2024-01-01", env="BACKTEST_END_DATE")
    BACKTEST_INITIAL_BALANCE: float = Field(default=10000.0, env="BACKTEST_INITIAL_BALANCE")
    
    # Advanced Features
    ENABLE_GRID_TRADING: bool = Field(default=False, env="ENABLE_GRID_TRADING")
    GRID_LEVELS: int = Field(default=10, env="GRID_LEVELS")
    GRID_SPACING: float = Field(default=0.02, env="GRID_SPACING")  # 2%
    
    ENABLE_DCA: bool = Field(default=False, env="ENABLE_DCA")
    DCA_INTERVAL: int = Field(default=24, env="DCA_INTERVAL")  # hours
    DCA_AMOUNT: float = Field(default=100.0, env="DCA_AMOUNT")
    
    ENABLE_ARBITRAGE: bool = Field(default=False, env="ENABLE_ARBITRAGE")
    ARBITRAGE_THRESHOLD: float = Field(default=0.005, env="ARBITRAGE_THRESHOLD")  # 0.5%
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global configuration instance
config = TradingConfig()

# Trading strategies configuration
STRATEGIES_CONFIG = {
    "momentum": {
        "enabled": True,
        "weight": 0.3,
        "parameters": {
            "lookback_period": 20,
            "momentum_threshold": 0.02
        }
    },
    "mean_reversion": {
        "enabled": True,
        "weight": 0.25,
        "parameters": {
            "bollinger_period": 20,
            "bollinger_std": 2.0
        }
    },
    "trend_following": {
        "enabled": True,
        "weight": 0.25,
        "parameters": {
            "short_ma": 10,
            "long_ma": 50,
            "trend_strength": 0.01
        }
    },
    "ml_prediction": {
        "enabled": True,
        "weight": 0.2,
        "parameters": {
            "model_type": "lstm",
            "prediction_horizon": 24,
            "confidence_threshold": 0.7
        }
    }
}

# Market hours (UTC)
MARKET_HOURS = {
    "crypto": {
        "open": "00:00",
        "close": "23:59",
        "timezone": "UTC"
    }
}

# Notification settings
NOTIFICATIONS = {
    "email": {
        "enabled": False,
        "smtp_server": "",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "recipients": []
    },
    "telegram": {
        "enabled": False,
        "bot_token": "",
        "chat_id": ""
    },
    "discord": {
        "enabled": False,
        "webhook_url": ""
    }
}