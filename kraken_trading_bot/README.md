# Kraken Trading Bot - Top 0.1% Performance

A sophisticated, high-performance trading bot for the Kraken cryptocurrency exchange, designed to achieve top 0.1% performance through advanced machine learning, multi-strategy ensemble approaches, and comprehensive risk management.

## 🚀 Features

### Core Trading Capabilities
- **Multi-Strategy Ensemble**: Combines RSI, MACD, Bollinger Bands, Volume Analysis, and Moving Average strategies
- **Machine Learning Integration**: Random Forest, Gradient Boosting, and Logistic Regression models
- **Real-time Market Analysis**: 5-minute trading cycles with live market data
- **Advanced Risk Management**: Position sizing, stop-loss, take-profit, and drawdown protection
- **Multi-Pair Trading**: Simultaneous trading across multiple cryptocurrency pairs

### Advanced Features
- **Sentiment Analysis**: Social media and news sentiment integration
- **Arbitrage Detection**: Cross-exchange price difference monitoring
- **Performance Analytics**: Comprehensive metrics including Sharpe ratio, win rate, and drawdown analysis
- **Web Dashboard**: Real-time monitoring and control interface
- **Database Storage**: PostgreSQL for trade history and performance tracking
- **Redis Caching**: High-performance data caching for market data

### Risk Management
- **Position Sizing**: Dynamic position sizing based on account balance and risk tolerance
- **Stop Loss/Take Profit**: Automatic order placement for risk control
- **Daily Loss Limits**: Configurable daily loss thresholds
- **Consecutive Loss Protection**: Automatic trading suspension after consecutive losses
- **Maximum Drawdown Protection**: Emergency stop on excessive drawdown

## 📊 Performance Metrics

The bot tracks comprehensive performance metrics:
- **Sharpe Ratio**: Risk-adjusted returns
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Value at Risk (VaR)**: 95% confidence interval for potential losses
- **Volatility**: Standard deviation of returns

## 🛠 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Redis server
- Kraken API credentials

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd kraken_trading_bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
# Kraken API credentials
KRAKEN_API_KEY=your_api_key_here
KRAKEN_SECRET_KEY=your_secret_key_here

# Database configuration
DATABASE_URL=postgresql://user:password@localhost/kraken_bot

# Redis configuration
REDIS_URL=redis://localhost:6379

# Trading configuration
TRADING_PAIRS=["XBT/USD", "ETH/USD", "ADA/USD", "DOT/USD", "LINK/USD"]
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
STOP_LOSS_PCT=0.02
TAKE_PROFIT_PCT=0.04

# Machine learning
ENABLE_ML=true
ML_MODEL_PATH=models/
ML_RETRAIN_INTERVAL=24

# Web interface
WEB_PORT=8000
WEB_HOST=0.0.0.0
```

4. **Initialize database**
```bash
python -c "from models.database import init_db; init_db()"
```

5. **Train initial ML models**
```bash
python -c "from main import KrakenTradingBot; import asyncio; bot = KrakenTradingBot(); asyncio.run(bot.train_ml_models())"
```

## 🚀 Usage

### Start the Trading Bot
```bash
python main.py
```

### Start the Web Interface
```bash
python web_interface.py
```

The web interface will be available at `http://localhost:8000`

### API Endpoints

#### Status and Monitoring
- `GET /api/status` - Bot status and metrics
- `GET /api/positions` - Current positions
- `GET /api/trades` - Trade history
- `GET /api/performance` - Performance metrics

#### Market Data
- `GET /api/market-data/{symbol}` - OHLCV data
- `GET /api/chart/{symbol}` - Interactive charts
- `GET /api/symbols` - Available trading pairs

#### Trading Operations
- `POST /api/order` - Place orders
- `DELETE /api/order/{order_id}` - Cancel orders
- `GET /api/orders` - Open orders

#### Configuration
- `GET /api/config` - Current configuration
- `GET /api/risk-limits` - Risk management settings
- `POST /api/risk-limits` - Update risk limits

## 📈 Strategy Details

### Technical Analysis Strategies

#### RSI Strategy
- **Period**: 14 (configurable)
- **Oversold**: 30
- **Overbought**: 70
- **Signal**: Buy on oversold crossover, sell on overbought crossover

#### MACD Strategy
- **Fast Period**: 12
- **Slow Period**: 26
- **Signal Period**: 9
- **Signal**: Buy on positive histogram crossover, sell on negative

#### Bollinger Bands Strategy
- **Period**: 20
- **Standard Deviation**: 2.0
- **Signal**: Buy at lower band, sell at upper band

#### Volume Strategy
- **Volume Threshold**: 1.5x average
- **Price Change Threshold**: 1%
- **Signal**: High volume with price movement

#### Moving Average Strategy
- **Fast MA**: 10-period
- **Slow MA**: 30-period
- **Signal**: Golden cross (buy), death cross (sell)

### Machine Learning Models

#### Feature Engineering
- Technical indicators (RSI, MACD, Bollinger Bands)
- Price momentum and volatility
- Volume metrics
- Moving averages
- Price ratios and returns

#### Model Types
- **Random Forest**: 100 estimators, max depth 10
- **Gradient Boosting**: 100 estimators, max depth 5
- **Logistic Regression**: L2 regularization

#### Ensemble Approach
- Weighted voting based on model performance
- Dynamic weight adjustment
- Confidence-based signal filtering

## 🔧 Configuration

### Trading Parameters
```python
# Risk Management
MAX_POSITION_SIZE = 0.1      # 10% of portfolio per trade
MAX_DAILY_LOSS = 0.05        # 5% daily loss limit
STOP_LOSS_PCT = 0.02         # 2% stop loss
TAKE_PROFIT_PCT = 0.04       # 4% take profit

# Strategy Weights
STRATEGY_WEIGHTS = {
    "rsi": 0.2,
    "macd": 0.2,
    "bollinger": 0.15,
    "volume": 0.1,
    "machine_learning": 0.25,
    "sentiment": 0.1
}
```

### Emergency Stop Conditions
```python
EMERGENCY_STOP_CONDITIONS = {
    "max_daily_loss": 0.05,
    "max_consecutive_losses": 5,
    "max_drawdown": 0.15,
    "market_volatility_threshold": 0.1
}
```

## 📊 Performance Tracking

The bot maintains comprehensive performance records:

### Database Tables
- **trades**: Executed trades with P&L
- **orders**: Order history and status
- **market_data**: OHLCV data storage
- **performance**: Daily performance metrics
- **strategies**: Strategy signal history
- **sentiment**: Sentiment analysis data
- **arbitrage**: Arbitrage opportunities

### Key Metrics
- **Total P&L**: Cumulative profit/loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Consecutive Wins/Losses**: Streak tracking

## 🔒 Security Features

- **API Key Encryption**: Secure storage of exchange credentials
- **Rate Limiting**: Respects exchange API limits
- **Error Handling**: Comprehensive exception handling
- **Logging**: Detailed audit trail
- **Backup**: Automatic database backups

## 🚨 Risk Warnings

⚠️ **Important**: This trading bot is for educational and research purposes. Cryptocurrency trading involves substantial risk of loss. Never trade with money you cannot afford to lose.

### Risk Factors
- **Market Volatility**: Cryptocurrency markets are highly volatile
- **Technical Risk**: Software bugs or API failures
- **Regulatory Risk**: Changing regulations may affect trading
- **Liquidity Risk**: Some pairs may have low liquidity
- **Execution Risk**: Slippage and partial fills

### Recommendations
- Start with small amounts
- Monitor performance closely
- Set appropriate risk limits
- Keep API keys secure
- Regular performance reviews

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines and ensure all tests pass before submitting pull requests.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black .
flake8 .
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the logs for debugging

## 🔄 Updates

The bot is continuously improved with:
- New trading strategies
- Enhanced ML models
- Improved risk management
- Better performance analytics
- Additional exchange integrations

---

**Disclaimer**: This software is provided "as is" without warranty. Trading cryptocurrencies involves risk, and past performance does not guarantee future results. Use at your own risk.