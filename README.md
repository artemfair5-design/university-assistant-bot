# Универ-Ассистент MAX

Этот репозиторий содержит **асинхронного чат-бота** для мессенджера MAX и **мини-приложение**, разработанные в рамках хакатона. Бот автоматически собирает данные о пользователях и предоставляет доступ к мини-приложению через кнопку.

## 📁 Структура проекта

university-assistant-bot/
├── .env
├── README.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── database.py
├── async_bot.py
├── user_data.json
└── docs/
    ├── auth.html
    ├── dashboard.html
    ├── index.html
    ├── background.jpg
    ├── styles/
    │   ├── background.css
    │   ├── auth.css
    │   ├── dashboard.css
    │   ├── menu.css
    │   └── components/
    │       ├── search-bar.css
    │       └── menu-buttons.css
    └── scripts/
        ├── auth.js
        ├── menu.js
        └── components/
            ├── search-bar.js
            └── menu-buttons.js


## 🚀 Быстрый старт (Docker)

### Требования

*   Установленный [Docker](https://www.docker.com/products/docker-desktop/)
*   Установленный [Git](https://git-scm.com/downloads)

### Установка и запуск

1.  **Клонируйте репозиторий:**

    
    git clone https://github.com/artemfair5-design/ university-assistant-bot.git
    cd university-assistant-bot
    

2.  **Настройте переменные окружения:**
    *   Создайте файл `.env` в корне репозитория.
    *   Добавьте токен бота:
        
        MAX_TOKEN=f9LHodD0cOJBJLYDixtV3RsHw4y35JeYVSFSTTalbyYsr6QB1T06ejZ0S_-Z2Ctnhvze3dV9OgzBzOzltVr6
        

3.  **Соберите Docker-образ:**

    
    docker build -t univers-assistant-max .
    
    Эта команда читает инструкции из файла `Dockerfile` и создаёт образ с именем `univers-assistant-max`.

4.  **Запустите контейнер:**

    *   Если вы **используете** `.env` файл, передайте его в контейнер:
        
        docker run -d --env-file .env --name univers-assistant-max-container univers-assistant-max
        
        > Эта команда запускает контейнер в фоновом режиме (`-d`), присваивает ему имя (`--name`), передаёт переменные из `.env`  и использует созданный образ (`univers-assistant-max`).

5.  **Проверьте запуск:**

    *   Посмотрите список запущенных контейнеров:
        
        docker ps
        
        Вы должны увидеть `univers-assistant-max-container`.
    *   Посмотрите логи контейнера:
        
        docker logs univers-assistant-max-container
        
        Вы должны увидеть логи запуска бота (например, `INFO - Запуск бота с long polling...`).

Теперь бот **работает внутри Docker-контейнера**. Он будет получать сообщения от MAX.

## 💻 Локальный запуск (без Docker)

> **Примечание:** Этот способ требует установки Python и зависимостей на вашей локальной машине.

### Требования

*   Python 3.11 или выше
*   Установленный [Git](https://git-scm.com/downloads)

### Установка и запуск

1.  **Клонируйте репозиторий:**

    
    git clone https://github.com/artemfair5-design/university-assistant-bot.git
    cd university-assistant-bot
    

2.  **Перейдите в папку бота:**

    
    cd bot
    

3.  **(Рекомендуется) Создайте виртуальное окружение:**

    python -m venv venv
    
4.  **Установите зависимости:**

    pip install -r requirements.txt
    

5.  **Настройте переменные окружения :**
    *   Создайте файл `.env` в папке `bot/` (`university-assistant-bot/bot/.env`).
    *   Добавьте токен бота:
        
        MAX_TOKEN=f9LHodD0cOJBJLYDixtV3RsHw4y35JeYVSFSTTalbyYsr6QB1T06ejZ0S_-Z2Ctnhvze3dV9OgzBzOzltVr6

6.  **Запустите бота:**

    
    python async_bot.py
    

    Бот запустится и начнёт слушать обновления через `long polling`. Вы увидите логи в терминале.

## 📦 Docker-образ

Docker-образ собирается с использованием инструкций, содержащихся в файле `Dockerfile` в корне репозитория. Он устанавливает Python, зависимости из `requirements.txt` и запускает `async_bot.py`.

## 📋 `requirements.txt`

Файл `requirements.txt` (в корне репозитория и/или в папке `bot/`) содержит список всех Python-библиотек, необходимых для запуска бота, с указанием версий.
