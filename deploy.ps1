# Скрипт развертывания для Windows

Write-Host "🚀 Запуск развертывания Универ-Ассистент..." -ForegroundColor Green

# Проверяем .env файл
if (-not (Test-Path .env)) {
    Write-Host "❌ Файл .env не найден. Создайте его из .env.example" -ForegroundColor Red
    exit 1
}

Write-Host "🛑 Останавливаем существующие контейнеры..." -ForegroundColor Yellow
docker-compose down

Write-Host "🔨 Собираем и запускаем контейнеры..." -ForegroundColor Yellow
docker-compose up -d --build

Write-Host "⏳ Ждем запуска сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "📊 Статус сервисов:" -ForegroundColor Cyan
docker-compose ps

Write-Host "🔍 Проверяем работу бота..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/health" -TimeoutSec 10
    Write-Host "✅ Бот работает: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Бот не отвечает: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "📝 Логи:" -ForegroundColor Yellow
    docker-compose logs university-bot
    exit 1
}

Write-Host "✅ Развертывание завершено успешно!" -ForegroundColor Green
Write-Host "🌐 Бот доступен по: http://localhost:5000" -ForegroundColor Cyan
Write-Host "📝 Логи: docker-compose logs -f university-bot" -ForegroundColor Yellow