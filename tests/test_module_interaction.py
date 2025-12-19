"""
Test interactions between different modules
"""

import pytest
from src.data import MarketData
from src.execution import OrderExecutor
from src.risk import RiskManager

def test_data_to_execution_flow():
    """Test flow from data collection to order execution"""
    # Setup
    data = MarketData()
    executor = OrderExecutor()
    risk = RiskManager()
    
    # Simulate data collection
    ticker = data.get_ticker("binance", "BTC/USDT")
    assert "price" in ticker
    assert ticker["symbol"] == "BTC/USDT"
    
    # Simulate risk check
    price = ticker["price"]
    risk_check = risk.can_open_position(
        symbol="BTC/USDT",
        size=0.01,
        price=price,
        leverage=1.0
    )
    
    if risk_check["allowed"]:
        # Simulate order execution
        executor.is_connected = True
        order = executor.place_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="market",
            quantity=0.01,
            price=price
        )
        assert order["status"] == "pending"
        
        # Add to risk tracking
        risk.add_position(
            position_id=order["id"],
            symbol="BTC/USDT",
            size=0.01,
            entry_price=price,
            position_type="long"
        )
        
        # Update position with new price
        new_price = price * 1.01  # 1% increase
        position = risk.update_position_price(order["id"], new_price)
        assert position["pnl"] > 0  # Should be profitable
        
    print("✓ Data → Risk → Execution flow working")

def test_complete_trading_scenario():
    """Test a complete trading scenario"""
    risk = RiskManager({
        "max_position_size": 10000,
        "max_daily_loss": 500,
        "max_open_positions": 3,
        "risk_per_trade": 0.02
    })
    
    executor = OrderExecutor("binance")
    executor.is_connected = True
    
    # Open multiple positions
    symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    
    for i, symbol in enumerate(symbols):
        # Check risk
        risk_result = risk.can_open_position(
            symbol=symbol,
            size=0.1,
            price=50000 / (i + 1),  # Different prices
            leverage=1.0
        )
        
        if risk_result["allowed"]:
            # Place order
            order = executor.place_order(
                symbol=symbol,
                side="buy",
                order_type="market",
                quantity=0.1
            )
            
            # Track in risk manager
            risk.add_position(
                position_id=order["id"],
                symbol=symbol,
                size=0.1,
                entry_price=50000 / (i + 1),
                position_type="long"
            )
    
    # Check risk summary
    summary = risk.get_risk_summary()
    assert "open_positions" in summary
    assert summary["open_positions"] <= 3
    
    print("✓ Complete trading scenario working")
