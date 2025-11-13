import asyncio
import logging
import os
import random
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
WELCOME_TEXT = """🧠 Добро пожаловать в MAX Мозг!

Умная платформа для студентов, абитуриентов и сотрудников университета."""

ROLE_SELECTION_TEXT = """🎯 MAX Мозг

Выберите вашу роль для персонализированного доступа:"""

ROLE_APPROVED = """✅ Отлично! Теперь у вас есть доступ к MAX Мозг.

Нажмите кнопку ниже, чтобы открыть интеллектуальную платформу."""

ROLE_APPROVAL_PENDING = """⏳ Ваша роль *{role}* отправлена на подтверждение администратору.

Ожидайте уведомления!"""

ROLE_REJECTED = """⚠️ Для получения полного доступа к MAX Мозг необходимо подтверждение статуса.

Обратитесь к администрации для верификации."""

ROLE_CHANGE_BLOCKED = """🚫 *Смена роли невозможна*

Вы уже выбрали роль *{role}* и не можете её изменить.

Обратитесь к администратору."""

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

# Роли
MAX_ROLES = {
    "абитуриент": "🎓 Абитуриент",
    "студент": "👨‍🎓 Студент",
    "работник": "👨‍💼 Работник",
    "администрация": "👑 Администрация",
    "гость": "👤 Гость"
}

# Роли, требующие подтверждения
ROLES_REQUIRING_APPROVAL = ["студент", "работник", "администрация"]

# Кэш для сообщений
message_cache = {}

# --- Функции клавиатур ---
async def get_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(CallbackButton(text="🧠 Начать работу с MAX", payload="start"))
    return builder.as_markup()

async def get_role_selection_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="🎓 Я абитуриент", payload="role_applicant"))
    builder.row(CallbackButton(text="👨‍🎓 Я студент", payload="role_student"))
    builder.row(CallbackButton(text="👨‍💼 Я сотрудник", payload="role_worker"))
    builder.row(CallbackButton(text="👑 Администрация", payload="role_admin"))
    builder.row(CallbackButton(text="👤 Гостевой доступ", payload="role_guest"))
    return builder.as_markup()

async def get_max_app_keyboard(event, user_role="гость"):
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id
    is_approved = await db.is_role_approved(user_id)
    current_role = (await db.get_user_role_info(user_id)).get('selected_role', 'гость')
    
    builder = InlineKeyboardBuilder()
    timestamp = int(datetime.now().timestamp())
    random_param = random.randint(1000, 9999)
    web_app_url = f"https://artemfair5-design.github.io/university-assistant-bot/auth.html?t={timestamp}&r={random_param}"
    
    try:
        builder.row(OpenAppButton(
            text="🧠 Открыть MAX Мозг",
            web_app=web_app_url,
            contact_id=event.bot.me.user_id if hasattr(event.bot, 'me') else 0
        ))
    except Exception as e:
        logger.error(f"Ошибка OpenAppButton: {e}, URL: {web_app_url}")
        builder.row(CallbackButton(text="🧠 Открыть MAX Мозг", payload="open_max_app"))
    
    if not is_approved and current_role in ROLES_REQUIRING_APPROVAL:
        builder.row(CallbackButton(text="⏳ Ожидание подтверждения", payload="pending_approval"))
    if await db.can_change_role(user_id):
        builder.row(CallbackButton(text="🔄 Сменить роль", payload="change_role"))
    builder.row(CallbackButton(text="📞 Поддержка", payload="support"))
    
    return builder.as_markup()

async def get_support_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="📞 Поддержка", payload="support"))
    return builder.as_markup()

# --- Универсальная отправка/редактирование сообщений ---
async def send_response(bot_instance, chat_id, text, keyboard=None, remove_previous=True, user_id=None):
    """Редактирует существующее сообщение или отправляет новое с управлением кэшем."""
    try:
        cache_key = (chat_id, user_id) if user_id else chat_id
        attachments = [keyboard] if keyboard else []

        # Проверяем, есть ли сообщение в кэше и нужно ли редактировать
        if remove_previous and cache_key in message_cache:
            old_message_id = message_cache[cache_key]
            try:
                # Пытаемся отредактировать существующее сообщение
                edited_message = await bot_instance.edit_message(
                    chat_id=chat_id,
                    message_id=old_message_id,
                    text=text,
                    attachments=attachments
                )
                logger.info(f"Отредактировано сообщение {old_message_id} в чате {chat_id} для {cache_key}")
                return edited_message
            except Exception as e:
                logger.warning(f"Не удалось отредактировать сообщение {old_message_id}: {e}")
                # Удаляем из кэша, чтобы отправить новое сообщение
                message_cache.pop(cache_key, None)

        # Если редактирование не удалось или кэша нет, отправляем новое сообщение
        sent_message = await bot_instance.send_message(
            chat_id=chat_id,
            text=text,
            attachments=attachments
        )
        if keyboard:
            message_cache[cache_key] = sent_message.message_id
            logger.info(f"Сохранили новое сообщение {sent_message.message_id} для {cache_key}")
        else:
            # Если нет клавиатуры, не сохраняем в кэш, чтобы избежать лишних попыток редактирования
            logger.info(f"Отправлено сообщение без клавиатуры в чат {chat_id} для {cache_key}")
        
        return sent_message
    except Exception as e:
        logger.error(f"Ошибка отправки/редактирования в чат {chat_id}: {e}")
        # Fallback: отправляем новое сообщение без кэширования
        sent_message = await bot_instance.send_message(chat_id=chat_id, text=text)
        return sent_message

# --- Вспомогательные функции ---
async def handle_role_pending_approval(event, role_name):
    role_display = MAX_ROLES.get(role_name, "Пользователь")
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id
    message = ROLE_APPROVAL_PENDING.format(role=role_display)
    keyboard = await get_support_keyboard()
    await send_response(event.bot, chat_id, message, keyboard, user_id=user_id)

async def notify_admins_about_pending_role(event, user_id: int, role_name: str):
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
            # Уведомления админам отправляем как новые сообщения
            await send_response(event.bot, admin_id, message, remove_previous=False, user_id=user_id)
        except Exception as e:
            logger.warning(f"Не удалось уведомить администратора {admin_id}: {e}")

# --- Обработчики событий ---
async def handle_start_response(event, response_text=None):
    keyboard = await get_start_keyboard()
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    user_id = event.message.sender.user_id if hasattr(event, 'message') else event.user.user_id
    response_text = response_text or "🧠 Добро пожаловать в MAX Мозг!"
    await send_response(event.bot, chat_id, response_text, keyboard, user_id=user_id)

async def handle_role_selection(event):
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    
    can_change = await db.can_change_role(user_id)
    current_role = (await db.get_user_role_info(user_id)).get('selected_role')
    
    if current_role and current_role != 'гость' and not can_change:
        keyboard = await get_max_app_keyboard(event, user_role=current_role)
        message = ROLE_CHANGE_BLOCKED.format(role=MAX_ROLES.get(current_role, current_role))
        await send_response(event.bot, chat_id, message, keyboard, user_id=user_id)
        return
    
    keyboard = await get_role_selection_keyboard()
    await send_response(event.bot, chat_id, ROLE_SELECTION_TEXT, keyboard, user_id=user_id)

async def handle_role_approved(event, role_name):
    role_display = MAX_ROLES.get(role_name, "Пользователь")
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id
    approval_text = f"✅ Роль {role_display} подтверждена!\nТеперь вы можете использовать все возможности MAX Мозг."
    keyboard = await get_support_keyboard()
    await send_response(event.bot, chat_id, approval_text, keyboard, user_id=user_id)

async def handle_role_rejected(event):
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id
    keyboard = await get_support_keyboard()
    await send_response(event.bot, chat_id, ROLE_REJECTED, keyboard, user_id=user_id)

# --- Обработчики команд ---
async def get_statistics_text():
    try:
        stats = await db.get_user_stats()
        status_text = "\n".join([f"  - {status}: {count}" for status, count in stats.get('status_stats', {}).items()])
        role_text = "\n".join([f"  - {role}: {count}" for role, count in stats.get('role_stats', {}).items()])
        return f"""📊 Статистика MAX Мозг:
👥 Всего пользователей: {stats['total_users']}
💬 Сообщений: {stats['total_messages']}
⭐ Отзывов: {stats['total_feedback']}
🔥 Активных за 7 дней: {stats['active_users_7d']}
✅ Подтвержденных ролей: {stats.get('approved_users', 0)}
🧠 Доступов: {stats.get('mini_app_users', 0)}
🏷️ Статусы:\n{status_text or '  - Нет данных'}
🎯 Роли:\n{role_text or '  - Нет данных'}"""
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        return "❌ Не удалось получить статистику."

async def get_user_profile_text(user_id: int):
    try:
        user_info = await db.get_user_info(user_id)
        if not user_info:
            return "❌ Пользователь не найден"
        role_display = MAX_ROLES.get(user_info.get('selected_role', 'гость'), 'Гость')
        role_status = "✅ Подтверждена" if user_info.get('role_approved') else "⏳ Ожидает"
        can_change = "✅ Да" if user_info.get('role_change_allowed', True) else "❌ Нет"
        return f"""🧠 Ваш профиль:
🆔 ID: {user_info['user_id']}
👤 Имя: {user_info['first_name'] or 'Не указано'} {user_info['last_name'] or ''}
📛 Юзернейм: @{user_info['username'] or 'Не указан'}
🎯 Роль: {role_display}
✅ Статус: {role_status}
🔄 Смена роли: {can_change}
🧠 Доступов: {user_info['mini_app_access_count'] or 0}
📅 Регистрация: {user_info['registration_date'].strftime('%d.%m.%Y %H:%M')}
💬 Сообщений: {user_info['message_count']}"""
    except Exception as e:
        logger.error(f"Ошибка профиля: {e}")
        return "❌ Не удалось загрузить профиль"

COMMAND_HANDLERS = {
    'помощь': lambda: HELP_TEXT,
    'help': lambda: HELP_TEXT,
    'статистика': get_statistics_text,
    'роли': lambda: "🔄 Нажмите кнопку для выбора роли",
    'max': lambda: "🧠 MAX Мозг - интеллектуальная платформа"
}

# --- Админ-команды ---
async def handle_admin_status(event, user_id: int):
    if event.message.sender.user_id not in ADMIN_IDS:
        return "❌ У вас нет прав администратора"
    user_info = await db.get_user_info(user_id)
    if not user_info:
        return f"❌ Пользователь {user_id} не найден"
    role_display = MAX_ROLES.get(user_info.get('selected_role', 'гость'), 'Гость')
    role_status = "✅ Подтверждена" if user_info.get('role_approved') else "❌ Не подтверждена"
    can_change = "✅ Да" if user_info.get('role_change_allowed', True) else "❌ Нет"
    return f"""🧠 Профиль {user_id}:
👤 Имя: {user_info['first_name'] or 'Не указано'} {user_info['last_name'] or ''}
📛 Юзернейм: @{user_info['username'] or 'Не указан'}
🎯 Роль: {role_display}
✅ Статус: {role_status}
🔄 Смена роли: {can_change}
🧠 Доступов: {user_info['mini_app_access_count'] or 0}
📅 Регистрация: {user_info['registration_date'].strftime('%d.%m.%Y %H:%M')}
💬 Сообщений: {user_info['message_count']}"""

async def handle_set_status(event, user_id: int, new_status: str):
    if event.message.sender.user_id not in ADMIN_IDS:
        return "❌ У вас нет прав администратора"
    try:
        await db.update_user_status(
            user_id=user_id,
            new_status=new_status,
            changed_by=f"admin_{event.message.sender.user_id}",
            reason=f"Установлен админом {event.message.sender.user_id}"
        )
        return f"✅ Статус {user_id} изменен на '{new_status}'"
    except Exception as e:
        logger.error(f"Ошибка установки статуса: {e}")
        return f"❌ Ошибка: {e}"

# --- Обработчики событий ---
@dp.bot_started()
async def bot_started(event: BotStarted):
    logger.info(f"Бот запущен. Chat ID: {event.chat_id}")
    try:
        await db.save_user_data(event.user)
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
    await handle_start_response(event, '🧠 Привет! Я MAX Мозг. Нажми кнопку для начала.')

@dp.message_created(Command('start'))
async def handle_start(event: MessageCreated):
    user_id = event.message.sender.user_id
    logger.info(f"Команда /start от {user_id}")
    try:
        await db.save_user_data(event.message.sender, event.message.body.text)
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
    await handle_start_response(event)

@dp.message_created()
async def handle_message(event: MessageCreated):
    user_id = event.message.sender.user_id
    chat_id = event.message.recipient.chat_id
    text = event.message.body.text
    
    logger.info(f"Сообщение от {user_id}: '{text}'")
    
    try:
        await db.save_user_data(event.message.sender, text)
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
    
    text_lower = text.lower().strip()
    
    if text_lower.startswith('отзыв:'):
        feedback_text = text_lower.replace('отзыв:', '', 1).strip()
        if feedback_text:
            logger.info(f"Отзыв от {user_id}: {feedback_text}")
        await handle_role_selection(event)
        return
    
    if text_lower in ['мойпрофиль', 'профиль', 'profile', 'мой профиль']:
        profile_text = await get_user_profile_text(user_id)
        await send_response(event.bot, chat_id, profile_text, remove_previous=False, user_id=user_id)
        return
    
    if text_lower in ['роли', 'роль', 'roles', 'role', 'выбор роли']:
        await handle_role_selection(event)
        return
    
    if any(cmd in text_lower for cmd in ['start', 'меню', 'начать', 'max', 'макс']):
        await handle_start_response(event)
        return
    
    for command, handler in COMMAND_HANDLERS.items():
        if command in text_lower or text_lower == command:
            response_text = await handler() if asyncio.iscoroutinefunction(handler) else handler()
            if command in ['роли', 'roles']:
                await handle_role_selection(event)
            else:
                await send_response(event.bot, chat_id, response_text, remove_previous=False, user_id=user_id)
            return
    
    await handle_start_response(event, "🤔 Не понял команду. Нажми кнопку.")

# --- Админ-команды ---
@dp.message_created(Command('status'))
async def handle_admin_status_command(event: MessageCreated):
    chat_id = event.message.recipient.chat_id
    user_id = event.message.sender.user_id
    try:
        parts = event.message.body.text.split()
        if len(parts) < 2:
            await send_response(event.bot, chat_id, "❌ Использование: /status <user_id>", remove_previous=False, user_id=user_id)
            return
        target_user_id = int(parts[1])
        response = await handle_admin_status(event, target_user_id)
        await send_response(event.bot, chat_id, response, remove_previous=False, user_id=user_id)
    except ValueError:
        await send_response(event.bot, chat_id, "❌ Неверный формат user_id", remove_previous=False, user_id=user_id)
    except Exception as e:
        logger.error(f"Ошибка команды status: {e}")
        await send_response(event.bot, chat_id, "❌ Ошибка команды", remove_previous=False, user_id=user_id)

@dp.message_created(Command('set_status'))
async def handle_set_status_command(event: MessageCreated):
    chat_id = event.message.recipient.chat_id
    user_id = event.message.sender.user_id
    try:
        parts = event.message.body.text.split()
        if len(parts) < 3:
            await send_response(event.bot, chat_id, "❌ Использование: /set_status <user_id> <status>", remove_previous=False, user_id=user_id)
            return
        target_user_id = int(parts[1])
        new_status = ' '.join(parts[2:])
        response = await handle_set_status(event, target_user_id, new_status)
        await send_response(event.bot, chat_id, response, remove_previous=False, user_id=user_id)
    except ValueError:
        await send_response(event.bot, chat_id, "❌ Неверный формат user_id", remove_previous=False, user_id=user_id)
    except Exception as e:
        logger.error(f"Ошибка команды set_status: {e}")
        await send_response(event.bot, chat_id, "❌ Ошибка команды", remove_previous=False, user_id=user_id)

@dp.message_created(Command('approve_role'))
async def handle_approve_role_command(event: MessageCreated):
    chat_id = event.message.recipient.chat_id
    user_id = event.message.sender.user_id
    
    if user_id not in ADMIN_IDS:
        await send_response(event.bot, chat_id, "❌ Нет прав администратора", remove_previous=False, user_id=user_id)
        return
    
    try:
        parts = event.message.body.text.split()
        if len(parts) < 2:
            await send_response(event.bot, chat_id, "❌ Использование: /approve_role <user_id>", remove_previous=False, user_id=user_id)
            return
        target_user_id = int(parts[1])
        await db.approve_user_role(target_user_id, f"admin_{user_id}")
        
        user_info = await db.get_user_info(target_user_id)
        if user_info:
            role_display = MAX_ROLES.get(user_info.get('selected_role', 'пользователь'), 'Пользователь')
            keyboard = await get_support_keyboard()
            await send_response(
                event.bot,
                target_user_id,
                f"✅ Роль *{role_display}* подтверждена!\nПолный доступ к MAX Мозг открыт.",
                keyboard=keyboard,
                user_id=target_user_id
            )
        
        await send_response(event.bot, chat_id, f"✅ Роль {target_user_id} подтверждена!", remove_previous=False, user_id=user_id)
    except ValueError:
        await send_response(event.bot, chat_id, "❌ Неверный формат user_id", remove_previous=False, user_id=user_id)
    except Exception as e:
        logger.error(f"Ошибка подтверждения роли: {e}")
        await send_response(event.bot, chat_id, f"❌ Ошибка: {e}", remove_previous=False, user_id=user_id)

@dp.message_created(Command('admin'))
async def handle_admin_help(event: MessageCreated):
    chat_id = event.message.recipient.chat_id
    user_id = event.message.sender.user_id
    response = ADMIN_HELP if user_id in ADMIN_IDS else "❌ Нет прав администратора"
    await send_response(event.bot, chat_id, response, remove_previous=False, user_id=user_id)

# --- Обработчик callback'ов ---
@dp.message_callback()
async def handle_callback(event: MessageCallback):
    user_id = event.callback.user.user_id
    payload = event.callback.payload
    chat_id = event.message.recipient.chat_id
    
    logger.info(f"Callback от {user_id}: {payload}")
    
    try:
        await db.save_user_data(event.callback.user)
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
    
    if payload == "start":
        await handle_role_selection(event)
        return
    
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
        
        allow_role_change = role_name == 'гость'
        await db.update_user_role(user_id, role_name, allow_role_change)
        await db.update_user_status(
            user_id=user_id,
            new_status=role_name,
            changed_by="user_choice",
            reason=f"Выбрана роль: {role_name}"
        )
        await db.log_mini_app_access(user_id, {
            'first_name': event.callback.user.first_name,
            'last_name': event.callback.user.last_name,
            'username': event.callback.user.username,
            'selected_role': role_name
        })
        
        if role_name in ROLES_REQUIRING_APPROVAL:
            await notify_admins_about_pending_role(event, user_id, role_name)
            await handle_role_pending_approval(event, role_name)
        else:
            await handle_role_approved(event, role_name)
        return
    
    if payload == "change_role":
        await handle_role_selection(event)
        return
    
    if payload in ["support", "contact_admin"]:
        await send_response(event.bot, chat_id,
                           "📞 Поддержка:\nEmail: artemfair5@gmail.com\nТелеграм: t.me/Mulllymka1",
                           remove_previous=False, user_id=user_id)
        return
    
    if payload == "open_max_app":
        await send_response(event.bot, chat_id,
                           "🧠 Открыть MAX Мозг: https://artemfair5-design.github.io/university-assistant-bot/auth.html",
                           remove_previous=False, user_id=user_id)
        return
    
    if payload == "pending_approval":
        current_role = (await db.get_user_info(user_id)).get('selected_role', 'гость')
        await handle_role_pending_approval(event, current_role)
        return

# --- Основная функция ---
async def main():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            await db.connect()
            break
        except Exception as e:
            logger.error(f"Попытка {attempt + 1}/{max_retries} подключения к БД: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep((attempt + 1) * 5)
            else:
                logger.error("Не удалось подключиться к БД")
                return
    
    try:
        stats = await db.get_user_stats()
        logger.info(f"Статистика: {stats}")
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
    
    try:
        await bot.delete_webhook()
        logger.info("Вебхуки удалены")
    except Exception as e:
        logger.warning(f"Не удалось удалить вебхуки: {e}")
    
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

async def shutdown():
    await db.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка бота: {e}")
    finally:
        asyncio.run(shutdown())