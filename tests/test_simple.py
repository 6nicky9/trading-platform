"""
Simple tests to verify basic functionality
"""

def test_always_passes():
    """This test always passes - to verify testing works"""
    assert 1 + 1 == 2

def test_core_import():
    """Test that we can import core module"""
    try:
        from src.core import TradingPlatform
        platform = TradingPlatform()
        assert platform.name == "Trading Platform"
        assert platform.version == "0.1.0"
        print("✓ Core module imports successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
        raise

def test_web_import():
    """Test that we can import web module"""
    try:
        from src.web.api import app
        assert app is not None
        print("✓ Web module imports successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
        raise
