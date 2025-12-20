"""
NotificationDashboard.py - Веб-интерфейс для управления уведомлениями
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict
import json
import yaml
from .NotificationManager import get_notification_manager, Notification, NotificationType, NotificationPriority


class NotificationDashboard:
    """Дашборд для управления уведомлениями"""
    
    def __init__(self):
        self.manager = get_notification_manager()
    
    def display_notification_panel(self):
        """Панель управления уведомлениями"""
        st.title("🔔 Управление уведомлениями")
        
        # Статистика
        stats = self.manager.get_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего", stats['total'])
        
        with col2:
            st.metric("Отправлено", stats['sent'])
        
        with col3:
            st.metric("Прочитано", stats['read'])
        
        with col4:
            st.metric("Не прочитано", stats['unread'])
        
        st.markdown("---")
        
        # Вкладки
        tab1, tab2, tab3, tab4 = st.tabs(["📋 История", "⚙️ Настройки", "📊 Статистика", "📤 Тестирование"])
        
        with tab1:
            self._display_notification_history()
        
        with tab2:
            self._display_notification_settings()
        
        with tab3:
            self._display_notification_stats(stats)
        
        with tab4:
            self._display_test_notifications()
    
    def _display_notification_history(self):
        """Отображение истории уведомлений"""
        st.subheader("📋 История уведомлений")
        
        # Фильтры
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_read = st.checkbox("Показать прочитанные", value=True)
            show_unread = st.checkbox("Показать непрочитанные", value=True)
        
        with col2:
            limit = st.slider("Количество записей", 10, 100, 50)
        
        with col3:
            if st.button("🗑️ Очистить историю"):
                cleared = self.manager.clear_history()
                st.success(f"Очищено {cleared} записей")
                st.rerun()
        
        # Получаем историю
        read_filter = None
        if not show_read and show_unread:
            read_filter = False
        elif show_read and not show_unread:
            read_filter = True
        
        history = self.manager.get_notification_history(limit=limit, read=read_filter)
        
        if not history:
            st.info("История уведомлений пуста")
            return
        
        # Отображаем таблицу
        df = pd.DataFrame(history)
        
        # Форматируем колонки
        if 'timestamp' in df.columns:
            df['Время'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        if 'priority' in df.columns:
            # Добавляем эмодзи для приоритета
            priority_emojis = {
                'critical': '🚨',
                'high': '⚠️',
                'normal': 'ℹ️',
                'low': '📝'
            }
            df['Приоритет'] = df['priority'].map(lambda x: f"{priority_emojis.get(x, '')} {x}")
        
        # Выбираем колонки для отображения
        display_cols = []
        for col in ['Время', 'title', 'message', 'Приоритет', 'type', 'sent']:
            if col in df.columns:
                display_cols.append(col)
        
        st.dataframe(
            df[display_cols].rename(columns={
                'title': 'Заголовок',
                'message': 'Сообщение',
                'type': 'Тип',
                'sent': 'Отправлено'
            }),
            use_container_width=True,
            height=400
        )
        
        # Детали выбранного уведомления
        if not df.empty:
            st.subheader("🔍 Детали уведомления")
            
            selected_index = st.selectbox(
                "Выберите уведомление для просмотра",
                range(len(df)),
                format_func=lambda x: f"{df.iloc[x]['Время']} - {df.iloc[x]['Заголовок']}"
            )
            
            if selected_index is not None:
                notification = history[selected_index]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {notification.get('id')}")
                    st.write(f"**Тип:** {notification.get('type')}")
                    st.write(f"**Приоритет:** {notification.get('priority')}")
                    st.write(f"**Отправлено:** {'✅' if notification.get('sent') else '❌'}")
                    st.write(f"**Прочитано:** {'✅' if notification.get('read') else '❌'}")
                    st.write(f"**Статус доставки:** {notification.get('delivery_status')}")
                
                with col2:
                    st.write(f"**Заголовок:** {notification.get('title')}")
                    st.write(f"**Сообщение:** {notification.get('message')}")
                    st.write(f"**Время:** {notification.get('timestamp')}")
                
                # Дополнительные данные
                if notification.get('data'):
                    st.subheader("📊 Дополнительные данные")
                    data_df = pd.DataFrame([notification['data']]).T.reset_index()
                    data_df.columns = ['Ключ', 'Значение']
                    st.dataframe(data_df, use_container_width=True)
                
                # Кнопки управления
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if not notification.get('read'):
                        if st.button("✅ Пометить как прочитанное"):
                            if self.manager.mark_as_read(notification['id']):
                                st.success("Уведомление помечено как прочитанное")
                                st.rerun()
                
                with col2:
                    if st.button("🗑️ Удалить уведомление"):
                        if self.manager.delete_notification(notification['id']):
                            st.success("Уведомление удалено")
                            st.rerun()
                
                with col3:
                    if st.button("📋 Пометить все как прочитанные"):
                        marked = self.manager.mark_all_as_read()
                        st.success(f"Помечено {marked} уведомлений")
                        st.rerun()
    
    def _display_notification_settings(self):
        """Отображение настроек уведомлений"""
        st.subheader("⚙️ Настройки каналов")
        
        try:
            # Загружаем конфигурацию
            with open('config/notifications.yaml', 'r') as f:
                config = yaml.safe_load(f)
        except:
            config = {}
        
        # Telegram
        with st.expander("📱 Telegram", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                telegram_enabled = st.checkbox(
                    "Включить Telegram уведомления",
                    value=config.get('telegram', {}).get('enabled', False)
                )
            
            with col2:
                telegram_silent = st.checkbox(
                    "Без звука",
                    value=config.get('telegram', {}).get('silent', False),
                    disabled=not telegram_enabled
                )
            
            telegram_bot_token = st.text_input(
                "Bot Token",
                value=config.get('telegram', {}).get('bot_token', ''),
                type="password",
                disabled=not telegram_enabled
            )
            
            telegram_chat_id = st.text_input(
                "Chat ID",
                value=config.get('telegram', {}).get('chat_id', ''),
                disabled=not telegram_enabled
            )
            
            if telegram_enabled and (not telegram_bot_token or not telegram_chat_id):
                st.warning("Заполните Bot Token и Chat ID для активации Telegram")
        
        # Email
        with st.expander("📧 Email"):
            email_enabled = st.checkbox(
                "Включить Email уведомления",
                value=config.get('email', {}).get('enabled', False)
            )
            
            if email_enabled:
                col1, col2 = st.columns(2)
                
                with col1:
                    smtp_server = st.text_input(
                        "SMTP сервер",
                        value=config.get('email', {}).get('smtp_server', 'smtp.gmail.com')
                    )
                    smtp_port = st.number_input(
                        "SMTP порт",
                        value=config.get('email', {}).get('smtp_port', 587),
                        min_value=1,
                        max_value=65535
                    )
                
                with col2:
                    smtp_username = st.text_input(
                        "Имя пользователя",
                        value=config.get('email', {}).get('username', '')
                    )
                    smtp_password = st.text_input(
                        "Пароль",
                        value=config.get('email', {}).get('password', ''),
                        type="password"
                    )
                
                sender_email = st.text_input(
                    "Email отправителя",
                    value=config.get('email', {}).get('sender_email', '')
                )
                
                receiver_emails = st.text_area(
                    "Email получателей (каждый с новой строки)",
                    value='\n'.join(config.get('email', {}).get('receiver_emails', []))
                )
        
        # Pushbullet
        with st.expander("📱 Pushbullet"):
            pushbullet_enabled = st.checkbox(
                "Включить Pushbullet уведомления",
                value=config.get('pushbullet', {}).get('enabled', False)
            )
            
            if pushbullet_enabled:
                pushbullet_token = st.text_input(
                    "Access Token",
                    value=config.get('pushbullet', {}).get('access_token', ''),
                    type="password"
                )
                
                pushbullet_device = st.text_input(
                    "Device ID (опционально)",
                    value=config.get('pushbullet', {}).get('device_id', '')
                )
        
        # Discord
        with st.expander("💬 Discord"):
            discord_enabled = st.checkbox(
                "Включить Discord уведомления",
                value=config.get('discord', {}).get('enabled', False)
            )
            
            if discord_enabled:
                discord_webhook = st.text_input(
                    "Webhook URL",
                    value=config.get('discord', {}).get('webhook_url', '')
                )
        
        # Сохранение настроек
        st.markdown("---")
        
        if st.button("💾 Сохранить настройки"):
            # Обновляем конфигурацию
            updated_config = {
                'telegram': {
                    'enabled': telegram_enabled,
                    'bot_token': telegram_bot_token,
                    'chat_id': telegram_chat_id,
                    'silent': telegram_silent
                },
                'email': {
                    'enabled': email_enabled,
                    'smtp_server': smtp_server if email_enabled else '',
                    'smtp_port': smtp_port if email_enabled else 587,
                    'username': smtp_username if email_enabled else '',
                    'password': smtp_password if email_enabled else '',
                    'sender_email': sender_email if email_enabled else '',
                    'receiver_emails': receiver_emails.split('\n') if email_enabled else []
                },
                'pushbullet': {
                    'enabled': pushbullet_enabled,
                    'access_token': pushbullet_token if pushbullet_enabled else '',
                    'device_id': pushbullet_device if pushbullet_enabled else ''
                },
                'discord': {
                    'enabled': discord_enabled,
                    'webhook_url': discord_webhook if discord_enabled else ''
                }
            }
            
            try:
                with open('config/notifications.yaml', 'w') as f:
                    yaml.dump(updated_config, f, default_flow_style=False)
                
                st.success("Настройки сохранены!")
                st.info("Перезапустите приложение для применения изменений")
                
            except Exception as e:
                st.error(f"Ошибка сохранения: {e}")
    
    def _display_notification_stats(self, stats: Dict):
        """Отображение статистики уведомлений"""
        st.subheader("📊 Статистика уведомлений")
        
        # График по типам
        if stats.get('by_type'):
            st.write("**Распределение по типам:**")
            
            fig1 = go.Figure(data=[
                go.Pie(
                    labels=list(stats['by_type'].keys()),
                    values=list(stats['by_type'].values()),
                    hole=.3,
                    marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                )
            ])
            
            fig1.update_layout(
                title="Уведомления по типам",
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig1, use_container_width=True)
        
        # График по приоритетам
        if stats.get('by_priority'):
            st.write("**Распределение по приоритетам:**")
            
            fig2 = go.Figure(data=[
                go.Bar(
                    x=list(stats['by_priority'].keys()),
                    y=list(stats['by_priority'].values()),
                    marker_color=['#FF6B6B', '#FFA726', '#42A5F5', '#66BB6A']
                )
            ])
            
            fig2.update_layout(
                title="Уведомления по приоритетам",
                xaxis_title="Приоритет",
                yaxis_title="Количество",
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Включенные каналы
        st.subheader("🌐 Активные каналы")
        
        enabled_channels = stats.get('enabled_channels', [])
        if enabled_channels:
            for channel in enabled_channels:
                st.success(f"✅ {channel.capitalize()}")
        else:
            st.warning("Нет активных каналов уведомлений")
        
        # Дополнительная статистика
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Успешно отправлено", stats['sent'])
        
        with col2:
            st.metric("Не удалось отправить", stats.get('failed', 0))
        
        # Экспорт данных
        st.markdown("---")
        
        if st.button("📥 Экспорт статистики (JSON)"):
            export_data = {
                'stats': stats,
                'timestamp': datetime.now().isoformat(),
                'total_notifications': stats['total']
            }
            
            st.download_button(
                label="Скачать статистику",
                data=json.dumps(export_data, indent=2),
                file_name=f"notification_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    def _display_test_notifications(self):
        """Отображение панели тестирования уведомлений"""
        st.subheader("📤 Тестирование уведомлений")
        
        st.info("Отправьте тестовые уведомления для проверки настроенных каналов")
        
        # Форма для тестового уведомления
        with st.form("test_notification_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                test_title = st.text_input("Заголовок", value="Тестовое уведомление")
                test_priority = st.selectbox(
                    "Приоритет",
                    options=['low', 'normal', 'high', 'critical'],
                    format_func=lambda x: {
                        'low': '📝 Низкий',
                        'normal': 'ℹ️ Обычный',
                        'high': '⚠️ Высокий',
                        'critical': '🚨 Критический'
                    }[x]
                )
            
            with col2:
                test_message = st.text_area(
                    "Сообщение",
                    value="Это тестовое уведомление для проверки системы. Время отправки: " +
                          datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                test_channels = st.multiselect(
                    "Каналы",
                    options=['telegram', 'email', 'pushbullet', 'discord'],
                    default=['telegram']
                )
            
            # Дополнительные данные
            with st.expander("Дополнительные данные (опционально)"):
                test_data_key = st.text_input("Ключ данных")
                test_data_value = st.text_input("Значение данных")
                
                if test_data_key and test_data_value:
                    st.info(f"Данные: {test_data_key} = {test_data_value}")
            
            submit_button = st.form_submit_button("📤 Отправить тестовое уведомление")
            
            if submit_button:
                if not test_title or not test_message:
                    st.error("Заполните заголовок и сообщение")
                    return
                
                # Создаем уведомление
                notification = Notification(
                    title=test_title,
                    message=test_message,
                    notification_type=NotificationType.TELEGRAM,  # По умолчанию
                    priority=NotificationPriority(test_priority),
                    data={test_data_key: test_data_value} if test_data_key and test_data_value else {}
                )
                
                # Временно включаем выбранные каналы
                original_enabled = self.manager.enabled_channels.copy()
                
                try:
                    # Активируем только выбранные каналы для теста
                    self.manager.enabled_channels = [
                        NotificationType(channel) for channel in test_channels
                        if channel in ['telegram', 'email', 'pushbullet', 'discord']
                    ]
                    
                    # Отправляем уведомление
                    success = self.manager.send_notification(notification)
                    
                    if success:
                        st.success(f"✅ Тестовое уведомление отправлено через {len(test_channels)} канал(ов)")
                    else:
                        st.error("❌ Не удалось отправить тестовое уведомление")
                        
                except Exception as e:
                    st.error(f"Ошибка отправки: {e}")
                    
                finally:
                    # Восстанавливаем оригинальные настройки
                    self.manager.enabled_channels = original_enabled
        
        # Быстрые тестовые уведомления
        st.markdown("---")
        st.subheader("🚀 Быстрые тесты")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Тест торгового сигнала"):
                success = self.manager.send_trade_signal(
                    symbol="BTC/USDT",
                    action="BUY",
                    price=51234.56,
                    confidence=0.78,
                    strategy="MA Crossover"
                )
                if success:
                    st.success("✅ Тестовый торговый сигнал отправлен")
                else:
                    st.error("❌ Не удалось отправить сигнал")
        
        with col2:
            if st.button("💰 Тест ценового алерта"):
                success = self.manager.send_price_alert(
                    symbol="ETH/USDT",
                    price=3250.75,
                    threshold=3200,
                    direction="above"
                )
                if success:
                    st.success("✅ Тестовый ценовой алерт отправлен")
                else:
                    st.error("❌ Не удалось отправить алерт")
        
        with col3:
            if st.button("🚨 Тест ошибки"):
                success = self.manager.send_error_alert(
                    error_type="ConnectionError",
                    error_message="Потеряно соединение с Binance API",
                    component="WebSocket Client"
                )
                if success:
                    st.success("✅ Тестовое уведомление об ошибке отправлено")
                else:
                    st.error("❌ Не удалось отправить уведомление об ошибке")


def main():
    """Основная функция для тестирования дашборда"""
    st.set_page_config(page_title="Notification Dashboard", layout="wide")
    
    st.title("🔔 Notification Management Dashboard")
    
    dashboard = NotificationDashboard()
    dashboard.display_notification_panel()


if __name__ == "__main__":
    main()
