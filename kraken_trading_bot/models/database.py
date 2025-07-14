"""
Database models for the Kraken Trading Bot
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional
import json

from config import config

Base = declarative_base()

class Trade(Base):
    """Trade model for storing executed trades"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    order_id = Column(String(100), nullable=False)
    strategy = Column(String(50), nullable=False)
    pnl = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    
class Order(Base):
    """Order model for storing order information"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), unique=True, nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), nullable=False)  # 'market', 'limit', 'stop'
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    status = Column(String(20), default='pending')  # 'pending', 'filled', 'cancelled'
    timestamp = Column(DateTime, default=datetime.utcnow)
    strategy = Column(String(50), nullable=False)
    
class MarketData(Base):
    """Market data model for storing OHLCV data"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
class Performance(Base):
    """Performance metrics model"""
    __tablename__ = 'performance'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    
class Strategy(Base):
    """Strategy performance model"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    signal = Column(String(10), nullable=False)  # 'buy', 'sell', 'hold'
    confidence = Column(Float, nullable=False)
    parameters = Column(Text, nullable=True)  # JSON string of strategy parameters
    
class Sentiment(Base):
    """Sentiment analysis data model"""
    __tablename__ = 'sentiment'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    source = Column(String(50), nullable=False)  # 'twitter', 'reddit', 'news'
    sentiment_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    text = Column(Text, nullable=True)
    
class Arbitrage(Base):
    """Arbitrage opportunities model"""
    __tablename__ = 'arbitrage'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    exchange1 = Column(String(50), nullable=False)
    exchange2 = Column(String(50), nullable=False)
    price1 = Column(Float, nullable=False)
    price2 = Column(Float, nullable=False)
    spread = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    executed = Column(Boolean, default=False)

# Database connection
engine = create_engine(config.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)