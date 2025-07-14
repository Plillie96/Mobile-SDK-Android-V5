"""
Kraken API Client for trading operations
"""
import asyncio
import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import ccxt.async_support as ccxt
from loguru import logger
import sys
import os

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import config

class KrakenClient:
    """Advanced Kraken API client with comprehensive trading functionality"""
    
    def __init__(self, api_key: str = None, secret_key: str = None, sandbox: bool = True):
        self.api_key = api_key or config.KRAKEN_API_KEY
        self.secret_key = secret_key or config.KRAKEN_SECRET_KEY
        self.sandbox = sandbox or config.KRAKEN_SANDBOX
        
        # Initialize CCXT exchange
        self.exchange = ccxt.kraken({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'sandbox': self.sandbox,
            'enableRateLimit': True,
            'options': {
                'adjustForTimeDifference': True,
            }
        })
        
        self.session = None
        self.base_url = "https://api.kraken.com" if not self.sandbox else "https://api.kraken.com"
        
    async def __aenter__(self):
        await self.exchange.load_markets()
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exchange.close()
        if self.session:
            await self.session.close()
    
    def _get_kraken_signature(self, urlpath: str, data: Dict, nonce: str) -> str:
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        
        signature = hmac.new(
            base64.b64decode(self.secret_key),
            message,
            hashlib.sha512
        )
        sigdigest = base64.b64encode(signature.digest())
        
        return sigdigest.decode()
    
    async def _make_private_request(self, endpoint: str, data: Dict) -> Dict:
        """Make authenticated private API request"""
        nonce = str(int(time.time() * 1000))
        data['nonce'] = nonce
        
        urlpath = f'/0/private/{endpoint}'
        signature = self._get_kraken_signature(urlpath, data, nonce)
        
        headers = {
            'API-Key': self.api_key,
            'API-Sign': signature,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        async with self.session.post(
            f"{self.base_url}{urlpath}",
            data=data,
            headers=headers
        ) as response:
            result = await response.json()
            if result.get('error'):
                logger.error(f"Kraken API error: {result['error']}")
                raise Exception(f"Kraken API error: {result['error']}")
            return result['result']
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            return {k: v['free'] for k, v in balance['total'].items() if v['free'] > 0}
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {}
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker information"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'last': ticker['last'],
                'volume': ticker['baseVolume'],
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}
    
    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Get order book for a symbol"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            return {
                'symbol': symbol,
                'bids': orderbook['bids'],
                'asks': orderbook['asks'],
                'timestamp': orderbook['timestamp']
            }
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return {}
    
    async def get_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> List[Dict]:
        """Get OHLCV data"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return [
                {
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
                for candle in ohlcv
            ]
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    async def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """Place a market order"""
        try:
            order = await self.exchange.create_market_order(symbol, side, amount)
            logger.info(f"Market order placed: {order}")
            return order
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return {}
    
    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """Place a limit order"""
        try:
            order = await self.exchange.create_limit_order(symbol, side, amount, price)
            logger.info(f"Limit order placed: {order}")
            return order
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return {}
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open orders"""
        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []
    
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status"""
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            return {}
    
    async def get_trade_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history"""
        try:
            trades = await self.exchange.fetch_my_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            return []
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        try:
            positions = await self.exchange.fetch_positions()
            return [pos for pos in positions if pos['size'] != 0]
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    async def get_funding_rate(self, symbol: str) -> float:
        """Get funding rate for perpetual futures"""
        try:
            # Note: Kraken doesn't have perpetual futures, this is for compatibility
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching funding rate: {e}")
            return 0.0
    
    async def get_server_time(self) -> Dict[str, Any]:
        """Get server time"""
        try:
            time_data = await self.exchange.fetch_time()
            return {'timestamp': time_data}
        except Exception as e:
            logger.error(f"Error fetching server time: {e}")
            return {}
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        try:
            markets = await self.exchange.load_markets()
            return {
                'markets': markets,
                'symbols': list(markets.keys()),
                'currencies': list(self.exchange.currencies.keys())
            }
        except Exception as e:
            logger.error(f"Error fetching exchange info: {e}")
            return {}
    
    async def get_24hr_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get 24-hour ticker statistics"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'priceChange': ticker['change'],
                'priceChangePercent': ticker['percentage'],
                'weightedAvgPrice': ticker['average'],
                'prevClosePrice': ticker['previousClose'],
                'lastPrice': ticker['last'],
                'lastQty': ticker['lastQty'],
                'bidPrice': ticker['bid'],
                'askPrice': ticker['ask'],
                'openPrice': ticker['open'],
                'highPrice': ticker['high'],
                'lowPrice': ticker['low'],
                'volume': ticker['baseVolume'],
                'quoteVolume': ticker['quoteVolume'],
                'openTime': ticker['openTime'],
                'closeTime': ticker['closeTime'],
                'count': ticker['count']
            }
        except Exception as e:
            logger.error(f"Error fetching 24hr ticker for {symbol}: {e}")
            return {}