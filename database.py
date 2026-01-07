#!/usr/bin/env python3
"""
Многопользовательская база данных
"""

import json
import os
import asyncio
import aiofiles
from datetime import datetime
from config import USERS_DB_FILE

class UserDatabase:
    def __init__(self):
        self.db_file = USERS_DB_FILE
        self.users = {}
        self.load_users()
    
    def load_users(self):
        """Загрузка пользователей из файла"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    self.users = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки базы: {e}")
            self.users = {}
    
    def save_users(self):
        """Сохранение пользователей в файл"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения базы: {e}")
    
    def add_user(self, user_data):
        """Добавление нового пользователя"""
        phone = user_data['phone']
        self.users[phone] = {
            **user_data,
            'created_at': datetime.now().isoformat(),
            'last_run': None,
            'status': 'pending',
            'attempts': 0
        }
        self.save_users()
        return True
    
    def update_user(self, phone, updates):
        """Обновление данных пользователя"""
        if phone in self.users:
            self.users[phone].update(updates)
            self.users[phone]['last_run'] = datetime.now().isoformat()
            self.save_users()
            return True
        return False
    
    def get_user(self, phone):
        """Получение данных пользователя"""
        return self.users.get(phone)
    
    def get_all_users(self):
        """Получение всех пользователей"""
        return self.users.values()
    
    def remove_user(self, phone):
        """Удаление пользователя"""
        if phone in self.users:
            del self.users[phone]
            self.save_users()
            return True
        return False
    
    def get_pending_users(self):
        """Получение пользователей, ожидающих обработки"""
        return [user for user in self.users.values() if user['status'] == 'pending']
