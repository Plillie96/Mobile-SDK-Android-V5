# 🚀 Kraken Trading Bot - Top 0.1% Performance

A sophisticated algorithmic trading bot for the Kraken cryptocurrency exchange, designed to achieve top-tier performance through advanced machine learning, technical analysis, and risk management.

## 🌟 Features

### 🤖 Advanced Trading Strategies
- **Multi-Strategy Ensemble**: Combines RSI, MACD, Bollinger Bands, and ML predictions
- **Machine Learning Integration**: Random Forest, Gradient Boosting, and Linear Regression models
- **Real-time Signal Generation**: Dynamic signal strength calculation and validation
- **Multi-timeframe Analysis**: 1m, 5m, 15m, 1h, 4h, 1d timeframes

### 🛡️ Risk Management
- **Kelly Criterion Position Sizing**: Optimal position sizing based on win rate and risk
- **Dynamic Stop Losses**: ATR and volatility-based stop loss calculation
- **Portfolio Protection**: Maximum drawdown limits and daily loss protection
- **Correlation Management**: Prevents over-concentration in similar assets
- **Emergency Stop**: Automatic position closure on risk threshold breaches

### 📊 Technical Analysis
- **Comprehensive Indicators**: RSI, MACD, Bollinger Bands, Stochastic, ADX, CCI
- **Volume Analysis**: VWAP and volume confirmation signals
- **Support/Resistance**: Dynamic level calculation
- **Volatility Measurement**: Real-time volatility tracking and adjustment

### 🧠 Machine Learning
- **Ensemble Models**: Multiple ML models for robust predictions
- **Feature Engineering**: 30+ technical and market features
- **Auto-retraining**: Models retrain automatically every 24 hours
- **Confidence Scoring**: Prediction confidence and signal strength

### 📈 Performance Monitoring
- **Real-time Dashboard**: Web-based monitoring interface
- **Performance Metrics**: Sharpe ratio, win rate, profit factor, max drawdown
- **Trade History**: Comprehensive trade logging and analysis
- **Risk Metrics**: VaR, volatility, and drawdown tracking

### 🔧 Advanced Features
- **Async Architecture**: High-performance async/await implementation
- **Rate Limiting**: Respects exchange API limits
- **Error Handling**: Robust error recovery and logging
- **Configuration Management**: Environment-based configuration
- **WebSocket Support**: Real-time data streaming

## 📋 Requirements

- Python 3.8+
- Kraken API credentials
- PostgreSQL (optional, for advanced features)
- Redis (optional, for caching)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd kraken-trading-bot

# Install dependencies
pip install -r requirements.txt

# Create configuration
python main.py --setup
```

### 2. Configuration

```bash
# Copy and edit the configuration template
cp .env.template .env

# Edit .env with your Kraken API credentials
nano .env
```

Required environment variables:
```env
KRAKEN_API_KEY=your_api_key_here
KRAKEN_SECRET_KEY=your_secret_key_here
```

### 3. Run the Bot

```bash
# Run with web dashboard (recommended)
python main.py --with-dashboard

# Run bot only
python main.py --bot-only

# Check status
python main.py --status
```

## 📊 Dashboard

Access the web dashboard at `http://localhost:8000` to monitor:

- **Real-time Portfolio Value**: Live portfolio tracking
- **Open Positions**: Current positions and P&L
- **Performance Metrics**: Win rate, Sharpe ratio, drawdown
- **Risk Metrics**: VaR, volatility, position exposure
- **Trade History**: Detailed trade analysis
- **Bot Controls**: Start/stop/emergency stop buttons

## 🔧 Configuration

### Trading Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_POSITION_SIZE` | 0.1 | Maximum position size (10% of portfolio) |
| `MAX_DAILY_LOSS` | 0.05 | Maximum daily loss (5%) |
| `STOP_LOSS_PERCENTAGE` | 0.02 | Stop loss percentage (2%) |
| `TAKE_PROFIT_PERCENTAGE` | 0.04 | Take profit percentage (4%) |

### Technical Analysis

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RSI_PERIOD` | 14 | RSI calculation period |
| `RSI_OVERSOLD` | 30 | RSI oversold threshold |
| `RSI_OVERBOUGHT` | 70 | RSI overbought threshold |
| `MACD_FAST` | 12 | MACD fast period |
| `MACD_SLOW` | 26 | MACD slow period |
| `BOLLINGER_PERIOD` | 20 | Bollinger Bands period |

### Strategy Weights

The bot uses ensemble weighting for signal generation:

```python
STRATEGY_WEIGHTS = {
    "rsi": 0.2,           # 20% weight
    "macd": 0.25,         # 25% weight
    "bollinger": 0.2,     # 20% weight
    "volume": 0.15,       # 15% weight
    "ml_prediction": 0.2  # 20% weight
}
```

## 🏗️ Architecture

```
kraken-trading-bot/
├── main.py                 # Main entry point
├── config.py              # Configuration management
├── requirements.txt       # Dependencies
├── src/
│   ├── __init__.py
│   ├── exchange.py        # Kraken API interface
│   ├── technical_analysis.py  # Technical indicators
│   ├── machine_learning.py    # ML models
│   ├── risk_management.py     # Risk management
│   ├── trading_bot.py         # Main bot logic
│   └── dashboard.py           # Web dashboard
├── models/                # ML model storage
├── logs/                  # Log files
└── .env                   # Configuration file
```

## 📈 Performance Metrics

The bot tracks comprehensive performance metrics:

- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Ratio of gross profit to gross loss
- **Value at Risk (VaR)**: 95% confidence interval loss estimate
- **Volatility**: Portfolio volatility measurement

## 🛡️ Risk Management Features

### Position Sizing
- Kelly Criterion-based sizing
- Volatility-adjusted position sizes
- Signal strength weighting

### Stop Losses
- Dynamic ATR-based stops
- Volatility-adjusted stops
- Trailing stop implementation

### Portfolio Protection
- Maximum daily loss limits
- Maximum drawdown protection
- Correlation limits
- Emergency stop functionality

## 🔍 Technical Indicators

### Momentum Indicators
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **Stochastic**: Stochastic Oscillator
- **Williams %R**: Williams Percent Range

### Trend Indicators
- **Moving Averages**: SMA, EMA (20, 50, 200)
- **ADX**: Average Directional Index
- **CCI**: Commodity Channel Index

### Volatility Indicators
- **Bollinger Bands**: Price channels
- **ATR**: Average True Range
- **Volatility**: Rolling standard deviation

### Volume Indicators
- **VWAP**: Volume Weighted Average Price
- **Volume Ratio**: Current vs average volume

## 🤖 Machine Learning

### Models Used
- **Random Forest**: Ensemble of decision trees
- **Gradient Boosting**: Sequential model training
- **Linear Regression**: Simple linear predictions
- **Ridge Regression**: Regularized linear model

### Features
- 30+ technical indicators
- Price-based features (returns, ratios)
- Volume features
- Time-based features (hour, day of week)
- Momentum and volatility features

### Training
- Automatic retraining every 24 hours
- Cross-validation for model selection
- Ensemble weighting for predictions
- Confidence scoring for signal strength

## 📊 Dashboard Features

### Real-time Monitoring
- Live portfolio value updates
- Open positions tracking
- P&L visualization
- Risk metrics display

### Performance Analytics
- Portfolio performance charts
- Trade distribution analysis
- Win/loss ratio visualization
- Drawdown tracking

### Bot Controls
- Start/stop functionality
- Emergency stop button
- Configuration updates
- Log viewing

## 🔧 Advanced Usage

### Custom Strategies

Add custom strategies by extending the `TechnicalAnalyzer` class:

```python
def custom_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
    # Your custom logic here
    return {'signal': 'buy', 'strength': 0.8}
```

### Custom Risk Management

Extend risk management by modifying the `RiskManager` class:

```python
def custom_risk_check(self, position: Position) -> bool:
    # Your custom risk logic
    return True
```

### Backtesting

Backtesting functionality is planned for future releases:

```bash
python main.py --backtest --start-date 2023-01-01 --end-date 2024-01-01
```

## 🚨 Important Notes

### Risk Disclaimer
- This bot is for educational and research purposes
- Cryptocurrency trading involves significant risk
- Past performance does not guarantee future results
- Always test with small amounts first

### API Limits
- Respects Kraken API rate limits
- Implements exponential backoff
- Handles API errors gracefully

### Security
- Never share your API credentials
- Use API keys with trading permissions only
- Regularly rotate API keys
- Monitor for unauthorized access

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify API credentials in `.env`
   - Check internet connection
   - Ensure API keys have trading permissions

2. **Insufficient Funds**
   - Check account balance
   - Verify minimum trade amounts
   - Adjust position sizing parameters

3. **Model Training Errors**
   - Ensure sufficient historical data
   - Check disk space for model storage
   - Verify feature calculation

### Logs

Check logs for detailed error information:

```bash
tail -f logs/trading_bot.log
```

## 📚 API Reference

### TradingBot Class

```python
class TradingBot:
    async def initialize() -> bool
    async def run()
    async def emergency_stop()
    def get_performance_stats() -> Dict[str, Any]
```

### RiskManager Class

```python
class RiskManager:
    def calculate_position_size() -> float
    def calculate_stop_loss() -> float
    def check_risk_limits() -> Dict[str, Any]
    def get_risk_metrics() -> RiskMetrics
```

### TechnicalAnalyzer Class

```python
class TechnicalAnalyzer:
    def analyze_all() -> pd.DataFrame
    def generate_signals() -> Dict[str, pd.Series]
    def calculate_support_resistance() -> Dict[str, float]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Kraken API for exchange integration
- TA-Lib for technical analysis
- Scikit-learn for machine learning
- FastAPI for web dashboard
- Plotly for data visualization

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the logs for error details

---

**⚠️ Disclaimer**: This software is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. Use at your own risk.