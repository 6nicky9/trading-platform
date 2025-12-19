"""
Basic tests for all project modules
"""

def test_core_module():
    """Test core module import"""
    try:
        from src.core import TradingPlatform
        platform = TradingPlatform()
        assert platform.name == "Trading Platform"
        print("✅ Core module: OK")
        return True
    except Exception as e:
        print(f"❌ Core module error: {e}")
        return False

def test_web_module():
    """Test web module import"""
    try:
        from src.web.api import app
        assert app is not None
        print("✅ Web module: OK")
        return True
    except Exception as e:
        print(f"❌ Web module error: {e}")
        return False

def test_import_all_modules():
    """Test importing all main modules"""
    modules_to_test = [
        ("src.bots", "BaseTradingBot"),
        ("src.data", "MarketData"),
        ("src.execution", "OrderExecutor"),
        ("src.risk", "RiskManager"),
    ]
    
    all_passed = True
    
    for module, class_name in modules_to_test:
        try:
            exec(f"from {module} import {class_name}")
            print(f"✅ {module}.{class_name}: OK")
        except Exception as e:
            print(f"❌ {module}.{class_name}: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("=== STARTING MODULE TESTS ===")
    core_ok = test_core_module()
    web_ok = test_web_module()
    imports_ok = test_import_all_modules()
    
    if all([core_ok, web_ok, imports_ok]):
        print("=== ALL TESTS PASSED ===")
    else:
        print("=== SOME TESTS FAILED ===")
        exit(1)
