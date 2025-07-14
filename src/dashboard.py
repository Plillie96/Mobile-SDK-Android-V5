"""
Trading Bot Dashboard
Web interface for monitoring and controlling the trading bot
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

class TradingDashboard:
    """Web Dashboard for Trading Bot Monitoring"""
    
    def __init__(self, trading_bot):
        self.trading_bot = trading_bot
        self.app = FastAPI(title="Kraken Trading Bot Dashboard", version="1.0.0")
        self.websocket_connections: List[WebSocket] = []
        
        # Setup routes
        self.setup_routes()
        
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            return HTMLResponse(self.get_dashboard_html())
        
        @self.app.get("/api/status")
        async def get_status():
            """Get bot status"""
            try:
                return {
                    "is_running": self.trading_bot.is_running,
                    "portfolio_value": self.trading_bot.portfolio_value,
                    "open_positions": len(self.trading_bot.risk_manager.positions),
                    "last_update": datetime.now().isoformat(),
                    "emergency_stop": self.trading_bot.emergency_stop_triggered
                }
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/performance")
        async def get_performance():
            """Get performance statistics"""
            try:
                return self.trading_bot.get_performance_stats()
            except Exception as e:
                logger.error(f"Error getting performance: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/positions")
        async def get_positions():
            """Get current positions"""
            try:
                positions = []
                for symbol, position in self.trading_bot.risk_manager.positions.items():
                    positions.append({
                        "symbol": symbol,
                        "side": position.side,
                        "size": position.size,
                        "entry_price": position.entry_price,
                        "current_price": position.current_price,
                        "pnl": position.pnl,
                        "pnl_percentage": position.pnl_percentage,
                        "entry_time": position.entry_time.isoformat(),
                        "stop_loss": position.stop_loss,
                        "take_profit": position.take_profit
                    })
                return positions
            except Exception as e:
                logger.error(f"Error getting positions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/risk-metrics")
        async def get_risk_metrics():
            """Get risk metrics"""
            try:
                metrics = self.trading_bot.risk_manager.get_risk_metrics(self.trading_bot.portfolio_value)
                return {
                    "total_pnl": metrics.total_pnl,
                    "total_pnl_percentage": metrics.total_pnl_percentage,
                    "daily_pnl": metrics.daily_pnl,
                    "daily_pnl_percentage": metrics.daily_pnl_percentage,
                    "max_drawdown": metrics.max_drawdown,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "volatility": metrics.volatility,
                    "var_95": metrics.var_95,
                    "position_count": metrics.position_count,
                    "open_positions": metrics.open_positions
                }
            except Exception as e:
                logger.error(f"Error getting risk metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/start")
        async def start_bot():
            """Start the trading bot"""
            try:
                if not self.trading_bot.is_running:
                    asyncio.create_task(self.trading_bot.run())
                    return {"message": "Trading bot started"}
                else:
                    return {"message": "Trading bot is already running"}
            except Exception as e:
                logger.error(f"Error starting bot: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/stop")
        async def stop_bot():
            """Stop the trading bot"""
            try:
                self.trading_bot.is_running = False
                return {"message": "Trading bot stopped"}
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/emergency-stop")
        async def emergency_stop():
            """Emergency stop - close all positions"""
            try:
                await self.trading_bot.emergency_stop()
                return {"message": "Emergency stop executed"}
            except Exception as e:
                logger.error(f"Error emergency stop: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Send real-time updates every 5 seconds
                    await asyncio.sleep(5)
                    
                    # Get current status
                    status = {
                        "timestamp": datetime.now().isoformat(),
                        "portfolio_value": self.trading_bot.portfolio_value,
                        "open_positions": len(self.trading_bot.risk_manager.positions),
                        "is_running": self.trading_bot.is_running
                    }
                    
                    await websocket.send_text(json.dumps(status))
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
    
    def get_dashboard_html(self) -> str:
        """Get the main dashboard HTML"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Kraken Trading Bot Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                .status-card { margin-bottom: 20px; }
                .metric-card { text-align: center; padding: 15px; }
                .positive { color: #28a745; }
                .negative { color: #dc3545; }
                .neutral { color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <h1 class="mt-4 mb-4">Kraken Trading Bot Dashboard</h1>
                
                <!-- Status Section -->
                <div class="row">
                    <div class="col-md-3">
                        <div class="card status-card">
                            <div class="card-body">
                                <h5 class="card-title">Bot Status</h5>
                                <div id="bot-status">Loading...</div>
                                <button id="start-btn" class="btn btn-success btn-sm mt-2">Start</button>
                                <button id="stop-btn" class="btn btn-danger btn-sm mt-2">Stop</button>
                                <button id="emergency-btn" class="btn btn-warning btn-sm mt-2">Emergency Stop</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-3">
                        <div class="card status-card">
                            <div class="card-body">
                                <h5 class="card-title">Portfolio Value</h5>
                                <div id="portfolio-value" class="h4">$0.00</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-3">
                        <div class="card status-card">
                            <div class="card-body">
                                <h5 class="card-title">Open Positions</h5>
                                <div id="open-positions" class="h4">0</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-3">
                        <div class="card status-card">
                            <div class="card-body">
                                <h5 class="card-title">Total P&L</h5>
                                <div id="total-pnl" class="h4">$0.00</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Performance Metrics -->
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Performance Metrics</h5>
                                <div class="row" id="performance-metrics">
                                    <div class="col-md-2 metric-card">
                                        <div class="h6">Win Rate</div>
                                        <div id="win-rate">0%</div>
                                    </div>
                                    <div class="col-md-2 metric-card">
                                        <div class="h6">Total Trades</div>
                                        <div id="total-trades">0</div>
                                    </div>
                                    <div class="col-md-2 metric-card">
                                        <div class="h6">Sharpe Ratio</div>
                                        <div id="sharpe-ratio">0.00</div>
                                    </div>
                                    <div class="col-md-2 metric-card">
                                        <div class="h6">Max Drawdown</div>
                                        <div id="max-drawdown">0%</div>
                                    </div>
                                    <div class="col-md-2 metric-card">
                                        <div class="h6">Daily P&L</div>
                                        <div id="daily-pnl">$0.00</div>
                                    </div>
                                    <div class="col-md-2 metric-card">
                                        <div class="h6">Volatility</div>
                                        <div id="volatility">0%</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Charts -->
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Portfolio Value Over Time</h5>
                                <canvas id="portfolio-chart"></canvas>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">P&L Distribution</h5>
                                <canvas id="pnl-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Positions Table -->
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Current Positions</h5>
                                <div class="table-responsive">
                                    <table class="table table-striped" id="positions-table">
                                        <thead>
                                            <tr>
                                                <th>Symbol</th>
                                                <th>Side</th>
                                                <th>Size</th>
                                                <th>Entry Price</th>
                                                <th>Current Price</th>
                                                <th>P&L</th>
                                                <th>P&L %</th>
                                                <th>Entry Time</th>
                                            </tr>
                                        </thead>
                                        <tbody id="positions-tbody">
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // WebSocket connection
                const ws = new WebSocket('ws://localhost:8000/ws');
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                };
                
                // Update dashboard with real-time data
                function updateDashboard(data) {
                    document.getElementById('portfolio-value').textContent = '$' + data.portfolio_value.toLocaleString();
                    document.getElementById('open-positions').textContent = data.open_positions;
                }
                
                // API calls
                async function fetchData(endpoint) {
                    try {
                        const response = await fetch('/api/' + endpoint);
                        return await response.json();
                    } catch (error) {
                        console.error('Error fetching data:', error);
                        return null;
                    }
                }
                
                // Update all dashboard data
                async function updateAllData() {
                    // Update status
                    const status = await fetchData('status');
                    if (status) {
                        document.getElementById('bot-status').textContent = status.is_running ? 'Running' : 'Stopped';
                        document.getElementById('portfolio-value').textContent = '$' + status.portfolio_value.toLocaleString();
                        document.getElementById('open-positions').textContent = status.open_positions;
                    }
                    
                    // Update performance
                    const performance = await fetchData('performance');
                    if (performance && performance.win_rate !== undefined) {
                        document.getElementById('win-rate').textContent = (performance.win_rate * 100).toFixed(1) + '%';
                        document.getElementById('total-trades').textContent = performance.total_trades;
                        document.getElementById('sharpe-ratio').textContent = performance.sharpe_ratio.toFixed(2);
                        document.getElementById('total-pnl').textContent = '$' + performance.total_pnl.toFixed(2);
                        document.getElementById('total-pnl').className = performance.total_pnl >= 0 ? 'h4 positive' : 'h4 negative';
                    }
                    
                    // Update risk metrics
                    const riskMetrics = await fetchData('risk-metrics');
                    if (riskMetrics) {
                        document.getElementById('max-drawdown').textContent = (riskMetrics.max_drawdown * 100).toFixed(1) + '%';
                        document.getElementById('daily-pnl').textContent = '$' + riskMetrics.daily_pnl.toFixed(2);
                        document.getElementById('volatility').textContent = (riskMetrics.volatility * 100).toFixed(1) + '%';
                    }
                    
                    // Update positions
                    const positions = await fetchData('positions');
                    if (positions) {
                        updatePositionsTable(positions);
                    }
                }
                
                // Update positions table
                function updatePositionsTable(positions) {
                    const tbody = document.getElementById('positions-tbody');
                    tbody.innerHTML = '';
                    
                    positions.forEach(position => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td>${position.symbol}</td>
                            <td>${position.side}</td>
                            <td>${position.size.toFixed(4)}</td>
                            <td>$${position.entry_price.toFixed(2)}</td>
                            <td>$${position.current_price.toFixed(2)}</td>
                            <td class="${position.pnl >= 0 ? 'positive' : 'negative'}">$${position.pnl.toFixed(2)}</td>
                            <td class="${position.pnl_percentage >= 0 ? 'positive' : 'negative'}">${(position.pnl_percentage * 100).toFixed(2)}%</td>
                            <td>${new Date(position.entry_time).toLocaleString()}</td>
                        `;
                    });
                }
                
                // Button event listeners
                document.getElementById('start-btn').addEventListener('click', async () => {
                    await fetch('/api/start', { method: 'POST' });
                    setTimeout(updateAllData, 1000);
                });
                
                document.getElementById('stop-btn').addEventListener('click', async () => {
                    await fetch('/api/stop', { method: 'POST' });
                    setTimeout(updateAllData, 1000);
                });
                
                document.getElementById('emergency-btn').addEventListener('click', async () => {
                    if (confirm('Are you sure you want to execute emergency stop? This will close all positions.')) {
                        await fetch('/api/emergency-stop', { method: 'POST' });
                        setTimeout(updateAllData, 1000);
                    }
                });
                
                // Initial load
                updateAllData();
                
                // Update every 30 seconds
                setInterval(updateAllData, 30000);
            </script>
        </body>
        </html>
        """
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the dashboard server"""
        try:
            uvicorn.run(self.app, host=host, port=port)
        except Exception as e:
            logger.error(f"Error running dashboard: {e}")

def create_dash_app(trading_bot):
    """Create a Dash app for advanced analytics"""
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Trading Bot Analytics", className="text-center mb-4"),
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Portfolio Performance", className="card-title"),
                        dcc.Graph(id='portfolio-performance-chart')
                    ])
                ])
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Trade Analysis", className="card-title"),
                        dcc.Graph(id='trade-analysis-chart')
                    ])
                ])
            ])
        ]),
        
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # 30 seconds
            n_intervals=0
        )
    ])
    
    @app.callback(
        Output('portfolio-performance-chart', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_portfolio_chart(n):
        try:
            # Get trade history
            trades = trading_bot.trade_history
            
            if not trades:
                return go.Figure().add_annotation(
                    text="No trades recorded yet",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
            
            # Create portfolio value over time
            df = pd.DataFrame(trades)
            df['cumulative_pnl'] = df['pnl'].cumsum()
            df['portfolio_value'] = df['portfolio_value']
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Portfolio Value', 'Cumulative P&L'),
                vertical_spacing=0.1
            )
            
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['portfolio_value'], 
                          mode='lines', name='Portfolio Value'),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['cumulative_pnl'], 
                          mode='lines', name='Cumulative P&L'),
                row=2, col=1
            )
            
            fig.update_layout(height=600, showlegend=True)
            return fig
            
        except Exception as e:
            logger.error(f"Error updating portfolio chart: {e}")
            return go.Figure()
    
    @app.callback(
        Output('trade-analysis-chart', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_trade_chart(n):
        try:
            trades = trading_bot.trade_history
            
            if not trades:
                return go.Figure().add_annotation(
                    text="No trades recorded yet",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
            
            df = pd.DataFrame(trades)
            
            # P&L distribution
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('P&L Distribution', 'Win/Loss Ratio'),
                specs=[[{"type": "histogram"}, {"type": "pie"}]]
            )
            
            fig.add_trace(
                go.Histogram(x=df['pnl'], nbinsx=20, name='P&L Distribution'),
                row=1, col=1
            )
            
            # Win/Loss pie chart
            winning_trades = len(df[df['pnl'] > 0])
            losing_trades = len(df[df['pnl'] < 0])
            
            fig.add_trace(
                go.Pie(labels=['Winning', 'Losing'], 
                      values=[winning_trades, losing_trades],
                      name='Win/Loss Ratio'),
                row=1, col=2
            )
            
            fig.update_layout(height=400, showlegend=True)
            return fig
            
        except Exception as e:
            logger.error(f"Error updating trade chart: {e}")
            return go.Figure()
    
    return app