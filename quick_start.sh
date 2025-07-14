#!/bin/bash

# Kraken Trading Bot - Quick Start Script
# This script helps you get the trading bot running quickly

set -e

echo "🚀 Kraken Trading Bot - Quick Start"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs models data

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚙️  Creating configuration file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Kraken API credentials"
    echo "   You can get them from: https://www.kraken.com/u/settings/api"
    echo ""
    echo "🔧 Important settings to configure:"
    echo "   - KRAKEN_API_KEY"
    echo "   - KRAKEN_SECRET_KEY"
    echo "   - KRAKEN_SANDBOX=true (for testing)"
    echo ""
    echo "⚠️  Please edit .env file before running the bot!"
    exit 0
fi

# Check if API keys are configured
if grep -q "your_api_key_here" .env; then
    echo "⚠️  Warning: API keys not configured in .env file"
    echo "   Please edit .env file with your actual API credentials"
    echo ""
    echo "🔧 You can get API keys from: https://www.kraken.com/u/settings/api"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Available commands:"
echo "   python main.py --mode bot          # Run trading bot"
echo "   python main.py --mode dashboard    # Run web dashboard"
echo "   python main.py --mode backtest     # Run backtest"
echo "   python main.py --mode bot --sandbox # Run in sandbox mode"
echo ""
echo "📊 Dashboard will be available at: http://localhost:8050"
echo ""
echo "⚠️  Remember:"
echo "   - Start with sandbox mode for testing"
echo "   - Use small amounts initially"
echo "   - Monitor performance closely"
echo "   - This is for educational purposes only"
echo ""
echo "🎯 Happy trading!"