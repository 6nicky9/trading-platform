"""
OrderExecutor.py - Advanced order execution system with smart order routing
Handles trade execution, order management, and position tracking across multiple exchanges
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import json
from decimal import Decimal, ROUND_DOWN
import heapq


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT_MARKET = "take_profit_market"
    TAKE_PROFIT_LIMIT = "take_profit_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    NEW = "new"
    PENDING_NEW = "pending_new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    PENDING_CANCEL = "pending_cancel"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderTimeInForce(Enum):
    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    DAY = "DAY"  # Day order


@dataclass
class Order:
    """Enhanced order data class with precision handling"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    trigger_price: Optional[Decimal] = None
    time_in_force: OrderTimeInForce = OrderTimeInForce.GTC
    status: OrderStatus = OrderStatus.NEW
    filled_amount: Decimal = Decimal('0')
    average_price: Decimal = Decimal('0')
    commission: Decimal = Decimal('0')
    commission_asset: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    client_order_id: str = ""
    parent_order_id: Optional[str] = None
    iceberg_amount: Optional[Decimal] = None
    reduce_only: bool = False
    post_only: bool = False
    tags: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure Decimal precision
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))
        if isinstance(self.filled_amount, (int, float)):
            self.filled_amount = Decimal(str(self.filled_amount))
        if isinstance(self.average_price, (int, float)):
            self.average_price = Decimal(str(self.average_price))
        if isinstance(self.commission, (int, float)):
            self.commission = Decimal(str(self.commission))
    
    def is_active(self) -> bool:
        """Check if order is still active"""
        return self.status in [
            OrderStatus.NEW, 
            OrderStatus.PENDING_NEW, 
            OrderStatus.PARTIALLY_FILLED
        ]
    
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED
    
    def is_cancellable(self) -> bool:
        return self.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]
    
    def get_remaining_amount(self) -> Decimal:
        return self.amount - self.filled_amount
    
    def get_fill_percentage(self) -> float:
        if self.amount == Decimal('0'):
            return 0.0
        return float((self.filled_amount / self.amount) * 100)
    
    def update_fill(self, fill_amount: Decimal, fill_price: Decimal, commission: Decimal = Decimal('0')) -> None:
        """Update order with new fill"""
        self.filled_amount += fill_amount
        total_value = (self.average_price * (self.filled_amount - fill_amount)) + (fill_price * fill_amount)
        self.average_price = total_value / self.filled_amount if self.filled_amount > 0 else Decimal('0')
        self.commission += commission
        
        if self.filled_amount >= self.amount:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
        
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'amount': str(self.amount),
            'price': str(self.price) if self.price else None,
            'stop_price': str(self.stop_price) if self.stop_price else None,
            'trigger_price': str(self.trigger_price) if self.trigger_price else None,
            'time_in_force': self.time_in_force.value,
            'status': self.status.value,
            'filled_amount': str(self.filled_amount),
            'average_price': str(self.average_price),
            'commission': str(self.commission),
            'commission_asset': self.commission_asset,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'client_order_id': self.client_order_id,
            'parent_order_id': self.parent_order_id,
            'iceberg_amount': str(self.iceberg_amount) if self.iceberg_amount else None,
            'reduce_only': self.reduce_only,
            'post_only': self.post_only,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        kwargs = {
            'id': data['id'],
            'symbol': data['symbol'],
            'side': OrderSide(data['side']),
            'order_type': OrderType(data['order_type']),
            'amount': Decimal(data['amount']),
            'time_in_force': OrderTimeInForce(data.get('time_in_force', 'GTC')),
            'status': OrderStatus(data['status']),
            'filled_amount': Decimal(data.get('filled_amount', '0')),
            'average_price': Decimal(data.get('average_price', '0')),
            'commission': Decimal(data.get('commission', '0')),
            'commission_asset': data.get('commission_asset', ''),
            'created_at': datetime.fromisoformat(data['created_at']),
            'updated_at': datetime.fromisoformat(data['updated_at']),
            'client_order_id': data.get('client_order_id', ''),
            'parent_order_id': data.get('parent_order_id'),
            'reduce_only': data.get('reduce_only', False),
            'post_only': data.get('post_only', False),
            'tags': data.get('tags', {})
        }
        
        # Handle optional Decimal fields
        if data.get('price'):
            kwargs['price'] = Decimal(data['price'])
        if data.get('stop_price'):
            kwargs['stop_price'] = Decimal(data['stop_price'])
        if data.get('trigger_price'):
            kwargs['trigger_price'] = Decimal(data['trigger_price'])
        if data.get('iceberg_amount'):
            kwargs['iceberg_amount'] = Decimal(data['iceberg_amount'])
        
        return cls(**kwargs)


@dataclass
class ExecutionReport:
    """Execution report for order fills"""
    order_id: str
    symbol: str
    side: OrderSide
    executed_amount: Decimal
    executed_price: Decimal
    commission: Decimal
    commission_asset: str
    execution_time: datetime = field(default_factory=datetime.now)
    trade_id: str = ""
    is_maker: bool = False
    liquidation: bool = False


class SmartOrderRouter:
    """Smart order routing across multiple exchanges"""
    
    def __init__(self, exchanges: List['OrderExecutor']):
        self.exchanges = {ex.exchange_name: ex for ex in exchanges}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def find_best_execution(
        self,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        order_type: OrderType = OrderType.MARKET
    ) -> Tuple[str, Decimal]:
        """Find best exchange for execution"""
        best_price = Decimal('0')
        best_exchange = None
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                if side == OrderSide.BUY:
                    # For buys, look for lowest ask
                    ticker = await exchange.get_ticker(symbol)
                    price = ticker.ask if hasattr(ticker, 'ask') else ticker.last_price
                else:
                    # For sells, look for highest bid
                    ticker = await exchange.get_ticker(symbol)
                    price = ticker.bid if hasattr(ticker, 'bid') else ticker.last_price
                
                if price:
                    price = Decimal(str(price))
                    if best_exchange is None or \
                       (side == OrderSide.BUY and price < best_price) or \
                       (side == OrderSide.SELL and price > best_price):
                        best_price = price
                        best_exchange = exchange_name
            except Exception as e:
                self.logger.warning(f"Failed to get price from {exchange_name}: {e}")
        
        return best_exchange, best_price
    
    async def execute_with_smart_routing(
        self,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None
    ) -> List[ExecutionReport]:
        """Execute order using smart routing"""
        reports = []
        
        if order_type == OrderType.MARKET:
            # Split order across exchanges for better execution
            remaining_amount = amount
            min_chunk = Decimal('0.001')  # Minimum trade size
            
            while remaining_amount > min_chunk:
                exchange_name, best_price = await self.find_best_execution(
                    symbol, side, remaining_amount, order_type
                )
                
                if not exchange_name:
                    break
                
                chunk_amount = min(remaining_amount, amount * Decimal('0.3'))  # 30% max per exchange
                exchange = self.exchanges[exchange_name]
                
                try:
                    order = await exchange.create_order(
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        amount=chunk_amount,
                        price=price or best_price
                    )
                    
                    if order.is_filled():
                        report = ExecutionReport(
                            order_id=order.id,
                            symbol=symbol,
                            side=side,
                            executed_amount=order.filled_amount,
                            executed_price=order.average_price,
                            commission=order.commission,
                            commission_asset=order.commission_asset
                        )
                        reports.append(report)
                        remaining_amount -= order.filled_amount
                    
                except Exception as e:
                    self.logger.error(f"Failed to execute on {exchange_name}: {e}")
        
        return reports


class OrderExecutor(ABC):
    """Abstract order executor with enhanced features"""
    
    def __init__(
        self,
        exchange_name: str,
        api_key: str = "",
        api_secret: str = "",
        test_mode: bool = True,
        enable_rate_limit: bool = True
    ):
        self.exchange_name = exchange_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.test_mode = test_mode
        self.enable_rate_limit = enable_rate_limit
        
        self.connected = False
        self.session = None
        self.rate_limiter = RateLimiter() if enable_rate_limit else None
        
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, 'Position'] = {}
        self.balance: Dict[str, Decimal] = {}
        
        self.logger = self._setup_logger()
        self.logger.info(f"Initialized {exchange_name} executor (test_mode={test_mode})")
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"{self.__class__.__name__}.{self.exchange_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def _rate_limit(self):
        """Apply rate limiting if enabled"""
        if self.rate_limiter:
            await self.rate_limiter.acquire()
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from exchange"""
        pass
    
    @abstractmethod
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        params: Optional[Dict] = None
    ) -> Order:
        """Create new order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """Cancel order by ID"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: Optional[str] = None) -> Optional[Order]:
        """Get order by ID"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        pass
    
    @abstractmethod
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Order]:
        """Get order history"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        pass
    
    async def create_oco_order(
        self,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        price: Decimal,
        stop_price: Decimal,
        stop_limit_price: Optional[Decimal] = None
    ) -> Tuple[Order, Order]:
        """Create OCO (One Cancels Other) order"""
        # Main limit order
        limit_order = await self.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            amount=amount,
            price=price
        )
        
        # Stop order (market or limit)
        stop_order_type = OrderType.STOP_LIMIT if stop_limit_price else OrderType.STOP_MARKET
        stop_order_price = stop_limit_price if stop_limit_price else None
        
        stop_order = await self.create_order(
            symbol=symbol,
            side=side,
            order_type=stop_order_type,
            amount=amount,
            price=stop_order_price,
            stop_price=stop_price
        )
        
        # Link orders
        limit_order.tags['oco_pair'] = stop_order.id
        stop_order.tags['oco_pair'] = limit_order.id
        
        return limit_order, stop_order
    
    async def create_bracket_order(
        self,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        entry_price: Decimal,
        take_profit_price: Decimal,
        stop_loss_price: Decimal,
        stop_loss_type: OrderType = OrderType.STOP_MARKET
    ) -> Tuple[Order, Order, Order]:
        """Create bracket order (entry, take profit, stop loss)"""
        # Entry order
        entry_order = await self.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            amount=amount,
            price=entry_price
        )
        
        # Take profit order (opposite side)
        take_profit_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
        take_profit_order = await self.create_order(
            symbol=symbol,
            side=take_profit_side,
            order_type=OrderType.LIMIT,
            amount=amount,
            price=take_profit_price
        )
        
        # Stop loss order
        stop_loss_order = await self.create_order(
            symbol=symbol,
            side=take_profit_side,
            order_type=stop_loss_type,
            amount=amount,
            price=None if stop_loss_type == OrderType.STOP_MARKET else stop_loss_price,
            stop_price=stop_loss_price
        )
        
        # Link all orders
        bracket_id = str(uuid.uuid4())
        for order in [entry_order, take_profit_order, stop_loss_order]:
            order.tags['bracket_id'] = bracket_id
            order.tags['bracket_orders'] = [
                entry_order.id,
                take_profit_order.id,
                stop_loss_order.id
            ]
        
        return entry_order, take_profit_order, stop_loss_order
    
    async def batch_create_orders(self, orders: List[Dict]) -> List[Order]:
        """Create multiple orders in batch"""
        created_orders = []
        for order_params in orders:
            try:
                order = await self.create_order(**order_params)
                created_orders.append(order)
            except Exception as e:
                self.logger.error(f"Failed to create order: {e}")
        return created_orders
    
    async def batch_cancel_orders(self, order_ids: List[str]) -> Dict[str, bool]:
        """Cancel multiple orders"""
        results = {}
        for order_id in order_ids:
            try:
                success = await self.cancel_order(order_id)
                results[order_id] = success
            except Exception as e:
                self.logger.error(f"Failed to cancel order {order_id}: {e}")
                results[order_id] = False
        return results
    
    def track_order(self, order: Order) -> None:
        """Track order in local cache"""
        self.orders[order.id] = order
        self.logger.debug(f"Tracking order {order.id}")
    
    def get_tracked_order(self, order_id: str) -> Optional[Order]:
        """Get tracked order from cache"""
        return self.orders.get(order_id)
    
    async def sync_orders(self, symbol: Optional[str] = None) -> None:
        """Sync local order cache with exchange"""
        open_orders = await self.get_open_orders(symbol)
        for order in open_orders:
            self.track_order(order)
    
    def get_order_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked orders"""
        total_orders = len(self.orders)
        active_orders = sum(1 for o in self.orders.values() if o.is_active())
        filled_orders = sum(1 for o in self.orders.values() if o.is_filled())
        
        total_volume = Decimal('0')
        total_commission = Decimal('0')
        
        for order in self.orders.values():
            if order.is_filled():
                total_volume += order.filled_amount * order.average_price
                total_commission += order.commission
        
        return {
            'total_orders': total_orders,
            'active_orders': active_orders,
            'filled_orders': filled_orders,
            'total_volume': float(total_volume),
            'total_commission': float(total_commission),
            'exchange': self.exchange_name,
            'test_mode': self.test_mode
        }


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.semaphore = asyncio.Semaphore(requests_per_second)
        self.last_reset = time.time()
        self.request_count = 0
    
    async def acquire(self):
        await self.semaphore.acquire()
        current_time = time.time()
        
        if current_time - self.last_reset >= 1.0:
            self.last_reset = current_time
            self.request_count = 0
        
        self.request_count += 1
        
        if self.request_count >= self.requests_per_second:
            await asyncio.sleep(1.0 - (current_time - self.last_reset))
        
        self.semaphore.release()


class MockOrderExecutor(OrderExecutor):
    """Mock order executor for testing with realistic behavior"""
    
    def __init__(
        self,
        exchange_name: str = "MockExchange",
        api_key: str = "",
        api_secret: str = "",
        test_mode: bool = True
    ):
        super().__init__(exchange_name, api_key, api_secret, test_mode)
        self.balance = {
            'USDT': Decimal('10000'),
            'BTC': Decimal('0.5'),
            'ETH': Decimal('5.0')
        }
        self.order_counter = 1
        self.tickers = {
            'BTC/USDT': Decimal('50000'),
            'ETH/USDT': Decimal('3000'),
            'ADA/USDT': Decimal('0.5')
        }
    
    async def connect(self) -> bool:
        await asyncio.sleep(0.1)  # Simulate connection delay
        self.connected = True
        self.logger.info(f"Connected to {self.exchange_name}")
        return True
    
    async def disconnect(self) -> None:
        self.connected = False
        self.logger.info(f"Disconnected from {self.exchange_name}")
    
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        params: Optional[Dict] = None
    ) -> Order:
        if not self.connected:
            raise ConnectionError("Not connected to exchange")
        
        await self._rate_limit()
        
        # Generate order ID
        order_id = f"{self.exchange_name}_{self.order_counter}_{int(time.time())}"
        self.order_counter += 1
        
        # Determine execution price
        current_price = self.tickers.get(symbol, Decimal('100'))
        execution_price = price or current_price
        
        # Create order object
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            stop_price=stop_price,
            client_order_id=f"mock_{uuid.uuid4().hex[:8]}",
            tags={
                'exchange': self.exchange_name,
                'test': self.test_mode,
                'created_at': datetime.now().isoformat()
            }
        )
        
        # Simulate order execution based on type
        if order_type == OrderType.MARKET:
            # Immediate fill for market orders
            order.update_fill(amount, execution_price, amount * execution_price * Decimal('0.001'))
            order.status = OrderStatus.FILLED
            
            # Update balance
            base_currency = symbol.split('/')[0]
            quote_currency = symbol.split('/')[1]
            
            if side == OrderSide.BUY:
                self.balance[base_currency] = self.balance.get(base_currency, Decimal('0')) + amount
                self.balance[quote_currency] = self.balance.get(quote_currency, Decimal('0')) - (amount * execution_price)
            else:
                self.balance[base_currency] = self.balance.get(base_currency, Decimal('0')) - amount
                self.balance[quote_currency] = self.balance.get(quote_currency, Decimal('0')) + (amount * execution_price)
            
        elif order_type == OrderType.LIMIT:
            # Limit orders remain open
            order.status = OrderStatus.NEW
        
        self.track_order(order)
        self.logger.info(f"Created order {order_id}: {side.value} {amount} {symbol}")
        
        return order
    
    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        await self._rate_limit()
        
        order = self.get_tracked_order(order_id)
        if not order:
            self.logger.warning(f"Order {order_id} not found")
            return False
        
        if order.is_cancellable():
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            self.logger.info(f"Cancelled order {order_id}")
            return True
        
        self.logger.warning(f"Cannot cancel order {order_id} with status {order.status.value}")
        return False
    
    async def get_order(self, order_id: str, symbol: Optional[str] = None) -> Optional[Order]:
        await self._rate_limit()
        return self.get_tracked_order(order_id)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        await self._rate_limit()
        open_orders = []
        for order in self.orders.values():
            if order.is_active():
                if symbol is None or order.symbol == symbol:
                    open_orders.append(order)
        return open_orders
    
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Order]:
        await self._rate_limit()
        all_orders = list(self.orders.values())
        
        # Apply filters
        if symbol:
            all_orders = [o for o in all_orders if o.symbol == symbol]
        if start_time:
            all_orders = [o for o in all_orders if o.created_at >= start_time]
        if end_time:
            all_orders = [o for o in all_orders if o.created_at <= end_time]
        
        # Sort and limit
        all_orders.sort(key=lambda x: x.created_at, reverse=True)
        return all_orders[:limit]
    
    async def get_balance(self) -> Dict[str, Decimal]:
        await self._rate_limit()
        return self.balance.copy()


async def example_usage():
    """Enhanced example usage"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    # Create mock executor
    executor = MockOrderExecutor(
        exchange_name="Binance",
        test_mode=True
    )
    
    # Connect
    await executor.connect()
    
    try:
        print(f"Connected to {executor.exchange_name}")
        
        # Get balance
        balance = await executor.get_balance()
        print(f"Initial balance: {balance}")
        
        # Create market buy order
        buy_order = await executor.create_order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=Decimal('0.01')
        )
        
        print(f"\nMarket Buy Order:")
        print(f"  ID: {buy_order.id}")
        print(f"  Status: {buy_order.status.value}")
        print(f"  Filled: {buy_order.filled_amount} @ ${buy_order.average_price}")
        
        # Create limit sell order
        sell_order = await executor.create_order(
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            amount=Decimal('0.005'),
            price=Decimal('51000')
        )
        
        print(f"\nLimit Sell Order:")
        print(f"  ID: {sell_order.id}")
        print(f"  Status: {sell_order.status.value}")
        print(f"  Price: ${sell_order.price}")
        
        # Get open orders
        open_orders = await executor.get_open_orders()
        print(f"\nOpen Orders: {len(open_orders)}")
        
        # Create OCO order
        limit_order, stop_order = await executor.create_oco_order(
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            amount=Decimal('1.0'),
            price=Decimal('2950'),
            stop_price=Decimal('3100')
        )
        
        print(f"\nOCO Orders Created:")
        print(f"  Limit Order: {limit_order.id}")
        print(f"  Stop Order: {stop_order.id}")
        
        # Get order summary
        summary = executor.get_order_summary()
        print(f"\nOrder Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Update balance
        balance = await executor.get_balance()
        print(f"\nFinal Balance: {balance}")
        
    finally:
        await executor.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())
