# async_bot.py
import asyncio
import logging
import json
import os
from datetime import datetime
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated, MessageCallback
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types.attachments.buttons.callback_button import CallbackButton
from maxapi.types.attachments.buttons.message_button import MessageButton
from maxapi.types.attachments.buttons.open_app_button import OpenAppButton # <-- Импортируем OpenAppButton

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

# --- Текстовые шаблоны ---
WELCOME_TEXT = """🧠 Добро пожаловать в MAX Мозг!

Умная платформа для студентов, абитуриентов и сотрудников университета."""

ROLE_SELECTION_TEXT = """🎯 MAX Мозг

Выберите вашу роль для персонализированного доступа:"""

ROLE_APPROVED = """✅ Отлично! Теперь у вас есть доступ к MAX Мозг.

Нажмите кнопку ниже, чтобы открыть интеллектуальную платформу."""

ROLE_APPROVAL_PENDING = """⏳ Ваша роль *{role}* отправлена на подтверждение администратору.

Доступ к MAX Мозг будет открыт после подтверждения вашего статуса.

Ожидайте уведомления!"""

ROLE_REJECTED = """⚠️ Для получения полного доступа к MAX Мозг необходимо подтверждение статуса.

Обратитесь к администрации для верификации."""

ROLE_CHANGE_BLOCKED = """🚫 *Смена роли невозможна*

Вы уже выбрали роль *{role}* и не можете её изменить.

Если вам нужна другая роль, обратитесь к администратору."""

ADMIN_ROLE_APPROVAL_NOTIFICATION = """👨‍💼 *Требуется подтверждение роли*

Пользователь *{user_name}* (@{username}) выбрал роль *{role}*.

ID пользователя: `{user_id}`

Для подтверждения используйте:
`/approve_role {user_id}`"""

ADMIN_HELP = """👨‍💼 Админ-команды MAX Мозг:
/status <user_id> - Статус пользователя
/set_status <user_id> <status> - Установить статус
/approve_role <user_id> - Подтвердить роль пользователя
/statistics - Статистика платформы
/users - Список пользователей"""

HELP_TEXT = """🧠 Помощь MAX Мозг:
- отзыв: Оставить отзыв (напишите 'отзыв: ваш текст')
- статистика: Статистика платформы
- мойпрофиль: Ваш профиль
- роли: Выбор роли для доступа"""

# Список администраторов
ADMIN_IDS = [71636492, 12217116]

# Роли для нового мини-приложения
MAX_ROLES = {
    "абитуриент": "🎓 Абитуриент",
    "студент": "👨‍🎓 Студент",
    "работник": "👨‍💼 Работник",
    "администрация": "👑 Администрация",
    "гость": "👤 Гость"
}

# Роли, требующие подтверждения администратора
ROLES_REQUIRING_APPROVAL = ["абитуриент", "студент", "работник", "администрация"]

# --- Функции для генерации inline-клавиатуры ---
async def get_main_menu_inline_keyboard(event): # <-- Принимаем event
    """Генерирует главное меню с inline-кнопками."""
    builder = InlineKeyboardBuilder()

    # Пытаемся получить user_id бота через get_me()
    try:
        bot_me_info = await event.bot.get_me() # <-- Используем event.bot.get_me() асинхронно
        bot_user_id = bot_me_info.user_id
        bot_username = bot_me_info.username # <-- Получаем username бота
    except Exception as e:
        logger.error(f"Не удалось получить user_id/username бота: {e}")
        bot_user_id = 0 # Значение по умолчанию, если не удалось получить
        bot_username = "t27_hakaton_bot" # Значение по умолчанию

    # Кнопка мини-приложения (используем username и user_id бота)
    try:
        import random
        timestamp = int(datetime.now().timestamp())
        random_param = random.randint(1000, 9999)
        # ИСПОЛЬЗУЕМ USERNAME бота и параметры для мини-приложения
        # Это правильный способ для OpenAppButton в MAX API
        # web_app_url = f"https://max.ru/app?app_domain={bot_username}&t={timestamp}&r={random_param}" # <-- Используем username бота

        # builder.row( # <-- Убираем row() перед OpenAppButton, если он один
        builder.add(OpenAppButton(
            text="📱 Открыть приложение",
            # ПЕРЕДАЁМ USERNAME бота как web_app и USER_ID как contact_id
            web_app=bot_username, # <-- Используем username бота
            contact_id=bot_user_id # <-- Используем user_id бота
        ))
        # builder.row() # <-- Убираем, если не добавляем другие кнопки в тот же ряд

    except Exception as e:
        logger.error(f"Ошибка создания OpenAppButton: {e}")
        # Fallback: отправляем сообщение с URL
        builder.add(MessageButton(
            text="📱 Открыть приложение",
            message_text="📱 Открыть мини-приложение: https://artemfair5-design.github.io/university-assistant-bot/  "
        ))

    # --- Проверка статуса роли ---
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id # <-- Получаем user_id из event
    is_approved = await db.is_role_approved(user_id)
    role_info = await db.get_user_role_info(user_id)
    current_role = role_info.get('selected_role', 'гость')

    if not is_approved and current_role in ROLES_REQUIRING_APPROVAL:
        builder.row() # Новый ряд для статуса
        builder.add(CallbackButton(text="⏳ Статус подтверждения", payload="pending_approval"))

    # --- Кнопка смены роли ---
    # АДМИНИСТРАТОРЫ могут всегда менять роль, остальные - только если разрешено
    if user_id in ADMIN_IDS or await db.can_change_role(user_id):
        builder.row() # Новый ряд для кнопки смены роли
        builder.add(CallbackButton(text="🔄 Сменить роль", payload="change_role"))

    builder.row() # Новый ряд
    builder.add(CallbackButton(text="📞 Поддержка", payload="support"))

    # Возвращаем объект вложения
    return builder.as_markup()

# --- Функция для отправки сообщения с inline-клавиатурой, с перезаписью и fallback ---
async def send_message_with_inline_keyboard_fallback(bot, chat_id, user_id, text, keyboard_attachment=None):
    """
    Пытается отредактировать последнее отправленное ботом сообщение в чате user_id.
    Если не удаётся (например, ID не найдено или сообщение устарело), отправляет новое.
    """
    # Получаем ID последнего сообщения из БД (передаём user_id)
    last_msg_id = await db.get_last_message_id(user_id) # <-- ПЕРЕДАЁМ user_id

    attachments_to_send = []
    if keyboard_attachment:
        attachments_to_send.append(keyboard_attachment)

    if last_msg_id:
        try:
            logger.info(f"Пытаюсь отредактировать сообщение {last_msg_id} в чате {chat_id} для user_id {user_id}")

            # --- Вызов MAX API для редактирования сообщения ---
            # ВАЖНО: MAX API может НЕ поддерживать редактирование клавиатуры или attachments!
            # Попробуем отредактировать *только текст*.
            api_url = "https://api.max.ru/v1/messages.edit" # URL метода edit
            headers = {
                "Authorization": f"Bearer {bot.token}", # Используем токен бота
                "Content-Type": "application/json"
            }
            payload = {
                "access_token": bot.token, # Токен доступа
                "message_id": last_msg_id, # ID сообщения для редактирования
                "chat_id": chat_id, # ID чата
                "message": text # Новый текст
            }

            # ATTACHMENTS НЕ ПЕРЕДАЁМ ПРИ РЕДАКТИРОВАНИИ
            # if attachments_to_send:
            #     payload["attachments"] = attachments_to_send # <-- MAX API может не поддерживать редактирование attachments

            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, headers=headers) as response:
                    response_data = await response.json()
                    if response.status == 200 and response_data.get("success"):
                        logger.info(f"Сообщение {last_msg_id} в чате {chat_id} успешно отредактировано (только текст).")
                        # ID сообщения не меняется при редактировании, но мы НЕ обновляем last_message_id в БД,
                        # потому что оно осталось тем же. Клавиатура не изменилась при редактировании.
                        # Если клавиатура *должна* измениться, нужно отправить новое сообщение.
                        # Поэтому, если attachments_to_send не пустой, или если нужно обновить клавиатуру, всегда отправляем новое сообщение.
                        if attachments_to_send:
                             logger.info("Клавиатура изменилась или добавлена. Отправляем новое сообщение вместо редактирования.")
                             raise aiohttp.ClientResponseError(request_info=None, history=None, status=400, message="Keyboard changed, sending new message")
                        return response_data
                    else:
                        error_details = response_data.get("error", "Unknown error")
                        logger.warning(f"Редактирование сообщения {last_msg_id} не удалось ({response.status}): {error_details}")
                        # Если редактирование не удалось, отправим новое сообщение
                        raise aiohttp.ClientResponseError(request_info=None, history=None, status=response.status, message=error_details)

        except aiohttp.ClientResponseError as e:
            logger.info(f"Отправляем новое сообщение в чат {chat_id} для user_id {user_id} (редактирование не удалось или клавиатура изменилась).")
            # Отправляем новое сообщение
            try:
                # Попробуем отправить с клавиатурой как attachments
                sent_message = await bot.send_message(chat_id=chat_id, text=text, attachments=attachments_to_send)
                # Сохраняем ID *нового* отправленного сообщения в БД (передаём user_id)
                new_message_id = getattr(sent_message, 'message_id', None)
                if new_message_id:
                    await db.update_last_message_id(user_id, str(new_message_id)) # <-- ПЕРЕДАЁМ user_id
                    logger.info(f"Сохранён ID нового сообщения {new_message_id} для user_id {user_id}")
                else:
                    logger.warning(f"Не удалось получить ID отправленного сообщения в чат {chat_id} для user_id {user_id}.")
                return sent_message
            except Exception as attach_error:
                logger.error(f"Ошибка отправки нового сообщения с клавиатурой: {attach_error}")
                # Fallback без клавиатуры
                try:
                    sent_message = await bot.send_message(chat_id=chat_id, text=text)
                    new_message_id = getattr(sent_message, 'message_id', None)
                    if new_message_id:
                        await db.update_last_message_id(user_id, str(new_message_id)) # <-- ПЕРЕДАЁМ user_id
                    logger.info(f"Сообщение без клавиатуры отправлено в чат {chat_id} для user_id {user_id} как fallback.")
                    return sent_message
                except Exception as fallback_error:
                    logger.error(f"Ошибка при отправке fallback-сообщения: {fallback_error}")
                    return None

        except Exception as e:
            logger.error(f"Неожиданная ошибка при редактировании сообщения: {e}")
            # Отправляем новое сообщение как fallback
            try:
                sent_message = await bot.send_message(chat_id=chat_id, text=text, attachments=attachments_to_send)
                new_message_id = getattr(sent_message, 'message_id', None)
                if new_message_id:
                    await db.update_last_message_id(user_id, str(new_message_id)) # <-- ПЕРЕДАЁМ user_id
                logger.info(f"Сообщение с клавиатурой отправлено в чат {chat_id} для user_id {user_id} как fallback после ошибки редактирования.")
                return sent_message
            except Exception as fallback_error:
                logger.error(f"Ошибка при отправке fallback-сообщения после ошибки редактирования: {fallback_error}")
                try:
                    sent_message = await bot.send_message(chat_id=chat_id, text=text)
                    new_message_id = getattr(sent_message, 'message_id', None)
                    if new_message_id:
                        await db.update_last_message_id(user_id, str(new_message_id)) # <-- ПЕРЕДАЁМ user_id
                    logger.info(f"Сообщение без клавиатуры отправлено в чат {chat_id} для user_id {user_id} как double-fallback.")
                    return sent_message
                except Exception as double_fallback_error:
                    logger.error(f"Ошибка при отправке double-fallback-сообщения: {double_fallback_error}")
                    return None

    else:
        # Если last_msg_id не было в БД, отправляем новое сообщение
        logger.info(f"Отправляем новое сообщение в чат {chat_id} для user_id {user_id} (предыдущего сообщения не было).")
        try:
            # Попробуем отправить с клавиатурой как attachments
            sent_message = await bot.send_message(chat_id=chat_id, text=text, attachments=attachments_to_send)
            # Сохраняем ID *нового* отправленного сообщения в БД (передаём user_id)
            new_message_id = getattr(sent_message, 'message_id', None)
            if new_message_id:
                await db.update_last_message_id(user_id, str(new_message_id)) # <-- ПЕРЕДАЁМ user_id
                logger.info(f"Сохранён ID нового сообщения {new_message_id} для user_id {user_id}")
            else:
                logger.warning(f"Не удалось получить ID отправленного сообщения в чат {chat_id} для user_id {user_id}.")
            return sent_message
        except Exception as e:
            logger.error(f"Ошибка отправки нового сообщения с клавиатурой: {e}")
            # Fallback без клавиатуры
            try:
                sent_message = await bot.send_message(chat_id=chat_id, text=text)
                new_message_id = getattr(sent_message, 'message_id', None)
                if new_message_id:
                    await db.update_last_message_id(user_id, str(new_message_id)) # <-- ПЕРЕДАЁМ user_id
                logger.info(f"Сообщение без клавиатуры отправлено в чат {chat_id} для user_id {user_id} как fallback.")
                return sent_message
            except Exception as fallback_e:
                logger.error(f"Ошибка при отправке fallback-сообщения: {fallback_e}")
                return None

# --- Обработчики событий ---
@dp.bot_started()
async def bot_started(event: BotStarted):
    logger.info(f"MAX Мозг бот запущен. Chat ID: {event.chat_id}")
    try:
        await db.save_user_data(event.user)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")

    # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ С ПЕРЕЗАПИСЬЮ
    keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
    await send_message_with_inline_keyboard_fallback(
        bot=event.bot,
        chat_id=event.chat_id,
        user_id=event.user.user_id, # <-- Передаём user_id
        text='🧠 Привет! Я MAX Мозг - интеллектуальный ассистент. Нажмите кнопку для начала работы.',
        keyboard_attachment=keyboard # <-- Передаём клавиатуру
    )

@dp.message_created(Command('start'))
async def handle_start(event: MessageCreated):
    user_id = event.message.sender.user_id
    logger.info(f"Команда /start от user_id {user_id}")

    try:
        await db.save_user_data(event.message.sender, event.message.body.text)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")

    # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ С ПЕРЕЗАПИСЬЮ
    keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
    await send_message_with_inline_keyboard_fallback(
        bot=event.bot,
        chat_id=event.message.recipient.chat_id,
        user_id=user_id, # <-- Передаём user_id
        text='🧠 Привет! Я MAX Мозг - интеллектуальный ассистент. Нажмите кнопку для начала работы.',
        keyboard_attachment=keyboard # <-- Передаём клавиатуру
    )

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
            # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для временного сообщения)
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="✅ Спасибо за ваш отзыв! Мы его обязательно рассмотрим.",
                keyboard_attachment=None # <-- Временное сообщение без клавиатуры
            )
            # Затем снова показываем главное меню
            keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="Что вы хотите сделать дальше?",
                keyboard_attachment=keyboard # <-- Передаём клавиатуру
            )
        else:
            # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для временного сообщения)
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="❌ Пожалуйста, укажите текст отзыва после 'отзыв:'.",
                keyboard_attachment=None # <-- Временное сообщение без клавиатуры
            )
            # Затем снова показываем главное меню
            keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="Что вы хотите сделать дальше?",
                keyboard_attachment=keyboard # <-- Передаём клавиатуру
            )
        return

    # Обработка команды "мойпрофиль"
    if any(cmd in text_lower for cmd in ['мойпрофиль', 'профиль', 'profile', 'мой профиль']):
        try:
            profile_text = await get_user_profile_text(user_id) # <-- Вызов асинхронной функции
            # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для сообщения профиля)
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text=profile_text,
                keyboard_attachment=None # <-- Сообщение профиля без клавиатуры
            )
            # Затем снова показываем главное меню
            keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="Что вы хотите сделать дальше?",
                keyboard_attachment=keyboard # <-- Передаём клавиатуру
            )
        except Exception as e:
            logger.error(f"Ошибка получения профиля: {e}")
            # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для временного сообщения)
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="❌ Ошибка при загрузке профиля",
                keyboard_attachment=None # <-- Временное сообщение без клавиатуры
            )
            # Затем снова показываем главное меню
            keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="Что вы хотите сделать дальше?",
                keyboard_attachment=keyboard # <-- Передаём клавиатуру
            )
        return

    # Обработка команды выбора роли
    if any(cmd in text_lower for cmd in ['роли', 'роль', 'roles', 'role', 'выбор роли']):
        # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        await handle_role_selection(event) # <-- Этот обработчик должен сам вызывать send_message_with_inline_keyboard_fallback
        return

    # Обработка основных команд
    if any(cmd in text_lower for cmd in ['start', 'меню', 'начать', 'max', 'макс']):
        # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            user_id=user_id, # <-- Передаём user_id
            text='🧠 Привет! Я MAX Мозг - интеллектуальный ассистент. Нажмите кнопку для начала работы.',
            keyboard_attachment=keyboard # <-- Передаём клавиатуру
        )
        return

    # Поиск команды в словаре обработчиков
    for command, handler in COMMAND_HANDLERS.items():
        if command in text_lower or text_lower == command:
            try:
                if asyncio.iscoroutinefunction(handler):
                    response_text = await handler()
                else:
                    response_text = handler()

                # Для команды роли показываем клавиатуру выбора
                if command in ['роли', 'roles']:
                    # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
                    await handle_role_selection(event) # <-- Этот обработчик должен сам вызывать send_message_with_inline_keyboard_fallback
                else:
                    # Для других команд показываем временное сообщение и главное меню
                    # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для временного сообщения)
                    await send_message_with_inline_keyboard_fallback(
                        bot=event.bot,
                        chat_id=event.message.recipient.chat_id,
                        user_id=user_id, # <-- Передаём user_id
                        text=response_text,
                        keyboard_attachment=None # <-- Временное сообщение без клавиатуры
                    )
                    # Затем снова показываем главное меню
                    keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
                    await send_message_with_inline_keyboard_fallback(
                        bot=event.bot,
                        chat_id=event.message.recipient.chat_id,
                        user_id=user_id, # <-- Передаём user_id
                        text="Что вы хотите сделать дальше?",
                        keyboard_attachment=keyboard # <-- Передаём клавиатуру
                    )
                return
            except Exception as e:
                logger.error(f"Ошибка обработки команды {command}: {e}")
                # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для временного сообщения)
                await send_message_with_inline_keyboard_fallback(
                    bot=event.bot,
                    chat_id=event.message.recipient.chat_id,
                    user_id=user_id, # <-- Передаём user_id
                    text="❌ Произошла ошибка при обработке команды.",
                    keyboard_attachment=None # <-- Временное сообщение без клавиатуры
                )
                # Затем снова показываем главное меню
                keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
                await send_message_with_inline_keyboard_fallback(
                    bot=event.bot,
                    chat_id=event.message.recipient.chat_id,
                    user_id=user_id, # <-- Передаём user_id
                    text="Что вы хотите сделать дальше?",
                    keyboard_attachment=keyboard # <-- Передаём клавиатуру
                )
                return

    # Если команда не распознана, показываем начальный экран
    # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
    keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
    await send_message_with_inline_keyboard_fallback(
        bot=event.bot,
        chat_id=event.message.recipient.chat_id,
        user_id=user_id, # <-- Передаём user_id
        text="🤔 Не понял вашу команду. Используйте кнопки меню или напишите 'помощь'.",
        keyboard_attachment=keyboard # <-- Передаём клавиатуру
    )

# --- Обработчик callback'ов для кнопок ---
@dp.message_callback()
async def handle_callback(event: MessageCallback):
    """Обрабатывает нажатия на inline-кнопки для MAX Мозг."""
    user_id = event.callback.user.user_id
    payload = event.callback.payload

    logger.info(f"Callback от user_id {user_id}: {payload}")

    try:
        await db.save_user_data(event.callback.user)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")

    # Обработка начала работы
    if payload == "start":
        # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        await handle_role_selection(event) # <-- Этот обработчик должен сам вызывать send_message_with_inline_keyboard_fallback
        return

    # Обработка выбора ролей (тоже внутри handle_callback, если не вынесено)
    role_mapping = {
        "role_applicant": "абитуриент",
        "role_student": "студент",
        "role_worker": "работник",
        "role_admin": "администрация",
        "role_guest": "гость"
    }

    if payload in role_mapping:
        role_name = role_mapping[payload]
        logger.info(f"Пользователь {user_id} выбрал роль: {role_name}")

        try:
            # Для АДМИНИСТРАТОРОВ всегда разрешаем смену роли
            # Для обычных пользователей блокируем смену не-гостевых ролей
            allow_role_change = (user_id in ADMIN_IDS) or (role_name == 'гость')

            # Сохраняем роль с настройками блокировки
            await db.update_user_role(user_id, role_name, allow_role_change)

            # Обновляем статус пользователя
            await db.update_user_status(
                user_id=user_id,
                new_status=role_name,
                changed_by="user_choice",
                reason=f"Пользователь выбрал роль: {role_name}"
            )

            # Логируем доступ к мини-приложению
            await db.log_mini_app_access(user_id, {
                'first_name': event.callback.user.first_name,
                'last_name': event.callback.user.last_name,
                'username': event.callback.user.username,
                'selected_role': role_name
            })

            # Если роль требует подтверждения и пользователь не администратор
            if role_name in ROLES_REQUIRING_APPROVAL and user_id not in ADMIN_IDS:
                # Уведомляем администраторов
                await notify_admins_about_pending_role(event, user_id, role_name)
                # Показываем пользователю сообщение о ожидании подтверждения
                await handle_role_pending_approval(event, role_name)
            else:
                # Для гостевой роли или администратора сразу даем доступ
                await handle_role_approved(event, role_name)

        except Exception as e:
            logger.error(f"Ошибка сохранения роли пользователя: {e}")
            # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для временного сообщения)
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="❌ Ошибка при выборе роли",
                keyboard_attachment=None # <-- Временное сообщение без клавиатуры
            )
            # Затем снова показываем главное меню
            keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=event.message.recipient.chat_id,
                user_id=user_id, # <-- Передаём user_id
                text="Что вы хотите сделать дальше?",
                keyboard_attachment=keyboard # <-- Передаём клавиатуру
            )
        return

    # Обновляем главное меню
    if payload == "back_to_menu":
        # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            user_id=user_id, # <-- Передаём user_id
            text="Главное меню MAX Мозг:",
            keyboard_attachment=keyboard # <-- Передаём клавиатуру
        )
        return

    # Обработка открытия приложения (fallback)
    if payload == "open_max_app":
        web_app_url = "https://artemfair5-design.github.io/university-assistant-bot/"
        # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для временного сообщения)
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            user_id=user_id, # <-- Передаём user_id
            text=f"🧠 Открыть MAX Мозг: {web_app_url}",
            keyboard_attachment=None # <-- Временное сообщение без клавиатуры
        )
        # Затем снова показываем главное меню
        keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id,
            user_id=user_id, # <-- Передаём user_id
            text="Что вы хотите сделать дальше?",
            keyboard_attachment=keyboard # <-- Передаём клавиатуру
        )
        return

    # Если payload неизвестен
    # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
    keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
    await send_message_with_inline_keyboard_fallback(
        bot=event.bot,
        chat_id=event.message.recipient.chat_id,
        user_id=user_id, # <-- Передаём user_id
        text="🤔 Неизвестная команда. Используйте кнопки меню.",
        keyboard_attachment=keyboard # <-- Передаём клавиатуру
    )

# --- Вспомогательные функции ---
async def handle_role_selection(event):
    """Обрабатывает выбор роли (вспомогательная функция)."""
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id

    # АДМИНИСТРАТОРЫ могут всегда менять роль, остальные - только если разрешено
    if user_id in ADMIN_IDS or await db.can_change_role(user_id):
        keyboard = await get_role_selection_keyboard(event) # <-- Вызов функции, которая возвращает клавиатуру
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id,
            user_id=user_id, # <-- Передаём user_id
            text=ROLE_SELECTION_TEXT,
            keyboard_attachment=keyboard # <-- Передаём клавиатуру
        )
    else:
        # Если смена роли заблокирована, показываем главное меню
        current_role_info = await db.get_user_role_info(user_id)
        current_role = current_role_info.get('selected_role', 'гость')
        message = ROLE_CHANGE_BLOCKED.format(role=MAX_ROLES.get(current_role, current_role))
        keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
        await send_message_with_inline_keyboard_fallback(
            bot=event.bot,
            chat_id=event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id,
            user_id=user_id, # <-- Передаём user_id
            text=message,
            keyboard_attachment=keyboard # <-- Передаём клавиатуру
        )

async def get_role_selection_keyboard(event): # <-- Новая функция для клавиатуры выбора роли
    """Генерирует клавиатуру выбора роли."""
    builder = InlineKeyboardBuilder()
    builder.add(CallbackButton(text="🎓 Я абитуриент", payload="role_applicant"))
    builder.row()
    builder.add(CallbackButton(text="👨‍🎓 Я студент", payload="role_student"))
    builder.row()
    builder.add(CallbackButton(text="👨‍💼 Я сотрудник", payload="role_worker"))
    builder.row()
    builder.add(CallbackButton(text="👑 Администрация", payload="role_admin"))
    builder.row()
    builder.add(CallbackButton(text="👤 Гостевой доступ", payload="role_guest"))
    builder.row()
    builder.add(CallbackButton(text="◀️ Назад", payload="back_to_menu")) # Кнопка "назад"
    return builder.as_markup()

async def handle_role_pending_approval(event, role_name):
    """Обрабатывает ожидание подтверждения роли."""
    role_display = MAX_ROLES.get(role_name, "Пользователь")
    message = ROLE_APPROVAL_PENDING.format(role=role_display)
    keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
    await send_message_with_inline_keyboard_fallback(
        bot=event.bot,
        chat_id=event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id,
        user_id=event.callback.user.user_id, # <-- Передаём user_id
        text=message,
        keyboard_attachment=keyboard # <-- Передаём клавиатуру
    )

async def handle_role_approved(event, role_name):
    """Обрабатывает подтверждение роли."""
    role_display = MAX_ROLES.get(role_name, "Пользователь")
    message = f"{ROLE_APPROVED}\n\n🎯 Ваша роль: {role_display}"
    keyboard = await get_main_menu_inline_keyboard(event) # <-- Передаём event
    await send_message_with_inline_keyboard_fallback(
        bot=event.bot,
        chat_id=event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id,
        user_id=event.callback.user.user_id, # <-- Передаём user_id
        text=message,
        keyboard_attachment=keyboard # <-- Передаём клавиатуру
    )

async def notify_admins_about_pending_role(event, user_id: int, role_name: str):
    """Уведомляет администраторов о необходимости подтверждения роли."""
    user = event.callback.user
    role_display = MAX_ROLES.get(role_name, role_name)

    message = ADMIN_ROLE_APPROVAL_NOTIFICATION.format(
        user_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
        username=user.username or 'нет username',
        role=role_display,
        user_id=user_id
    )

    for admin_id in ADMIN_IDS:
        try:
            # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ (без клавиатуры для уведомления админу)
            await send_message_with_inline_keyboard_fallback(
                bot=event.bot,
                chat_id=admin_id,
                user_id=admin_id, # <-- Админ уведомляется как пользователь
                text=message,
                keyboard_attachment=None # <-- Уведомление без клавиатуры
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить администратора {admin_id}: {e}")

async def get_user_profile_text(user_id: int):
    """Генерирует текст профиля пользователя для MAX Мозг."""
    user_info = await db.get_user_info(user_id)
    if not user_info:
        return "❌ Пользователь не найден в базе данных."

    # Извлекаем данные
    first_name = user_info.get('first_name', 'Не указано')
    last_name = user_info.get('last_name', '')
    username = user_info.get('username', 'Не указан')
    selected_role = user_info.get('selected_role', 'гость')
    registration_date_str = user_info.get('registration_date', 'Неизвестно')
    last_activity_str = user_info.get('last_activity', 'Неизвестно')
    message_count = user_info.get('message_count', 0)
    feedback_count = user_info.get('feedback_count', 0)

    # --- Форматируем дату регистрации ---
    reg_date_clean = registration_date_str
    if reg_date_clean and reg_date_clean != 'Неизвестно':
        # Убираем T и оставляем только YYYY-MM-DD HH:MM
        reg_date_clean = reg_date_clean.replace('T', ' ')[:16]
    else:
        reg_date_clean = 'Неизвестно'

    # --- Форматируем дату последней активности (ИСПРАВЛЕНО) ---
    last_activity_clean = last_activity_str
    if last_activity_clean and last_activity_clean != 'Неизвестно':
        # Убираем T и оставляем только YYYY-MM-DD HH:MM
        last_activity_clean = last_activity_clean.replace('T', ' ')[:16] # <-- УБРАНА БУКВА 'T' и лишние кавычки/звездочки
    else:
        last_activity_clean = 'Неизвестно'

    # --- Форматируем полное имя ---
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name

    # --- Форматируем роль ---
    role_display = MAX_ROLES.get(selected_role, selected_role)

    # --- Форматируем профиль ---
    profile_text = f"""👤 Ваш профиль MAX Мозг

📋 Информация:
ID: {user_info.get('user_id', 'Неизвестно')}
Имя: {full_name}
Username: @{username}
Роль: {role_display}

📊 Статистика:
Сообщений: {message_count}
Отзывов: {feedback_count}
Дата регистрации: {reg_date_clean}
Последняя активность: {last_activity_clean}"""

    # Информация о полноте данных (пример)
    fields_present = sum([
        bool(first_name and first_name != 'Не указано'),
        bool(last_name and last_name != ''),
        bool(username and username != 'Не указан'),
        bool(selected_role and selected_role != 'гость'),
        bool(reg_date_clean and reg_date_clean != 'Неизвестно'),
        bool(last_activity_clean and last_activity_clean != 'Неизвестно'),
        # ... (добавь другие поля, если есть)
    ])
    total_fields = 6 # Общее количество проверяемых полей
    completeness_percent = int((fields_present / total_fields) * 100)

    profile_text += f"\nПолнота данных: {completeness_percent}%"

    return profile_text

# --- Словарь обработчиков команд ---
COMMAND_HANDLERS = {
    'помощь': lambda: HELP_TEXT,
    'help': lambda: HELP_TEXT,
    'статистика': get_statistics_text,
    'роли': lambda: "🔄 Нажмите на кнопку ниже, чтобы выбрать или сменить роль",
    'max': lambda: "🧠 MAX Мозг - интеллектуальная платформа для университета",
    'мозг': lambda: "🧠 MAX Мозг - интеллектуальная платформа для университета",
}

async def get_statistics_text():
    """Генерирует текст статистики для MAX Мозг."""
    try:
        stats = await db.get_user_stats()
        status_stats_str = "\n".join([f"- {status}: {count}" for status, count in stats.get('status_stats', {}).items()])
        role_stats_str = "\n".join([f"- {role}: {count}" for role, count in stats.get('role_stats', {}).items()])

        return f"""📊 Статистика MAX Мозг:

Всего пользователей: {stats['total_users']}
Сообщений в боте: {stats['total_messages']}
Отзывов: {stats['total_feedback']}
Активных за 7 дней: {stats['active_users_7d']}
Подтвержденных ролей: {stats.get('approved_users', 0)}
Доступов к платформе: {stats.get('mini_app_users', 0)}

Распределение по статусам:
{status_stats_str if status_stats_str else '- Нет данных'}

Распределение по ролям:
{role_stats_str if role_stats_str else '- Нет данных'}"""
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return "❌ Не удалось получить статистику."

# --- Основная функция ---
async def main():
    logger.info("Запуск бота с long polling...")
    logger.info(f"Загружено данных о {len(db.user_data)} пользователях")

    try:
        await bot.delete_webhook()
        logger.info("Старые вебхуки удалены")
    except Exception as e:
        logger.warning(f"Не удалось удалить вебхуки: {e}")

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
        logger.info(f"Сохранено данных о {len(db.user_data)} пользователях")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
