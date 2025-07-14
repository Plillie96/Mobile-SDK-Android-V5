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
from datetime import datetime, timedelta
import aiohttp
import ccxt
import krakenex
from loguru import logger

from config import config


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
    datetime: str = ''
    last_trade_timestamp: Optional[int] = None
    info: Optional[Dict] = None


@dataclass
class Trade:
    """Trade data structure"""
    id: str
    order_id: str
    symbol: str
    side: str
    amount: float
    price: float
    cost: float
    fee: float
    timestamp: int
    datetime: str
    info: Optional[Dict] = None


@dataclass
class Balance:
    """Balance data structure"""
    currency: str
    free: float
    used: float
    total: float


class KrakenExchange:
    """Kraken Exchange Interface"""
    
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
        
        # Initialize Krakenex for additional features
        self.kraken = krakenex.API(
            key=self.api_key,
            secret=self.secret_key
        )
        
        self.session = None
        self._rate_limits = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _sign_message(self, endpoint: str, data: Dict) -> Dict:
        """Sign API request for authentication"""
        if not self.api_key or not self.secret_key:
            raise ValueError("API key and secret are required for authenticated requests")
            
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
        sigdigest = base64.b64encode(signature.digest())
        
        return {
            'API-Key': self.api_key,
            'API-Sign': sigdigest.decode(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker information"""
        try:
            ticker = await asyncio.to_thread(self.exchange.fetch_ticker, symbol)
            return {
                'symbol': ticker['symbol'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'last': ticker['last'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'timestamp': ticker['timestamp'],
                'datetime': ticker['datetime']
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise
    
    async def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Get OHLCV data"""
        try:
            ohlcv = await asyncio.to_thread(
                self.exchange.fetch_ohlcv, 
                symbol, 
                timeframe, 
                limit=limit
            )
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
        try:
            balance = await asyncio.to_thread(self.exchange.fetch_balance)
            balances = []
            
            for currency, data in balance['total'].items():
                if data > 0:  # Only include currencies with balance
                    balances.append(Balance(
                        currency=currency,
                        free=balance['free'].get(currency, 0),
                        used=balance['used'].get(currency, 0),
                        total=data
                    ))
            
            return balances
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    async def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Get open orders"""
        try:
            orders = await asyncio.to_thread(self.exchange.fetch_open_orders, symbol)
            return [self._parse_order(order) for order in orders]
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise
    
    async def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Order]:
        """Get order history"""
        try:
            orders = await asyncio.to_thread(
                self.exchange.fetch_orders, 
                symbol, 
                limit=limit
            )
            return [self._parse_order(order) for order in orders]
        except Exception as e:
            logger.error(f"Error fetching order history: {e}")
            raise
    
    async def place_order(self, symbol: str, side: str, order_type: str, 
                         amount: float, price: float = None, 
                         stop_loss: float = None, take_profit: float = None) -> Order:
        """Place a new order"""
        try:
            # Validate order parameters
            if amount < config.MIN_TRADE_AMOUNT:
                raise ValueError(f"Order amount {amount} is below minimum {config.MIN_TRADE_AMOUNT}")
            
            # Prepare order parameters
            params = {}
            if stop_loss:
                params['stopLoss'] = stop_loss
            if take_profit:
                params['takeProfit'] = take_profit
            
            # Place the order
            order = await asyncio.to_thread(
                self.exchange.create_order,
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )
            
            logger.info(f"Order placed: {order['id']} - {side} {amount} {symbol} @ {price}")
            return self._parse_order(order)
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order"""
        try:
            result = await asyncio.to_thread(
                self.exchange.cancel_order,
                order_id,
                symbol
            )
            logger.info(f"Order cancelled: {order_id}")
            return result['status'] == 'canceled'
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise
    
    async def get_trade_history(self, symbol: str = None, limit: int = 100) -> List[Trade]:
        """Get trade history"""
        try:
            trades = await asyncio.to_thread(
                self.exchange.fetch_my_trades,
                symbol,
                limit=limit
            )
            return [self._parse_trade(trade) for trade in trades]
        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            raise
    
    def _parse_order(self, order_data: Dict) -> Order:
        """Parse order data from exchange format"""
        return Order(
            id=order_data['id'],
            symbol=order_data['symbol'],
            side=order_data['side'],
            type=order_data['type'],
            amount=order_data['amount'],
            price=order_data.get('price'),
            status=order_data['status'],
            filled=order_data.get('filled', 0),
            remaining=order_data.get('remaining', 0),
            cost=order_data.get('cost', 0),
            fee=order_data.get('fee', {}).get('cost', 0) if order_data.get('fee') else 0,
            timestamp=order_data['timestamp'],
            datetime=order_data['datetime'],
            last_trade_timestamp=order_data.get('lastTradeTimestamp'),
            info=order_data
        )
    
    def _parse_trade(self, trade_data: Dict) -> Trade:
        """Parse trade data from exchange format"""
        return Trade(
            id=trade_data['id'],
            order_id=trade_data['order'],
            symbol=trade_data['symbol'],
            side=trade_data['side'],
            amount=trade_data['amount'],
            price=trade_data['price'],
            cost=trade_data['cost'],
            fee=trade_data.get('fee', {}).get('cost', 0) if trade_data.get('fee') else 0,
            timestamp=trade_data['timestamp'],
            datetime=trade_data['datetime'],
            info=trade_data
        )
    
    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book"""
        try:
            orderbook = await asyncio.to_thread(
                self.exchange.fetch_order_book,
                symbol,
                limit
            )
            return {
                'bids': orderbook['bids'],
                'asks': orderbook['asks'],
                'timestamp': orderbook['timestamp'],
                'datetime': orderbook['datetime']
            }
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            raise
    
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades"""
        try:
            trades = await asyncio.to_thread(
                self.exchange.fetch_trades,
                symbol,
                limit=limit
            )
            return [
                {
                    'id': trade['id'],
                    'timestamp': trade['timestamp'],
                    'datetime': trade['datetime'],
                    'symbol': trade['symbol'],
                    'side': trade['side'],
                    'amount': trade['amount'],
                    'price': trade['price'],
                    'cost': trade['cost']
                }
                for trade in trades
            ]
        except Exception as e:
            logger.error(f"Error fetching recent trades for {symbol}: {e}")
            raise
    
    async def get_funding_rate(self, symbol: str) -> float:
        """Get funding rate for perpetual futures"""
        try:
            # Note: Kraken doesn't have perpetual futures, this is for compatibility
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching funding rate for {symbol}: {e}")
            raise
    
    async def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position for a symbol"""
        try:
            # For spot trading, positions are just balances
            balance = await self.get_balance()
            for bal in balance:
                if bal.currency in symbol:
                    return {
                        'symbol': symbol,
                        'size': bal.total,
                        'side': 'long' if bal.total > 0 else 'short',
                        'unrealized_pnl': 0.0,
                        'realized_pnl': 0.0
                    }
            return None
        except Exception as e:
            logger.error(f"Error fetching position for {symbol}: {e}")
            raise
    
    def calculate_fees(self, amount: float, price: float, side: str) -> float:
        """Calculate trading fees"""
        # Kraken fee structure (simplified)
        # Maker: 0.16% - 0.26%
        # Taker: 0.26% - 0.36%
        # Volume-based discounts apply
        
        base_fee = 0.0026  # 0.26% taker fee
        return amount * price * base_fee
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            await self.get_balance()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False