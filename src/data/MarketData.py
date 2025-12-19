"""
MarketData.py - Market data collection and processing module
Handles real-time and historical market data from various exchanges
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
import time
import json


@dataclass
class Candle:
    """Data class for OHLCV candle"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = ""
    
    def to_dict(self) -> Dict:
        """Convert candle to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'symbol': self.symbol
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Candle':
        """Create Candle from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data['volume'],
            symbol=data.get('symbol', '')
        )


@dataclass
class Ticker:
    """Data class for real-time ticker information"""
    symbol: str
    last_price: float
    bid: float
    ask: float
    volume_24h: float
    high_24h: float
    low_24h: float
    change_24h: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def spread(self) -> float:
        """Calculate bid-ask spread"""
        return abs(self.ask - self.bid)
    
    def spread_percentage(self) -> float:
        """Calculate spread as percentage"""
        if self.ask == 0:
            return 0
        return (self.spread() / self.ask) * 100


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    def __init__(self, api_key: str = "", api_secret: str = ""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = self._setup_logger()
        self.connected = False
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for market data provider"""
        logger = logging.getLogger(f"{self.__class__.__name__}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to data provider"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from data provider"""
        pass
    
    @abstractmethod
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = '1m',
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Candle]:
        """Get OHLCV data"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get current ticker data"""
        pass
    
    @abstractmethod
    async def get_order_book(
        self, 
        symbol: str, 
        depth: int = 20
    ) -> Dict[str, List[List[float]]]:
        """Get order book data"""
        pass


class MarketDataProcessor:
    """Process and analyze market data"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @staticmethod
    def candles_to_dataframe(candles: List[Candle]) -> pd.DataFrame:
        """Convert list of candles to pandas DataFrame"""
        if not candles:
            return pd.DataFrame()
        
        data = {
            'timestamp': [c.timestamp for c in candles],
            'open': [c.open for c in candles],
            'high': [c.high for c in candles],
            'low': [c.low for c in candles],
            'close': [c.close for c in candles],
            'volume': [c.volume for c in candles]
        }
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    @staticmethod
    def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators on DataFrame"""
        if df.empty:
            return df
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        
        return df
    
    @staticmethod
    def detect_patterns(df: pd.DataFrame) -> Dict[str, List[datetime]]:
        """Detect candlestick patterns in data"""
        patterns = {
            'doji': [],
            'hammer': [],
            'engulfing_bullish': [],
            'engulfing_bearish': [],
            'morning_star': [],
            'evening_star': []
        }
        
        if len(df) < 3:
            return patterns
        
        for i in range(2, len(df)):
            # Doji pattern
            body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
            total_range = df['high'].iloc[i] - df['low'].iloc[i]
            if total_range > 0 and body_size / total_range < 0.1:
                patterns['doji'].append(df.index[i])
            
            # Hammer pattern
            if i > 0:
                is_downtrend = df['close'].iloc[i-1] < df['open'].iloc[i-1]
                body = abs(df['close'].iloc[i] - df['open'].iloc[i])
                lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
                upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                
                if is_downtrend and lower_shadow > body * 2 and upper_shadow < body * 0.1:
                    patterns['hammer'].append(df.index[i])
        
        return patterns
    
    @staticmethod
    def calculate_support_resistance(
        df: pd.DataFrame, 
        window: int = 20
    ) -> Dict[str, List[float]]:
        """Calculate support and resistance levels"""
        if len(df) < window:
            return {'support': [], 'resistance': []}
        
        highs = df['high'].rolling(window=window).max()
        lows = df['low'].rolling(window=window).min()
        
        # Find consolidation zones
        support_levels = []
        resistance_levels = []
        
        for i in range(window, len(df)):
            if df['low'].iloc[i] <= lows.iloc[i] + (lows.iloc[i] * 0.001):
                support_levels.append(df['low'].iloc[i])
            
            if df['high'].iloc[i] >= highs.iloc[i] - (highs.iloc[i] * 0.001):
                resistance_levels.append(df['high'].iloc[i])
        
        # Remove duplicates and keep only significant levels
        support_levels = sorted(list(set([round(level, 2) for level in support_levels])))[:5]
        resistance_levels = sorted(list(set([round(level, 2) for level in resistance_levels])), reverse=True)[:5]
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }


class MarketDataCache:
    """Cache for market data to reduce API calls"""
    
    def __init__(self, ttl_seconds: int = 60):
        self.cache = {}
        self.ttl = ttl_seconds
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp"""
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()
        self.logger.info("Market data cache cleared")


class MockMarketDataProvider(MarketDataProvider):
    """Mock market data provider for testing"""
    
    def __init__(self, api_key: str = "", api_secret: str = ""):
        super().__init__(api_key, api_secret)
        self.prices = {
            'BTC/USDT': 50000.0,
            'ETH/USDT': 3000.0,
            'ADA/USDT': 0.5
        }
    
    async def connect(self) -> bool:
        self.logger.info("Connected to mock market data provider")
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        self.logger.info("Disconnected from mock market data provider")
        self.connected = False
    
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = '1m',
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Candle]:
        """Generate mock OHLCV data"""
        candles = []
        base_price = self.prices.get(symbol, 100.0)
        
        end = end_time or datetime.now()
        start = start_time or end - timedelta(minutes=limit)
        
        current_time = start
        while current_time <= end and len(candles) < limit:
            # Generate random candle data
            open_price = base_price + np.random.normal(0, base_price * 0.01)
            close_price = open_price + np.random.normal(0, base_price * 0.02)
            high_price = max(open_price, close_price) + abs(np.random.normal(0, base_price * 0.01))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, base_price * 0.01))
            volume = np.random.uniform(100, 1000)
            
            candle = Candle(
                timestamp=current_time,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=round(volume, 2),
                symbol=symbol
            )
            candles.append(candle)
            
            # Move to next candle based on timeframe
            if 'm' in timeframe:
                minutes = int(timeframe.replace('m', ''))
                current_time += timedelta(minutes=minutes)
            elif 'h' in timeframe:
                hours = int(timeframe.replace('h', ''))
                current_time += timedelta(hours=hours)
            elif 'd' in timeframe:
                current_time += timedelta(days=1)
        
        return candles
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get mock ticker data"""
        base_price = self.prices.get(symbol, 100.0)
        change = np.random.normal(0, base_price * 0.02)
        
        return Ticker(
            symbol=symbol,
            last_price=round(base_price + change, 2),
            bid=round(base_price + change - (base_price * 0.0001), 2),
            ask=round(base_price + change + (base_price * 0.0001), 2),
            volume_24h=round(np.random.uniform(1000, 10000), 2),
            high_24h=round(base_price * 1.02, 2),
            low_24h=round(base_price * 0.98, 2),
            change_24h=round(change / base_price * 100, 2)
        )
    
    async def get_order_book(
        self, 
        symbol: str, 
        depth: int = 20
    ) -> Dict[str, List[List[float]]]:
        """Generate mock order book"""
        base_price = self.prices.get(symbol, 100.0)
        
        bids = []
        asks = []
        
        for i in range(depth):
            bid_price = base_price * (1 - (i + 1) * 0.0005)
            bid_amount = np.random.uniform(0.1, 5.0)
            bids.append([round(bid_price, 2), round(bid_amount, 4)])
            
            ask_price = base_price * (1 + (i + 1) * 0.0005)
            ask_amount = np.random.uniform(0.1, 5.0)
            asks.append([round(ask_price, 2), round(ask_amount, 4)])
        
        return {
            'bids': sorted(bids, key=lambda x: x[0], reverse=True),
            'asks': sorted(asks, key=lambda x: x[0])
        }


# Example usage
async def example_usage():
    """Example of how to use the MarketData classes"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create mock data provider
    provider = MockMarketDataProvider()
    
    # Connect to provider
    await provider.connect()
    
    try:
        # Get OHLCV data
        candles = await provider.get_ohlcv('BTC/USDT', timeframe='1h', limit=50)
        print(f"Retrieved {len(candles)} candles")
        
        # Process data
        processor = MarketDataProcessor()
        df = processor.candles_to_dataframe(candles)
        
        if not df.empty:
            # Calculate indicators
            df = processor.calculate_technical_indicators(df)
            print(f"\nLatest data:")
            print(df.tail())
            
            # Detect patterns
            patterns = processor.detect_patterns(df)
            print(f"\nDetected patterns: {patterns}")
            
            # Calculate support/resistance
            levels = processor.calculate_support_resistance(df)
            print(f"\nSupport levels: {levels['support']}")
            print(f"Resistance levels: {levels['resistance']}")
        
        # Get ticker data
        ticker = await provider.get_ticker('BTC/USDT')
        print(f"\nTicker data:")
        print(f"Price: ${ticker.last_price}")
        print(f"24h Change: {ticker.change_24h}%")
        print(f"Spread: {ticker.spread_percentage():.4f}%")
        
        # Get order book
        order_book = await provider.get_order_book('BTC/USDT', depth=5)
        print(f"\nOrder Book (top 5):")
        print("Bids:", order_book['bids'][:3])
        print("Asks:", order_book['asks'][:3])
        
    finally:
        # Disconnect
        await provider.disconnect()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())