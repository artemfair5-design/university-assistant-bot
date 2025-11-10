#!/usr/bin/env python3
"""
Скрипт управления Docker Compose развертыванием
"""

import os
import subprocess
import sys

def run_command(command):
    """Выполняет команду в shell"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)

def deploy():
    """Развертывание приложения"""
    print("🚀 Запуск развертывания...")
    run_command("docker-compose down")
    run_command("docker-compose up -d --build")
    print("✅ Развертывание завершено")

def logs():
    """Просмотр логов"""
    print("📝 Просмотр логов...")
    run_command("docker-compose logs -f university-bot")

def status():
    """Статус сервисов"""
    print("📊 Статус сервисов...")
    run_command("docker-compose ps")

def stop():
    """Остановка сервисов"""
    print("🛑 Остановка сервисов...")
    run_command("docker-compose down")

def restart():
    """Перезапуск сервисов"""
    print("🔄 Перезапуск сервисов...")
    run_command("docker-compose restart")

def update():
    """Обновление из Git и перезапуск"""
    print("📥 Обновление кода...")
    run_command("git pull")
    deploy()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python manage.py [deploy|logs|status|stop|restart|update]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "deploy":
        deploy()
    elif command == "logs":
        logs()
    elif command == "status":
        status()
    elif command == "stop":
        stop()
    elif command == "restart":
        restart()
    elif command == "update":
        update()
    else:
        print(f"❌ Неизвестная команда: {command}")