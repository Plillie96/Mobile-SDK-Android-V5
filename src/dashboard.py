"""
Trading Bot Dashboard
Web-based dashboard for monitoring and controlling the trading bot
"""
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import threading
import time

from config import config


class TradingDashboard:
    """Web dashboard for trading bot monitoring"""
    
    def __init__(self, trading_bot):
        self.trading_bot = trading_bot
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()
        
    def setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Kraken Trading Bot Dashboard", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Status Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Bot Status", className="card-title"),
                            html.H2(id="bot-status", className="text-success"),
                            html.P("Trading Bot Status")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Account Value", className="card-title"),
                            html.H2(id="account-value", className="text-primary"),
                            html.P("Current Account Value")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Total P&L", className="card-title"),
                            html.H2(id="total-pnl", className="text-info"),
                            html.P("Total Profit/Loss")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Open Positions", className="card-title"),
                            html.H2(id="open-positions", className="text-warning"),
                            html.P("Number of Open Positions")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Charts Row
            dbc.Row([
                # Price Chart
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Price Chart"),
                        dbc.CardBody([
                            dcc.Graph(id="price-chart")
                        ])
                    ])
                ], width=8),
                
                # Performance Metrics
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Performance Metrics"),
                        dbc.CardBody([
                            html.Div(id="performance-metrics")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            # Signals and Positions Row
            dbc.Row([
                # Trading Signals
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Trading Signals"),
                        dbc.CardBody([
                            html.Div(id="trading-signals")
                        ])
                    ])
                ], width=6),
                
                # Open Positions
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Open Positions"),
                        dbc.CardBody([
                            html.Div(id="open-positions-table")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Risk Management Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Risk Management"),
                        dbc.CardBody([
                            html.Div(id="risk-metrics")
                        ])
                    ])
                ], width=6),
                
                # Trade History
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Recent Trades"),
                        dbc.CardBody([
                            html.Div(id="trade-history")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Control Panel"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button("Start Bot", id="start-bot", color="success", className="me-2"),
                                    dbc.Button("Stop Bot", id="stop-bot", color="danger", className="me-2"),
                                    dbc.Button("Close All Positions", id="close-positions", color="warning")
                                ])
                            ]),
                            html.Hr(),
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Update Interval (seconds):"),
                                    dcc.Slider(
                                        id="update-interval",
                                        min=5,
                                        max=60,
                                        step=5,
                                        value=30,
                                        marks={i: str(i) for i in range(5, 61, 10)}
                                    )
                                ])
                            ])
                        ])
                    ])
                ])
            ]),
            
            # Hidden div for storing data
            html.Div(id="data-store", style={"display": "none"}),
            
            # Interval component for updates
            dcc.Interval(
                id="interval-component",
                interval=30*1000,  # 30 seconds
                n_intervals=0
            )
        ], fluid=True)
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output("bot-status", "children"),
             Output("account-value", "children"),
             Output("total-pnl", "children"),
             Output("open-positions", "children")],
            [Input("interval-component", "n_intervals")]
        )
        def update_status_cards(n):
            try:
                status = self.trading_bot.get_status()
                
                bot_status = "🟢 Running" if status['is_running'] else "🔴 Stopped"
                account_value = f"${status['account_value']:,.2f}"
                total_pnl = f"${status.get('performance_metrics', {}).get('total_pnl', 0):,.2f}"
                open_positions = str(status['positions'])
                
                return bot_status, account_value, total_pnl, open_positions
            except Exception as e:
                return "❌ Error", "$0.00", "$0.00", "0"
        
        @self.app.callback(
            Output("price-chart", "figure"),
            [Input("interval-component", "n_intervals")]
        )
        def update_price_chart(n):
            try:
                # Get market data for first trading pair
                if not self.trading_bot.market_data:
                    return go.Figure()
                
                symbol = list(self.trading_bot.market_data.keys())[0]
                if symbol.endswith('_current'):
                    symbol = symbol.replace('_current', '')
                
                if symbol not in self.trading_bot.market_data:
                    return go.Figure()
                
                df = self.trading_bot.market_data[symbol]
                
                # Create candlestick chart
                fig = make_subplots(
                    rows=3, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=(f'{symbol} Price', 'Volume', 'RSI'),
                    row_heights=[0.6, 0.2, 0.2]
                )
                
                # Candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=df.index,
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        name='OHLC'
                    ),
                    row=1, col=1
                )
                
                # Volume
                fig.add_trace(
                    go.Bar(
                        x=df.index,
                        y=df['volume'],
                        name='Volume',
                        marker_color='rgba(0,0,255,0.3)'
                    ),
                    row=2, col=1
                )
                
                # RSI
                if 'rsi' in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df['rsi'],
                            name='RSI',
                            line=dict(color='purple')
                        ),
                        row=3, col=1
                    )
                    
                    # Add RSI overbought/oversold lines
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
                
                fig.update_layout(
                    title=f'{symbol} Price Chart',
                    xaxis_rangeslider_visible=False,
                    height=600
                )
                
                return fig
                
            except Exception as e:
                return go.Figure()
        
        @self.app.callback(
            Output("performance-metrics", "children"),
            [Input("interval-component", "n_intervals")]
        )
        def update_performance_metrics(n):
            try:
                metrics = self.trading_bot.performance_metrics
                
                if not metrics:
                    return html.P("No performance data available")
                
                return html.Div([
                    html.Div([
                        html.Strong("Sharpe Ratio: "),
                        html.Span(f"{metrics.get('sharpe_ratio', 0):.3f}")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Max Drawdown: "),
                        html.Span(f"{metrics.get('max_drawdown', 0)*100:.2f}%")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Volatility: "),
                        html.Span(f"{metrics.get('volatility', 0)*100:.2f}%")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("VaR (95%): "),
                        html.Span(f"${metrics.get('var_95', 0):,.2f}")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Daily P&L: "),
                        html.Span(f"${metrics.get('daily_pnl', 0):,.2f}")
                    ], className="mb-2")
                ])
                
            except Exception as e:
                return html.P("Error loading performance metrics")
        
        @self.app.callback(
            Output("trading-signals", "children"),
            [Input("interval-component", "n_intervals")]
        )
        def update_trading_signals(n):
            try:
                signals = self.trading_bot.signals
                
                if not signals:
                    return html.P("No signals available")
                
                signal_cards = []
                for symbol, signal in signals.items():
                    color = "success" if signal['signal'] == 'buy' else "danger" if signal['signal'] == 'sell' else "secondary"
                    
                    signal_cards.append(
                        dbc.Card([
                            dbc.CardBody([
                                html.H6(symbol, className="card-title"),
                                html.P(f"Signal: {signal['signal'].upper()}", className=f"text-{color}"),
                                html.P(f"Strength: {signal['strength']:.3f}"),
                                html.P(f"Confidence: {signal['confidence']:.3f}"),
                                html.Small(f"Indicators: {', '.join(signal.get('indicators', []))}")
                            ])
                        ], className="mb-2")
                    )
                
                return html.Div(signal_cards)
                
            except Exception as e:
                return html.P("Error loading trading signals")
        
        @self.app.callback(
            Output("open-positions-table", "children"),
            [Input("interval-component", "n_intervals")]
        )
        def update_open_positions(n):
            try:
                positions = self.trading_bot.risk_manager.positions
                
                if not positions:
                    return html.P("No open positions")
                
                table_header = [
                    html.Thead(html.Tr([
                        html.Th("Symbol"),
                        html.Th("Side"),
                        html.Th("Size"),
                        html.Th("Entry Price"),
                        html.Th("Current Price"),
                        html.Th("P&L")
                    ]))
                ]
                
                table_rows = []
                for symbol, position in positions.items():
                    pnl_color = "success" if position.unrealized_pnl > 0 else "danger"
                    
                    table_rows.append(html.Tr([
                        html.Td(symbol),
                        html.Td(position.side),
                        html.Td(f"{position.size:.4f}"),
                        html.Td(f"${position.entry_price:.2f}"),
                        html.Td(f"${position.current_price:.2f}"),
                        html.Td(f"${position.unrealized_pnl:.2f}", className=f"text-{pnl_color}")
                    ]))
                
                table_body = [html.Tbody(table_rows)]
                
                return dbc.Table(table_header + table_body, striped=True, bordered=True, hover=True)
                
            except Exception as e:
                return html.P("Error loading positions")
        
        @self.app.callback(
            Output("risk-metrics", "children"),
            [Input("interval-component", "n_intervals")]
        )
        def update_risk_metrics(n):
            try:
                risk_report = self.trading_bot.get_risk_report()
                
                if not risk_report:
                    return html.P("No risk data available")
                
                metrics = risk_report.get('metrics', {})
                limits = risk_report.get('risk_limits', {})
                current = risk_report.get('current_limits', {})
                
                return html.Div([
                    html.Div([
                        html.Strong("Max Position Size: "),
                        html.Span(f"{limits.get('max_position_size', 0)*100:.1f}%")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Max Drawdown: "),
                        html.Span(f"{limits.get('max_drawdown', 0)*100:.1f}%")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Daily Loss Limit: "),
                        html.Span(f"{limits.get('daily_loss_limit', 0)*100:.1f}%")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Current Drawdown: "),
                        html.Span(f"{current.get('current_drawdown', 0)*100:.2f}%")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Daily Loss: "),
                        html.Span(f"${current.get('daily_loss', 0):,.2f}")
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Trade Count: "),
                        html.Span(str(current.get('trade_count', 0)))
                    ], className="mb-2")
                ])
                
            except Exception as e:
                return html.P("Error loading risk metrics")
        
        @self.app.callback(
            Output("trade-history", "children"),
            [Input("interval-component", "n_intervals")]
        )
        def update_trade_history(n):
            try:
                trade_history = self.trading_bot.trade_history
                
                if not trade_history:
                    return html.P("No trade history")
                
                # Show last 10 trades
                recent_trades = trade_history[-10:]
                
                table_header = [
                    html.Thead(html.Tr([
                        html.Th("Symbol"),
                        html.Th("Side"),
                        html.Th("Entry"),
                        html.Th("Exit"),
                        html.Th("P&L"),
                        html.Th("Time")
                    ]))
                ]
                
                table_rows = []
                for trade in recent_trades:
                    pnl_color = "success" if trade['pnl'] > 0 else "danger"
                    
                    table_rows.append(html.Tr([
                        html.Td(trade['symbol']),
                        html.Td(trade['side']),
                        html.Td(f"${trade['entry_price']:.2f}"),
                        html.Td(f"${trade['exit_price']:.2f}"),
                        html.Td(f"${trade['pnl']:.2f}", className=f"text-{pnl_color}"),
                        html.Td(trade['timestamp'].strftime("%H:%M:%S"))
                    ]))
                
                table_body = [html.Tbody(table_rows)]
                
                return dbc.Table(table_header + table_body, striped=True, bordered=True, hover=True)
                
            except Exception as e:
                return html.P("Error loading trade history")
        
        @self.app.callback(
            Output("interval-component", "interval"),
            [Input("update-interval", "value")]
        )
        def update_interval(value):
            return value * 1000  # Convert to milliseconds
    
    def run(self, host: str = "0.0.0.0", port: int = 8050, debug: bool = False):
        """Run the dashboard"""
        self.app.run_server(host=host, port=port, debug=debug)


def create_dashboard(trading_bot):
    """Create and return dashboard instance"""
    return TradingDashboard(trading_bot)