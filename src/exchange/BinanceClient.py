"""
BinanceClient.py - Client for Binance exchange
"""

import os
import time
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from binance.client import Client
from binance.enums import *

class BinanceClient:
    """Binance exchange client wrapper"""
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = None
        self.connect()
    
    def connect(self):
        """Connect to Binance API"""
        try:
            api_key = os.getenv('BINANCE_API_KEY', '')
            api_secret = os.getenv('BINANCE_API_SECRET', '')
            
            if self.testnet or not api_key:
                # Use testnet by default or if no API keys
                self.client = Client(
                    api_key=api_key or 'test_key',
                    api_secret=api_secret or 'test_secret',
                    testnet=True
                )
                self.logger.info("Connected to Binance Testnet")
            else:
                self.client = Client(api_key, api_secret)
                self.logger.info("Connected to Binance Live")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance: {e}")
            raise
    
    def get_account_balance(self) -> Dict[str, Decimal]:
        """Get account balances"""
        try:
            account = self.client.get_account()
            balances = {}
            for balance in account['balances']:
                free = Decimal(balance['free'])
                locked = Decimal(balance['locked'])
                total = free + locked
                if total > 0:
                    balances[balance['asset']] = total
            return balances
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return {}
    
    def get_ticker_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price for symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return Decimal(ticker['price'])
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Dict:
        """Create new order"""
        try:
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': quantity,
            }
            
            if price:
                params['price'] = price
                params['timeInForce'] = 'GTC'
            
            order = self.client.create_order(**params)
            self.logger.info(f"Order created: {order}")
            return order
            
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            raise
    
    def get_klines(
        self,
        symbol: str,
        interval: str = '1h',
        limit: int = 100
    ) -> List[Dict]:
        """Get candlestick data"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            candles = []
            for k in klines:
                candles.append({
                    'time': k[0],
                    'open': Decimal(k[1]),
                    'high': Decimal(k[2]),
                    'low': Decimal(k[3]),
                    'close': Decimal(k[4]),
                    'volume': Decimal(k[5]),
                    'close_time': k[6],
                    'quote_volume': Decimal(k[7]),
                })
            return candles
        except Exception as e:
            self.logger.error(f"Error getting klines: {e}")
            return []
