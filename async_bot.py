# async_bot.py
import asyncio
import logging
import os
from datetime import datetime
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated, OpenAppButton, MessageCallback
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types.attachments.buttons.callback_button import CallbackButton

# Импортируем нашу базу данных
from database import db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('MAX_TOKEN', 'f9LHodD0cOJBJLYDixtV3RsHw4y35JeYVSFSTTalbyYsr6QB1T06ejZ0S_-Z2Ctnhvze3dV9OgzBzOzltVr6')
bot = Bot(TOKEN)
dp = Dispatcher()

# --- Текстовые шаблоны ---
WELCOME_TEXT = """🎓 Добро пожаловать в Универ-Ассистент MAX!

Для автоматической регистрации в мини-приложении просто нажмите кнопку ниже."""

HELP_TEXT = """🎓 Помощь Универ-Ассистент:
- отзыв: Оставить отзыв (напишите 'отзыв: ваш текст')
- статистика: Показать статистику бота
- мойпрофиль: Показать ваши данные"""

# --- Универсальные функции ---
async def get_start_keyboard():
    """Генерирует начальную клавиатуру с кнопкой Старт."""
    builder = InlineKeyboardBuilder()
    builder.add(CallbackButton(text="🚀 Старт", payload="start"))
    return builder.as_markup()

async def get_main_menu_keyboard(event):
    """Генерирует главное меню с inline-кнопками."""
    builder = InlineKeyboardBuilder()
    
    try:
        bot_me = event.bot.me
        
        if bot_me:
            web_app_url = "https://artemfair5-design.github.io/university-assistant-bot/"
            
            builder.row(
                OpenAppButton(
                    text="📱 Открыть приложение",
                    web_app=web_app_url,
                    contact_id=bot_me.user_id
                )
            )
            
    except Exception as e:
        logger.error(f"Ошибка создания OpenAppButton: {e}")
        builder.row(
            CallbackButton(
                text="📱 Открыть приложение (Fallback)",
                payload="open_app_fallback"
            )
        )
    
    return builder.as_markup()

async def send_response(bot_instance, chat_id, text, keyboard=None):
    """Универсальная функция отправки сообщений."""
    try:
        attachments = [keyboard] if keyboard else []
        await bot_instance.send_message(chat_id=chat_id, text=text, attachments=attachments)
        logger.info(f"Сообщение отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        try:
            await bot_instance.send_message(chat_id=chat_id, text=text)
        except Exception as fallback_e:
            logger.error(f"Fallback тоже не сработал: {fallback_e}")

# --- Словарь обработчиков команд ---
async def get_statistics_text():
    """Генерирует текст статистики"""
    try:
        stats = await db.get_user_stats()
        return f"""📊 Статистика бота:

👥 Всего пользователей: {stats['total_users']}
💬 Всего сообщений: {stats['total_messages']}
⭐ Отзывов: {stats['total_feedback']}
🔥 Активных за 7 дней: {stats['active_users_7d']}"""
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return "❌ Не удалось получить статистику. Проверьте подключение к базе данных."

COMMAND_HANDLERS = {
    'помощь': lambda: HELP_TEXT,
    'help': lambda: HELP_TEXT,
    'статистика': get_statistics_text,
}

# --- Обработчики событий ---
async def handle_start_response(event, response_text=None):
    """Обрабатывает начальный ответ с кнопкой Старт."""
    keyboard = await get_start_keyboard()
    
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    
    if response_text is None:
        response_text = "🎓 Добро пожаловать! Нажмите кнопку 'Старт' для начала работы."
    
    await send_response(event.bot, chat_id, response_text, keyboard)

async def handle_common_response(event, response_text=None):
    """Обрабатывает общий ответ с основной клавиатурой."""
    keyboard = await get_main_menu_keyboard(event)
    
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    
    if response_text is None:
        response_text = WELCOME_TEXT
    
    await send_response(event.bot, chat_id, response_text, keyboard)

@dp.bot_started()
async def bot_started(event: BotStarted):
    logger.info(f"Бот запущен. Chat ID: {event.chat_id}")
    try:
        await db.save_user_data(event.user)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
    
    await handle_start_response(event, '🎓 Привет! Я Универ-Ассистент. Нажмите кнопку "Старт" для начала работы.')

@dp.message_created(Command('start'))
async def handle_start(event: MessageCreated):
    user_id = event.message.sender.user_id
    logger.info(f"Команда /start от user_id {user_id}")
    
    try:
        await db.save_user_data(event.message.sender, event.message.body.text)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
    
    await handle_start_response(event)

@dp.message_created()
async def handle_message(event: MessageCreated):
    user_id = event.message.sender.user_id
    text = event.message.body.text
    
    logger.info(f"Сообщение от user_id {user_id}: '{text}'")
    
    try:
        await db.save_user_data(event.message.sender, text)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
    
    text_lower = text.lower().strip()
    
    # Обработка отзыва
    if text_lower.startswith('отзыв:'):
        feedback_text = text_lower.replace('отзыв:', '', 1).strip()
        if feedback_text:
            logger.info(f"Отзыв от user_id {user_id}: {feedback_text}")
            await handle_common_response(event, "✅ Спасибо за ваш отзыв! Мы его обязательно рассмотрим.")
        else:
            await handle_common_response(event, "❌ Пожалуйста, укажите текст отзыва после 'отзыв:'.")
        return
    
    # Обработка основных команд
    if any(cmd in text_lower for cmd in ['start', 'меню', 'начать']):
        await handle_start_response(event)
        return
    
    # Поиск команды в словаре обработчиков
    for command, handler in COMMAND_HANDLERS.items():
        if command in text_lower or text_lower == command:
            try:
                if asyncio.iscoroutinefunction(handler):
                    response_text = await handler()
                else:
                    response_text = handler()
                await handle_common_response(event, response_text)
                return
            except Exception as e:
                logger.error(f"Ошибка обработки команды {command}: {e}")
                await handle_common_response(event, "❌ Произошла ошибка при выполнении команды.")
                return
    
    # Если команда не распознана, показываем начальный экран
    await handle_start_response(event, "🤔 Не понял вашу команду. Нажмите кнопку 'Старт' для начала работы.")

# --- Обработчик callback'ов для кнопок ---
@dp.message_callback()
async def handle_callback(event: MessageCallback):
    """Обрабатывает нажатия на inline-кнопки."""
    user_id = event.callback.user.user_id
    payload = event.callback.payload
    
    logger.info(f"Callback от user_id {user_id}: {payload}")
    
    try:
        await db.save_user_data(event.callback.user)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
    
    if payload == "start":
        await handle_common_response(event)
        return
    
    if payload == "open_app_fallback":
        web_app_url = "https://artemfair5-design.github.io/university-assistant-bot/"
        await send_response(event.bot, event.message.recipient.chat_id, f"📱 Открыть мини-приложение: {web_app_url}")
        return

# --- Основная функция ---
async def main():
    # Подключаемся к базе данных
    max_retries = 5
    for attempt in range(max_retries):
        try:
            await db.connect()
            break
        except Exception as e:
            logger.error(f"Попытка {attempt + 1}/{max_retries} подключения к БД не удалась: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                logger.info(f"Повторная попытка через {wait_time} секунд...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Не удалось подключиться к базе данных после всех попыток")
                return
    
    try:
        stats = await db.get_user_stats()
        logger.info(f"Статистика базы данных: {stats}")
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
    
    try:
        await bot.delete_webhook()
        logger.info("Старые вебхуки удалены")
    except Exception as e:
        logger.warning(f"Не удалось удалить вебхуки: {e}")
    
    logger.info("Запуск бота с long polling...")
    await dp.start_polling(bot)

async def shutdown():
    """Корректное завершение работы"""
    await db.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен по запросу пользователя")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        # Корректно закрываем соединения
        asyncio.run(shutdown())