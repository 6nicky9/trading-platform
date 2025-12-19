"""
Integration tests for trading platform modules
"""

import pytest
from src.core import TradingPlatform
from src.bots import BaseTradingBot
from src.data import MarketData
from src.execution import OrderExecutor
from src.risk import RiskManager
from src.web.api import app
from fastapi.testclient import TestClient

def test_all_modules_can_be_imported():
    """Test that all main modules can be imported without errors"""
    # This test verifies that our module structure is correct
    assert TradingPlatform is not None
    assert BaseTradingBot is not None
    assert MarketData is not None
    assert OrderExecutor is not None
    assert RiskManager is not None
    assert app is not None
    print("✓ All modules imported successfully")

def test_trading_platform_integration():
    """Test basic integration between modules"""
    # Create instances of all main modules
    platform = TradingPlatform()
    data = MarketData()
    executor = OrderExecutor()
    risk = RiskManager()
    
    # Test that they can work together
    assert platform.name == "Trading Platform"
    
    # Test market data connection
    data_result = data.connect_exchange("binance")
    assert data_result is True
    
    # Test risk manager configuration
    risk_config = risk.config
    assert "max_position_size" in risk_config
    
    # Test order executor
    executor.is_connected = True  # Simulate connection
    order = executor.place_order(
        symbol="BTC/USDT",
        side="buy",
        order_type="market",
        quantity=0.01
    )
    assert "id" in order
    assert order["symbol"] == "BTC/USDT"
    
    print("✓ Module integration working")

def test_web_api_integration():
    """Test web API integration"""
    client = TestClient(app)
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Trading Platform API"
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    
    # Test markets endpoint
    response = client.get("/markets")
    assert response.status_code == 200
    assert "markets" in response.json()
    
    print("✓ Web API integration working")

def test_risk_position_sizing():
    """Test risk management position sizing"""
    risk = RiskManager()
    
    # Test position size calculation
    result = risk.calculate_position_size(
        capital=10000,
        entry_price=45000,
        stop_loss_price=44000
    )
    
    assert "position_size" in result
    assert result["position_size"] > 0
    assert result["risk_amount"] == 200  # 2% of 10000
    
    # Test position approval
    approval = risk.can_open_position(
        symbol="BTC/USDT",
        size=0.1,
        price=45000,
        leverage=1.0
    )
    assert "allowed" in approval
    
    print("✓ Risk management working")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
