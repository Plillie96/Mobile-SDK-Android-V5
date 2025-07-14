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
    
    # Kraken API credentials
    kraken_api_key: str = Field(default="", env="KRAKEN_API_KEY")
    kraken_secret_key: str = Field(default="", env="KRAKEN_SECRET_KEY")
    
    # Trading pairs
    trading_pairs: List[str] = Field(
        default=["XBT/USD", "ETH/USD", "ADA/USD", "DOT/USD", "LINK/USD"],
        env="TRADING_PAIRS"
    )
    
    # Risk management
    max_position_size: float = Field(default=0.1, env="MAX_POSITION_SIZE")  # 10% of portfolio
    max_daily_loss: float = Field(default=0.05, env="MAX_DAILY_LOSS")  # 5% daily loss limit
    stop_loss_pct: float = Field(default=0.02, env="STOP_LOSS_PCT")  # 2% stop loss
    take_profit_pct: float = Field(default=0.04, env="TAKE_PROFIT_PCT")  # 4% take profit
    
    # Strategy parameters
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
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost/kraken_bot",
        env="DATABASE_URL"
    )
    
    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/trading_bot.log", env="LOG_FILE")
    
    # Web interface
    web_port: int = Field(default=8000, env="WEB_PORT")
    web_host: str = Field(default="0.0.0.0", env="WEB_HOST")
    
    # Performance tracking
    performance_metrics: List[str] = Field(
        default=["sharpe_ratio", "max_drawdown", "win_rate", "profit_factor"],
        env="PERFORMANCE_METRICS"
    )
    
    # Advanced features
    enable_machine_learning: bool = Field(default=True, env="ENABLE_ML")
    enable_sentiment_analysis: bool = Field(default=True, env="ENABLE_SENTIMENT")
    enable_news_trading: bool = Field(default=True, env="ENABLE_NEWS")
    enable_arbitrage: bool = Field(default=True, env="ENABLE_ARBITRAGE")
    
    # Machine learning parameters
    ml_model_path: str = Field(default="models/", env="ML_MODEL_PATH")
    ml_retrain_interval: int = Field(default=24, env="ML_RETRAIN_INTERVAL")  # hours
    
    # Sentiment analysis
    sentiment_sources: List[str] = Field(
        default=["twitter", "reddit", "news"],
        env="SENTIMENT_SOURCES"
    )
    
    # Arbitrage settings
    arbitrage_threshold: float = Field(default=0.005, env="ARBITRAGE_THRESHOLD")  # 0.5%
    arbitrage_exchanges: List[str] = Field(
        default=["binance", "coinbase", "kraken"],
        env="ARBITRAGE_EXCHANGES"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global configuration instance
config = TradingConfig()

# Strategy weights for ensemble approach
STRATEGY_WEIGHTS = {
    "rsi": 0.2,
    "macd": 0.2,
    "bollinger": 0.15,
    "volume": 0.1,
    "machine_learning": 0.25,
    "sentiment": 0.1
}

# Market hours (UTC)
MARKET_HOURS = {
    "start": "00:00",
    "end": "23:59"
}

# Emergency stop conditions
EMERGENCY_STOP_CONDITIONS = {
    "max_daily_loss": 0.05,
    "max_consecutive_losses": 5,
    "max_drawdown": 0.15,
    "market_volatility_threshold": 0.1
}