#!/usr/bin/env python3
"""
Проверка ВСЕХ модулей проекта
"""

import os
import sys
import importlib

def check_file_exists(path):
    """Проверяет существует ли файл"""
    exists = os.path.exists(path)
    status = "✅ ЕСТЬ" if exists else "❌ НЕТ"
    print(f"{status} {path}")
    return exists

def check_import(module_path):
    """Проверяет импорт модуля"""
    try:
        module = importlib.import_module(module_path)
        print(f"✅ Импорт: {module_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта {module_path}: {str(e)[:100]}")
        return False

def check_class_in_module(module_path, class_name):
    """Проверяет наличие класса в модуле"""
    try:
        module = importlib.import_module(module_path)
        if hasattr(module, class_name):
            print(f"✅ Класс {class_name} найден в {module_path}")
            return True
        else:
            print(f"❌ Класс {class_name} НЕ найден в {module_path}")
            return False
    except:
        return False

def main():
    print("🔍 ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")
    print("=" * 60)
    
    # 1. Проверяем файлы
    print("\n1. Проверка файловой структуры:")
    files_to_check = [
        "src/__init__.py",
        "src/bots/__init__.py",
        "src/bots/BaseTradingBot.py",
        "src/data/__init__.py",
        "src/data/MarketData.py",
        "src/execution/__init__.py",
        "src/execution/OrderExecutor.py",
        "src/risk/__init__.py",
        "src/risk/RiskManager.py",
        "requirements.txt",
        ".github/workflows/python.yml"
    ]
    
    all_files_exist = True
    for file in files_to_check:
        if not check_file_exists(file):
            all_files_exist = False
    
    print("\n2. Проверка импортов:")
    modules_to_check = [
        "src.bots.BaseTradingBot",
        "src.data.MarketData",
        "src.execution.OrderExecutor", 
        "src.risk.RiskManager"
    ]
    
    all_imports_ok = True
    for module in modules_to_check:
        if not check_import(module):
            all_imports_ok = False
    
    print("\n3. Проверка основных классов:")
    classes_to_check = [
        ("src.bots.BaseTradingBot", "BaseTradingBot"),
        ("src.bots.BaseTradingBot", "ExampleTradingBot"),
        ("src.data.MarketData", "MarketDataProcessor"),
        ("src.execution.OrderExecutor", "OrderExecutor"),
        ("src.execution.OrderExecutor", "MockOrderExecutor"),
        ("src.risk.RiskManager", "RiskManager")
    ]
    
    all_classes_ok = True
    for module_path, class_name in classes_to_check:
        if not check_class_in_module(module_path, class_name):
            all_classes_ok = False
    
    print("\n4. Проверка зависимостей:")
    try:
        import httpx
        print(f"✅ httpx версия: {httpx.__version__}")
    except:
        print("❌ httpx не установлен")
    
    try:
        import pandas
        print(f"✅ pandas версия: {pandas.__version__}")
    except:
        print("❌ pandas не установлен")
    
    try:
        import numpy
        print(f"✅ numpy версия: {numpy.__version__}")
    except:
        print("❌ numpy не установлен")
    
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    
    if all_files_exist and all_imports_ok and all_classes_ok:
        print("🎉 ВСЁ ОТЛИЧНО! Проект полностью готов!")
        print("Следующий шаг: написать тесты функциональности.")
    else:
        print("⚠️  ЕСТЬ ПРОБЛЕМЫ:")
        if not all_files_exist:
            print("  - Отсутствуют некоторые файлы")
        if not all_imports_ok:
            print("  - Ошибки импорта модулей")
        if not all_classes_ok:
            print("  - Отсутствуют классы")
        
        print("\n📋 Для исправления:")
        print("1. Создайте отсутствующие файлы")
        print("2. Проверьте пути импортов")
        print("3. Убедитесь, что классы правильно названы")

if __name__ == "__main__":
    main()
