from telethon import TelegramClient
import asyncio

API_ID = 31360391
API_HASH = 'a24b830f1eacee823178f75001ab4792'
PHONE = '+79920502008'

client = TelegramClient('userbot', API_ID, API_HASH)

async def keep_online():
    await client.start(PHONE)
    print("✅ Бот запущен и онлайн")
    
    while True:
        try:
            # Просто проверяем соединение
            await client.get_me()
            await asyncio.sleep(300)  # Проверка каждые 5 минут
        except:
            print("⚠️ Переподключение...")
            await asyncio.sleep(5)

# Запуск
with client:
    client.loop.run_until_complete(keep_online())
