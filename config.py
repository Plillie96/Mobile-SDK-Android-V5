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
    
    # API Configuration
    kraken_api_key: str = Field(default="", env="KRAKEN_API_KEY")
    kraken_secret_key: str = Field(default="", env="KRAKEN_SECRET_KEY")
    
    # Trading pairs to monitor
    trading_pairs: List[str] = Field(
        default=["XBT/USD", "ETH/USD", "ADA/USD", "DOT/USD", "LINK/USD"],
        env="TRADING_PAIRS"
    )
    
    # Risk Management
    max_position_size: float = Field(default=0.1, env="MAX_POSITION_SIZE")  # 10% of portfolio
    max_daily_loss: float = Field(default=0.05, env="MAX_DAILY_LOSS")  # 5% daily loss limit
    stop_loss_percentage: float = Field(default=0.02, env="STOP_LOSS_PERCENTAGE")  # 2% stop loss
    take_profit_percentage: float = Field(default=0.04, env="TAKE_PROFIT_PERCENTAGE")  # 4% take profit
    
    # Strategy Parameters
    rsi_period: int = Field(default=14, env="RSI_PERIOD")
    rsi_oversold: int = Field(default=30, env="RSI_OVERSOLD")
    rsi_overbought: int = Field(default=70, env="RSI_OVERBOUGHT")
    
    macd_fast: int = Field(default=12, env="MACD_FAST")
    macd_slow: int = Field(default=26, env="MACD_SLOW")
    macd_signal: int = Field(default=9, env="MACD_SIGNAL")
    
    bollinger_period: int = Field(default=20, env="BOLLINGER_PERIOD")
    bollinger_std: float = Field(default=2.0, env="BOLLINGER_STD")
    
    # Timeframes for analysis
    timeframes: List[str] = Field(
        default=["1m", "5m", "15m", "1h", "4h", "1d"],
        env="TIMEFRAMES"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost/kraken_bot",
        env="DATABASE_URL"
    )
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="trading_bot.log", env="LOG_FILE")
    
    # Performance Monitoring
    performance_update_interval: int = Field(default=300, env="PERFORMANCE_UPDATE_INTERVAL")  # 5 minutes
    
    # Backtesting
    backtest_start_date: str = Field(default="2023-01-01", env="BACKTEST_START_DATE")
    backtest_end_date: str = Field(default="2024-01-01", env="BACKTEST_END_DATE")
    
    # Machine Learning
    ml_model_path: str = Field(default="models/", env="ML_MODEL_PATH")
    retrain_interval_hours: int = Field(default=24, env="RETRAIN_INTERVAL_HOURS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global configuration instance
config = TradingConfig()

# Strategy weights for ensemble approach
STRATEGY_WEIGHTS = {
    "rsi": 0.2,
    "macd": 0.25,
    "bollinger": 0.2,
    "volume": 0.15,
    "ml_prediction": 0.2
}

# Market hours (UTC)
MARKET_HOURS = {
    "start": "00:00",
    "end": "23:59"
}

# Emergency stop conditions
EMERGENCY_STOP_CONDITIONS = {
    "max_consecutive_losses": 5,
    "max_hourly_drawdown": 0.1,  # 10%
    "max_volatility_threshold": 0.5  # 50% price movement
}