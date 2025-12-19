"""
Tests for execution module
"""

import pytest
from src.execution import OrderExecutor

def test_order_executor_initialization():
    """Test OrderExecutor initialization"""
    executor = OrderExecutor(exchange_name="binance")
    assert executor.exchange_name == "binance"
    assert executor.is_connected == False
    assert executor.orders == []

def test_order_placement():
    """Test placing orders"""
    executor = OrderExecutor()
    executor.is_connected = True  # Simulate connection
    
    order = executor.place_order(
        symbol="BTC/USDT",
        side="buy",
        order_type="market",
        quantity=0.01
    )
    
    assert order["symbol"] == "BTC/USDT"
    assert order["side"] == "buy"
    assert order["type"] == "market"
    assert order["quantity"] == 0.01
    assert len(executor.orders) == 1
