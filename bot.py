#!/usr/bin/env python3
"""
🤖 DeepSeek Telegram Bot для BotHost
Оптимизирован для облачного хостинга
"""

import os
import sys
import json
import logging
from telethon import TelegramClient

# ========== КОНФИГУРАЦИЯ ИЗ ПЕРЕМЕННЫХ СРЕДЫ ==========
# На BotHost используйте Environment Variables!
API_ID = int(os.getenv('API_ID', '1234567'))
API_HASH = os.getenv('API_HASH', 'ваш_api_hash')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-52e8d589ca9746a1b15ca0fc489676e0')
TARGET_CHAT_ID = int(os.getenv('TARGET_CHAT_ID', '-1002546268711'))

# Настройки из переменных среды или по умолчанию
COMMENT_PROBABILITY = float(os.getenv('COMMENT_PROBABILITY', '0.3'))
SESSION_NAME = os.getenv('SESSION_NAME', 'deepseek_bot')

# ========== БАЗОВАЯ КОНФИГУРАЦИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ========== ПРОСТОЙ БОТ ДЛЯ НАЧАЛА ==========
@client.on(events.NewMessage(chats=TARGET_CHAT_ID))
async def handle_message(event):
    """Обработка сообщений в чате"""
    try:
        me = await client.get_me()
        
        # Пропускаем свои сообщения
        if event.sender_id == me.id:
            return
        
        message = event.message.text
        
        # Простой ответ для теста
        if 'привет' in message.lower():
            await event.reply("Привет! Я бот на BotHost! 🤖")
            logger.info(f"Ответил на сообщение: {message[:50]}")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")

@client.on(events.NewMessage(pattern='^\.stats$', outgoing=True))
async def stats_command(event):
    """Команда статистики"""
    await event.edit("🤖 Бот работает на BotHost!\n✅ Все системы в норме")

# ========== ЗАПУСК ==========
async def main():
    """Основная функция запуска"""
    await client.start()
    me = await client.get_me()
    
    logger.info(f"✅ Бот запущен на BotHost!")
    logger.info(f"👤 Аккаунт: @{me.username}")
    logger.info(f"💬 Чат: {TARGET_CHAT_ID}")
    
    # Отправляем уведомление
    try:
        await client.send_message(
            'me',
            f"🤖 **Бот запущен на BotHost!**\n\n"
            f"👤 Аккаунт: {me.first_name}\n"
            f"💬 Чат ID: {TARGET_CHAT_ID}\n"
            f"🌐 Хостинг: BotHost\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")
    
    logger.info("🔄 Ожидаю сообщения...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # Проверка конфигурации
    required_vars = ['API_ID', 'API_HASH']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"❌ Отсутствуют переменные: {missing}")
        logger.info("Настройте в панели BotHost:")
        logger.info("1. API_ID - ваш Telegram API ID")
        logger.info("2. API_HASH - ваш Telegram API Hash")
        sys.exit(1)
    
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
