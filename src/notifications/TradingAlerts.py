"""
TradingAlerts.py - Интеграция уведомлений с торговой системой
"""

import asyncio
from typing import Dict, Optional
from datetime import datetime
from .NotificationManager import get_notification_manager, NotificationPriority


class TradingAlerts:
    """Класс для отправки торговых алертов"""
    
    def __init__(self):
        self.manager = get_notification_manager()
    
    async def on_trade_signal(self, signal_data: Dict):
        """Обработчик торговых сигналов"""
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            action = signal_data.get('action', 'UNKNOWN').upper()
            price = signal_data.get('price', 0)
            confidence = signal_data.get('confidence', 0)
            strategy = signal_data.get('strategy', 'Unknown')
            
            # Определяем приоритет на основе уверенности
            if confidence >= 0.8:
                priority = NotificationPriority.HIGH
            elif confidence >= 0.6:
                priority = NotificationPriority.NORMAL
            else:
                priority = NotificationPriority.LOW
            
            # Отправляем уведомление
            success = self.manager.send_trade_signal(
                symbol=symbol,
                action=action,
                price=price,
                confidence=confidence,
                strategy=strategy
            )
            
            return success
            
        except Exception as e:
            print(f"Error sending trade signal notification: {e}")
            return False
    
    async def on_position_opened(self, position_data: Dict):
        """Обработчик открытия позиции"""
        try:
            symbol = position_data.get('symbol', 'UNKNOWN')
            side = position_data.get('side', 'UNKNOWN').upper()
            amount = position_data.get('amount', 0)
            entry_price = position_data.get('entry_price', 0)
            stop_loss = position_data.get('stop_loss')
            take_profit = position_data.get('take_profit')
            
            title = f"📈 Позиция открыта: {side} {symbol}"
            message = f"Открыта позиция {side} {amount} {symbol} по цене ${entry_price:,.2f}"
            
            data = {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'entry_price': entry_price,
                'position_value': amount * entry_price,
                'timestamp': datetime.now().isoformat()
            }
            
            if stop_loss:
                message += f"\nСтоп-лосс: ${stop_loss:,.2f}"
                data['stop_loss'] = stop_loss
            
            if take_profit:
                message += f"\nТейк-профит: ${take_profit:,.2f}"
                data['take_profit'] = take_profit
            
            # Создаем и отправляем уведомление
            from .NotificationManager import Notification, NotificationType
            
            notification = Notification(
                title=title,
                message=message,
                notification_type=NotificationType.TELEGRAM,
                priority=NotificationPriority.NORMAL,
                data=data
            )
            
            return self.manager.send_notification(notification)
            
        except Exception as e:
            print(f"Error sending position opened notification: {e}")
            return False
    
    async def on_position_closed(self, position_data: Dict):
        """Обработчик закрытия позиции"""
        try:
            symbol = position_data.get('symbol', 'UNKNOWN')
            side = position_data.get('side', 'UNKNOWN').upper()
            amount = position_data.get('amount', 0)
            entry_price = position_data.get('entry_price', 0)
            exit_price = position_data.get('exit_price', 0)
            pnl = position_data.get('pnl', 0)
            pnl_percent = position_data.get('pnl_percent', 0)
            
            # Определяем результат
            if pnl > 0:
                emoji = "💰"
                result = "ПРИБЫЛЬ"
            elif pnl < 0:
                emoji = "📉"
                result = "УБЫТОК"
            else:
                emoji = "➖"
                result = "БЕЗ ИЗМЕНЕНИЙ"
            
            title = f"{emoji} Позиция закрыта: {result} {symbol}"
            message = f"Закрыта позиция {side} {amount} {symbol}\n"
            message += f"Вход: ${entry_price:,.2f} | Выход: ${exit_price:,.2f}\n"
            message += f"P&L: ${pnl:,.2f} ({pnl_percent:+.2f}%)"
            
            data = {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'result': result.lower(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Создаем и отправляем уведомление
            from .NotificationManager import Notification, NotificationType, NotificationPriority
            
            priority = NotificationPriority.HIGH if abs(pnl_percent) > 5 else NotificationPriority.NORMAL
            
            notification = Notification(
                title=title,
                message=message,
                notification_type=NotificationType.TELEGRAM,
                priority=priority,
                data=data
            )
            
            return self.manager.send_notification(notification)
            
        except Exception as e:
            print(f"Error sending position closed notification: {e}")
            return False
    
    async def on_price_alert(self, alert_data: Dict):
        """Обработчик ценовых алертов"""
        try:
            symbol = alert_data.get('symbol', 'UNKNOWN')
            current_price = alert_data.get('current_price', 0)
            threshold = alert_data.get('threshold', 0)
            direction = alert_data.get('direction', 'above')
            
            title = f"📊 Ценовой алерт: {symbol}"
            
            if direction == 'above':
                message = f"Цена {symbol} превысила уровень ${threshold:,.2f}\n"
                message += f"Текущая цена: ${current_price:,.2f}"
            else:
                message = f"Цена {symbol} упала ниже уровня ${threshold:,.2f}\n"
                message += f"Текущая цена: ${current_price:,.2f}"
            
            data = {
                'symbol': symbol,
                'current_price': current_price,
                'threshold': threshold,
                'direction': direction,
                'timestamp': datetime.now().isoformat()
            }
            
            # Создаем и отправляем уведомление
            from .NotificationManager import Notification, NotificationType, NotificationPriority
            
            notification = Notification(
                title=title,
                message=message,
                notification_type=NotificationType.TELEGRAM,
                priority=NotificationPriority.NORMAL,
                data=data
            )
            
            return self.manager.send_notification(notification)
            
        except Exception as e:
            print(f"Error sending price alert notification: {e}")
            return False
    
    async def on_system_error(self, error_data: Dict):
        """Обработчик системных ошибок"""
        try:
            error_type = error_data.get('error_type', 'UnknownError')
            error_message = error_data.get('error_message', 'No details')
            component = error_data.get('component', 'Unknown')
            
            title = f"🚨 Системная ошибка: {component}"
            message = f"Тип: {error_type}\nСообщение: {error_message}"
            
            data = {
                'error_type': error_type,
                'error_message': error_message,
                'component': component,
                'timestamp': datetime.now().isoformat()
            }
            
            # Создаем и отправляем уведомление
            from .NotificationManager import Notification, NotificationType, NotificationPriority
            
            notification = Notification(
                title=title,
                message=message,
                notification_type=NotificationType.TELEGRAM,
                priority=NotificationPriority.CRITICAL,
                data=data
            )
            
            return self.manager.send_notification(notification)
            
        except Exception as e:
            print(f"Error sending system error notification: {e}")
            return False
    
    async def on_performance_report(self, report_data: Dict):
        """Обработчик отчетов о производительности"""
        try:
            period = report_data.get('period', 'daily').capitalize()
            profit_loss = report_data.get('profit_loss', 0)
            trades_count = report_data.get('trades_count', 0)
            win_rate = report_data.get('win_rate', 0)
            
            title = f"📈 {period} отчет"
            
            if profit_loss >= 0:
                message = f"Прибыль: ${profit_loss:,.2f}\n"
                message += f"Сделок: {trades_count}\n"
                message += f"Win Rate: {win_rate:.1%}"
            else:
                message = f"Убыток: ${profit_loss:,.2f}\n"
                message += f"Сделок: {trades_count}\n"
                message += f"Win Rate: {win_rate:.1%}"
            
            data = {
                'period': period,
                'profit_loss': profit_loss,
                'trades_count': trades_count,
                'win_rate': win_rate,
                'timestamp': datetime.now().isoformat()
            }
            
            # Создаем и отправляем уведомление
            from .NotificationManager import Notification, NotificationType, NotificationPriority
            
            priority = NotificationPriority.NORMAL if profit_loss >= 0 else NotificationPriority.HIGH
            
            notification = Notification(
                title=title,
                message=message,
                notification_type=NotificationType.EMAIL,  # Отчеты лучше отправлять на email
                priority=priority,
                data=data
            )
            
            return self.manager.send_notification(notification)
            
        except Exception as e:
            print(f"Error sending performance report notification: {e}")
            return False


# Синглтон для глобального доступа
_trading_alerts = None

def get_trading_alerts() -> TradingAlerts:
    """Получение глобального экземпляра TradingAlerts"""
    global _trading_alerts
    if _trading_alerts is None:
        _trading_alerts = TradingAlerts()
    return _trading_alerts


if __name__ == "__main__":
    # Тестирование системы алертов
    import asyncio
    
    async def test_alerts():
        alerts = TradingAlerts()
        
        # Тестовые данные
        test_signals = [
            {
                'symbol': 'BTC/USDT',
                'action': 'buy',
                'price': 51234.56,
                'confidence': 0.85,
                'strategy': 'MA Crossover'
            },
            {
                'symbol': 'ETH/USDT',
                'action': 'sell',
                'price': 3250.75,
                'confidence': 0.72,
                'strategy': 'RSI Divergence'
            }
        ]
        
        for signal in test_signals:
            success = await alerts.on_trade_signal(signal)
            print(f"Trade signal sent: {success}")
            await asyncio.sleep(1)
        
        # Тест позиции
        position_data = {
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'amount': 0.1,
            'entry_price': 51234.56,
            'stop_loss': 49000,
            'take_profit': 55000
        }
        
        success = await alerts.on_position_opened(position_data)
        print(f"Position opened notification sent: {success}")
    
    asyncio.run(test_alerts())
