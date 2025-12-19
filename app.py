#!/usr/bin/env python3
"""
Trading Bot Web Interface - Streamlit App
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
import json
import os
from datetime import datetime, timedelta
import numpy as np

# Настройка страницы
st.set_page_config(
    page_title="Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("🤖 Crypto Trading Bot Dashboard")
st.markdown("---")

# Загрузка конфигурации
@st.cache_data
def load_config():
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except:
        return {}

# Загрузка логов сделок
@st.cache_data(ttl=60)
def load_trades():
    trades = []
    log_file = "logs/trades.json"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    trades.append(json.loads(line.strip()))
        except:
            pass
    return trades

# Загрузка данных баланса
def load_balance_history():
    # Временные данные для демо
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    balance = [10000 + i*50 + (i%7)*100 for i in range(30)]
    return pd.DataFrame({'Date': dates, 'Balance': balance})

# Боковая панель
with st.sidebar:
    st.header("⚙️ Настройки бота")
    
    # Статус бота
    bot_status = st.selectbox(
        "Статус бота",
        ["🟢 Активен", "🟡 Пауза", "🔴 Остановлен"]
    )
    
    # Режим торговли
    trading_mode = st.radio(
        "Режим торговли",
        ["📊 Paper Trading", "💰 Live Trading"]
    )
    
    # Параметры риска
    st.subheader("Управление рисками")
    risk_per_trade = st.slider("Риск на сделку (%)", 0.1, 10.0, 2.0, 0.1)
    max_daily_loss = st.slider("Макс. дневной убыток (%)", 1.0, 20.0, 5.0, 0.5)
    stop_loss = st.slider("Стоп-лосс (%)", 0.5, 15.0, 5.0, 0.5)
    
    # Кнопки управления
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Запустить", use_container_width=True):
            st.success("Бот запущен")
    with col2:
        if st.button("⏸️ Пауза", use_container_width=True):
            st.warning("Бот на паузе")
    
    if st.button("🔄 Обновить данные", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Быстрая статистика")
    
    config = load_config()
    if config:
        st.info(f"**Бот:** {config.get('bot', {}).get('name', 'Trading Bot')}")
        st.info(f"**Символы:** {len(config.get('trading', {}).get('symbols', []))}")
        st.info(f"**Баланс:** ${config.get('trading', {}).get('initial_balance', 0):,.2f}")

# Основное содержимое
tab1, tab2, tab3, tab4 = st.tabs(["📊 Дашборд", "📈 Графики", "📋 Сделки", "⚙️ Настройки"])

with tab1:
    # KPI карточки
    st.subheader("📊 Ключевые метрики")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Общий P&L",
            value="$1,245.50",
            delta="+12.45%",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="Сегодняшний P&L",
            value="$124.30",
            delta="+1.24%",
            delta_color="normal"
        )
    
    with col3:
        trades = load_trades()
        st.metric(
            label="Всего сделок",
            value=len(trades),
            delta=f"+{len([t for t in trades if t.get('action') == 'BUY'])} покупок"
        )
    
    with col4:
        win_rate = 65  # Пример
        st.metric(
            label="Win Rate",
            value=f"{win_rate}%",
            delta="+5%",
            delta_color="normal"
        )
    
    # График баланса
    st.subheader("📈 Динамика баланса")
    
    balance_df = load_balance_history()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=balance_df['Date'],
        y=balance_df['Balance'],
        mode='lines+markers',
        name='Баланс',
        line=dict(color='#00CC96', width=3)
    ))
    fig.update_layout(
        title="История баланса",
        xaxis_title="Дата",
        yaxis_title="Баланс ($)",
        hovermode='x unified',
        template='plotly_dark'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Графики стратегий
    st.subheader("📊 Анализ стратегий")
    
    # Интерактивный график с индикаторами
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('Цена и скользящие средние', 'RSI индикатор'),
        row_heights=[0.7, 0.3]
    )
    
    # Генерируем демо данные
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    # График цены и MA
    fig.add_trace(
        go.Scatter(x=dates, y=prices, name='Цена', line=dict(color='white')),
        row=1, col=1
    )
    
    # MA 20
    ma20 = pd.Series(prices).rolling(20).mean()
    fig.add_trace(
        go.Scatter(x=dates, y=ma20, name='MA 20', line=dict(color='orange', dash='dash')),
        row=1, col=1
    )
    
    # MA 50
    ma50 = pd.Series(prices).rolling(50).mean()
    fig.add_trace(
        go.Scatter(x=dates, y=ma50, name='MA 50', line=dict(color='red', dash='dash')),
        row=1, col=1
    )
    
    # RSI индикатор
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    fig.add_trace(
        go.Scatter(x=dates, y=rsi, name='RSI', line=dict(color='cyan')),
        row=2, col=1
    )
    
    # Добавляем горизонтальные линии для RSI
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
    
    fig.update_layout(height=600, showlegend=True, template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("📋 История сделок")
    
    if trades:
        # Преобразуем в DataFrame
        df = pd.DataFrame(trades)
        
        # Форматируем колонки
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['Время'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Выбираем колонки для отображения
        display_cols = []
        for col in ['symbol', 'action', 'price', 'size', 'confidence', 'Время']:
            if col in df.columns:
                display_cols.append(col)
        
        st.dataframe(
            df[display_cols].rename(columns={
                'symbol': 'Пара',
                'action': 'Действие',
                'price': 'Цена',
                'size': 'Объем',
                'confidence': 'Уверенность'
            }),
            use_container_width=True,
            height=400
        )
        
        # Статистика сделок
        col1, col2 = st.columns(2)
        with col1:
            if 'action' in df.columns:
                buy_count = len(df[df['action'] == 'BUY'])
                sell_count = len(df[df['action'] == 'SELL'])
                st.metric("Покупки", buy_count)
                st.metric("Продажи", sell_count)
        
        with col2:
            if 'price' in df.columns and 'size' in df.columns:
                total_volume = (df['price'] * df['size']).sum()
                st.metric("Общий объем", f"${total_volume:,.2f}")
    else:
        st.info("📭 Сделок пока нет")

with tab4:
    st.subheader("⚙️ Настройки бота")
    
    # Загружаем конфиг
    config = load_config()
    
    # Редактор конфигурации
    st.subheader("Конфигурация YAML")
    
    if config:
        # Отображаем как редактируемый JSON
        edited_config = st.text_area(
            "Редактировать конфигурацию",
            value=yaml.dump(config, default_flow_style=False),
            height=400
        )
        
        if st.button("💾 Сохранить изменения"):
            try:
                new_config = yaml.safe_load(edited_config)
                with open('config.yaml', 'w') as f:
                    yaml.dump(new_config, f, default_flow_style=False)
                st.success("Конфигурация сохранена!")
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")
    
    # Настройки стратегии
    st.subheader("📈 Настройки стратегии")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fast_ma = st.number_input("Быстрая MA", min_value=5, max_value=50, value=10)
        slow_ma = st.number_input("Медленная MA", min_value=20, max_value=200, value=30)
    
    with col2:
        rsi_period = st.number_input("RSI период", min_value=5, max_value=50, value=14)
        rsi_oversold = st.number_input("RSI перепроданность", min_value=0, max_value=50, value=30)
        rsi_overbought = st.number_input("RSI перекупленность", min_value=50, max_value=100, value=70)

# Футер
st.markdown("---")
st.markdown("""
<div style="text-align: center">
    <p>🤖 <b>Trading Bot Dashboard</b> v1.0 | 📊 Режим: {mode} | 🕐 Последнее обновление: {time}</p>
</div>
""".format(
    mode="Paper Trading" if trading_mode == "📊 Paper Trading" else "Live",
    time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
), unsafe_allow_html=True)

# Запуск автоматического обновления
if st.button("🔄 Авто-обновление каждые 60 сек"):
    st.rerun()
