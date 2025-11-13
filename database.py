import asyncpg
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        
    async def connect(self):
        """Подключается к PostgreSQL в Docker"""
        try:
            self.pool = await asyncpg.create_pool(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5432)),
                user=os.getenv('DB_USER', 'botuser'),
                password=os.getenv('DB_PASSWORD', 'botpass'),
                database=os.getenv('DB_NAME', 'university_bot'),
                min_size=1,
                max_size=10
            )
            logger.info("Успешное подключение к PostgreSQL для MAX Мозг")
            await self.init_db()
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise

    async def init_db(self):
        """Инициализирует таблицы в базе данных"""
        async with self.pool.acquire() as conn:
            # Таблица пользователей (базовая структура)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    telegram TEXT,
                    max_username TEXT,
                    email TEXT,
                    phone TEXT,
                    registration_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    last_activity TIMESTAMP WITH TIME ZONE NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Добавляем ВСЕ недостающие колонки
            await self._add_missing_columns(conn)
            
            # Таблица отзывов
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    feedback_text TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Таблица активности (расширенная)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_activity (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    activity_type TEXT NOT NULL,
                    activity_data TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Таблица статусов пользователей
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_status_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    changed_by TEXT DEFAULT 'system',
                    reason TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Создаем индексы с обработкой ошибок
            await self._create_indexes(conn)
            
            logger.info("Таблицы базы данных MAX Мозг инициализированы")

    async def _add_missing_columns(self, conn):
        """Добавляет все недостающие колонки в таблицу users"""
        columns_to_add = [
            ('is_applicant', 'BOOLEAN'),
            ('user_status', 'TEXT DEFAULT %s' % "'student'"),
            ('last_mini_app_access', 'TIMESTAMP WITH TIME ZONE'),
            ('mini_app_access_count', 'INTEGER DEFAULT 0'),
            ('selected_role', 'TEXT'),
            # НОВЫЕ КОЛОНКИ ДЛЯ СИСТЕМЫ РОЛЕЙ
            ('role_approved', 'BOOLEAN DEFAULT FALSE'),
            ('role_change_allowed', 'BOOLEAN DEFAULT TRUE'),
            ('role_selected_at', 'TIMESTAMP WITH TIME ZONE'),
            ('admin_verified', 'BOOLEAN DEFAULT FALSE')
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(f'''
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                ''')
                logger.info(f"Колонка {column_name} добавлена или уже существует")
            except Exception as e:
                logger.warning(f"Не удалось добавить колонку {column_name}: {e}")

    async def _create_indexes(self, conn):
        """Создает индексы с обработкой ошибок"""
        indexes = [
            ('idx_users_user_id', 'users(user_id)'),
            ('idx_feedback_user_id', 'feedback(user_id)'),
            ('idx_activity_user_id', 'user_activity(user_id)'),
            ('idx_status_history_user_id', 'user_status_history(user_id)'),
            ('idx_users_selected_role', 'users(selected_role)'),
            ('idx_users_role_approved', 'users(role_approved)')
        ]
        
        # Индексы для новых колонок (могут не существовать сначала)
        optional_indexes = [
            ('idx_users_applicant', 'users(is_applicant)'),
            ('idx_users_status', 'users(user_status)')
        ]
        
        # Создаем основные индексы
        for index_name, index_def in indexes:
            try:
                await conn.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}')
                logger.info(f"Индекс {index_name} создан или уже существует")
            except Exception as e:
                logger.warning(f"Не удалось создать индекс {index_name}: {e}")
        
        # Пытаемся создать опциональные индексы (могут упасть если колонки нет)
        for index_name, index_def in optional_indexes:
            try:
                await conn.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}')
                logger.info(f"Индекс {index_name} создан или уже существует")
            except Exception as e:
                logger.warning(f"Не удалось создать индекс {index_name} (колонка может отсутствовать): {e}")

    async def save_user_data(self, user_info, message_text: str = None):
        """Сохраняет или обновляет данные пользователя"""
        current_time = datetime.now()
        
        user_id = user_info.user_id
        first_name = getattr(user_info, 'first_name', '') or ''
        last_name = getattr(user_info, 'last_name', '') or ''
        username = getattr(user_info, 'username', '') or ''
        telegram_username = f"@{username}" if username else ''
        
        async with self.pool.acquire() as conn:
            # Используем INSERT ... ON CONFLICT для атомарной вставки/обновления
            await conn.execute('''
                INSERT INTO users 
                (user_id, first_name, last_name, username, telegram, max_username, 
                 registration_date, last_activity, message_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 1)
                ON CONFLICT (user_id) 
                DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    username = EXCLUDED.username,
                    telegram = EXCLUDED.telegram,
                    max_username = EXCLUDED.max_username,
                    last_activity = EXCLUDED.last_activity,
                    message_count = users.message_count + 1,
                    updated_at = NOW()
            ''', user_id, first_name, last_name, username, telegram_username,
               username, current_time, current_time)
            
            # Анализируем сообщение если есть
            if message_text:
                await self._analyze_message_for_data(conn, user_id, message_text)
            
            # Сохраняем активность
            await conn.execute('''
                INSERT INTO user_activity (user_id, activity_type, activity_data)
                VALUES ($1, 'message', $2)
            ''', user_id, message_text)

    async def _analyze_message_for_data(self, conn, user_id: int, message_text: str):
        """Анализирует сообщение для извлечения дополнительных данных"""
        import re
        
        text_lower = message_text.lower()
        
        # Поиск email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message_text)
        if emails:
            await conn.execute(
                'UPDATE users SET email = $1, updated_at = NOW() WHERE user_id = $2',
                emails[0], user_id
            )
        
        # Поиск номера телефона
        phone_pattern = r'[\+]?[7-8]?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
        phones = re.findall(phone_pattern, message_text)
        if phones:
            await conn.execute(
                'UPDATE users SET phone = $1, updated_at = NOW() WHERE user_id = $2',
                phones[0].strip(), user_id
            )
        
        # Сохраняем отзыв
        if text_lower.startswith('отзыв:'):
            feedback_text = text_lower.replace('отзыв:', '', 1).strip()
            if feedback_text:
                await conn.execute('''
                    INSERT INTO feedback (user_id, feedback_text)
                    VALUES ($1, $2)
                ''', user_id, feedback_text)

    async def update_user_role(self, user_id: int, role_name: str, allow_change: bool = True):
        """Обновляет роль пользователя с настройками блокировки"""
        async with self.pool.acquire() as conn:
            try:
                current_time = datetime.now()
                
                # Для гостевой роли всегда разрешаем смену, для остальных - по настройке
                is_guest = role_name == 'гость'
                final_allow_change = allow_change if not is_guest else True
                
                await conn.execute('''
                    UPDATE users 
                    SET selected_role = $1, 
                        role_change_allowed = $2,
                        role_selected_at = $3,
                        role_approved = $4,
                        admin_verified = $4,
                        updated_at = NOW()
                    WHERE user_id = $5
                ''', role_name, final_allow_change, current_time, is_guest, user_id)
                
                logger.info(f"Роль пользователя {user_id} обновлена: {role_name}, смена разрешена: {final_allow_change}")
                
            except Exception as e:
                logger.error(f"Ошибка обновления роли пользователя: {e}")
                raise

    async def approve_user_role(self, user_id: int, approved_by: str = 'admin'):
        """Подтверждает роль пользователя администратором"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('''
                    UPDATE users 
                    SET role_approved = TRUE,
                        admin_verified = TRUE,
                        updated_at = NOW()
                    WHERE user_id = $1
                ''', user_id)
                
                # Логируем в историю статусов
                await conn.execute('''
                    INSERT INTO user_status_history (user_id, old_status, new_status, changed_by, reason)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, 'pending', 'approved', approved_by, 'Роль подтверждена администратором')
                
                logger.info(f"Роль пользователя {user_id} подтверждена администратором")
                
            except Exception as e:
                logger.error(f"Ошибка подтверждения роли: {e}")
                raise

    async def can_change_role(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь сменить роль"""
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchval('''
                    SELECT role_change_allowed FROM users WHERE user_id = $1
                ''', user_id)
                return bool(result) if result is not None else True
            except Exception as e:
                logger.warning(f"Ошибка проверки возможности смены роли: {e}")
                return True

    async def is_role_approved(self, user_id: int) -> bool:
        """Проверяет, подтверждена ли роль пользователя"""
        async with self.pool.acquire() as conn:
            try:
                # Для гостевой роли всегда считаем подтвержденной
                result = await conn.fetchrow('''
                    SELECT selected_role, role_approved FROM users WHERE user_id = $1
                ''', user_id)
                
                if not result:
                    return False
                    
                # Если роль гость - автоматически подтверждена
                if result['selected_role'] == 'гость':
                    return True
                    
                return bool(result['role_approved'])
            except Exception as e:
                logger.warning(f"Ошибка проверки подтверждения роли: {e}")
                return False

    async def get_user_role_info(self, user_id: int) -> Dict[str, Any]:
        """Получает полную информацию о роли пользователя"""
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow('''
                    SELECT selected_role, role_approved, role_change_allowed, 
                           role_selected_at, admin_verified, user_status
                    FROM users 
                    WHERE user_id = $1
                ''', user_id)
                
                if row:
                    return dict(row)
                return {}
            except Exception as e:
                logger.warning(f"Ошибка получения информации о роли: {e}")
                return {}

    async def log_mini_app_access(self, user_id: int, user_data: Dict[str, Any] = None):
        """Логирует доступ пользователя к мини-приложению MAX Мозг"""
        current_time = datetime.now()
        
        async with self.pool.acquire() as conn:
            try:
                # Обновляем счетчик доступа и время последнего доступа
                await conn.execute('''
                    UPDATE users 
                    SET last_mini_app_access = $1, 
                        mini_app_access_count = COALESCE(mini_app_access_count, 0) + 1,
                        updated_at = NOW()
                    WHERE user_id = $2
                ''', current_time, user_id)
                
                # Сохраняем выбранную роль если есть
                if user_data and 'selected_role' in user_data:
                    await conn.execute('''
                        UPDATE users 
                        SET selected_role = $1, updated_at = NOW()
                        WHERE user_id = $2
                    ''', user_data['selected_role'], user_id)
                
                # Логируем активность
                activity_data = json.dumps({
                    'user_data': user_data,
                    'access_type': 'max_mozg_app',
                    'platform': 'MAX Мозг'
                }) if user_data else None
                
                await conn.execute('''
                    INSERT INTO user_activity (user_id, activity_type, activity_data)
                    VALUES ($1, 'max_app_access', $2)
                ''', user_id, activity_data)
                
                logger.info(f"Логирован доступ к MAX Мозг для user_id {user_id}")
            except Exception as e:
                logger.warning(f"Не удалось залогировать доступ к MAX Мозг: {e}")

    async def update_user_status(self, user_id: int, new_status: str, changed_by: str = 'system', reason: str = None):
        """Обновляет статус пользователя и сохраняет историю изменений"""
        async with self.pool.acquire() as conn:
            try:
                # Получаем текущий статус
                old_status = await conn.fetchval(
                    'SELECT user_status FROM users WHERE user_id = $1', user_id
                )
                
                # Обновляем статус
                await conn.execute('''
                    UPDATE users 
                    SET user_status = $1, updated_at = NOW()
                    WHERE user_id = $2
                ''', new_status, user_id)
                
                # Сохраняем в историю
                await conn.execute('''
                    INSERT INTO user_status_history (user_id, old_status, new_status, changed_by, reason)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, old_status, new_status, changed_by, reason)
                
                # Логируем активность
                activity_data = json.dumps({
                    'old_status': old_status,
                    'new_status': new_status,
                    'changed_by': changed_by,
                    'reason': reason,
                    'platform': 'MAX Мозг'
                })
                
                await conn.execute('''
                    INSERT INTO user_activity (user_id, activity_type, activity_data)
                    VALUES ($1, 'status_change', $2)
                ''', user_id, activity_data)
                
                logger.info(f"Статус пользователя {user_id} изменен в MAX Мозг: {old_status} -> {new_status}")
            except Exception as e:
                logger.warning(f"Не удалось обновить статус пользователя: {e}")

    async def update_user_applicant_status(self, user_id: int, is_applicant: bool):
        """Обновляет статус абитуриента пользователя"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    'UPDATE users SET is_applicant = $1, updated_at = NOW() WHERE user_id = $2',
                    is_applicant, user_id
                )
                logger.info(f"Статус абитуриента обновлен для user_id {user_id}: {is_applicant}")
            except Exception as e:
                logger.warning(f"Не удалось обновить статус абитуриента: {e}")

    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о пользователе"""
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow('''
                    SELECT user_id, first_name, last_name, username, user_status, 
                           is_applicant, selected_role, mini_app_access_count, 
                           last_mini_app_access, registration_date, message_count,
                           role_approved, role_change_allowed, admin_verified
                    FROM users 
                    WHERE user_id = $1
                ''', user_id)
                
                if row:
                    return dict(row)
                return None
            except Exception as e:
                logger.warning(f"Не удалось получить информацию о пользователе {user_id}: {e}")
                return None

    async def get_user_stats(self) -> Dict[str, Any]:
        """Получает общую статистику для MAX Мозг"""
        async with self.pool.acquire() as conn:
            try:
                total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
                total_feedback = await conn.fetchval('SELECT COUNT(*) FROM feedback')
                total_messages = await conn.fetchval('SELECT COALESCE(SUM(message_count), 0) FROM users')
                
                # Пытаемся получить дополнительные статистики
                applicant_users = 0
                mini_app_users = 0
                approved_users = 0
                status_stats = {}
                role_stats = {}
                
                try:
                    applicant_users = await conn.fetchval('SELECT COUNT(*) FROM users WHERE is_applicant = TRUE')
                except Exception:
                    pass
                
                try:
                    mini_app_users = await conn.fetchval('SELECT COUNT(*) FROM users WHERE mini_app_access_count > 0')
                except Exception:
                    pass
                
                try:
                    approved_users = await conn.fetchval('SELECT COUNT(*) FROM users WHERE role_approved = TRUE')
                except Exception:
                    pass
                
                try:
                    status_stats_rows = await conn.fetch('''
                        SELECT user_status, COUNT(*) as count 
                        FROM users 
                        WHERE user_status IS NOT NULL 
                        GROUP BY user_status
                    ''')
                    status_stats = {row['user_status']: row['count'] for row in status_stats_rows}
                except Exception:
                    pass
                
                try:
                    role_stats_rows = await conn.fetch('''
                        SELECT selected_role, COUNT(*) as count 
                        FROM users 
                        WHERE selected_role IS NOT NULL 
                        GROUP BY selected_role
                    ''')
                    role_stats = {row['selected_role']: row['count'] for row in role_stats_rows}
                except Exception:
                    pass
                
                # Активные пользователи за последние 7 дней
                active_users = await conn.fetchval('''
                    SELECT COUNT(DISTINCT user_id) FROM user_activity 
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                ''')
                
                return {
                    'total_users': total_users,
                    'total_feedback': total_feedback,
                    'total_messages': total_messages,
                    'active_users_7d': active_users,
                    'applicant_users': applicant_users,
                    'mini_app_users': mini_app_users,
                    'approved_users': approved_users,
                    'status_stats': status_stats,
                    'role_stats': role_stats
                }
            except Exception as e:
                logger.error(f"Ошибка получения статистики MAX Мозг: {e}")
                return {
                    'total_users': 0,
                    'total_feedback': 0,
                    'total_messages': 0,
                    'active_users_7d': 0,
                    'applicant_users': 0,
                    'mini_app_users': 0,
                    'approved_users': 0,
                    'status_stats': {},
                    'role_stats': {}
                }

    async def close(self):
        """Закрывает соединение с базой данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Соединение с PostgreSQL для MAX Мозг закрыто")

# Глобальный экземпляр базы данных
db = Database()