"""
WebSocketDashboard.py - Веб-компоненты для отображения реальных данных
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from ..websocket.MarketStreamer import get_market_streamer


class WebSocketDashboard:
    """Дашборд для отображения реальных данных через WebSocket"""
    
    def __init__(self):
        self.streamer = get_market_streamer()
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Настройка callback функций для обновления данных"""
        
        # Callback для обновления свечных данных в сессии Streamlit
        def update_candle_data(candle):
            cache_key = f"candle_{candle.get('symbol', 'btcusdt')}"
            
            if cache_key not in st.session_state:
                st.session_state[cache_key] = []
            
            candles = st.session_state[cache_key]
            
            if candle['is_closed']:
                candles.append(candle)
                if len(candles) > 100:
                    candles.pop(0)
            else:
                if candles and not candles[-1]['is_closed']:
                    candles[-1] = candle
                else:
                    candles.append(candle)
        
        # Подписываемся на данные
        self.streamer.subscribe("binance", "btcusdt", "kline_1m", update_candle_data)
        self.streamer.subscribe("binance", "ethusdt", "kline_1m", update_candle_data)
    
    def display_real_time_chart(self, symbol: str = "btcusdt", title: str = None):
        """Отображение реального графика цен"""
        
        cache_key = f"candle_{symbol}"
        
        if cache_key not in st.session_state:
            st.session_state[cache_key] = []
        
        candles = st.session_state[cache_key]
        
        if not candles:
            st.info(f"Ожидание данных для {symbol}...")
            return
        
        # Создаем DataFrame из свечей
        df = pd.DataFrame(candles)
        
        # Создаем график
        fig = go.Figure(data=[
            go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=symbol.upper()
            )
        ])
        
        fig.update_layout(
            title=title or f"{symbol.upper()} - Real-time",
            yaxis_title="Price (USD)",
            xaxis_title="Time",
            template="plotly_dark",
            height=500,
            showlegend=True
        )
        
        # Обновляем макет для лучшего отображения времени
        fig.update_xaxes(
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=15, label="15m", step="minute", stepmode="backward"),
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_ticker_panel(self, symbols: List[str] = None):
        """Панель с тикерами в реальном времени"""
        
        if symbols is None:
            symbols = ["btcusdt", "ethusdt", "adausdt", "solusdt"]
        
        st.subheader("📊 Таймеры в реальном времени")
        
        # Создаем колонки для тикеров
        cols = st.columns(len(symbols))
        
        for idx, symbol in enumerate(symbols):
            cache_key = f"ticker_{symbol}"
            
            if cache_key in self.streamer.data_cache:
                ticker = self.streamer.data_cache[cache_key]
                
                with cols[idx]:
                    # Определяем цвет изменения цены
                    change_percent = ticker.get('price_change_percent', 0)
                    if change_percent > 0:
                        color = "green"
                        arrow = "↑"
                    elif change_percent < 0:
                        color = "red"
                        arrow = "↓"
                    else:
                        color = "gray"
                        arrow = "→"
                    
                    # Отображаем тикер
                    st.metric(
                        label=symbol.upper(),
                        value=f"${ticker.get('last_price', 0):,.2f}",
                        delta=f"{arrow} {abs(change_percent):.2f}%",
                        delta_color="normal" if change_percent >= 0 else "inverse"
                    )
                    
                    # Дополнительная информация
                    st.caption(f"24h Vol: ${ticker.get('volume_24h', 0):,.0f}")
            else:
                with cols[idx]:
                    st.metric(
                        label=symbol.upper(),
                        value="...",
                        delta="..."
                    )
    
    def display_order_book(self, symbol: str = "btcusdt", depth: int = 10):
        """Отображение стакана ордеров"""
        
        cache_key = f"orderbook_{symbol}"
        
        if cache_key not in self.streamer.data_cache:
            st.info(f"Ожидание данных стакана для {symbol}...")
            return
        
        orderbook = self.streamer.data_cache[cache_key]
        
        st.subheader(f"📖 Стакан ордеров - {symbol.upper()}")
        
        # Создаем DataFrame для bids и asks
        bids_df = pd.DataFrame(orderbook.get('bids', []), columns=['Цена', 'Объем'])
        asks_df = pd.DataFrame(orderbook.get('asks', []), columns=['Цена', 'Объем'])
        
        # Ограничиваем глубину
        bids_df = bids_df.head(depth)
        asks_df = asks_df.head(depth)
        
        # Вычисляем суммарный объем
        bids_df['Суммарный объем'] = bids_df['Объем'].cumsum()
        asks_df['Суммарный объем'] = asks_df['Объем'].cumsum()
        
        # Отображаем две таблицы рядом
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🟢 Покупки (Bids)**")
            st.dataframe(
                bids_df.style.format({
                    'Цена': '${:,.2f}',
                    'Объем': '{:,.4f}',
                    'Суммарный объем': '{:,.4f}'
                }),
                use_container_width=True,
                height=400
            )
        
        with col2:
            st.markdown("**🔴 Продажи (Asks)**")
            st.dataframe(
                asks_df.style.format({
                    'Цена': '${:,.2f}',
                    'Объем': '{:,.4f}',
                    'Суммарный объем': '{:,.4f}'
                }),
                use_container_width=True,
                height=400
            )
        
        # Отображаем спред
        if not bids_df.empty and not asks_df.empty:
            best_bid = bids_df['Цена'].iloc[0]
            best_ask = asks_df['Цена'].iloc[0]
            spread = best_ask - best_bid
            spread_percent = (spread / best_bid) * 100
            
            st.info(f"**Спред:** ${spread:.2f} ({spread_percent:.2f}%) | "
                   f**Лучшая цена покупки:** ${best_bid:.2f} | "
                   f**Лучшая цена продажи:** ${best_ask:.2f}")
    
    def display_trade_history(self, symbol: str = "btcusdt", limit: int = 20):
        """Отображение истории сделок"""
        
        cache_key = f"trades_{symbol}"
        
        if cache_key not in self.streamer.data_cache:
            st.info(f"Ожидание данных сделок для {symbol}...")
            return
        
        trades = self.streamer.data_cache[cache_key]
        
        if not trades:
            return
        
        # Берем последние сделки
        recent_trades = trades[-limit:] if len(trades) > limit else trades
        
        st.subheader(f"🔄 Последние сделки - {symbol.upper()}")
        
        # Создаем DataFrame
        trades_df = pd.DataFrame(recent_trades)
        
        # Форматируем время
        if 'timestamp' in trades_df.columns:
            trades_df['Время'] = pd.to_datetime(trades_df['timestamp']).dt.strftime('%H:%M:%S')
        
        # Определяем направление сделки
        trades_df['Тип'] = trades_df['is_buyer_maker'].apply(
            lambda x: '🟢 Покупка' if not x else '🔴 Продажа'
        )
        
        # Отображаем таблицу
        display_cols = ['Время', 'Цена', 'Объем', 'Тип']
        
        st.dataframe(
            trades_df[display_cols].rename(columns={
                'Цена': 'Цена ($)',
                'Объем': 'Объем'
            }),
            use_container_width=True,
            height=300
        )
    
    def display_websocket_status(self):
        """Отображение статуса WebSocket соединений"""
        
        st.subheader("📡 Статус WebSocket соединений")
        
        status_cols = st.columns(3)
        
        with status_cols[0]:
            if self.streamer.running:
                st.success("🟢 WebSocket активен")
                st.caption(f"Подписок: {len(self.streamer.callbacks)}")
            else:
                st.error("🔴 WebSocket неактивен")
                if st.button("Запустить WebSocket"):
                    self.streamer.start()
                    st.rerun()
        
        with status_cols[1]:
            if self.streamer.data_cache:
                st.info(f"📊 Данные: {len(self.streamer.data_cache)} потоков")
            else:
                st.warning("📭 Нет данных")
        
        with status_cols[2]:
            # Кнопка обновления
            if st.button("🔄 Обновить данные"):
                st.rerun()
        
        # Отображаем список активных потоков
        if self.streamer.callbacks:
            st.markdown("**Активные потоки:**")
            for stream_key in self.streamer.callbacks.keys():
                st.caption(f"• {stream_key}")


def main():
    """Основная функция для тестирования дашборда"""
    import streamlit as st
    
    st.set_page_config(page_title="WebSocket Dashboard", layout="wide")
    
    st.title("🌐 WebSocket Dashboard - Real-time Market Data")
    
    # Инициализируем дашборд
    dashboard = WebSocketDashboard()
    
    # Запускаем WebSocket если еще не запущен
    if not dashboard.streamer.running:
        dashboard.streamer.start()
    
    # Отображаем статус
    dashboard.display_websocket_status()
    
    st.markdown("---")
    
    # Панель тикеров
    dashboard.display_ticker_panel()
    
    st.markdown("---")
    
    # Основные графики
    col1, col2 = st.columns(2)
    
    with col1:
        dashboard.display_real_time_chart("btcusdt", "Bitcoin (BTC/USDT)")
    
    with col2:
        dashboard.display_real_time_chart("ethusdt", "Ethereum (ETH/USDT)")
    
    st.markdown("---")
    
    # Стакан ордеров и история сделок
    tab1, tab2, tab3 = st.tabs(["📖 Стакан ордеров", "🔄 История сделок", "⚙️ Настройки"])
    
    with tab1:
        dashboard.display_order_book("btcusdt", 15)
    
    with tab2:
        dashboard.display_trade_history("btcusdt", 30)
    
    with tab3:
        st.subheader("Настройки WebSocket")
        
        # Выбор символов
        selected_symbols = st.multiselect(
            "Символы для отображения",
            options=["btcusdt", "ethusdt", "adausdt", "solusdt", "bnbusdt", "xrpusdt"],
            default=["btcusdt", "ethusdt"]
        )
        
        # Интервал обновления
        update_interval = st.slider("Интервал обновления (сек)", 1, 60, 5)
        
        # Сохранение настроек
        if st.button("💾 Сохранить настройки"):
            st.success("Настройки сохранены")
        
        # Экспорт данных
        if st.button("📥 Экспорт данных (JSON)"):
            if dashboard.streamer.data_cache:
                # Преобразуем данные для экспорта
                export_data = {}
                for key, value in dashboard.streamer.data_cache.items():
                    if isinstance(value, list):
                        export_data[key] = value[-100:]  # Последние 100 записей
                    else:
                        export_data[key] = value
                
                # Создаем JSON для скачивания
                st.download_button(
                    label="Скачать данные",
                    data=json.dumps(export_data, default=str, indent=2),
                    file_name=f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    # Футер
    st.markdown("---")
    st.caption(f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("⚡ Данные обновляются в реальном времени через WebSocket")


if __name__ == "__main__":
    main()
