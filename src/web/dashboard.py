"""
FastAPI Web Dashboard for Kraken Trading Bot
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import config
from trading_bot import KrakenTradingBot

app = FastAPI(
    title="Kraken Trading Bot Dashboard",
    description="Real-time monitoring and control for the Kraken trading bot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
bot: Optional[KrakenTradingBot] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the trading bot on startup"""
    global bot
    try:
        bot = KrakenTradingBot()
        await bot.initialize()
        print("Trading bot initialized successfully")
    except Exception as e:
        print(f"Failed to initialize trading bot: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the trading bot"""
    global bot
    if bot:
        await bot.shutdown()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kraken Trading Bot Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .metric-card { border-left: 4px solid #007bff; }
            .profit { color: #28a745; }
            .loss { color: #dc3545; }
            .status-running { color: #28a745; }
            .status-stopped { color: #dc3545; }
            .chart-container { height: 400px; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container-fluid">
                <span class="navbar-brand mb-0 h1">
                    <i class="fas fa-robot"></i> Kraken Trading Bot Dashboard
                </span>
                <span class="navbar-text">
                    <span id="status-indicator" class="status-running">
                        <i class="fas fa-circle"></i> Running
                    </span>
                </span>
            </div>
        </nav>

        <div class="container-fluid mt-4">
            <div class="row">
                <!-- Performance Metrics -->
                <div class="col-md-3">
                    <div class="card metric-card">
                        <div class="card-body">
                            <h5 class="card-title">Total Return</h5>
                            <h3 id="total-return" class="profit">$0.00</h3>
                            <small class="text-muted">All time</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card">
                        <div class="card-body">
                            <h5 class="card-title">Daily P&L</h5>
                            <h3 id="daily-pnl" class="profit">$0.00</h3>
                            <small class="text-muted">Today</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card">
                        <div class="card-body">
                            <h5 class="card-title">Active Positions</h5>
                            <h3 id="active-positions">0</h3>
                            <small class="text-muted">Open trades</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card">
                        <div class="card-body">
                            <h5 class="card-title">Win Rate</h5>
                            <h3 id="win-rate">0%</h3>
                            <small class="text-muted">Success rate</small>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <!-- Trading Activity -->
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-chart-line"></i> Trading Activity</h5>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="trading-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Trades -->
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-list"></i> Recent Trades</h5>
                        </div>
                        <div class="card-body">
                            <div id="recent-trades" style="max-height: 300px; overflow-y: auto;">
                                <p class="text-muted">No recent trades</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <!-- Active Positions -->
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-positions"></i> Active Positions</h5>
                        </div>
                        <div class="card-body">
                            <div id="active-positions-list">
                                <p class="text-muted">No active positions</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Strategy Performance -->
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-chart-pie"></i> Strategy Performance</h5>
                        </div>
                        <div class="card-body">
                            <div id="strategy-performance">
                                <p class="text-muted">Loading strategy data...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // Update dashboard data every 5 seconds
            setInterval(updateDashboard, 5000);
            
            async function updateDashboard() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    // Update metrics
                    document.getElementById('total-return').textContent = '$' + data.performance_metrics.total_return.toFixed(2);
                    document.getElementById('daily-pnl').textContent = '$' + data.performance_metrics.daily_pnl.toFixed(2);
                    document.getElementById('active-positions').textContent = Object.keys(data.risk_report.positions).length;
                    
                    // Update status
                    const statusIndicator = document.getElementById('status-indicator');
                    if (data.is_running) {
                        statusIndicator.className = 'status-running';
                        statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Running';
                    } else {
                        statusIndicator.className = 'status-stopped';
                        statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Stopped';
                    }
                    
                    // Update recent trades
                    updateRecentTrades(data.recent_trades);
                    
                    // Update active positions
                    updateActivePositions(data.risk_report.positions);
                    
                    // Update strategy performance
                    updateStrategyPerformance(data.performance_metrics.strategy_performance);
                    
                } catch (error) {
                    console.error('Error updating dashboard:', error);
                }
            }
            
            function updateRecentTrades(trades) {
                const container = document.getElementById('recent-trades');
                if (!trades || trades.length === 0) {
                    container.innerHTML = '<p class="text-muted">No recent trades</p>';
                    return;
                }
                
                let html = '';
                trades.slice(0, 10).forEach(trade => {
                    const pnlClass = trade.pnl >= 0 ? 'profit' : 'loss';
                    html += `
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div>
                                <strong>${trade.symbol}</strong><br>
                                <small class="text-muted">${trade.side} ${trade.size}</small>
                            </div>
                            <div class="text-end">
                                <div class="${pnlClass}">$${trade.pnl.toFixed(2)}</div>
                                <small class="text-muted">$${trade.price}</small>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            }
            
            function updateActivePositions(positions) {
                const container = document.getElementById('active-positions-list');
                if (!positions || Object.keys(positions).length === 0) {
                    container.innerHTML = '<p class="text-muted">No active positions</p>';
                    return;
                }
                
                let html = '';
                Object.entries(positions).forEach(([symbol, pos]) => {
                    const pnlClass = pos.unrealized_pnl >= 0 ? 'profit' : 'loss';
                    html += `
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div>
                                <strong>${symbol}</strong><br>
                                <small class="text-muted">${pos.side} ${pos.size}</small>
                            </div>
                            <div class="text-end">
                                <div class="${pnlClass}">$${pos.unrealized_pnl.toFixed(2)}</div>
                                <small class="text-muted">$${pos.current_price}</small>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            }
            
            function updateStrategyPerformance(strategies) {
                const container = document.getElementById('strategy-performance');
                if (!strategies || Object.keys(strategies).length === 0) {
                    container.innerHTML = '<p class="text-muted">No strategy data available</p>';
                    return;
                }
                
                let html = '';
                Object.entries(strategies).forEach(([name, perf]) => {
                    const winRate = perf.win_rate ? (perf.win_rate * 100).toFixed(1) : '0';
                    const totalReturn = perf.total_return ? perf.total_return.toFixed(2) : '0';
                    html += `
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div>
                                <strong>${name.replace('_', ' ').toUpperCase()}</strong><br>
                                <small class="text-muted">Win Rate: ${winRate}%</small>
                            </div>
                            <div class="text-end">
                                <div>$${totalReturn}</div>
                                <small class="text-muted">${perf.total_trades || 0} trades</small>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            }
            
            // Initial load
            updateDashboard();
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/status")
async def get_status():
    """Get current bot status"""
    global bot
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        status = bot.get_status()
        
        # Add recent trades (last 10)
        recent_trades = []
        if hasattr(bot.risk_manager, 'trades'):
            recent_trades = bot.risk_manager.trades[-10:]
        
        status['recent_trades'] = recent_trades
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start")
async def start_bot(background_tasks: BackgroundTasks):
    """Start the trading bot"""
    global bot
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    if bot.is_running:
        return {"message": "Bot is already running"}
    
    try:
        background_tasks.add_task(bot.run)
        return {"message": "Bot started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop")
async def stop_bot():
    """Stop the trading bot"""
    global bot
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        bot.is_running = False
        return {"message": "Bot stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance")
async def get_performance():
    """Get performance metrics"""
    global bot
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        return bot.performance_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions():
    """Get current positions"""
    global bot
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        return bot.risk_manager.get_risk_report()['positions']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies")
async def get_strategies():
    """Get strategy performance"""
    global bot
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        return bot.strategy_manager.get_strategy_performance()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest")
async def run_backtest(start_date: str, end_date: str, initial_balance: float = 10000):
    """Run backtest"""
    global bot
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        results = await bot.backtest(start_date, end_date, initial_balance)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "dashboard:app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        reload=True
    )