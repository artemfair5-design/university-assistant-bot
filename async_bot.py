import asyncio
import logging
import os
import socket
from datetime import datetime
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated, OpenAppButton, MessageCallback
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types.attachments.buttons.callback_button import CallbackButton
from maxapi.types.input_media import InputMediaBuffer  # ← ДОБАВЬТЕ ЭТОТ ИМПОРТ
import aiohttp

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

# --- Текстовые шаблоны (ОБНОВЛЕНЫ ДЛЯ MAX МОЗГ) ---
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

# Прямая ссылка на профиль в MAX
MAX_PROFILE_URL = "https://max.ru/u/f9LHodD0cOKjtP4JqI_7NVijOYB4HbrU9UeT3xlr7m76Mmz7CEgQUmEQLzE  "

# --- Универсальные функции (ОБНОВЛЕНЫ) ---
async def get_start_keyboard():
    """Генерирует начальную клавиатуру для MAX Мозг."""
    builder = InlineKeyboardBuilder()
    builder.add(CallbackButton(text="🧠 Начать работу с MAX", payload="start"))
    return builder.as_markup()

async def get_role_selection_keyboard():
    """Генерирует клавиатуру выбора роли для MAX Мозг."""
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="🎓 Я абитуриент", payload="role_applicant"))
    builder.row(CallbackButton(text="👨‍🎓 Я студент", payload="role_student"))
    builder.row(CallbackButton(text="👨‍💼 Я сотрудник", payload="role_worker"))
    builder.row(CallbackButton(text="👑 Администрация", payload="role_admin"))
    builder.row(CallbackButton(text="👤 Гостевой доступ", payload="role_guest"))
    return builder.as_markup()

async def get_main_menu_keyboard(event, user_role="гость"):
    """Генерирует главное меню MAX Мозг с проверкой доступа"""
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id
    
    # Проверяем подтверждена ли роль
    is_approved = await db.is_role_approved(user_id)
    role_info = await db.get_user_role_info(user_id)
    current_role = role_info.get('selected_role', 'гость')
    
    builder = InlineKeyboardBuilder()
    
    # Кнопка мини-приложения ВСЕГДА доступна
    try:
        import random
        timestamp = int(datetime.now().timestamp())
        random_param = random.randint(1000, 9999)
        web_app_url = f"https://artemfair5-design.github.io/university-assistant-bot/auth.html?t={timestamp}&r={random_param}"
        
        builder.row(
            OpenAppButton(
                text="🧠 Открыть MAX Мозг",
                web_app=web_app_url,
                contact_id=event.bot.me.user_id if hasattr(event.bot, 'me') else 0
            )
        )
            
    except Exception as e:
        logger.error(f"Ошибка создания OpenAppButton для Max: {e}")
        builder.row(CallbackButton(text="🧠 Открыть MAX Мозг", payload="open_max_app"))
    
    # Дополнительные кнопки в зависимости от статуса
    if not is_approved and current_role in ROLES_REQUIRING_APPROVAL:
        builder.row(CallbackButton(text="⏳ Статус подтверждения", payload="pending_approval"))
    
    # АДМИНИСТРАТОРЫ могут всегда менять роль, остальные - только если разрешено
    if user_id in ADMIN_IDS or await db.can_change_role(user_id):
        builder.row(CallbackButton(text="🔄 Сменить роль", payload="change_role"))
    
    builder.row(CallbackButton(text="📞 Поддержка", payload="support"))
    
    return builder.as_markup()

async def send_main_menu(bot_instance, chat_id, text, keyboard=None):
    """Отправляет основное меню - всегда одно сообщение с кнопками"""
    try:
        attachments = [keyboard] if keyboard else []
        sent_message = await bot_instance.send_message(
            chat_id=chat_id, 
            text=text, 
            attachments=attachments
        )
        logger.info(f"Главное меню отправлено в чат {chat_id}")
        return sent_message
    except Exception as e:
        logger.error(f"Ошибка отправки главного меню: {e}")
        try:
            return await bot_instance.send_message(chat_id=chat_id, text=text)
        except Exception as fallback_e:
            logger.error(f"Fallback тоже не сработал: {fallback_e}")

async def send_temporary_message(bot_instance, chat_id, text):
    """Отправляет временное сообщение (исчезает после следующего действия)"""
    try:
        return await bot_instance.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logger.error(f"Ошибка отправки временного сообщения: {e}")

async def send_keyboard_message(bot_instance, chat_id, text, keyboard):
    """Отправляет сообщение с клавиатурой"""
    try:
        return await bot_instance.send_message(
            chat_id=chat_id, 
            text=text, 
            attachments=[keyboard]
        )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения с клавиатурой: {e}")

# --- Функция для генерации QR-кода ---
async def generate_qr_code(url):
    """Генерирует QR-код для указанной ссылки"""
    try:
        import qrcode
        from io import BytesIO
        
        # Создаем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем в bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes
    except ImportError:
        logger.error("Библиотека qrcode не установлена. Установите: pip install qrcode[pil]")
        return None
    except Exception as e:
        logger.error(f"Ошибка генерации QR-кода: {e}")
        return None

async def send_qr_code(bot_instance, chat_id, qr_code_bytes, caption="🧠 QR-код моего профиля в MAX"):
    """Отправляет QR-код через MAX API - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        # Создаем InputMediaBuffer ПРАВИЛЬНО - без параметра 'type'
        buffer_obj = InputMediaBuffer(
            media=qr_code_bytes.getvalue(),  # передаем bytes
            filename="qr_code.png"
        )

        # Отправляем сообщение с вложением
        await bot_instance.send_message(
            chat_id=chat_id,
            text=caption,
            attachments=[buffer_obj]  # передаем как список вложений
        )
        
        logger.info(f"QR-код успешно отправлен в чат {chat_id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки QR-кода: {e}")
        return False

# --- Вспомогательные функции (НОВЫЕ) ---
async def handle_role_pending_approval(event, role_name):
    """Обрабатывает ожидание подтверждения роли"""
    role_display = MAX_ROLES.get(role_name, "Пользователь")
    
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    message = ROLE_APPROVAL_PENDING.format(role=role_display)
    
    # Показываем главное меню с информацией о статусе
    keyboard = await get_main_menu_keyboard(event, role_name)
    await send_main_menu(event.bot, chat_id, message, keyboard)

async def notify_admins_about_pending_role(event, user_id: int, role_name: str):
    """Уведомляет администраторов о необходимости подтверждения роли"""
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
            await send_temporary_message(event.bot, admin_id, message)
        except Exception as e:
            logger.warning(f"Не удалось уведомить администратора {admin_id}: {e}")

# --- Обработчики событий (ОБНОВЛЕНЫ) ---
async def handle_start_response(event, response_text=None):
    """Обрабатывает начальный ответ для MAX Мозг."""
    keyboard = await get_start_keyboard()
    
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    
    if response_text is None:
        response_text = "🧠 Добро пожаловать в MAX Мозг! Нажмите кнопку для начала работы."
    
    await send_main_menu(event.bot, chat_id, response_text, keyboard)

async def handle_role_selection(event):
    """Обрабатывает выбор роли для MAX Мозг с проверкой блокировки"""
    user_id = event.callback.user.user_id if hasattr(event, 'callback') else event.message.sender.user_id
    
    # АДМИНИСТРАТОРЫ могут всегда менять роль без ограничений
    if user_id in ADMIN_IDS:
        keyboard = await get_role_selection_keyboard()
        chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
        await send_main_menu(event.bot, chat_id, ROLE_SELECTION_TEXT, keyboard)
        return
    
    # Для обычных пользователей проверяем возможность смены роли
    can_change = await db.can_change_role(user_id)
    current_role_info = await db.get_user_role_info(user_id)
    current_role = current_role_info.get('selected_role')
    
    if current_role and current_role != 'гость' and not can_change:
        # Пользователь не может менять роль
        keyboard = await get_main_menu_keyboard(event, user_role=current_role)
        chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
        message = ROLE_CHANGE_BLOCKED.format(role=MAX_ROLES.get(current_role, current_role))
        await send_main_menu(event.bot, chat_id, message, keyboard)
        return
    
    # Показываем выбор роли
    keyboard = await get_role_selection_keyboard()
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    await send_main_menu(event.bot, chat_id, ROLE_SELECTION_TEXT, keyboard)

async def handle_role_approved(event, role_name):
    """Обрабатывает подтверждение выбора роли."""
    role_display = MAX_ROLES.get(role_name, "Пользователь")
    
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    
    approval_text = f"""✅ Роль {role_display} подтверждена!

Теперь вы можете использовать все возможности MAX Мозг."""
    
    # Показываем главное меню
    keyboard = await get_main_menu_keyboard(event, role_name)
    await send_main_menu(event.bot, chat_id, approval_text, keyboard)

async def handle_role_rejected(event):
    """Обрабатывает ограниченный доступ."""
    chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
    
    # Показываем главное меню
    keyboard = await get_main_menu_keyboard(event, user_role="гость")
    await send_main_menu(event.bot, chat_id, ROLE_REJECTED, keyboard)

# --- Словарь обработчиков команд (ОБНОВЛЕН) ---
async def get_statistics_text():
    """Генерирует текст статистики для MAX Мозг"""
    try:
        stats = await db.get_user_stats()
        status_text = "\n".join([f"  - {status}: {count}" for status, count in stats.get('status_stats', {}).items()])
        role_text = "\n".join([f"  - {role}: {count}" for role, count in stats.get('role_stats', {}).items()])
        
        return f"""📊 Статистика MAX Мозг:

👥 Всего пользователей: {stats['total_users']}
💬 Сообщений в боте: {stats['total_messages']}
⭐ Отзывов: {stats['total_feedback']}
🔥 Активных за 7 дней: {stats['active_users_7d']}
✅ Подтвержденных ролей: {stats.get('approved_users', 0)}
🧠 Доступов к платформе: {stats.get('mini_app_users', 0)}

🏷️ Распределение по статусам:
{status_text if status_text else '  - Нет данных'}

🎯 Распределение по ролям:
{role_text if role_text else '  - Нет данных'}"""
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return "❌ Не удалось получить статистику."

async def get_user_profile_text(user_id: int):
    """Генерирует текст профиля пользователя для MAX Мозг"""
    try:
        user_info = await db.get_user_info(user_id)
        if not user_info:
            return "❌ Пользователь не найден"
        
        role_display = MAX_ROLES.get(user_info.get('selected_role', 'гость'), 'Гость')
        role_status = "✅ Подтверждена" if user_info.get('role_approved') else "⏳ Ожидает подтверждения"
        can_change = "✅ Да" if user_info.get('role_change_allowed', True) else "❌ Нет"
        
        return f"""🧠 Ваш профиль MAX Мозг:

🆔 ID: {user_info['user_id']}
👤 Имя: {user_info['first_name'] or 'Не указано'} {user_info['last_name'] or ''}
📛 Юзернейм: @{user_info['username'] or 'Не указан'}
🎯 Роль: {role_display}
✅ Статус роли: {role_status}
🔄 Можно сменить роль: {can_change}
🧠 Доступов к платформе: {user_info['mini_app_access_count'] or 0}
📅 Регистрация: {user_info['registration_date'].strftime('%d.%m.%Y %H:%M')}
💬 Сообщений: {user_info['message_count']}"""
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {e}")
        return "❌ Не удалось загрузить профиль"

COMMAND_HANDLERS = {
    'помощь': lambda: HELP_TEXT,
    'help': lambda: HELP_TEXT,
    'статистика': get_statistics_text,
    'роли': lambda: "🔄 Нажмите на кнопку ниже, чтобы выбрать или сменить роль",
    'max': lambda: "🧠 MAX Мозг - интеллектуальная платформа для университета",
}

# --- Админ-команды (ОБНОВЛЕНЫ) ---
async def handle_admin_status(event, user_id: int):
    """Обрабатывает команду статуса пользователя для администратора"""
    if event.message.sender.user_id not in ADMIN_IDS:
        return "❌ У вас нет прав администратора"
    
    user_info = await db.get_user_info(user_id)
    if not user_info:
        return f"❌ Пользователь с ID {user_id} не найден"
    
    role_display = MAX_ROLES.get(user_info.get('selected_role', 'гость'), 'Гость')
    role_status = "✅ Подтверждена" if user_info.get('role_approved') else "❌ Не подтверждена"
    can_change = "✅ Да" if user_info.get('role_change_allowed', True) else "❌ Нет"
    
    return f"""🧠 Профиль пользователя {user_id}:

👤 Имя: {user_info['first_name'] or 'Не указано'} {user_info['last_name'] or ''}
📛 Юзернейм: @{user_info['username'] or 'Не указан'}
🎯 Роль: {role_display}
✅ Статус роли: {role_status}
🔄 Можно сменить роль: {can_change}
🧠 Доступов к MAX Мозг: {user_info['mini_app_access_count'] or 0}
📅 Регистрация: {user_info['registration_date'].strftime('%d.%m.%Y %H:%M')}
💬 Сообщений: {user_info['message_count']}"""

async def handle_set_status(event, user_id: int, new_status: str):
    """Обрабатывает команду установки статуса пользователя"""
    if event.message.sender.user_id not in ADMIN_IDS:
        return "❌ У вас нет прав администратора"
    
    try:
        await db.update_user_status(
            user_id=user_id,
            new_status=new_status,
            changed_by=f"admin_{event.message.sender.user_id}",
            reason=f"Установен администратором {event.message.sender.user_id}"
        )
        return f"✅ Статус пользователя {user_id} успешно изменен на '{new_status}'"
    except Exception as e:
        logger.error(f"Ошибка установки статуса: {e}")
        return f"❌ Не удалось установить статус: {e}"

# --- Обработчики событий бота (ОБНОВЛЕНЫ) ---
@dp.bot_started()
async def bot_started(event: BotStarted):
    logger.info(f"MAX Мозг бот запущен. Chat ID: {event.chat_id}")
    try:
        await db.save_user_data(event.user)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
    
    await handle_start_response(event, '🧠 Привет! Я MAX Мозг - интеллектуальный ассистент. Нажмите кнопку для начала работы.')

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
            await send_temporary_message(event.bot, event.message.recipient.chat_id, "✅ Спасибо за ваш отзыв!")
        # После отзыва показываем главное меню
        keyboard = await get_main_menu_keyboard(event)
        await send_main_menu(event.bot, event.message.recipient.chat_id, "Что вы хотите сделать дальше?", keyboard)
        return
    
    # Обработка команды "мойпрофиль"
    if text_lower in ['мойпрофиль', 'профиль', 'profile', 'мой профиль']:
        try:
            profile_text = await get_user_profile_text(user_id)
            # Показываем профиль как временное сообщение, затем главное меню
            await send_temporary_message(event.bot, event.message.recipient.chat_id, profile_text)
            keyboard = await get_main_menu_keyboard(event)
            await send_main_menu(event.bot, event.message.recipient.chat_id, "Что вы хотите сделать дальше?", keyboard)
        except Exception as e:
            logger.error(f"Ошибка получения профиля: {e}")
            await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Ошибка при загрузке профиля")
        return
    
    # Обработка команды выбора роли
    if text_lower in ['роли', 'роль', 'roles', 'role', 'выбор роли']:
        await handle_role_selection(event)
        return
    
    # Обработка основных команд
    if any(cmd in text_lower for cmd in ['start', 'меню', 'начать', 'max', 'макс']):
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
                
                # Для команды роли показываем клавиатуру выбора
                if command in ['роли', 'roles']:
                    await handle_role_selection(event)
                else:
                    # Для других команд показываем временное сообщение и главное меню
                    await send_temporary_message(event.bot, event.message.recipient.chat_id, response_text)
                    keyboard = await get_main_menu_keyboard(event)
                    await send_main_menu(event.bot, event.message.recipient.chat_id, "Что вы хотите сделать дальше?", keyboard)
                return
            except Exception as e:
                logger.error(f"Ошибка обработки команды {command}: {e}")
                await handle_start_response(event)
                return
    
    # Если команда не распознана, показываем начальный экран
    await handle_start_response(event, "🤔 Не понял вашу команду. Нажмите кнопку для работы с MAX Мозг.")

# --- Админ-команды обработчики ---
@dp.message_created(Command('status'))
async def handle_admin_status_command(event: MessageCreated):
    """Обрабатывает команду /status для администраторов"""
    try:
        parts = event.message.body.text.split()
        if len(parts) < 2:
            await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Использование: /status <user_id>")
            return
        
        user_id = int(parts[1])
        response = await handle_admin_status(event, user_id)
        await send_temporary_message(event.bot, event.message.recipient.chat_id, response)
        
    except ValueError:
        await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Неверный формат user_id")
    except Exception as e:
        logger.error(f"Ошибка обработки команды status: {e}")
        await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Ошибка при выполнении команды")

@dp.message_created(Command('set_status'))
async def handle_set_status_command(event: MessageCreated):
    """Обрабатывает команду /set_status для администраторов"""
    try:
        parts = event.message.body.text.split()
        if len(parts) < 3:
            await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Использование: /set_status <user_id> <status>")
            return
        
        user_id = int(parts[1])
        new_status = ' '.join(parts[2:])
        response = await handle_set_status(event, user_id, new_status)
        await send_temporary_message(event.bot, event.message.recipient.chat_id, response)
        
    except ValueError:
        await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Неверный формат user_id")
    except Exception as e:
        logger.error(f"Ошибка обработки команды set_status: {e}")
        await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Ошибка при выполнении команды")

@dp.message_created(Command('approve_role'))
async def handle_approve_role_command(event: MessageCreated):
    """Обрабатывает команду подтверждения роли пользователя"""
    if event.message.sender.user_id not in ADMIN_IDS:
        await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ У вас нет прав администратора")
        return
    
    try:
        parts = event.message.body.text.split()
        if len(parts) < 2:
            await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Использование: /approve_role <user_id>")
            return
        
        user_id = int(parts[1])
        
        # Подтверждаем роль пользователя
        await db.approve_user_role(user_id, f"admin_{event.message.sender.user_id}")
        
        # Получаем информацию о пользователе для уведомления
        user_info = await db.get_user_info(user_id)
        if user_info:
            # Уведомляем пользователя
            try:
                role_display = MAX_ROLES.get(user_info.get('selected_role', 'пользователь'), 'Пользователь')
                keyboard = await get_main_menu_keyboard(event, user_info.get('selected_role'))
                await send_main_menu(
                    event.bot, 
                    user_id,
                    f"✅ Ваша роль *{role_display}* подтверждена!\n\nТеперь вам доступен полный функционал MAX Мозг.",
                    keyboard=keyboard
                )
            except Exception as e:
                logger.warning(f"Не удалось уведомить пользователя {user_id}: {e}")
        
        await send_temporary_message(
            event.bot, 
            event.message.recipient.chat_id,
            f"✅ Роль пользователя {user_id} успешно подтверждена!"
        )
        
    except ValueError:
        await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Неверный формат user_id")
    except Exception as e:
        logger.error(f"Ошибка подтверждения роли: {e}")
        await send_temporary_message(event.bot, event.message.recipient.chat_id, f"❌ Ошибка при подтверждении роли: {e}")

@dp.message_created(Command('admin'))
async def handle_admin_help(event: MessageCreated):
    """Показывает справку по админ-командам"""
    if event.message.sender.user_id in ADMIN_IDS:
        await send_temporary_message(event.bot, event.message.recipient.chat_id, ADMIN_HELP)
    else:
        await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ У вас нет прав администратора")

# --- Обработчик callback'ов для кнопок (ОБНОВЛЕН) ---
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
        await handle_role_selection(event)
        return
    
    # Обработка выбора ролей
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
            await send_temporary_message(event.bot, event.message.recipient.chat_id, "❌ Ошибка при выборе роли")
        return
    
    # Обработка смены роли
    if payload == "change_role":
        await handle_role_selection(event)
        return
    
    # Обработка поддержки (ОБНОВЛЕНО - отправка QR-кода)
    if payload == "support":
        chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
        
        # Генерируем QR-код
        qr_code = await generate_qr_code(MAX_PROFILE_URL)
        
        if qr_code:
            try:
                # Отправляем QR-код
                success = await send_qr_code(event.bot, chat_id, qr_code, "🧠 QR-код для связи с администратором\n\nОтсканируйте код чтобы перейти в мой профиль MAX")
                
                if not success:
                    # Fallback: если не удалось отправить QR-код
                    await send_temporary_message(
                        event.bot, 
                        chat_id, 
                        f"👤 Ссылка на мой профиль в MAX:\n\n{MAX_PROFILE_URL}"
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка отправки QR-кода: {e}")
                # Fallback: отправляем ссылку
                await send_temporary_message(
                    event.bot, 
                    chat_id, 
                    f"👤 Ссылка на мой профиль в MAX:\n\n{MAX_PROFILE_URL}"
                )
        else:
            # Если не удалось сгенерировать QR-код
            await send_temporary_message(
                event.bot, 
                chat_id, 
                f"👤 Ссылка на мой профиль в MAX:\n\n{MAX_PROFILE_URL}"
            )
        
        # Показываем главное меню
        keyboard = await get_main_menu_keyboard(event)
        await send_main_menu(event.bot, chat_id, "Чем еще могу помочь?", keyboard)
        return
    
    # Обработка возврата в главное меню
    if payload == "back_to_menu":
        chat_id = event.message.recipient.chat_id if hasattr(event, 'message') else event.chat_id
        keyboard = await get_main_menu_keyboard(event)
        await send_keyboard_message(event.bot, chat_id, "Главное меню MAX Мозг:", keyboard)
        return
    
    # Обработка открытия приложения (fallback)
    if payload == "open_max_app":
        web_app_url = "  https://artemfair5-design.github.io/university-assistant-bot/auth.html  "
        await send_temporary_message(event.bot, event.message.recipient.chat_id, 
                          f"🧠 Открыть MAX Мозг: {web_app_url}")
        return
    
    # Обработка ожидания подтверждения
    if payload == "pending_approval":
        user_info = await db.get_user_info(user_id)
        current_role = user_info.get('selected_role', 'гость')
        await handle_role_pending_approval(event, current_role)
        return

# --- Функции для стабильности (НОВЫЕ) ---

async def check_platform_availability():
    """Проверяет доступность хоста MAX API"""
    try:
        socket.getaddrinfo('platform-api.max.ru', 443)
        return True
    except socket.gaierror:
        logger.error("Не удается разрешить host platform-api.max.ru")
        return False

async def health_check():
    """Проверяет работоспособность сервисов"""
    while True:
        try:
            # Проверка подключения к БД
            await db.execute("SELECT 1")
            
            # Проверка доступности MAX API
            async with aiohttp.ClientSession() as session:
                async with session.get('https://platform-api.max.ru/health  ', timeout=10) as resp:
                    if resp.status != 200:
                        logger.warning("MAX API недоступен")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        await asyncio.sleep(60)  # Проверка каждую минуту

async def resilient_polling():
    """Запуск polling с повторными попытками при ошибках"""
    max_retries = 5
    retry_delay = 30  # секунд
    
    for attempt in range(max_retries):
        try:
            # Проверяем доступность API перед запуском
            if not await check_platform_availability():
                logger.error("MAX API недоступен. Пропускаем запуск polling.")
                if attempt < max_retries - 1:
                    logger.info(f"Ожидание {retry_delay} секунд перед повторной проверкой...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error("MAX API недоступен. Завершение работы.")
                    return
            
            await dp.start_polling(bot)
            return  # Успешный запуск, выходим из цикла
        except Exception as e:
            logger.error(f"Ошибка polling (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Перезапуск через {retry_delay} секунд...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Достигнут лимит перезапусков. Завершение работы.")
                raise

async def graceful_shutdown():
    """Корректное закрытие ресурсов"""
    logger.info("Запуск корректного завершения работы...")
    # Отменяем все активные задачи, кроме текущей
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    
    # Даем задачам время на завершение
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    # Закрываем соединение с базой данных
    try:
        await db.close()
        logger.info("Соединение с базой данных закрыто.")
    except Exception as e:
        logger.error(f"Ошибка при закрытии базы данных: {e}")

# --- Основная функция ---
async def main():
    # Подключаемся к базе данных
    max_retries_db = 5
    for attempt in range(max_retries_db):
        try:
            await db.connect()
            logger.info("Подключение к базе данных успешно.")
            break
        except Exception as e:
            logger.error(f"Попытка {attempt + 1}/{max_retries_db} подключения к БД не удалась: {e}")
            if attempt < max_retries_db - 1:
                wait_time = (attempt + 1) * 5
                logger.info(f"Повторная попытка через {wait_time} секунд...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Не удалось подключиться к базе данных после всех попыток. Завершение.")
                return
    
    try:
        stats = await db.get_user_stats()
        logger.info(f"Статистика MAX Мозг: {stats}")
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
    
    try:
        await bot.delete_webhook()
        logger.info("Старые вебхуки удалены")
    except Exception as e:
        logger.warning(f"Не удалось удалить вебхуки: {e}")
    
    logger.info("Запуск бота MAX Мозг с long polling...")
    await resilient_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот MAX Мозг остановлен по запросу пользователя")
    except Exception as e:
        logger.error(f"Критическая ошибка при работе бота MAX Мозг: {e}")
    finally:
        # Корректно закрываем соединения
        try:
            asyncio.run(graceful_shutdown())
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logger.warning("Event loop уже закрыт при попытке graceful_shutdown.")
            else:
                logger.error(f"Ошибка при завершении работы: {e}")