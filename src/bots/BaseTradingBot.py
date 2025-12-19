"""
BaseTradingBot.py - Базовый класс для торговых ботов
Содержит основную логику для работы с торговыми API
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union


class BaseTradingBot(ABC):
    """
    Абстрактный базовый класс для торговых ботов.
    Определяет общий интерфейс для всех торговых ботов.
    """
    
    def __init__(self, api_key: str, api_secret: str, test_mode: bool = False):
        """
        Инициализация базового торгового бота.
        
        Args:
            api_key: API ключ для биржи
            api_secret: Секретный ключ API
            test_mode: Режим тестирования (не использовать реальные средства)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.test_mode = test_mode
        self.session = None
        self.logger = self._setup_logger()
        self.balance = {}
        self.open_orders = []
        
        self.logger.info(f"Торговый бот инициализирован (test_mode={test_mode})")
    
    def _setup_logger(self) -> logging.Logger:
        """Настройка системы логирования"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Подключение к бирже.
        
        Returns:
            bool: Успешность подключения
        """
        pass
    
    @abstractmethod
    def get_balance(self) -> Dict[str, float]:
        """
        Получение текущего баланса.
        
        Returns:
            Dict с балансами по валютам
        """
        pass
    
    @abstractmethod
    def get_market_price(self, symbol: str) -> float:
        """
        Получение текущей рыночной цены.
        
        Args:
            symbol: Торговая пара (например, 'BTC/USDT')
        
        Returns:
            Текущая цена
        """
        pass
    
    @abstractmethod
    def create_order(
        self, 
        symbol: str, 
        order_type: str, 
        side: str, 
        amount: float, 
        price: Optional[float] = None
    ) -> Dict:
        """
        Создание ордера.
        
        Args:
            symbol: Торговая пара
            order_type: Тип ордера (market, limit, etc.)
            side: Направление (buy/sell)
            amount: Количество
            price: Цена (для лимитных ордеров)
        
        Returns:
            Информация о созданном ордере
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Отмена ордера.
        
        Args:
            order_id: ID ордера
        
        Returns:
            bool: Успешность отмены
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict:
        """
        Получение статуса ордера.
        
        Args:
            order_id: ID ордера
        
        Returns:
            Информация о статусе ордера
        """
        pass
    
    def calculate_risk_amount(
        self, 
        total_balance: float, 
        risk_percentage: float = 2.0
    ) -> float:
        """
        Расчет суммы для торговли на основе риска.
        
        Args:
            total_balance: Общий баланс
            risk_percentage: Процент риска
        
        Returns:
            Сумма для торговли
        """
        if risk_percentage <= 0 or risk_percentage > 100:
            raise ValueError("Процент риска должен быть между 0 и 100")
        
        return total_balance * (risk_percentage / 100)
    
    def calculate_stop_loss(
        self, 
        entry_price: float, 
        stop_loss_percentage: float = 5.0
    ) -> float:
        """
        Расчет стоп-лосса.
        
        Args:
            entry_price: Цена входа
            stop_loss_percentage: Процент стоп-лосса
        
        Returns:
            Цена стоп-лосса
        """
        return entry_price * (1 - stop_loss_percentage / 100)
    
    def calculate_take_profit(
        self, 
        entry_price: float, 
        take_profit_percentage: float = 10.0
    ) -> float:
        """
        Расчет тейк-профита.
        
        Args:
            entry_price: Цена входа
            take_profit_percentage: Процент тейк-профита
        
        Returns:
            Цена тейк-профита
        """
        return entry_price * (1 + take_profit_percentage / 100)
    
    def log_trade(
        self, 
        symbol: str, 
        side: str, 
        amount: float, 
        price: float, 
        order_id: str
    ) -> None:
        """
        Логирование информации о сделке.
        
        Args:
            symbol: Торговая пара
            side: Направление (buy/sell)
            amount: Количество
            price: Цена
            order_id: ID ордера
        """
        trade_info = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'order_id': order_id,
            'test_mode': self.test_mode
        }
        
        self.logger.info(f"Сделка выполнена: {trade_info}")
    
    def health_check(self) -> Dict:
        """
        Проверка состояния бота.
        
        Returns:
            Dict с информацией о состоянии
        """
        return {
            'status': 'active',
            'test_mode': self.test_mode,
            'timestamp': datetime.now().isoformat(),
            'open_orders_count': len(self.open_orders),
            'has_balance': len(self.balance) > 0
        }
    
    def disconnect(self) -> None:
        """Закрытие соединения с биржей"""
        if self.session:
            self.session.close()
            self.session = None
            self.logger.info("Соединение с биржей закрыто")
    
    def __del__(self):
        """Деструктор - закрытие соединений при удалении объекта"""
        self.disconnect()


# Пример конкретной реализации (для демонстрации)
class ExampleTradingBot(BaseTradingBot):
    """Пример реализации торгового бота для конкретной биржи"""
    
    def connect(self) -> bool:
        self.logger.info("Подключение к Example Exchange...")
        # Здесь должна быть реальная логика подключения
        return True
    
    def get_balance(self) -> Dict[str, float]:
        # Заглушка для демонстрации
        return {'USDT': 1000.0, 'BTC': 0.05}
    
    def get_market_price(self, symbol: str) -> float:
        # Заглушка для демонстрации
        return 50000.0 if 'BTC' in symbol else 1.0
    
    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float] = None) -> Dict:
        order_id = f"order_{datetime.now().timestamp()}"
        actual_price = price or self.get_market_price(symbol)
        
        self.log_trade(symbol, side, amount, actual_price, order_id)
        
        return {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': actual_price,
            'status': 'filled' if order_type == 'market' else 'open'
        }
    
    def cancel_order(self, order_id: str) -> bool:
        self.logger.info(f"Отмена ордера {order_id}")
        return True
    
    def get_order_status(self, order_id: str) -> Dict:
        return {
            'order_id': order_id,
            'status': 'filled',
            'filled_amount': 1.0,
            'remaining_amount': 0.0
        }


# Пример использования
if __name__ == "__main__":
    # Инициализация бота
    bot = ExampleTradingBot(
        api_key="your_api_key",
        api_secret="your_api_secret",
        test_mode=True
    )
    
    # Подключение к бирже
    if bot.connect():
        print("Подключение успешно")
        
        # Получение баланса
        balance = bot.get_balance()
        print(f"Баланс: {balance}")
        
        # Получение цены
        price = bot.get_market_price("BTC/USDT")
        print(f"Текущая цена BTC: {price}")
        
        # Создание тестового ордера
        order = bot.create_order(
            symbol="BTC/USDT",
            order_type="market",
            side="buy",
            amount=0.001
        )
        print(f"Создан ордер: {order}")
        
        # Проверка здоровья системы
        health = bot.health_check()
        print(f"Состояние системы: {health}")
