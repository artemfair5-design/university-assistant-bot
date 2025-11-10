#!/bin/bash

# Скрипт развертывания бота с Docker Compose

set -e

echo "🚀 Запуск развертывания Универ-Ассистент..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Создайте его из .env.example"
    exit 1
fi

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose down

# Собираем и запускаем новые контейнеры
echo "🔨 Собираем и запускаем контейнеры..."
docker-compose up -d --build

# Проверяем здоровье сервисов
echo "🏥 Проверяем здоровье сервисов..."
sleep 10
docker-compose ps

# Проверяем что бот отвечает
echo "🔍 Проверяем работу бота..."
curl -f http://localhost:5000/health || {
    echo "❌ Бот не отвечает"
    docker-compose logs university-bot
    exit 1
}

echo "✅ Развертывание завершено успешно!"
echo "🌐 Бот доступен по: http://localhost:5000"
echo "📝 Логи: docker-compose logs -f university-bot"