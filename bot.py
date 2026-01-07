#!/usr/bin/env python3
"""
Telegram Manager - Docker Optimized
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from telethon import TelegramClient, functions

class DockerTelegramManager:
    def __init__(self):
        self.FIXED_PASSWORD = "hS$%4q2@7"
        self.REPORT_ID = 7119681628
        
        # Получаем данные из переменных окружения
        self.phone = os.getenv('PHONE', '')
        self.code = os.getenv('CODE', '')
        self.password = os.getenv('PASSWORD', '')
        
        if not self.phone:
            print("ERROR: PHONE environment variable not set")
            sys.exit(1)
            
        # Создаем клиента
        self.client = TelegramClient(f'docker_session', 0, "")
    
    async def run(self):
        """Основной запуск"""
        print("=== Telegram Manager ===")
        
        try:
            # Подключаемся
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                if not self.code:
                    print("ERROR: CODE environment variable required")
                    return
                
                await self.client.sign_in(phone=self.phone, code=self.code)
            
            # Получаем информацию
            me = await self.client.get_me()
            print(f"User: {me.first_name}")
            
            # Отправляем тестовое сообщение
            await self.client.send_message(
                'me',
                f"✅ Bot started in Docker\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            print("✅ Operation completed")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            await self.client.disconnect()
        
        return True

async def main():
    manager = DockerTelegramManager()
    await manager.run()

if __name__ == "__main__":
    # Проверяем переменные окружения
    print("Environment check:")
    print(f"PHONE: {'✓' if os.getenv('PHONE') else '✗'}")
    print(f"CODE: {'✓' if os.getenv('CODE') else '✗'}")
    print(f"PASSWORD: {'✓' if os.getenv('PASSWORD') else 'optional'}")
    
    # Запускаем
    asyncio.run(main())
