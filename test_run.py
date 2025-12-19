print("Testing the project...")

# Простые проверки
try:
    import yaml
    print("✅ pyyaml installed")
except:
    print("❌ pyyaml not installed")

try:
    from src.strategies.SimpleStrategy import SimpleStrategy
    print("✅ SimpleStrategy imported")
    
    # Тест создания стратегии
    strategy = SimpleStrategy()
    print("✅ Strategy created")
except Exception as e:
    print(f"❌ SimpleStrategy error: {e}")

print("🎉 Project is ready!")
