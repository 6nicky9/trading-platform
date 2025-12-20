#!/usr/bin/env python3
"""
Trading Bot Web Interface - Streamlit App с аутентификацией
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
from src.auth.Authentication import AuthenticationSystem, create_default_admin

# Инициализация системы аутентификации
auth = create_default_admin()

# Функция для проверки аутентификации
def check_auth():
    """Проверяет, аутентифицирован ли пользователь"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.token = None
    
    return st.session_state.authenticated

# Страница входа
def login_page():
    """Страница входа"""
    st.title("🔐 Вход в Trading Bot")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        remember_me = st.checkbox("Запомнить меня")
        
        submit_button = st.form_submit_button("Войти")
        
        if submit_button:
            if not username or not password:
                st.error("Заполните все поля")
                return
            
            success, message = auth.authenticate(username, password)
            
            if success:
                # Создаем токен
                token = auth.create_token(username)
                
                # Сохраняем в сессии
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.token = token
                st.session_state.role = auth.users[username].get('role', 'user')
                
                st.success(f"Добро пожаловать, {username}!")
                st.rerun()
            else:
                st.error(f"Ошибка входа: {message}")
    
    # Кнопка регистрации (только для демо)
    if st.button("📝 Зарегистрироваться"):
        st.session_state.show_register = True
        st.rerun()

# Страница регистрации
def register_page():
    """Страница регистрации"""
    st.title("📝 Регистрация")
    st.markdown("---")
    
    with st.form("register_form"):
        username = st.text_input("Имя пользователя")
        email = st.text_input("Email")
        password = st.text_input("Пароль", type="password")
        confirm_password = st.text_input("Подтвердите пароль", type="password")
        
        submit_button = st.form_submit_button("Зарегистрироваться")
        
        if submit_button:
            if not all([username, email, password, confirm_password]):
                st.error("Заполните все поля")
                return
            
            if password != confirm_password:
                st.error("Пароли не совпадают")
                return
            
            if len(password) < 8:
                st.error("Пароль должен быть не менее 8 символов")
                return
            
            success = auth.create_user(username, password, email)
            
            if success:
                st.success(f"Пользователь {username} успешно создан!")
                st.info("Теперь вы можете войти в систему")
                
                # Возвращаемся на страницу входа
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error("Пользователь с таким именем уже существует")
    
    if st.button("⬅️ Назад к входу"):
        st.session_state.show_register = False
        st.rerun()

# Основное приложение
def main_app():
    """Основное приложение после входа"""
    # Настройка страницы
    st.set_page_config(
        page_title="Trading Bot Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Заголовок с информацией о пользователе
    st.title(f"🤖 Crypto Trading Bot Dashboard")
    st.caption(f"👤 Вы вошли как: {st.session_state.username} ({st.session_state.role})")
    st.markdown("---")
    
    # Боковая панель с управлением пользователем
    with st.sidebar:
        st.header(f"👤 {st.session_state.username}")
        
        # Информация о пользователе
        user_info = auth.users.get(st.session_state.username, {})
        if user_info:
            st.caption(f"Роль: {user_info.get('role', 'user')}")
            if user_info.get('last_login'):
                last_login = datetime.fromisoformat(user_info['last_login'])
                st.caption(f"Последний вход: {last_login.strftime('%Y-%m-%d %H:%M')}")
        
        # Кнопка выхода
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.token = None
            st.rerun()
        
        st.markdown("---")
        
        # Меню управления пользователями (только для админов)
        if st.session_state.role == 'admin':
            st.subheader("👑 Админ панель")
            
            if st.button("Управление пользователями"):
                st.session_state.show_user_management = True
            
            if st.button("Статистика системы"):
                st.session_state.show_system_stats = True
            
            st.markdown("---")
        
        # Остальная боковая панель (как в предыдущей версии)
        st.header("⚙️ Настройки бота")
        
        # ... (остальной код боковой панели как в предыдущей версии)

# Главная функция
def main():
    """Главная функция приложения"""
    
    # Инициализация сессионных состояний
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    if 'show_user_management' not in st.session_state:
        st.session_state.show_user_management = False
    if 'show_system_stats' not in st.session_state:
        st.session_state.show_system_stats = False
    
    # Проверка аутентификации
    if not check_auth():
        if st.session_state.show_register:
            register_page()
        else:
            login_page()
        return
    
    # Основное приложение
    main_app()

if __name__ == "__main__":
    main()
