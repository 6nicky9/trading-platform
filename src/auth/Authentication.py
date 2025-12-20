"""
Authentication.py - Система аутентификации для веб-интерфейса
"""

import bcrypt
import jwt
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

class AuthenticationSystem:
    """Система аутентификации с JWT токенами"""
    
    def __init__(self, secret_key: str = None, users_file: str = "data/users.json"):
        self.secret_key = secret_key or os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
        self.users_file = users_file
        self.logger = logging.getLogger(self.__class__.__name__)
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Загружает пользователей из файла"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_users(self):
        """Сохраняет пользователей в файл"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def hash_password(self, password: str) -> str:
        """Хеширует пароль"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Проверяет пароль"""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    
    def create_user(self, username: str, password: str, email: str = "", role: str = "user") -> bool:
        """Создает нового пользователя"""
        if username in self.users:
            return False
        
        self.users[username] = {
            'username': username,
            'password_hash': self.hash_password(password),
            'email': email,
            'role': role,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'is_active': True
        }
        
        self._save_users()
        self.logger.info(f"User created: {username}")
        return True
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """Аутентифицирует пользователя"""
        user = self.users.get(username)
        
        if not user or not user.get('is_active', True):
            return False, "User not found or inactive"
        
        if not self.verify_password(password, user['password_hash']):
            return False, "Invalid password"
        
        # Обновляем время последнего входа
        user['last_login'] = datetime.now().isoformat()
        self._save_users()
        
        return True, "Success"
    
    def create_token(self, username: str, expires_hours: int = 24) -> str:
        """Создает JWT токен"""
        user = self.users.get(username)
        if not user:
            raise ValueError("User not found")
        
        payload = {
            'username': username,
            'role': user.get('role', 'user'),
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Верифицирует JWT токен"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Изменяет пароль пользователя"""
        user = self.users.get(username)
        if not user:
            return False
        
        if not self.verify_password(old_password, user['password_hash']):
            return False
        
        user['password_hash'] = self.hash_password(new_password)
        user['password_changed_at'] = datetime.now().isoformat()
        self._save_users()
        
        return True
    
    def reset_password(self, username: str, new_password: str) -> bool:
        """Сбрасывает пароль (для администратора)"""
        user = self.users.get(username)
        if not user:
            return False
        
        user['password_hash'] = self.hash_password(new_password)
        user['password_changed_at'] = datetime.now().isoformat()
        user['reset_required'] = True
        self._save_users()
        
        return True
    
    def get_user_stats(self) -> Dict:
        """Получает статистику пользователей"""
        return {
            'total_users': len(self.users),
            'active_users': sum(1 for u in self.users.values() if u.get('is_active', True)),
            'users': list(self.users.keys())
        }

# Создание дефолтного администратора при первом запуске
def create_default_admin():
    """Создает администратора по умолчанию"""
    auth = AuthenticationSystem()
    
    # Проверяем, есть ли уже администратор
    if 'admin' not in auth.users:
        auth.create_user(
            username='admin',
            password='admin123',  # В реальном проекте изменить!
            email='admin@tradingbot.com',
            role='admin'
        )
        print("✅ Создан администратор: admin / admin123")
        print("⚠️  ИЗМЕНИТЕ ПАРОЛЬ ПРИ ПЕРВОМ ВХОДЕ!")
    
    return auth

if __name__ == "__main__":
    # Тестирование системы аутентификации
    auth = create_default_admin()
    print(f"Пользователи: {auth.get_user_stats()}")
