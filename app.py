# В разделе с табами добавь новую вкладку:
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Дашборд", "📈 Графики", "📋 Сделки", "⚙️ Настройки", "🌐 WebSocket", "🔔 Уведомления"
])

# Добавь новую вкладку Уведомления
with tab6:
    st.subheader("🔔 Система уведомлений")
    
    try:
        from src.notifications.NotificationDashboard import NotificationDashboard
        
        # Создаем экземпляр дашборда
        notification_dashboard = NotificationDashboard()
        
        # Отображаем панель управления
        notification_dashboard.display_notification_panel()
        
    except ImportError as e:
        st.warning("Модуль уведомлений не установлен")
        st.code(f"Ошибка: {e}")
        
        # Альтернативная простая панель
        st.info("Для использования системы уведомлений установите необходимые зависимости:")
        st.code("""
        pip install python-telegram-bot>=20.0
        pip install requests>=2.31.0
        pip install pyyaml>=6.0
        """)
