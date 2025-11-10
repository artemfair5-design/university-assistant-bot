FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY bot/requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY bot/ .
COPY web-app/ ./web-app/

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
CMD ["python", "app.py"]