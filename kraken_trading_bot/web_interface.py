"""
Web interface for the Kraken Trading Bot
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Dict, Any, List
import asyncio
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import json

from config import config
from exchange.kraken_client import KrakenClient
from risk_management import RiskManager

app = FastAPI(title="Kraken Trading Bot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
exchange_client = None
risk_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global exchange_client, risk_manager
    
    exchange_client = KrakenClient()
    risk_manager = RiskManager()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Kraken Trading Bot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/status")
async def get_status():
    """Get bot status"""
    try:
        # Get server time
        server_time = exchange_client.get_server_time()
        
        # Get account balance
        balance = exchange_client.get_account_balance()
        
        # Get risk metrics
        risk_metrics = risk_manager.calculate_risk_metrics()
        
        return {
            "status": "running",
            "server_time": server_time,
            "account_balance": balance,
            "risk_metrics": {
                "total_pnl": risk_metrics.total_pnl,
                "daily_pnl": risk_metrics.daily_pnl,
                "max_drawdown": risk_metrics.max_drawdown,
                "sharpe_ratio": risk_metrics.sharpe_ratio,
                "win_rate": risk_metrics.win_rate,
                "total_trades": risk_metrics.total_trades
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions():
    """Get current positions"""
    try:
        position_summary = risk_manager.get_position_summary()
        return position_summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades")
async def get_trades(limit: int = 100):
    """Get recent trades"""
    try:
        trades = risk_manager.trade_history[-limit:] if risk_manager.trade_history else []
        
        # Convert datetime objects to strings for JSON serialization
        for trade in trades:
            trade['entry_time'] = trade['entry_time'].isoformat()
            trade['exit_time'] = trade['exit_time'].isoformat()
        
        return {
            "trades": trades,
            "total_count": len(risk_manager.trade_history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Get market data for a symbol"""
    try:
        # Convert timeframe to minutes
        timeframe_map = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": 1440
        }
        
        interval = timeframe_map.get(timeframe, 60)
        
        # Get OHLCV data
        data = exchange_client.get_ohlcv(symbol, interval=interval)
        
        if data.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Limit data points
        data = data.tail(limit)
        
        # Convert to JSON-serializable format
        market_data = []
        for timestamp, row in data.iterrows():
            market_data.append({
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": market_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chart/{symbol}")
async def get_chart(symbol: str, timeframe: str = "1h"):
    """Get chart data for a symbol"""
    try:
        # Get market data
        data = exchange_client.get_ohlcv(symbol, interval=60)  # 1-hour data
        
        if data.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Create candlestick chart
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(f'{symbol} Price', 'Volume'),
            row_width=[0.7, 0.3]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name=symbol
            ),
            row=1, col=1
        )
        
        # Volume chart
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['volume'],
                name='Volume'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Chart',
            xaxis_rangeslider_visible=False,
            height=600
        )
        
        # Convert to JSON
        chart_json = fig.to_json()
        
        return {
            "symbol": symbol,
            "chart": json.loads(chart_json)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance")
async def get_performance(days: int = 30):
    """Get performance metrics"""
    try:
        # Get risk metrics
        risk_metrics = risk_manager.calculate_risk_metrics()
        
        # Get trade history summary
        trade_summary = risk_manager.get_trade_history_summary(days)
        
        # Calculate additional metrics
        total_balance = sum(exchange_client.get_account_balance().values())
        
        return {
            "risk_metrics": {
                "total_pnl": risk_metrics.total_pnl,
                "daily_pnl": risk_metrics.daily_pnl,
                "max_drawdown": risk_metrics.max_drawdown,
                "sharpe_ratio": risk_metrics.sharpe_ratio,
                "win_rate": risk_metrics.win_rate,
                "profit_factor": risk_metrics.profit_factor,
                "total_trades": risk_metrics.total_trades,
                "winning_trades": risk_metrics.winning_trades,
                "losing_trades": risk_metrics.losing_trades,
                "avg_win": risk_metrics.avg_win,
                "avg_loss": risk_metrics.avg_loss,
                "largest_win": risk_metrics.largest_win,
                "largest_loss": risk_metrics.largest_loss,
                "consecutive_wins": risk_metrics.consecutive_wins,
                "consecutive_losses": risk_metrics.consecutive_losses,
                "volatility": risk_metrics.volatility,
                "var_95": risk_metrics.var_95
            },
            "trade_summary": trade_summary,
            "account_balance": total_balance,
            "period_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/symbols")
async def get_symbols():
    """Get available trading symbols"""
    try:
        return {
            "trading_pairs": config.trading_pairs,
            "available_pairs": list(exchange_client.get_tradable_asset_pairs().keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/order")
async def place_order(symbol: str, side: str, quantity: float, order_type: str = "market", price: float = None):
    """Place an order"""
    try:
        if order_type == "market":
            result = exchange_client.place_market_order(symbol, side, quantity)
        elif order_type == "limit" and price:
            result = exchange_client.place_limit_order(symbol, side, quantity, price)
        else:
            raise HTTPException(status_code=400, detail="Invalid order type or missing price")
        
        if result['success']:
            return {
                "success": True,
                "order_id": result['result']['txid'][0] if 'txid' in result['result'] else None,
                "message": f"{side.capitalize()} order placed successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/order/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order"""
    try:
        result = exchange_client.cancel_order(order_id)
        
        if result['success']:
            return {
                "success": True,
                "message": "Order cancelled successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def get_orders():
    """Get open orders"""
    try:
        orders = exchange_client.get_open_orders()
        return {
            "orders": orders,
            "count": len(orders)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/risk-limits")
async def get_risk_limits():
    """Get current risk limits and status"""
    try:
        should_stop, reason = risk_manager.should_stop_trading()
        
        return {
            "max_position_size": risk_manager.max_position_size,
            "max_daily_loss": risk_manager.max_daily_loss,
            "stop_loss_pct": risk_manager.stop_loss_pct,
            "take_profit_pct": risk_manager.take_profit_pct,
            "should_stop_trading": should_stop,
            "stop_reason": reason,
            "consecutive_losses": risk_manager.consecutive_losses,
            "daily_pnl": risk_manager.daily_pnl
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/risk-limits")
async def update_risk_limits(
    max_position_size: float = None,
    max_daily_loss: float = None,
    stop_loss_pct: float = None,
    take_profit_pct: float = None
):
    """Update risk limits"""
    try:
        if max_position_size is not None:
            risk_manager.max_position_size = max_position_size
        if max_daily_loss is not None:
            risk_manager.max_daily_loss = max_daily_loss
        if stop_loss_pct is not None:
            risk_manager.stop_loss_pct = stop_loss_pct
        if take_profit_pct is not None:
            risk_manager.take_profit_pct = take_profit_pct
        
        return {
            "success": True,
            "message": "Risk limits updated successfully",
            "new_limits": {
                "max_position_size": risk_manager.max_position_size,
                "max_daily_loss": risk_manager.max_daily_loss,
                "stop_loss_pct": risk_manager.stop_loss_pct,
                "take_profit_pct": risk_manager.take_profit_pct
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    try:
        return {
            "trading_pairs": config.trading_pairs,
            "enable_machine_learning": config.enable_machine_learning,
            "enable_sentiment_analysis": config.enable_sentiment_analysis,
            "enable_news_trading": config.enable_news_trading,
            "enable_arbitrage": config.enable_arbitrage,
            "strategy_weights": STRATEGY_WEIGHTS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_web_interface():
    """Run the web interface"""
    uvicorn.run(
        app,
        host=config.web_host,
        port=config.web_port,
        reload=False
    )

if __name__ == "__main__":
    run_web_interface()