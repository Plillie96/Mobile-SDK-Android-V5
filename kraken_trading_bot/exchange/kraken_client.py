"""
Kraken exchange client for trading operations
"""
import krakenex
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import time
import asyncio
import aiohttp
from loguru import logger

from config import config

class KrakenClient:
    """Kraken exchange client with advanced trading capabilities"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or config.kraken_api_key
        self.secret_key = secret_key or config.kraken_secret_key
        
        # Initialize Kraken API
        self.kraken = krakenex.API(
            key=self.api_key,
            secret=self.secret_key
        )
        
        # Initialize CCXT for additional functionality
        self.ccxt_kraken = ccxt.kraken({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'sandbox': False,  # Set to True for testing
            'enableRateLimit': True
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Cache for market data
        self.market_data_cache = {}
        self.cache_duration = 60  # seconds
        
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance
        
        Returns:
            Dictionary of asset balances
        """
        try:
            self._rate_limit()
            balance = self.kraken.query_private('Balance')
            
            if balance['error']:
                logger.error(f"Error getting balance: {balance['error']}")
                return {}
            
            # Convert to float values
            balances = {}
            for asset, amount in balance['result'].items():
                if float(amount) > 0:
                    balances[asset] = float(amount)
            
            return balances
            
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {}
    
    def get_ticker_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker information for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'XBTUSD')
            
        Returns:
            Dictionary with ticker information
        """
        try:
            self._rate_limit()
            ticker = self.kraken.query_public('Ticker', {'pair': symbol})
            
            if ticker['error']:
                logger.error(f"Error getting ticker: {ticker['error']}")
                return {}
            
            return ticker['result']
            
        except Exception as e:
            logger.error(f"Error getting ticker info: {e}")
            return {}
    
    def get_ohlcv(self, symbol: str, interval: int = 1, since: int = None) -> pd.DataFrame:
        """
        Get OHLCV data
        
        Args:
            symbol: Trading pair symbol
            interval: Time interval in minutes
            since: Timestamp to start from
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{interval}_{since}"
            if cache_key in self.market_data_cache:
                cached_data, cache_time = self.market_data_cache[cache_key]
                if time.time() - cache_time < self.cache_duration:
                    return cached_data
            
            self._rate_limit()
            
            # Use CCXT for OHLCV data
            ohlcv = self.ccxt_kraken.fetch_ohlcv(
                symbol=symbol,
                timeframe=f'{interval}m',
                since=since,
                limit=1000
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Cache the data
            self.market_data_cache[cache_key] = (df, time.time())
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data: {e}")
            return pd.DataFrame()
    
    def get_order_book(self, symbol: str, depth: int = 10) -> Dict[str, List]:
        """
        Get order book
        
        Args:
            symbol: Trading pair symbol
            depth: Number of orders to retrieve
            
        Returns:
            Dictionary with bids and asks
        """
        try:
            self._rate_limit()
            orderbook = self.kraken.query_public('Depth', {
                'pair': symbol,
                'count': depth
            })
            
            if orderbook['error']:
                logger.error(f"Error getting order book: {orderbook['error']}")
                return {'bids': [], 'asks': []}
            
            return orderbook['result']
            
        except Exception as e:
            logger.error(f"Error getting order book: {e}")
            return {'bids': [], 'asks': []}
    
    def place_market_order(self, symbol: str, side: str, volume: float) -> Dict[str, Any]:
        """
        Place a market order
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            volume: Order volume
            
        Returns:
            Order response
        """
        try:
            self._rate_limit()
            
            order_params = {
                'pair': symbol,
                'type': side,
                'ordertype': 'market',
                'volume': str(volume)
            }
            
            result = self.kraken.query_private('AddOrder', order_params)
            
            if result['error']:
                logger.error(f"Error placing market order: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            logger.info(f"Market order placed: {side} {volume} {symbol}")
            return {'success': True, 'result': result['result']}
            
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return {'success': False, 'error': str(e)}
    
    def place_limit_order(self, symbol: str, side: str, volume: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            volume: Order volume
            price: Order price
            
        Returns:
            Order response
        """
        try:
            self._rate_limit()
            
            order_params = {
                'pair': symbol,
                'type': side,
                'ordertype': 'limit',
                'volume': str(volume),
                'price': str(price)
            }
            
            result = self.kraken.query_private('AddOrder', order_params)
            
            if result['error']:
                logger.error(f"Error placing limit order: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            logger.info(f"Limit order placed: {side} {volume} {symbol} @ {price}")
            return {'success': True, 'result': result['result']}
            
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return {'success': False, 'error': str(e)}
    
    def place_stop_loss_order(self, symbol: str, side: str, volume: float, stop_price: float) -> Dict[str, Any]:
        """
        Place a stop-loss order
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            volume: Order volume
            stop_price: Stop price
            
        Returns:
            Order response
        """
        try:
            self._rate_limit()
            
            order_params = {
                'pair': symbol,
                'type': side,
                'ordertype': 'stop-loss',
                'volume': str(volume),
                'price': str(stop_price)
            }
            
            result = self.kraken.query_private('AddOrder', order_params)
            
            if result['error']:
                logger.error(f"Error placing stop-loss order: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            logger.info(f"Stop-loss order placed: {side} {volume} {symbol} @ {stop_price}")
            return {'success': True, 'result': result['result']}
            
        except Exception as e:
            logger.error(f"Error placing stop-loss order: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancellation response
        """
        try:
            self._rate_limit()
            
            result = self.kraken.query_private('CancelOrder', {'txid': order_id})
            
            if result['error']:
                logger.error(f"Error canceling order: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            logger.info(f"Order canceled: {order_id}")
            return {'success': True, 'result': result['result']}
            
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_open_orders(self) -> List[Dict[str, Any]]:
        """
        Get open orders
        
        Returns:
            List of open orders
        """
        try:
            self._rate_limit()
            
            result = self.kraken.query_private('OpenOrders')
            
            if result['error']:
                logger.error(f"Error getting open orders: {result['error']}")
                return []
            
            return result['result']['open']
            
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return []
    
    def get_closed_orders(self, start: int = None, end: int = None) -> List[Dict[str, Any]]:
        """
        Get closed orders
        
        Args:
            start: Start timestamp
            end: End timestamp
            
        Returns:
            List of closed orders
        """
        try:
            self._rate_limit()
            
            params = {}
            if start:
                params['start'] = start
            if end:
                params['end'] = end
            
            result = self.kraken.query_private('ClosedOrders', params)
            
            if result['error']:
                logger.error(f"Error getting closed orders: {result['error']}")
                return []
            
            return result['result']['closed']
            
        except Exception as e:
            logger.error(f"Error getting closed orders: {e}")
            return []
    
    def get_trade_history(self, start: int = None, end: int = None) -> List[Dict[str, Any]]:
        """
        Get trade history
        
        Args:
            start: Start timestamp
            end: End timestamp
            
        Returns:
            List of trades
        """
        try:
            self._rate_limit()
            
            params = {}
            if start:
                params['start'] = start
            if end:
                params['end'] = end
            
            result = self.kraken.query_private('TradesHistory', params)
            
            if result['error']:
                logger.error(f"Error getting trade history: {result['error']}")
                return []
            
            return result['result']['trades']
            
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []
    
    def get_server_time(self) -> Dict[str, Any]:
        """
        Get server time
        
        Returns:
            Server time information
        """
        try:
            self._rate_limit()
            
            result = self.kraken.query_public('Time')
            
            if result['error']:
                logger.error(f"Error getting server time: {result['error']}")
                return {}
            
            return result['result']
            
        except Exception as e:
            logger.error(f"Error getting server time: {e}")
            return {}
    
    def get_asset_info(self) -> Dict[str, Any]:
        """
        Get asset information
        
        Returns:
            Asset information
        """
        try:
            self._rate_limit()
            
            result = self.kraken.query_public('Assets')
            
            if result['error']:
                logger.error(f"Error getting asset info: {result['error']}")
                return {}
            
            return result['result']
            
        except Exception as e:
            logger.error(f"Error getting asset info: {e}")
            return {}
    
    def get_tradable_asset_pairs(self) -> Dict[str, Any]:
        """
        Get tradable asset pairs
        
        Returns:
            Tradable asset pairs information
        """
        try:
            self._rate_limit()
            
            result = self.kraken.query_public('AssetPairs')
            
            if result['error']:
                logger.error(f"Error getting asset pairs: {result['error']}")
                return {}
            
            return result['result']
            
        except Exception as e:
            logger.error(f"Error getting asset pairs: {e}")
            return {}
    
    def calculate_fees(self, symbol: str, volume: float, price: float) -> Dict[str, float]:
        """
        Calculate trading fees
        
        Args:
            symbol: Trading pair symbol
            volume: Trade volume
            price: Trade price
            
        Returns:
            Dictionary with fee information
        """
        try:
            # Get fee information from asset pairs
            pairs = self.get_tradable_asset_pairs()
            
            if symbol not in pairs:
                return {'maker_fee': 0.0, 'taker_fee': 0.0}
            
            pair_info = pairs[symbol]
            
            # Default Kraken fees (may vary based on volume)
            maker_fee = float(pair_info.get('fees', [0.16])[0]) / 100
            taker_fee = float(pair_info.get('fees', [0.26])[0]) / 100
            
            trade_value = volume * price
            
            return {
                'maker_fee': trade_value * maker_fee,
                'taker_fee': trade_value * taker_fee,
                'maker_fee_rate': maker_fee,
                'taker_fee_rate': taker_fee
            }
            
        except Exception as e:
            logger.error(f"Error calculating fees: {e}")
            return {'maker_fee': 0.0, 'taker_fee': 0.0}
    
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get market status and trading info
        
        Returns:
            Market status information
        """
        try:
            self._rate_limit()
            
            result = self.kraken.query_public('SystemStatus')
            
            if result['error']:
                logger.error(f"Error getting system status: {result['error']}")
                return {}
            
            return result['result']
            
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {}