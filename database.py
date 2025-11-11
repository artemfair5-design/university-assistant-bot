# database.py
import asyncpg
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

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
            logger.info("Успешное подключение к PostgreSQL")
            await self.init_db()
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise

    async def init_db(self):
        """Инициализирует таблицы в базе данных"""
        async with self.pool.acquire() as conn:
            # Таблица пользователей
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
            
            # Таблица отзывов
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    feedback_text TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Таблица активности
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_activity (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    activity_type TEXT NOT NULL,
                    activity_data TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Индексы для производительности
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_activity_user_id ON user_activity(user_id)')
            
            logger.info("Таблицы базы данных инициализированы")

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

    async def get_user_stats(self) -> Dict[str, Any]:
        """Получает общую статистику"""
        async with self.pool.acquire() as conn:
            total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
            total_feedback = await conn.fetchval('SELECT COUNT(*) FROM feedback')
            total_messages = await conn.fetchval('SELECT COALESCE(SUM(message_count), 0) FROM users')
            
            # Активные пользователи за последние 7 дней
            active_users = await conn.fetchval('''
                SELECT COUNT(DISTINCT user_id) FROM user_activity 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            ''')
            
            return {
                'total_users': total_users,
                'total_feedback': total_feedback,
                'total_messages': total_messages,
                'active_users_7d': active_users
            }

    async def close(self):
        """Закрывает соединение с базой данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Соединение с PostgreSQL закрыто")

# Глобальный экземпляр базы данных
db = Database()