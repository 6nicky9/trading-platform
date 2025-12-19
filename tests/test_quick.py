#!/usr/bin/env python3
"""
Быстрые тесты основных функций
"""

def test_1_calculations():
    """Тест 1: Проверка расчётов RiskManager"""
    from src.risk.RiskManager import RiskManager, RiskLevel
    
    rm = RiskManager(
        initial_capital=10000,
        risk_per_trade=0.02,
        risk_level=RiskLevel.MODERATE
    )
    
    # Тест расчёта размера позиции
    size, metrics = rm.calculate_position_size(
        entry_price=50000,
        stop_loss_price=49000
    )
    
    print(f"✓ Position size: {size}")
    print(f"✓ Position value: ${metrics.get('position_value', 0):.2f}")
    return True

def test_2_bot_creation():
    """Тест 2: Создание бота"""
    from src.bots.BaseTradingBot import ExampleTradingBot
    
    bot = ExampleTradingBot(
        api_key="test_key",
        api_secret="test_secret",
        test_mode=True
    )
    
    health = bot.health_check()
    print(f"✓ Bot health: {health['status']}")
    print(f"✓ Test mode: {health['test_mode']}")
    return True

def test_3_market_data():
    """Тест 3: Создание MarketDataProcessor"""
    from src.data.MarketData import MarketDataProcessor
    
    processor = MarketDataProcessor()
    print(f"✓ MarketDataProcessor created")
    return True

def test_4_order_types():
    """Тест 4: Проверка типов ордеров"""
    from src.execution.OrderExecutor import OrderSide, OrderType
    
    print(f"✓ OrderSide.BUY: {OrderSide.BUY.value}")
    print(f"✓ OrderSide.SELL: {OrderSide.SELL.value}")
    print(f"✓ OrderType.MARKET: {OrderType.MARKET.value}")
    print(f"✓ OrderType.LIMIT: {OrderType.LIMIT.value}")
    return True

def run_all_tests():
    print("🚀 ЗАПУСК БЫСТРЫХ ТЕСТОВ")
    print("=" * 50)
    
    tests = [
        ("Расчёты RiskManager", test_1_calculations),
        ("Создание бота", test_2_bot_creation),
        ("Market Data", test_3_market_data),
        ("Типы ордеров", test_4_order_types)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n🔍 {name}...")
            if test_func():
                print(f"✅ {name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {name} - НЕ ПРОЙДЕН")
                failed += 1
        except Exception as e:
            print(f"❌ {name} - ОШИБКА: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"РЕЗУЛЬТАТ: {passed} пройдено, {failed} не пройдено")
    
    if failed == 0:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        return True
    else:
        print("⚠️  ЕСТЬ НЕПРОЙДЕННЫЕ ТЕСТЫ")
        return False

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
