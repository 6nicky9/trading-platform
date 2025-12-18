"""
Tests for core trading platform functionality
"""

import pytest
from src.core import TradingPlatform

def test_platform_initialization():
    """Test that platform initializes correctly"""
    platform = TradingPlatform()
    assert platform.name == "Trading Platform"
    assert platform.version == "0.1.0"

def test_platform_start():
    """Test platform start method"""
    platform = TradingPlatform()
    result = platform.start()
    assert result is True

def test_platform_stop():
    """Test platform stop method"""
    platform = TradingPlatform()
    result = platform.stop()
    assert result is True

if __name__ == "__main__":
    pytest.main()
