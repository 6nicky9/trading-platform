#!/usr/bin/env python3
"""
Основной файл для запуска торгового бота
"""

import yaml
import logging
import time
from datetime import datetime
from src.strategies.SimpleStrategy import SimpleStrategy
from src.risk.RiskManager import RiskManager, RiskLevel

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_bot.log'),
            logging.StreamHandler()
        ]
    )

def load_config():
    """Загрузка конфигурации"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def main():
    """Основная функция запуска"""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ТОРГОВОГО БОТА")
    print("="*60)
    
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger("Main")
    
    # Загрузка конфигурации
    config = load_config()
    
    print(f"\n🤖 Бот: {config['bot']['name']}")
    print(f"📊 Режим: {config['bot']['mode'].upper()}")
    print(f"💰 Начальный баланс: ${config['trading']['initial_balance']}")
    print(f"📈 Торгуемые пары: {', '.join(config['trading']['symbols'])}")
    
    # Инициализация стратегии
    strategy_params = config['strategy']['parameters']
    strategy = SimpleStrategy(
        fast_period=strategy_params['fast_period'],
        slow_period=strategy_params['slow_period']
    )
    
    # Инициализация менеджера рисков
    risk_manager = RiskManager(
        initial_capital=config['trading']['initial_balance'],
        risk_per_trade=config['risk']['risk_per_trade'],
        risk_level=RiskLevel.MODERATE
    )
    
    print(f"\n📊 Стратегия: {config['strategy']['type']}")
    print(f"⚙️ Параметры: {strategy_params}")
    
    # Имитация рыночных данных
    sample_prices = {
        'BTC/USDT': [50000, 50200, 50100, 50300, 50500, 50400, 50600],
        'ETH/USDT': [3000, 3010, 3020, 3030, 3040, 3050, 3060]
    }
    
    print("\n🔍 Анализ рынка...")
    
    for symbol in config['trading']['symbols'][:2]:  # Первые 2 символа
        if symbol in sample_prices:
            market_data = {
                'symbol': symbol,
                'prices': sample_prices[symbol],
                'timestamp': datetime.now()
            }
            
            # Генерация сигнала
            signal = strategy.generate_signal(market_data)
            
            print(f"\n{symbol}:")
            print(f"  Цена: ${market_data['prices'][-1]}")
            if signal['action']:
                print(f"  Сигнал: {signal['action']}")
                print(f"  Уверенность: {signal['confidence']*100:.1f}%")
                
                # Расчёт размера позиции
                price = market_data['prices'][-1]
                stop_loss = price * (1 - config['risk']['stop_loss_pct'])
                position_size, metrics = risk_manager.calculate_position_size(
                    entry_price=price,
                    stop_loss_price=stop_loss
                )
                
                print(f"  Размер позиции: {position_size:.4f}")
                print(f"  Стоимость позиции: ${metrics.get('position_value', 0):.2f}")
            else:
                print(f"  Сигнал: НЕТ (ожидание)")
    
    print("\n" + "="*60)
    print("✅ Бот успешно инициализирован!")
    print("📋 Следующие шаги:")
    print("   1. Подключение к реальной бирже (Binance API)")
    print("   2. Настройка WebSocket для реальных данных")
    print("   3. Реализация исполнения ордеров")
    print("   4. Добавление больше стратегий")
    print("="*60)

if __name__ == "__main__":
    main()
