# В разделе с табами добавь новую вкладку:
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Дашборд", "📈 Графики", "📋 Сделки", "⚙️ Настройки", "🌐 WebSocket"])

# Добавь новую вкладку WebSocket
with tab5:
    st.subheader("🌐 WebSocket - Реальные данные")
    
    # Импортируем WebSocket дашборд
    try:
        from src.websocket.WebSocketDashboard import WebSocketDashboard
        
        # Создаем экземпляр дашборда
        ws_dashboard = WebSocketDashboard()
        
        # Отображаем компоненты
        ws_dashboard.display_websocket_status()
        ws_dashboard.display_ticker_panel()
        
        st.markdown("---")
        
        # Графики в реальном времени
        ws_dashboard.display_real_time_chart("btcusdt", "Bitcoin (BTC/USDT)")
        
        st.markdown("---")
        
        # Стакан ордеров
        ws_dashboard.display_order_book("btcusdt", 10)
        
    except ImportError as e:
        st.warning("WebSocket модуль не установлен")
        st.code(f"Ошибка: {e}")
