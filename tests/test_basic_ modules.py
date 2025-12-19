"""
Basic tests for all project modules
"""

def test_core_basics():
    from src.core import TradingPlatform
    platform = TradingPlatform()
    assert platform.name == "Trading Platform"
    assert platform.start() == True
    assert platform.stop() == True

def test_bots_module():
    from src.bots import BaseTradingBot
    bot = BaseTradingBot("TestBot")
    assert bot.name == "TestBot"
    assert bot.start() == True

def test_data_module():
    from src.data import MarketData
    data = MarketData()
    result = data.connect_exchange("binance")
    assert result == True

def test_execution_module():
    from src.execution import OrderExecutor
    executor = OrderExecutor()
    assert executor.exchange_name == "binance"

def test_risk_module():
    from src.risk import RiskManager
    risk = RiskManager()
    assert "max_position_size" in risk.config

def test_web_api():
    from src.web.api import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Trading Platform API"