# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости для PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем non-root пользователя
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Открываем порт
EXPOSE 5000

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Команда запуска
CMD ["python", "async_bot.py"]