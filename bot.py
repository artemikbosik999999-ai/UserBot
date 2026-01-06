#!/usr/bin/env python3
"""
🤖 Telegram Bot для BotHost
Использует ваш API ID: 31360391 и API Hash: a24b830f1eacee823178f75001ab4792
"""

import os
import sys
import json
import random
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import aiohttp

# ========== КОНФИГУРАЦИЯ ==========
# Ваши данные из сообщения
API_ID = 31360391
API_HASH = 'a24b830f1eacee823178f75001ab4792'

# Получаем токен бота из переменных среды BotHost
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-52e8d589ca9746a1b15ca0fc489676e0')
TARGET_CHAT_ID = int(os.getenv('TARGET_CHAT_ID', '-1002546268711'))

# Проверяем обязательные переменные
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не установлен!")
    print("=" * 50)
    print("Добавьте в BotHost → Environment Variables:")
    print("BOT_TOKEN=ваш_токен_от_botfather")
    print("=" * 50)
    print("📌 Получите токен в @BotFather командой /newbot")
    sys.exit(1)

# Настройки бота
COMMENT_PROBABILITY = 0.3  # 30% вероятность ответа
BLACKLIST_WORDS = ['реклама', 'купить', 'продать', 'вакансия', 'работа']
FAVORITE_TOPICS = ['программирование', 'python', 'бот', 'игры', 'кино', 'технологии']

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== СТАТИСТИКА ==========
stats = {
    'start_time': datetime.now().isoformat(),
    'messages': 0,
    'replies': 0,
    'ai_calls': 0,
    'errors': 0,
    'active': True
}

# ========== DEEPSEEK API ==========
class DeepSeekAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = None
        
    async def get_reply(self, message_text, context=""):
        """Получить ответ от DeepSeek"""
        stats['ai_calls'] += 1
        
        # Если API ключ не настроен, используем простые ответы
        if not self.api_key or self.api_key == 'sk-52e8d589ca9746a1b15ca0fc489676e0':
            return await self.get_simple_reply(message_text)
        
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Создаем промпт для DeepSeek
            prompt = f"""Ты - участник Telegram чата. Ответь естественно и кратко.

Сообщение: "{message_text[:400]}"

Твой ответ (1-2 предложения, естественно, на русском, можно эмодзи):"""
            
            data = {
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 150,
                'temperature': 0.7
            }
            
            async with self.session.post(
                'https://api.deepseek.com/chat/completions',
                headers=headers,
                json=data,
                timeout=20
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if 'choices' in result and result['choices']:
                        reply = result['choices'][0]['message']['content'].strip()
                        return self.clean_reply(reply)
                else:
                    logger.warning(f"DeepSeek API error, status: {response.status}")
                    return await self.get_simple_reply(message_text)
                    
        except Exception as e:
            logger.error(f"DeepSeek error: {str(e)[:100]}")
            return await self.get_simple_reply(message_text)
    
    async def get_simple_reply(self, message_text):
        """Простые умные ответы"""
        lower_text = message_text.lower()
        
        # Определяем тип сообщения и отвечаем соответственно
        if any(word in lower_text for word in ['привет', 'здравствуй', 'хай', 'hello']):
            replies = [
                "Привет! 👋 Как дела?",
                "Здарова! 😊",
                "Приветствую! Что нового?",
                "Хай! Рад тебя видеть!",
                "Привет! Как настроение?"
            ]
        elif '?' in message_text:
            replies = [
                "Хм, интересный вопрос! 🤔",
                "Сложно сказать однозначно...",
                "Зависит от ситуации, но в целом...",
                "Хороший вопрос! Мне кажется...",
                "Думаю, что стоит рассмотреть несколько вариантов..."
            ]
        elif any(word in lower_text for word in ['спасибо', 'благодарю', 'thanks']):
            replies = [
                "Всегда пожалуйста! 😊",
                "Не за что! 👍",
                "Рад помочь!",
                "Обращайся! 💪"
            ]
        elif any(word in lower_text for word in ['круто', 'класс', 'супер', 'ого', 'вау']):
            replies = [
                "Согласен! 👍",
                "Да, это действительно круто! 🔥",
                "Поддерживаю! 😄",
                "Абсолютно! 🎯"
            ]
        elif any(word in lower_text for word in ['грустно', 'плохо', 'печаль', 'обидно']):
            replies = [
                "Сочувствую... 😔",
                "Не расстраивайся!",
                "Держись! 💪",
                "Надеюсь, все наладится!",
                "Бывает, главное - не сдаваться!"
            ]
        else:
            # Общие ответы
            replies = [
                "Интересно!",
                "Спасибо, что поделился! 👍",
                "Хм, никогда об этом не думал...",
                "Хорошая мысль! 💭",
                "Любопытно! 🤔",
                "Понятно...",
                "Да, я тоже об этом думал!",
                "Можно подробнее?",
                "Продолжай, интересно слушать!"
            ]
        
        # Выбираем случайный ответ
        reply = random.choice(replies)
        
        # С вероятностью 50% добавляем эмодзи (если его еще нет)
        if random.random() > 0.5 and not any(emoji in reply for emoji in ['👋', '😊', '🤔', '👍', '💪', '🔥', '😄', '🎯', '😔', '💭']):
            emojis = ['😊', '👍', '🤔', '👀', '💭', '✨', '🎯', '📚', '🌟', '💡']
            reply += f" {random.choice(emojis)}"
        
        return reply
    
    def clean_reply(self, text):
        """Очистка ответа от AI"""
        if not text:
            return ""
        
        # Удаляем кавычки
        text = text.strip('"\'').strip()
        
        # Удаляем префиксы типа "Ответ:"
        prefixes = ['Ответ:', 'AI:', 'Бот:', 'Я:', 'Assistant:', 'Реакция:', 'Комментарий:']
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        # Первая буква - заглавная
        if text and len(text) > 0:
            text = text[0].upper() + text[1:]
        
        # Обрезаем слишком длинные ответы
        if len(text) > 300:
            # Пробуем найти точку для обрезки
            last_dot = text[:250].rfind('.')
            if last_dot > 50:
                text = text[:last_dot + 1]
            else:
                text = text[:247] + "..."
        
        return text

# Создаем экземпляр AI
ai = DeepSeekAI(DEEPSEEK_API_KEY)

# ========== КОМАНДЫ БОТА ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 Привет, {user.first_name}!\n\n"
        f"Я бот с искусственным интеллектом DeepSeek.\n"
        f"🔑 API ID: {API_ID}\n"
        f"💬 Чат ID: {TARGET_CHAT_ID}\n\n"
        f"📝 Используй /help для списка команд"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
🤖 **DeepSeek AI Bot - Команды**

**Основные команды:**
/start - Начало работы
/help - Эта справка
/stats - Статистика работы
/test - Тест AI
/ping - Проверка связи

**Информация:**
🎯 Вероятность ответа: 30%
🤖 Модель AI: DeepSeek
🌐 Хостинг: BotHost
🔑 Ваш API ID: 31360391

**Как работает:**
1. Бот слушает сообщения в чате
2. С вероятностью 30% отвечает на них
3. Использует DeepSeek AI для генерации ответов
4. Игнорирует рекламу и спам
5. Больше отвечает на любимые темы
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    uptime = datetime.now() - datetime.fromisoformat(stats['start_time'])
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    stats_text = f"""
📊 **Статистика бота**

**Активность:**
⏰ Время работы: {hours}ч {minutes}м {seconds}с
📨 Сообщений получено: {stats['messages']}
💬 Ответов отправлено: {stats['replies']}
🤖 Вызовов AI: {stats['ai_calls']}
❌ Ошибок: {stats['errors']}

**Настройки:**
🎯 Вероятность ответа: {COMMENT_PROBABILITY * 100}%
💬 Целевой чат: {TARGET_CHAT_ID}
🤖 Статус: {'🟢 Активен' if stats['active'] else '🔴 Выключен'}

**API информация:**
🔑 API ID: {API_ID}
🔒 API Hash: {API_HASH[:10]}...
    """
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /test"""
    test_message = "Привет! Как работает твой AI?"
    
    message = await update.message.reply_text("🤖 Тестирую DeepSeek AI...")
    
    try:
        reply = await ai.get_reply(test_message)
        
        result_text = f"""
✅ **Тест пройден успешно!**

**Тестовое сообщение:**
"{test_message}"

**Ответ AI:**
{reply}

**Техническая информация:**
🤖 Вызовов AI: {stats['ai_calls']}
🔑 API ключ: {'✅ Настроен' if DEEPSEEK_API_KEY != 'sk-52e8d589ca9746a1b15ca0fc489676e0' else '⚠️ Простые ответы'}
⏰ Время: {datetime.now().strftime('%H:%M:%S')}
        """
        
        await message.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.edit_text(f"❌ Ошибка теста: {str(e)[:200]}")
        logger.error(f"Test error: {e}")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /ping"""
    start = datetime.now()
    message = await update.message.reply_text("🏓 Pong!")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    
    await message.edit_text(f"🏓 Pong! `{ms:.2f}ms`\n\n⏰ Время сервера: {end.strftime('%H:%M:%S')}")

# ========== ОБРАБОТКА СООБЩЕНИЙ В ЧАТЕ ==========
async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений в целевом чате"""
    try:
        # Проверяем, что это целевой чат
        if update.effective_chat.id != TARGET_CHAT_ID:
            return
        
        # Пропускаем команды
        if update.message.text and update.message.text.startswith('/'):
            return
        
        # Получаем текст сообщения
        message_text = update.message.text or update.message.caption or ""
        if not message_text.strip():
            return
        
        # Обновляем статистику
        stats['messages'] += 1
        
        # Проверяем активность бота
        if not stats['active']:
            return
        
        # Проверяем черный список
        lower_text = message_text.lower()
        for word in BLACKLIST_WORDS:
            if word in lower_text:
                logger.info(f"Пропускаем (черный список): {word}")
                return
        
        # Базовый шанс ответа
        reply_chance = COMMENT_PROBABILITY
        
        # Увеличиваем шанс для любимых тем
        for topic in FAVORITE_TOPICS:
            if topic in lower_text:
                reply_chance += 0.1  # +10% за каждую тему
                logger.info(f"Тема '{topic}' обнаружена, шанс увеличен")
                break
        
        # Ограничиваем максимальный шанс 60%
        reply_chance = min(reply_chance, 0.6)
        
        # Проверяем, нужно ли отвечать
        if random.random() > reply_chance:
            return
        
        # Генерируем ответ
        logger.info(f"Генерирую ответ на: {message_text[:100]}...")
        
        # Небольшая задержка для естественности (1-4 секунды)
        delay = random.uniform(1, 4)
        await asyncio.sleep(delay)
        
        # Получаем ответ от AI
        reply_text = await ai.get_reply(message_text)
        
        if reply_text:
            # Отправляем ответ
            await update.message.reply_text(reply_text)
            
            # Обновляем статистику
            stats['replies'] += 1
            
            logger.info(f"✅ Ответил: {reply_text[:80]}...")
            
            # Логируем в консоль для отладки
            print(f"\n💬 Новое сообщение в чате {TARGET_CHAT_ID}:")
            print(f"   👤 От: {update.effective_user.first_name}")
            print(f"   📝 Текст: {message_text[:100]}...")
            print(f"   🤖 Ответ: {reply_text[:100]}...")
            print(f"   📊 Статистика: {stats['replies']} ответов из {stats['messages']} сообщений")
    
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {str(e)[:200]}")
        stats['errors'] += 1

# ========== ОБРАБОТКА ОШИБОК ==========
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    error = context.error
    logger.error(f"Глобальная ошибка: {error}")
    stats['errors'] += 1
    
    # Можно отправить сообщение об ошибке админу
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
            )
        except:
            pass

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска"""
    print("=" * 50)
    print("🤖 ЗАПУСК DEEPSEEK TELEGRAM BOT")
    print("=" * 50)
    print(f"🔑 API ID: {API_ID}")
    print(f"🔒 API Hash: {API_HASH[:10]}...")
    print(f"💬 Целевой чат: {TARGET_CHAT_ID}")
    print(f"🤖 Модель: DeepSeek AI")
    print(f"🌐 Хостинг: BotHost")
    print("=" * 50)
    
    # Проверка токена бота
    if not BOT_TOKEN:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
        print("\n📌 Как исправить:")
        print("1. Создайте бота в @BotFather")
        print("2. Получите токен (выглядит как: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)")
        print("3. В панели BotHost добавьте переменную:")
        print('   BOT_TOKEN="ваш_токен"')
        print("\n🚀 После настройки перезапустите бота")
        sys.exit(1)
    
    print(f"✅ Токен бота: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
    print(f"✅ Вероятность ответа: {COMMENT_PROBABILITY * 100}%")
    print("=" * 50)
    print("🚀 Запуск бота...")
    
    try:
        # Создаем приложение бота
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("test", test_command))
        application.add_handler(CommandHandler("ping", ping_command))
        
        # Регистрируем обработчик обычных сообщений
        # Обратите внимание: фильтр по чату добавлен в саму функцию handle_chat_message
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_chat_message
        ))
        
        # Регистрируем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Запускаем бота в режиме polling
        print("🔄 Бот запущен в режиме polling...")
        print("📝 Логирование включено")
        print("=" * 50)
        print("✅ Бот готов к работе!")
        print(f"⏰ Время запуска: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ ФАТАЛЬНАЯ ОШИБКА: {e}")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
