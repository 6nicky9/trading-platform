"""
UserManagement.py - Панель управления пользователями для администраторов
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from .Authentication import AuthenticationSystem

class UserManagement:
    """Панель управления пользователями"""
    
    def __init__(self, auth_system: AuthenticationSystem):
        self.auth = auth_system
    
    def show_user_management(self):
        """Отображает панель управления пользователями"""
        st.title("👑 Управление пользователями")
        st.markdown("---")
        
        # Статистика
        stats = self.auth.get_user_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего пользователей", stats['total_users'])
        with col2:
            st.metric("Активных", stats['active_users'])
        with col3:
            st.metric("Администраторов", 
                     sum(1 for u in self.auth.users.values() if u.get('role') == 'admin'))
        
        st.markdown("---")
        
        # Таблица пользователей
        st.subheader("📋 Список пользователей")
        
        users_data = []
        for username, user_info in self.auth.users.items():
            users_data.append({
                'Имя пользователя': username,
                'Email': user_info.get('email', ''),
                'Роль': user_info.get('role', 'user'),
                'Активен': '✅' if user_info.get('is_active', True) else '❌',
                'Создан': user_info.get('created_at', ''),
                'Последний вход': user_info.get('last_login', '')
            })
        
        df = pd.DataFrame(users_data)
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        
        # Добавление нового пользователя
        st.subheader("➕ Добавить пользователя")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Имя пользователя")
                new_email = st.text_input("Email")
            with col2:
                new_password = st.text_input("Пароль", type="password")
                new_role = st.selectbox("Роль", ["user", "admin"])
            
            if st.form_submit_button("Создать пользователя"):
                if not all([new_username, new_email, new_password]):
                    st.error("Заполните все поля")
                else:
                    success = self.auth.create_user(
                        username=new_username,
                        password=new_password,
                        email=new_email,
                        role=new_role
                    )
                    
                    if success:
                        st.success(f"Пользователь {new_username} создан!")
                        st.rerun()
                    else:
                        st.error("Пользователь уже существует")
        
        st.markdown("---")
        
        # Управление существующими пользователями
        st.subheader("⚙️ Управление пользователями")
        
        selected_user = st.selectbox(
            "Выберите пользователя",
            options=list(self.auth.users.keys())
        )
        
        if selected_user:
            user_info = self.auth.users[selected_user]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Имя:** {selected_user}")
                st.write(f"**Email:** {user_info.get('email', '')}")
                st.write(f"**Роль:** {user_info.get('role', 'user')}")
                st.write(f"**Создан:** {user_info.get('created_at', '')}")
            
            with col2:
                # Смена роли
                new_role = st.selectbox(
                    "Изменить роль",
                    ["user", "admin"],
                    index=0 if user_info.get('role') == 'user' else 1
                )
                
                # Статус активности
                is_active = st.checkbox(
                    "Активен",
                    value=user_info.get('is_active', True)
                )
                
                # Сброс пароля
                if st.button("🔄 Сбросить пароль", key="reset_password"):
                    new_password = "Temp123!"  # Генерация временного пароля
                    if self.auth.reset_password(selected_user, new_password):
                        st.success(f"Пароль сброшен. Новый пароль: {new_password}")
                        st.warning("⚠️ Сообщите пользователю об изменении пароля!")
                
                # Удаление пользователя
                if st.button("🗑️ Удалить пользователя", type="secondary"):
                    if st.checkbox(f"Подтвердите удаление {selected_user}"):
                        # В реальном проекте используйте soft delete
                        st.warning(f"Пользователь {selected_user} будет удален")
            
            # Сохранение изменений
            if st.button("💾 Сохранить изменения"):
                user_info['role'] = new_role
                user_info['is_active'] = is_active
                self.auth._save_users()
                st.success("Изменения сохранены")
                st.rerun()
