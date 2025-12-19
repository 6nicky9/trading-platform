#!/usr/bin/env python3
"""
Запуск веб-интерфейса Trading Bot
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Проверяем установлены ли все зависимости"""
    required = ['streamlit', 'plotly', 'pandas', 'yaml']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def create_sample_data():
    """Создаем пример данных для демонстрации"""
    data_dir = Path("data")
    logs_dir = Path("logs")
    
    # Создаем директории если их нет
    data_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    
    # Создаем пример логов если файл пустой
    log_file = logs_dir / "trades.json"
    if not log_file.exists() or log_file.stat().st_size == 0:
        import json
        from datetime import datetime, timedelta
        import random
        
        sample_trades = []
        symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']
        
        for i in range(20):
            trade = {
                'symbol': random.choice(symbols),
                'action': random.choice(['BUY', 'SELL']),
                'price': round(random.uniform(100, 50000), 2),
                'size': round(random.uniform(0.1, 5.0), 4),
                'confidence': round(random.uniform(0.5, 0.95), 2),
                'timestamp': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            }
            sample_trades.append(trade)
        
        with open(log_file, 'w') as f:
            for trade in sample_trades:
                f.write(json.dumps(trade) + '\n')
        
        print(f"✅ Созданы примеры сделок: {len(sample_trades)} записей")

def main():
    """Главная функция запуска"""
    print("🚀 Запуск веб-интерфейса Trading Bot")
    print("=" * 50)
    
    # Проверяем зависимости
    missing = check_dependencies()
    if missing:
        print(f"❌ Отсутствуют зависимости: {missing}")
        print("Установка...")
        for package in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("✅ Зависимости установлены")
    
    # Создаем пример данных
    create_sample_data()
    
    # Проверяем наличие файла app.py
    if not Path("app.py").exists():
        print("❌ Файл app.py не найден!")
        print("Создайте app.py с веб-интерфейсом")
        return
    
    print("\n✅ Все проверки пройдены")
    print("\n🌐 Веб-интерфейс будет доступен по адресам:")
    print("   - Локально: http://localhost:8501")
    print("   - Сети: http://ваш_ip:8501")
    print("\n📋 Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    # Запускаем Streamlit
    os.system("streamlit run app.py")

if __name__ == "__main__":
    main()
