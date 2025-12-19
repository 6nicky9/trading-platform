"""
Tests for risk management module
"""

import pytest
from src.risk import RiskManager

def test_risk_manager_initialization():
    """Test RiskManager initialization"""
    rm = RiskManager()
    assert rm.config["max_position_size"] == 1000.0
    assert rm.today_pnl == 0.0
    assert len(rm.open_positions) == 0

def test_can_open_position():
    """Test position opening checks"""
    rm = RiskManager()
    
    # Test valid position
    result = rm.can_open_position("BTC/USDT", 0.1, 45000, 1.0, "long")
    assert result["allowed"] == True
    
    # Test position size limit
    rm.config["max_position_size"] = 100
    result = rm.can_open_position("BTC/USDT", 0.1, 45000, 5.0, "long")
    assert result["allowed"] == False
    assert "exceeds max" in result["reason"]

def test_calculate_position_size():
    """Test position size calculation"""
    rm = RiskManager()
    
    result = rm.calculate_position_size(
        capital=10000,
        entry_price=45000,
        stop_loss_price=44000
    )
    
    assert "position_size" in result
    assert result["position_size"] > 0
    assert result["risk_amount"] == 10000 * 0.02  # 2% of capital
