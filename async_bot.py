# async_bot.py
import asyncio
import logging
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder # <-- Проверь, существует ли этот файл и класс там
from maxapi.types.attachments.buttons.callback_button import CallbackButton
# from maxapi.types.attachments.buttons.message_button import MessageButton
from maxapi.types.attachments.buttons.link_button import LinkButton # Если понадобится
# from maxapi.types.attachments.buttons.open_app_button import OpenAppButton # Если понадобится

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токен бота (убедись, что используешь правильный токен)
TOKEN = 'f9LHodD0cOJBJLYDixtV3RsHw4y35JeYVSFSTTalbyYsr6QB1T06ejZ0S_-Z2Ctnhvze3dV9OgzBzOzltVr6'
bot = Bot(TOKEN)
dp = Dispatcher()

# --- Демо-данные ---
DEMO_DATA = {
    "schedule": {
        "today": [
            {"time": "09:00-10:30", "subject": "Математический анализ", "room": "310", "teacher": "проф. Иванов"},
            {"time": "11:00-12:30", "subject": "Программирование", "room": "415", "teacher": "доц. Петрова"},
            {"time": "14:00-15:30", "subject": "Иностранный язык", "room": "201", "teacher": "ст. преп. Сидорова"}
        ]
    },
    "projects": [
        {"id": 1, "title": "Разработка мобильного приложения", "needs": "2 backend, 1 frontend, 1 дизайнер", "deadline": "2 месяца", "curator": "проф. Иванов", "status": "active"},
        {"id": 2, "title": "Исследование по Machine Learning", "needs": "3 исследователя", "deadline": "3 месяца", "curator": "доц. Петров", "status": "active"}
    ],
    "events": [
        {"title": "День открытых дверей", "date": "25.01.2024", "time": "18:00", "location": "актовый зал"},
        {"title": "Хакатон по веб-разработке", "date": "27.01.2024", "time": "10:00", "location": "ауд. 500"}
    ]
}

# --- Функции для генерации inline-клавиатуры ---
def get_main_menu_inline_keyboard():
    """Генерирует главное меню с inline-кнопками."""
    builder = InlineKeyboardBuilder()
    # Добавляем кнопки в первый ряд
    # Используем CallbackButton с payload
    builder.add(CallbackButton(text="📅 Расписание", payload="schedule")) # <-- CallbackButton с payload
    builder.add(CallbackButton(text="📝 Проекты", payload="projects"))    # <-- CallbackButton с payload
    # Новый ряд
    builder.row()
    builder.add(CallbackButton(text="🎓 Деканат", payload="dean"))  # <-- CallbackButton с payload
    builder.add(CallbackButton(text="📚 Библиотека", payload="library")) # <-- CallbackButton с payload
    # Новый ряд
    builder.row()
    builder.add(CallbackButton(text="🎭 Мероприятия", payload="events")) # <-- CallbackButton с payload
    builder.add(CallbackButton(text="ℹ️ Помощь", payload="help"))     # <-- CallbackButton с payload
    # Новый ряд
    builder.row()
    builder.add(LinkButton(text="🔗Открыть приложение", url="https://artemfair5-design.github.io/university-assistant-bot/")) # <-- LinkButton с URL
    # Возвращаем объект вложения
    return builder.as_markup()

# --- Функция для отправки сообщения с inline-клавиатурой, с fallback ---
async def send_message_with_inline_keyboard_fallback(bot, chat_id, text, keyboard_attachment=None):
    """
    Пытается отправить сообщение с inline-клавиатурой (как вложение).
    Если не получается (ошибка), отправляет без клавиатуры.
    """
    attachments_to_send = []
    if keyboard_attachment:
        try:
            logger.info(f"Пытаюсь отправить сообщение с inline-клавиатурой в чат {chat_id}")
            attachments_to_send.append(keyboard_attachment)
            # Передаём клавиатуру как вложение
            await bot.send_message(chat_id=chat_id, text=text, attachments=attachments_to_send)
            logger.info(f"Сообщение с inline-клавиатурой успешно отправлено в чат {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения с inline-клавиатурой: {e}")
            # Пытаемся отправить без клавиатуры как fallback
            try:
                await bot.send_message(chat_id=chat_id, text=text)
                logger.info(f"Сообщение без клавиатуры отправлено в чат {chat_id} как fallback.")
            except Exception as fallback_e:
                logger.error(f"Ошибка при отправке fallback-сообщения: {fallback_e}")
    else:
        # Если клавиатура не передана, просто отправляем текст
        logger.info(f"Отправляю сообщение без клавиатуры в чат {chat_id}")
        await bot.send_message(chat_id=chat_id, text=text)

# --- Обработчики событий ---
@dp.bot_started()
async def bot_started(event: BotStarted):
    logger.info(f"Бот запущен и готов к работе. Chat ID: {event.chat_id}")
    await send_message_with_inline_keyboard_fallback(
        bot=event.bot,
        chat_id=event.chat_id,
        text='Привет! Я Универ-Ассистент. Используйте команду /start или кнопки меню.',
        keyboard_attachment=get_main_menu_inline_keyboard()
    )

@dp.message_created(Command('start'))
async def handle_start(event: MessageCreated):
    # Правильно извлекаем user_id и text
    user_id = event.message.sender.user_id
    text = event.message.body.text

    logger.info(f"Получена команда /start от user_id {user_id}")
    welcome_text = """🎓 Добро пожаловать в Универ-Ассистент MAX!
    Я помогу вам с учебой и студенческой жизнью. Выберите нужный раздел:"""

    # Отправляем сообщение с inline-клавиатурой (или без, если fallback сработает)
    await send_message_with_inline_keyboard_fallback(
        bot=event.bot,
        chat_id=event.message.recipient.chat_id,
        text=welcome_text,
        keyboard_attachment=get_main_menu_inline_keyboard()
    )

# Обработчик для кнопок и текстовых команд (всех остальных сообщений)
@dp.message_created()
async def handle_message(event: MessageCreated):
    # Правильно извлекаем user_id и text
    user_id = event.message.sender.user_id
    text = event.message.body.text

    text_lower = text.lower().strip()
    logger.info(f"Получено сообщение от user_id {user_id}: '{text_lower}'")

    # --- Обработка команд/кнопок ---
    if 'start' in text_lower or 'меню' in text_lower or 'начать' in text_lower:
        welcome_text = """🎓 Добро пожаловать в Универ-Ассистент MAX!
        Я помогу вам с учебой и студенческой жизнью. Выберите нужный раздел:"""
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            text=welcome_text,
            keyboard_attachment=get_main_menu_inline_keyboard()
        )

    elif 'расписание' in text_lower or text_lower == 'schedule': # <-- Обработка payload для кнопки расписания
        schedule_data = DEMO_DATA["schedule"]
        schedule_text = "*Расписание на сегодня:*\n"
        for item in schedule_data["today"]:
            schedule_text += f"\n*{item['time']}* - {item['subject']} (ауд. {item['room']}) - {item['teacher']}"
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            text=schedule_text,
            keyboard_attachment=get_main_menu_inline_keyboard()
        )

    elif 'проект' in text_lower or text_lower == 'projects': # <-- Обработка payload для кнопки проектов
        projects_data = DEMO_DATA["projects"]
        if projects_data: # <-- ИСПРАВЛЕНО: было 'projects_'
             projects_text = "*Доступные проекты:*\n"
             for p in projects_data: # <-- ИСПРАВЛЕНО: было 'projects_'
                 projects_text += f"\n🚀 *{p['title']}*\n- Требуются: {p['needs']}\n- Дедлайн: {p['deadline']}\n- Куратор: {p['curator']}\n"
        else:
             projects_text = "К сожалению, на данный момент доступных проектов нет."
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            text=projects_text,
            keyboard_attachment=get_main_menu_inline_keyboard()
        )

    elif 'деканат' in text_lower or text_lower == 'dean':
        dean_text = "🎓 Информация о деканате:\n- Расписание консультаций: https://university.dean/schedule\n- Контакты: dean@university.edu"
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            text=dean_text,
            keyboard_attachment=get_main_menu_inline_keyboard()
        )

    elif 'библиотека' in text_lower or text_lower == 'library':
        lib_text = "📚 Информация о библиотеке:\n- Режим работы: Пн-Пт 9:00-18:00\n- Каталог: https://library.university.edu"
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            text=lib_text,
            keyboard_attachment=get_main_menu_inline_keyboard()
        )

    elif 'мероприятия' in text_lower or 'события' in text_lower or text_lower == 'events':
         events_data = DEMO_DATA["events"]
         events_text = "*Ближайшие мероприятия:*\n"
         for e in events_data: # <-- ИСПРАВЛЕНО: было 'events_'
             events_text += f"\n🎭 *{e['title']}*\n- Дата: {e['date']}\n- Время: {e['time']}\n- Место: {e['location']}\n"
         await send_message_with_inline_keyboard_fallback(
             bot=event.bot,
             chat_id=event.message.recipient.chat_id,
             text=events_text,
             keyboard_attachment=get_main_menu_inline_keyboard()
         )

    elif 'помощь' in text_lower or text_lower == 'help':
        help_text = """🎓 *Помощь Универ-Ассистент*:
        - *start* / *меню*: Показать главное меню
        - *расписание*: Узнать расписание на сегодня
        - *проекты*: Посмотреть доступные проекты
        - *деканат*: Информация о деканате
        - *библиотека*: Информация о библиотеке
        - *мероприятия*: Ближайшие события
        - *отзыв*: Оставить отзыв (напишите 'отзыв: ваш текст')"""
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            text=help_text,
            keyboard_attachment=get_main_menu_inline_keyboard()
        )

    elif text_lower.startswith('отзыв:'):
         feedback_text = text_lower.replace('отзыв:', '', 1).strip()
         if feedback_text:
             # Пока сохраняем в лог, можно модифицировать для сохранения в файл или БД позже
             logger.info(f"Получен отзыв от user_id {user_id}: {feedback_text}")
             await send_message_with_inline_keyboard_fallback(
                 bot=event.bot,
                 chat_id=event.message.recipient.chat_id,
                 text="✅ Спасибо за ваш отзыв! Мы его обязательно рассмотрим.",
                 keyboard_attachment=get_main_menu_inline_keyboard()
             )
         else:
             await send_message_with_inline_keyboard_fallback(
                 bot=event.bot,
                 chat_id=event.message.recipient.chat_id,
                 text="❌ Пожалуйста, укажите текст отзыва после 'отзыв:'.",
                 keyboard_attachment=get_main_menu_inline_keyboard()
             )

    elif 'открыть приложение' in text_lower or text_lower == '📱 открыть приложение': # <-- Обработка текста от MessageButton
         # maxapi может не поддерживать URL в кнопках напрямую в long polling или требовать специфичной настройки.
         # В качестве обходного пути, отправим сообщение с URL.
         app_url = "https://artemfair5-design.github.io/university-assistant-bot/" # Замени на свой URL
         app_text = f"📱 Открыть мини-приложение: {app_url}"
         await send_message_with_inline_keyboard_fallback(
             bot=event.bot,
             chat_id=event.message.recipient.chat_id,
             text=app_text,
             keyboard_attachment=get_main_menu_inline_keyboard()
         )

    else:
        unknown_text = "🤔 Не понял вашу команду. Используйте кнопки меню или напишите 'помощь'."
        logger.info(f"Неизвестная команда от user_id {user_id}: '{text_lower}'")
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            text=unknown_text,
            keyboard_attachment=get_main_menu_inline_keyboard()
        )

async def main():
    logger.info("Запуск бота с long polling...")
    # Удаляем все старые вебхуки (на всякий случай, если были настроены ранее)
    try:
        await bot.delete_webhook()
        logger.info("Старые вебхуки удалены (если были).")
    except Exception as e:
        logger.warning(f"Не удалось удалить вебхуки: {e}. Это нормально для long polling.")

    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
