"""
Kraken Exchange Interface
Handles all interactions with the Kraken API
"""
import asyncio
import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import aiohttp
import ccxt
import krakenex
from config import config
import logging

logger = logging.getLogger(__name__)

@dataclass
class Order:
    """Order data structure"""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    type: str  # 'market', 'limit', 'stop'
    amount: float
    price: Optional[float] = None
    status: str = 'open'
    filled: float = 0.0
    remaining: float = 0.0
    cost: float = 0.0
    fee: float = 0.0
    timestamp: int = 0

@dataclass
class Balance:
    """Balance data structure"""
    currency: str
    free: float
    used: float
    total: float

class KrakenExchange:
    """Advanced Kraken Exchange Interface"""
    
    def __init__(self):
        self.api_key = config.kraken_api_key
        self.secret_key = config.kraken_secret_key
        self.base_url = "https://api.kraken.com"
        self.session = None
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        
        # Initialize CCXT for additional functionality
        self.ccxt_exchange = ccxt.kraken({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'sandbox': False,
            'enableRateLimit': True,
        })
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _sign_message(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Sign API request for private endpoints"""
        if not self.api_key or not self.secret_key:
            raise ValueError("API credentials not configured")
            
        nonce = str(int(time.time() * 1000))
        data['nonce'] = nonce
        
        # Create signature
        post_data = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + post_data).encode()
        message = endpoint.encode() + hashlib.sha256(encoded).digest()
        
        signature = hmac.new(
            base64.b64decode(self.secret_key),
            message,
            hashlib.sha512
        )
        sig_digest = base64.b64encode(signature.digest())
        
        return {
            'API-Key': self.api_key,
            'API-Sign': sig_digest.decode(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker information"""
        await self._rate_limit()
        
        try:
            ticker = await self.ccxt_exchange.fetch_ticker(symbol)
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
            raise
    
    async def get_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> List[Dict[str, Any]]:
        """Get OHLCV data"""
        await self._rate_limit()
        
        try:
            ohlcv = await self.ccxt_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
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
            raise
    
    async def get_balance(self) -> List[Balance]:
        """Get account balance"""
        await self._rate_limit()
        
        try:
            balance = await self.ccxt_exchange.fetch_balance()
            balances = []
            
            for currency, amounts in balance['total'].items():
                if amounts > 0:
                    balances.append(Balance(
                        currency=currency,
                        free=balance['free'].get(currency, 0),
                        used=balance['used'].get(currency, 0),
                        total=amounts
                    ))
            
            return balances
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    async def place_order(self, symbol: str, side: str, order_type: str, 
                         amount: float, price: Optional[float] = None) -> Order:
        """Place a new order"""
        await self._rate_limit()
        
        try:
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': amount
            }
            
            if price and order_type == 'limit':
                order_params['price'] = price
            
            result = await self.ccxt_exchange.create_order(**order_params)
            
            return Order(
                id=result['id'],
                symbol=result['symbol'],
                side=result['side'],
                type=result['type'],
                amount=result['amount'],
                price=result.get('price'),
                status=result['status'],
                filled=result.get('filled', 0),
                remaining=result.get('remaining', 0),
                cost=result.get('cost', 0),
                fee=result.get('fee', {}).get('cost', 0) if result.get('fee') else 0,
                timestamp=result['timestamp']
            )
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an existing order"""
        await self._rate_limit()
        
        try:
            result = await self.ccxt_exchange.cancel_order(order_id, symbol)
            return result['status'] == 'canceled'
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            raise
    
    async def get_order_status(self, order_id: str, symbol: str) -> Order:
        """Get order status"""
        await self._rate_limit()
        
        try:
            result = await self.ccxt_exchange.fetch_order(order_id, symbol)
            
            return Order(
                id=result['id'],
                symbol=result['symbol'],
                side=result['side'],
                type=result['type'],
                amount=result['amount'],
                price=result.get('price'),
                status=result['status'],
                filled=result.get('filled', 0),
                remaining=result.get('remaining', 0),
                cost=result.get('cost', 0),
                fee=result.get('fee', {}).get('cost', 0) if result.get('fee') else 0,
                timestamp=result['timestamp']
            )
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            raise
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders"""
        await self._rate_limit()
        
        try:
            orders = await self.ccxt_exchange.fetch_open_orders(symbol)
            
            return [
                Order(
                    id=order['id'],
                    symbol=order['symbol'],
                    side=order['side'],
                    type=order['type'],
                    amount=order['amount'],
                    price=order.get('price'),
                    status=order['status'],
                    filled=order.get('filled', 0),
                    remaining=order.get('remaining', 0),
                    cost=order.get('cost', 0),
                    fee=order.get('fee', {}).get('cost', 0) if order.get('fee') else 0,
                    timestamp=order['timestamp']
                )
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise
    
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history"""
        await self._rate_limit()
        
        try:
            trades = await self.ccxt_exchange.fetch_my_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            raise
    
    def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """Get trading fees for a symbol"""
        try:
            fees = self.ccxt_exchange.fetch_trading_fees()
            return fees.get(symbol, {})
        except Exception as e:
            logger.error(f"Error fetching trading fees: {e}")
            return {'maker': 0.0016, 'taker': 0.0026}  # Default Kraken fees