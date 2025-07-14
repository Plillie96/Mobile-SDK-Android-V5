#!/bin/bash

# Kraken Trading Bot Deployment Script
# This script sets up and deploys the trading bot on a server

set -e

echo "🚀 Kraken Trading Bot Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Checking system requirements..."

# Check available disk space (need at least 5GB)
AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
if [ "$AVAILABLE_SPACE" -lt 5242880 ]; then
    print_error "Insufficient disk space. Need at least 5GB available."
    exit 1
fi

# Check available memory (need at least 2GB)
TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
if [ "$TOTAL_MEM" -lt 2048 ]; then
    print_warning "Low memory detected. Recommended: 4GB+ RAM"
fi

print_status "System requirements check passed"

# Create necessary directories
print_status "Creating directories..."
mkdir -p logs data models monitoring/grafana/dashboards monitoring/grafana/datasources nginx

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file..."
    cat > .env << EOF
# Kraken API Configuration
KRAKEN_API_KEY=your_api_key_here
KRAKEN_SECRET_KEY=your_secret_key_here
KRAKEN_SANDBOX=true

# Database Configuration
DATABASE_URL=postgresql://postgres:password@postgres:5432/kraken_bot
REDIS_URL=redis://redis:6379

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot.log

# Trading Parameters
TRADING_PAIRS=["XBT/USD","ETH/USD","ADA/USD"]
BASE_CURRENCY=USD
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.02
MAX_DAILY_TRADES=50
MIN_TRADE_AMOUNT=10.0

# Risk Management
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.04
TRAILING_STOP=true
TRAILING_STOP_PERCENTAGE=0.01

# Technical Analysis
RSI_PERIOD=14
RSI_OVERBOUGHT=70
RSI_OVERSOLD=30
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
BOLLINGER_PERIOD=20
BOLLINGER_STD=2.0

# Web Interface
WEB_PORT=8080
WEB_HOST=0.0.0.0

# Monitoring
PROMETHEUS_PORT=8000
GRAFANA_URL=http://localhost:3000

# External APIs (optional)
ALPHA_VANTAGE_API_KEY=
NEWS_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF
    print_warning "Please edit .env file with your Kraken API credentials before starting the bot"
fi

# Create database initialization script
print_status "Creating database initialization script..."
cat > init.sql << EOF
-- Initialize Kraken Bot Database
CREATE DATABASE IF NOT EXISTS kraken_bot;

-- Create tables for trading data
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    size DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    order_id VARCHAR(100) UNIQUE,
    fees DECIMAL(20,8) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    size DECIMAL(20,8) NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    current_price DECIMAL(20,8) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    trailing_stop DECIMAL(20,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(20,8) NOT NULL,
    high DECIMAL(20,8) NOT NULL,
    low DECIMAL(20,8) NOT NULL,
    close DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    total_return DECIMAL(20,8) NOT NULL,
    return_rate DECIMAL(10,4) NOT NULL,
    total_value DECIMAL(20,8) NOT NULL,
    max_drawdown DECIMAL(10,4) NOT NULL,
    daily_pnl DECIMAL(20,8) NOT NULL,
    daily_trades INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
EOF

# Create Prometheus configuration
print_status "Creating Prometheus configuration..."
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'kraken-trading-bot'
    static_configs:
      - targets: ['trading-bot:8000']
    scrape_interval: 5s
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF

# Create Grafana datasource configuration
print_status "Creating Grafana datasource configuration..."
mkdir -p monitoring/grafana/datasources
cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Create Nginx configuration
print_status "Creating Nginx configuration..."
cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream trading_bot {
        server trading-bot:8080;
    }

    upstream grafana {
        server grafana:3000;
    }

    upstream prometheus {
        server prometheus:9090;
    }

    server {
        listen 80;
        server_name localhost;

        # Trading Bot API
        location / {
            proxy_pass http://trading_bot;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Grafana Dashboard
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Prometheus Metrics
        location /prometheus/ {
            proxy_pass http://prometheus/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF

# Create systemd service file
print_status "Creating systemd service file..."
sudo tee /etc/systemd/system/kraken-trading-bot.service > /dev/null << EOF
[Unit]
Description=Kraken Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Build and start the services
print_status "Building Docker images..."
docker-compose build

print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check service status
print_status "Checking service status..."
docker-compose ps

print_status "Deployment completed successfully!"
echo ""
echo "🌐 Access Points:"
echo "   Trading Bot Dashboard: http://localhost"
echo "   Grafana Dashboard: http://localhost/grafana (admin/admin)"
echo "   Prometheus Metrics: http://localhost/prometheus"
echo ""
echo "📊 Monitoring:"
echo "   View logs: docker-compose logs -f trading-bot"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo ""
echo "⚠️  IMPORTANT:"
echo "   1. Edit .env file with your Kraken API credentials"
echo "   2. Set KRAKEN_SANDBOX=false for live trading"
echo "   3. Monitor the bot carefully in sandbox mode first"
echo ""
print_status "Deployment script completed!"