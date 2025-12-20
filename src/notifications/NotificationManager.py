"""
NotificationManager.py - Система уведомлений в реальном времени
"""

import logging
import smtplib
import requests
from typing import Dict, List, Optional, Union
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import asyncio
from enum import Enum


class NotificationType(Enum):
    """Типы уведомлений"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    PUSH_BULLET = "pushbullet"
    DISCORD = "discord"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Приоритеты уведомлений"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Notification:
    """Класс уведомления"""
    
    def __init__(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.TELEGRAM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict] = None
    ):
        self.id = f"notif_{datetime.now().timestamp()}_{hash(message)}"
        self.title = title
        self.message = message
        self.type = notification_type
        self.priority = priority
        self.data = data or {}
        self.timestamp = datetime.now()
        self.sent = False
        self.read = False
        self.delivery_status = "pending"
    
    def to_dict(self) -> Dict:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'priority': self.priority.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'sent': self.sent,
            'read': self.read,
            'delivery_status': self.delivery_status
        }
    
    def __str__(self) -> str:
        return f"{self.title}: {self.message}"


class NotificationManager:
    """Менеджер уведомлений для различных каналов"""
    
    def __init__(self, config_file: str = "config/notifications.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self.logger = self._setup_logger()
        self.notification_history: List[Notification] = []
        self.enabled_channels = self._get_enabled_channels()
        
    def _setup_logger(self) -> logging.Logger:
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
    
    def _load_config(self) -> Dict:
        """Загрузка конфигурации уведомлений"""
        default_config = {
            'telegram': {
                'enabled': False,
                'bot_token': '',
                'chat_id': '',
                'parse_mode': 'HTML',
                'silent': False
            },
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'sender_email': '',
                'receiver_emails': []
            },
            'pushbullet': {
                'enabled': False,
                'access_token': '',
                'device_id': ''
            },
            'discord': {
                'enabled': False,
                'webhook_url': ''
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': '#trading-alerts'
            },
            'webhook': {
                'enabled': False,
                'url': '',
                'headers': {},
                'method': 'POST'
            },
            'settings': {
                'retry_attempts': 3,
                'retry_delay': 5,
                'max_history': 1000,
                'log_file': 'logs/notifications.log'
            }
        }
        
        try:
            import yaml
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    # Объединяем с дефолтными значениями
                    for key, value in loaded_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
        except Exception as e:
            self.logger.warning(f"Failed to load notification config: {e}")
        
        return default_config
    
    def _get_enabled_channels(self) -> List[NotificationType]:
        """Получение списка включенных каналов"""
        enabled = []
        channels = {
            'telegram': NotificationType.TELEGRAM,
            'email': NotificationType.EMAIL,
            'pushbullet': NotificationType.PUSH_BULLET,
            'discord': NotificationType.DISCORD,
            'slack': NotificationType.SLACK,
            'webhook': NotificationType.WEBHOOK
        }
        
        for channel_name, channel_type in channels.items():
            if self.config.get(channel_name, {}).get('enabled', False):
                enabled.append(channel_type)
        
        return enabled
    
    def send_notification(self, notification: Notification) -> bool:
        """Отправка уведомления через выбранные каналы"""
        try:
            self.logger.info(f"Sending notification: {notification.title}")
            
            # Сохраняем уведомление в историю
            self.notification_history.append(notification)
            
            # Ограничиваем размер истории
            max_history = self.config['settings']['max_history']
            if len(self.notification_history) > max_history:
                self.notification_history = self.notification_history[-max_history:]
            
            # Отправляем через все включенные каналы
            results = []
            
            if NotificationType.TELEGRAM in self.enabled_channels:
                results.append(self._send_telegram(notification))
            
            if NotificationType.EMAIL in self.enabled_channels and notification.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
                results.append(self._send_email(notification))
            
            if NotificationType.PUSH_BULLET in self.enabled_channels:
                results.append(self._send_pushbullet(notification))
            
            if NotificationType.DISCORD in self.enabled_channels:
                results.append(self._send_discord(notification))
            
            if NotificationType.SLACK in self.enabled_channels:
                results.append(self._send_slack(notification))
            
            if NotificationType.WEBHOOK in self.enabled_channels:
                results.append(self._send_webhook(notification))
            
            # Если есть хотя бы один успешный результат
            success = any(results)
            notification.sent = success
            notification.delivery_status = "delivered" if success else "failed"
            
            self._log_notification(notification, success)
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            notification.delivery_status = "error"
            return False
    
    def _send_telegram(self, notification: Notification) -> bool:
        """Отправка уведомления в Telegram"""
        try:
            config = self.config['telegram']
            bot_token = config.get('bot_token')
            chat_id = config.get('chat_id')
            
            if not bot_token or not chat_id:
                self.logger.warning("Telegram bot token or chat ID not configured")
                return False
            
            # Форматируем сообщение
            message = f"*{notification.title}*\n\n{notification.message}"
            
            if notification.priority == NotificationPriority.CRITICAL:
                message = f"🚨 {message}"
            elif notification.priority == NotificationPriority.HIGH:
                message = f"⚠️ {message}"
            elif notification.priority == NotificationPriority.NORMAL:
                message = f"ℹ️ {message}"
            else:
                message = f"📝 {message}"
            
            # Добавляем дополнительные данные
            if notification.data:
                data_str = "\n".join([f"{k}: {v}" for k, v in notification.data.items()])
                message += f"\n\n{data_str}"
            
            # Отправляем сообщение
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_notification': config.get('silent', False)
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Telegram notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {e}")
            return False
    
    def _send_email(self, notification: Notification) -> bool:
        """Отправка уведомления по email"""
        try:
            config = self.config['email']
            
            if not config.get('enabled', False):
                return False
            
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Trading Bot] {notification.title}"
            msg['From'] = config['sender_email']
            msg['To'] = ', '.join(config['receiver_emails'])
            
            # Текстовое содержимое
            text = f"{notification.title}\n\n{notification.message}"
            
            if notification.data:
                text += f"\n\nДополнительные данные:\n"
                for key, value in notification.data.items():
                    text += f"{key}: {value}\n"
            
            # HTML содержимое
            html = f"""
            <html>
              <head></head>
              <body>
                <h2 style="color: {'#d63031' if notification.priority == NotificationPriority.CRITICAL else '#0984e3'}">
                  {notification.title}
                </h2>
                <p>{notification.message}</p>
            """
            
            if notification.data:
                html += """
                <h3>Дополнительные данные:</h3>
                <table style="border-collapse: collapse; width: 100%;">
                  <thead>
                    <tr style="background-color: #f2f2f2;">
                      <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Ключ</th>
                      <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Значение</th>
                    </tr>
                  </thead>
                  <tbody>
                """
                
                for key, value in notification.data.items():
                    html += f"""
                    <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;"><strong>{key}</strong></td>
                      <td style="border: 1px solid #ddd; padding: 8px;">{value}</td>
                    </tr>
                    """
                
                html += """
                  </tbody>
                </table>
                """
            
            html += f"""
                <hr>
                <p style="color: #636e72; font-size: 12px;">
                  Отправлено: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
                  Приоритет: {notification.priority.value}<br>
                  Trading Bot Notification System
                </p>
              </body>
            </html>
            """
            
            # Прикрепляем оба формата
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Отправляем email
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['username'], config['password'])
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_pushbullet(self, notification: Notification) -> bool:
        """Отправка уведомления через Pushbullet"""
        try:
            config = self.config['pushbullet']
            access_token = config.get('access_token')
            
            if not access_token:
                return False
            
            url = "https://api.pushbullet.com/v2/pushes"
            headers = {
                'Access-Token': access_token,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'type': 'note',
                'title': f"Trading Bot: {notification.title}",
                'body': notification.message,
                'device_iden': config.get('device_id')
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Pushbullet notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Pushbullet notification: {e}")
            return False
    
    def _send_discord(self, notification: Notification) -> bool:
        """Отправка уведомления в Discord"""
        try:
            config = self.config['discord']
            webhook_url = config.get('webhook_url')
            
            if not webhook_url:
                return False
            
            # Определяем цвет в зависимости от приоритета
            colors = {
                NotificationPriority.CRITICAL: 0xFF0000,  # Красный
                NotificationPriority.HIGH: 0xFFA500,      # Оранжевый
                NotificationPriority.NORMAL: 0x3498DB,    # Синий
                NotificationPriority.LOW: 0x2ECC71       # Зеленый
            }
            
            payload = {
                'embeds': [{
                    'title': notification.title,
                    'description': notification.message,
                    'color': colors.get(notification.priority, 0x3498DB),
                    'timestamp': notification.timestamp.isoformat(),
                    'fields': []
                }]
            }
            
            # Добавляем дополнительные данные как поля
            if notification.data:
                for key, value in notification.data.items():
                    payload['embeds'][0]['fields'].append({
                        'name': key,
                        'value': str(value),
                        'inline': True
                    })
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Discord notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {e}")
            return False
    
    def _send_slack(self, notification: Notification) -> bool:
        """Отправка уведомления в Slack"""
        try:
            config = self.config['slack']
            webhook_url = config.get('webhook_url')
            
            if not webhook_url:
                return False
            
            # Определяем иконку в зависимости от приоритета
            icons = {
                NotificationPriority.CRITICAL: ':red_circle:',
                NotificationPriority.HIGH: ':warning:',
                NotificationPriority.NORMAL: ':information_source:',
                NotificationPriority.LOW: ':white_check_mark:'
            }
            
            payload = {
                'channel': config.get('channel', '#trading-alerts'),
                'username': 'Trading Bot',
                'icon_emoji': icons.get(notification.priority, ':robot_face:'),
                'attachments': [{
                    'color': '#36a64f' if notification.priority == NotificationPriority.LOW else
                            '#3498db' if notification.priority == NotificationPriority.NORMAL else
                            '#e67e22' if notification.priority == NotificationPriority.HIGH else
                            '#e74c3c',
                    'title': notification.title,
                    'text': notification.message,
                    'fields': [],
                    'footer': f"Trading Bot | {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                    'ts': notification.timestamp.timestamp()
                }]
            }
            
            # Добавляем дополнительные данные
            if notification.data:
                for key, value in notification.data.items():
                    payload['attachments'][0]['fields'].append({
                        'title': key,
                        'value': str(value),
                        'short': True
                    })
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Slack notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def _send_webhook(self, notification: Notification) -> bool:
        """Отправка уведомления через вебхук"""
        try:
            config = self.config['webhook']
            url = config.get('url')
            
            if not url:
                return False
            
            payload = {
                'notification': notification.to_dict(),
                'source': 'trading_bot',
                'timestamp': datetime.now().isoformat()
            }
            
            headers = config.get('headers', {'Content-Type': 'application/json'})
            method = config.get('method', 'POST').upper()
            
            if method == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=payload, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=payload, headers=headers, timeout=10)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return False
            
            response.raise_for_status()
            
            self.logger.info(f"Webhook notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False
    
    def _log_notification(self, notification: Notification, success: bool):
        """Логирование уведомлений"""
        try:
            log_file = self.config['settings']['log_file']
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'notification': notification.to_dict(),
                'success': success
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
                
        except Exception as e:
            self.logger.error(f"Failed to log notification: {e}")
    
    def get_notification_history(self, limit: int = 50, read: Optional[bool] = None) -> List[Dict]:
        """Получение истории уведомлений"""
        history = self.notification_history.copy()
        
        if read is not None:
            history = [n for n in history if n.read == read]
        
        history.sort(key=lambda x: x.timestamp, reverse=True)
        return [n.to_dict() for n in history[:limit]]
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Пометить уведомление как прочитанное"""
        for notification in self.notification_history:
            if notification.id == notification_id:
                notification.read = True
                return True
        return False
    
    def mark_all_as_read(self) -> int:
        """Пометить все уведомления как прочитанные"""
        count = 0
        for notification in self.notification_history:
            if not notification.read:
                notification.read = True
                count += 1
        return count
    
    def delete_notification(self, notification_id: str) -> bool:
        """Удалить уведомление из истории"""
        for i, notification in enumerate(self.notification_history):
            if notification.id == notification_id:
                del self.notification_history[i]
                return True
        return False
    
    def clear_history(self) -> int:
        """Очистить историю уведомлений"""
        count = len(self.notification_history)
        self.notification_history = []
        return count
    
    def get_stats(self) -> Dict:
        """Получение статистики уведомлений"""
        total = len(self.notification_history)
        sent = sum(1 for n in self.notification_history if n.sent)
        read = sum(1 for n in self.notification_history if n.read)
        
        by_type = {}
        by_priority = {}
        
        for notification in self.notification_history:
            # По типам
            type_name = notification.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            
            # По приоритетам
            priority_name = notification.priority.value
            by_priority[priority_name] = by_priority.get(priority_name, 0) + 1
        
        return {
            'total': total,
            'sent': sent,
            'failed': total - sent,
            'read': read,
            'unread': total - read,
            'by_type': by_type,
            'by_priority': by_priority,
            'enabled_channels': [c.value for c in self.enabled_channels]
        }
    
    def send_trade_signal(self, symbol: str, action: str, price: float, 
                         confidence: float, strategy: str = "Unknown") -> bool:
        """Отправка уведомления о торговом сигнале"""
        title = f"Торговый сигнал: {action.upper()} {symbol}"
        message = f"Стратегия {strategy} обнаружила сигнал {action} для {symbol}"
        
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.TELEGRAM,
            priority=NotificationPriority.HIGH if confidence > 0.7 else NotificationPriority.NORMAL,
            data={
                'symbol': symbol,
                'action': action,
                'price': price,
                'confidence': confidence,
                'strategy': strategy,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return self.send_notification(notification)
    
    def send_price_alert(self, symbol: str, price: float, threshold: float,
                        direction: str = "above") -> bool:
        """Отправка уведомления о достижении ценового порога"""
        title = f"Ценовой алерт: {symbol}"
        message = f"Цена {symbol} достигла ${price:,.2f} ({direction} ${threshold:,.2f})"
        
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.TELEGRAM,
            priority=NotificationPriority.NORMAL,
            data={
                'symbol': symbol,
                'current_price': price,
                'threshold': threshold,
                'direction': direction,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return self.send_notification(notification)
    
    def send_error_alert(self, error_type: str, error_message: str,
                        component: str = "Unknown") -> bool:
        """Отправка уведомления об ошибке"""
        title = f"Ошибка в {component}"
        message = f"{error_type}: {error_message}"
        
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.TELEGRAM,
            priority=NotificationPriority.CRITICAL,
            data={
                'error_type': error_type,
                'component': component,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return self.send_notification(notification)
    
    def send_performance_report(self, profit_loss: float, trades_count: int,
                              win_rate: float, period: str = "daily") -> bool:
        """Отправка отчета о производительности"""
        title = f"Отчет за {period}"
        
        if profit_loss >= 0:
            message = f"Прибыль: ${profit_loss:,.2f} | Сделки: {trades_count} | Win Rate: {win_rate:.1%}"
            priority = NotificationPriority.LOW
        else:
            message = f"Убыток: ${profit_loss:,.2f} | Сделки: {trades_count} | Win Rate: {win_rate:.1%}"
            priority = NotificationPriority.NORMAL
        
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.EMAIL,
            priority=priority,
            data={
                'profit_loss': profit_loss,
                'trades_count': trades_count,
                'win_rate': win_rate,
                'period': period,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return self.send_notification(notification)


# Синглтон для глобального доступа
_notification_manager = None

def get_notification_manager() -> NotificationManager:
    """Получение глобального экземпляра менеджера уведомлений"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager


if __name__ == "__main__":
    # Тестирование системы уведомлений
    manager = NotificationManager()
    
    # Тестовые уведомления
    test_notifications = [
        Notification(
            title="Тестовое уведомление",
            message="Это тестовое сообщение для проверки системы",
            priority=NotificationPriority.NORMAL
        ),
        Notification(
            title="Торговый сигнал",
            message="Обнаружен сигнал покупки BTC/USDT",
            priority=NotificationPriority.HIGH,
            data={"symbol": "BTC/USDT", "price": 50000, "action": "BUY"}
        ),
        Notification(
            title="Критическая ошибка",
            message="Потеряно соединение с биржей",
            priority=NotificationPriority.CRITICAL
        )
    ]
    
    for notification in test_notifications:
        success = manager.send_notification(notification)
        print(f"Notification '{notification.title}' sent: {success}")
    
    # Вывод статистики
    stats = manager.get_stats()
    print(f"\nStatistics: {stats}")
