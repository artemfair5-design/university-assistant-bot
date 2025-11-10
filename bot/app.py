import os
import logging
import json
import requests  # <--- ОШИБКА 1: Не хватало этого импорта для bot.send_message
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
PORT = int(os.getenv('PORT', 5000))
LOCAL_MODE = os.getenv('LOCAL_MODE', 'true').lower() == 'true'

app = Flask(__name__)

class MaxBot: # <--- ОШИБКА 2: Класс называется MaxBot, а не LocalBot
    def __init__(self, token, api_url):
        self.token = token
        self.api_url = api_url
        self.logger = logging.getLogger(self.__class__.__name__)
        # <--- ОШИБКА 3: Не хватало инициализации списка responses
        self.responses = [] 

    def send_message(self, user_id, text, keyboard=None):
        """Отправка сообщения пользователю через MAX API"""
        url = f"{self.api_url}/v1/messages.send"
        payload = {
            "access_token": self.token,
            "user_id": user_id,
            "message": text
        }
        if keyboard:
            payload["keyboard"] = keyboard

        try:
            self.logger.info(f"Пытаюсь отправить сообщение пользователю {user_id}. Текст: '{text[:50]}...'")
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            # self.logger.info(f"Сообщение пользователю {user_id} отправлено успешно.")
            
            # <--- ДОБАВЛЕНО: Сохраняем сообщение в историю (для демонстрации)
            self.responses.append({
                "user_id": user_id,
                "text": text,
                "keyboard": keyboard,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP ошибка при отправке сообщения пользователю {user_id}: {e}")
            self.logger.error(f"Тело ответа: {response.text}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка запроса при отправке сообщения пользователю {user_id}: {e}")
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при отправке сообщения пользователю {user_id}: {e}")
        return None

    def get_main_menu(self):
        """Главное меню бота с кнопкой 'Открыть приложение'"""
        return {
            "inline": False,
            "buttons": [
                [
                    {"text": "📅 Расписание", "color": "primary"},
                    {"text": "📝 Проекты", "color": "primary"}
                ],
                [
                    {"text": "🎓 Деканат", "color": "secondary"},
                    {"text": "📚 Библиотека", "color": "secondary"}
                ],
                [
                    {"text": "🎭 Мероприятия", "color": "positive"},
                    {"text": "ℹ️ Помощь", "color": "negative"}
                ],
                [
                    # <--- ИСПРАВЛЕНО: Убран лишний пробел в URL
                    {"text": "📱 Открыть приложение", "color": "primary", "url": "https://artemfair5-design.github.io/university-assistant-bot/"}
                ]
            ]
        }
    
    def get_projects_keyboard(self):
        """Клавиатура для раздела проектов"""
        return {
            "inline": False,
            "buttons": [
                [
                    {"text": "📱 Открыть мини-приложение", "color": "primary", "url": "https://artemfair5-design.github.io/university-assistant-bot/"}
                ],
                [
                    {"text": "📅 Расписание", "color": "secondary"},
                    {"text": "🎓 Деканат", "color": "secondary"}
                ]
            ]
        }
    
    def get_deanery_keyboard(self):
        """Клавиатура для раздела деканата"""
        return {
            "inline": False,
            "buttons": [
                [
                    {"text": "📱 Документы деканата", "color": "primary", "url": "https://artemfair5-design.github.io/university-assistant-bot/"}
                ],
                [
                    {"text": "📅 Расписание", "color": "secondary"},
                    {"text": "📝 Проекты", "color": "secondary"}
                ]
            ]
        }
    
    def get_last_responses(self, count=5):
        """Получить последние ответы"""
        # <--- ИСПРАВЛЕНО: Срез должен быть с конца списка
        return self.responses[-count:] if len(self.responses) >= count else self.responses
    
    def clear_responses(self):
        """Очистить историю ответов"""
        self.responses.clear()
        return {"status": "cleared", "message": "История ответов очищена"}

# --- ИСПРАВЛЕНО: Создаем экземпляр MaxBot, а не LocalBot ---
# Токен и URL для локального режима можно не указывать, если используется фиктивный бот
# или можно использовать фиктивные значения, если MAX_API_URL не используется в send_message в этом режиме
# или если используется фиктивная реализация send_message
MAX_TOKEN = os.getenv('MAX_TOKEN', 'dummy_token_for_local') 
MAX_API_URL = os.getenv('MAX_API_URL', 'https://api.max.ru')
bot = MaxBot(MAX_TOKEN, MAX_API_URL)

# Демо-данные
DEMO_DATA = {
    "schedule": {
        "today": [
            {"time": "09:00-10:30", "subject": "Математический анализ", "room": "310", "teacher": "проф. Иванов"},
            {"time": "11:00-12:30", "subject": "Программирование", "room": "415", "teacher": "доц. Петрова"},
            {"time": "14:00-15:30", "subject": "Иностранный язык", "room": "201", "teacher": "ст. преп. Сидорова"}
        ],
        "tomorrow": [
            {"time": "10:00-11:30", "subject": "Физика", "room": "305", "teacher": "проф. Козлов"},
            {"time": "12:00-13:30", "subject": "Веб-разработка", "room": "420", "teacher": "доц. Николаев"}
        ]
    },
    "projects": [
        {
            "id": 1,
            "title": "Разработка мобильного приложения",
            "description": "Создание кроссплатформенного мобильного приложения для университета",
            "needs": "2 backend, 1 frontend, 1 дизайнер",
            "deadline": "2 месяца",
            "curator": "проф. Иванов",
            "status": "active",
            "participants": 3
        },
        {
            "id": 2,
            "title": "Исследование AI в образовании",
            "description": "Анализ применения искусственного интеллекта в образовательном процессе",
            "needs": "аналитики, исследователи",
            "deadline": "3 месяца",
            "curator": "доц. Петрова",
            "status": "active",
            "participants": 5
        }
    ],
    "events": [
        {
            "id": 1,
            "title": "День открытых дверей",
            "date": "2024-01-25",
            "time": "18:00",
            "location": "актовый зал",
            "description": "Знакомство с университетом для абитуриентов"
        }
    ]
}

# Маршруты Flask
@app.route('/')
def home():
    """Главная страница бота"""
    return jsonify({
        "status": "running",
        "service": "University Assistant Bot (Local Mode)",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "local_mode": LOCAL_MODE,
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook",
            "api_schedule": "/api/schedule",
            "api_projects": "/api/projects",
            "responses": "/responses",
            "test": "/test",
            "demo": "/demo"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "local_mode": LOCAL_MODE
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхука - локальная эмуляция"""
    try:
        data = request.json
        logger.info(f"📨 Получен вебхук: {json.dumps(data, ensure_ascii=False)}")
        
        if data and data.get('type') == 'message_new':
            user_id = data['object']['message']['from_id']
            text = data['object']['message']['text'].lower()
            
            # Обработка команд
            if text in ['start', 'начать', 'меню']:
                welcome_text = """🎓 Добро пожаловать в Универ-Ассистент (Локальный режим)!

Я помогу вам с учебой и студенческой жизнью. Выберите нужный раздел:"""
                bot.send_message(user_id, welcome_text, bot.get_main_menu())
                
            elif 'расписание' in text:
                schedule_text = """📅 *Расписание на сегодня:*

*09:00-10:30* - Математический анализ (ауд. 310)
*11:00-12:30* - Программирование (ауд. 415) 
*14:00-15:30* - Иностранный язык (ауд. 201)

💡 *Завтра:*
*10:00-11:30* - Физика (ауд. 305)
*12:00-13:30* - Веб-разработка (ауд. 420)"""
                bot.send_message(user_id, schedule_text, bot.get_main_menu())
                
            elif 'проект' in text:
                projects_text = """📝 *Доступные проекты:*

🚀 *Разработка мобильного приложения*
🔬 *Исследование AI в образовании*  
📊 *Анализ больших данных*

📱 Подробности и регистрация в нашем мини-приложении:"""
                bot.send_message(user_id, projects_text, bot.get_projects_keyboard())
                
            elif 'деканат' in text:
                deanery_text = """🎓 *Сервисы деканата:*

• 📄 Заказать справку об обучении
• 📝 Заявление на академический отпуск
• 🔄 Вопрос по переводу 
• 💰 Оплата обучения
• 📞 Контакты деканата

📱 Для оформления документов откройте мини-приложение:"""
                bot.send_message(user_id, deanery_text, bot.get_deanery_keyboard())
                
            elif 'библиотека' in text:
                library_text = """📚 *Электронная библиотека:*

• 🔍 Поиск литературы
• 📖 Электронные учебники
• 📚 Заказ книг
• ⏱ Продление срока

📱 Доступно в мини-приложении:"""
                bot.send_message(user_id, library_text, bot.get_projects_keyboard())
                
            elif 'мероприятия' in text or 'события' in text:
                events_text = """🎭 *Ближайшие мероприятия:*

*25.01* - День открытых дверей (18:00, актовый зал)
*27.01* - Хакатон по веб-разработке (10:00, ауд. 500)
*29.01* - Встреча с IT-компаниями (16:00, конференц-зал)

📱 Для регистрации откройте мини-приложение:"""
                bot.send_message(user_id, events_text, bot.get_projects_keyboard())
                
            elif 'помощь' in text:
                help_text = """ℹ️ *Помощь по боту Универ-Ассистент*

*Основные разделы:*
📅 *Расписание* - актуальное расписание занятий
📝 *Проекты* - проектная деятельность и исследовательская работа
🎓 *Деканат* - справки, документы, академические вопросы
📚 *Библиотека* - электронные ресурсы и заказ книг
🎭 *Мероприятия* - события и внеучебная деятельность

*Режим работы:* 🔧 Локальный (эмуляция)
*Мини-приложение:* https://artemfair5-design.github.io/university-assistant-bot/""" # <--- ИСПРАВЛЕНО: URL
                bot.send_message(user_id, help_text, bot.get_main_menu())
                
            else:
                unknown_text = """🤔 Не понял вашу команду. 

Используйте кнопки меню или напишите *помощь* для получения списка команд.

*Доступные команды:*
• расписание
• проекты
• деканат  
• библиотека
• мероприятия
• помощь"""
                bot.send_message(user_id, unknown_text, bot.get_main_menu())
        
        return jsonify({
            'status': 'ok',
            'message': 'Сообщение обработано в локальном режиме',
            'local_mode': True,
            'responses_count': len(bot.responses)
        })
    
    except Exception as e:
        logger.error(f"Ошибка в вебхуке: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/responses')
def get_responses():
    """Получить историю ответов бота"""
    count = request.args.get('count', 10, type=int)
    responses = bot.get_last_responses(count)
    
    return jsonify({
        "total_responses": len(bot.responses),
        "last_responses": responses,
        "local_mode": LOCAL_MODE
    })

@app.route('/responses/clear', methods=['POST'])
def clear_responses():
    """Очистить историю ответов"""
    result = bot.clear_responses()
    return jsonify(result)

@app.route('/test')
def test_interface():
    """Тестовый интерфейс для проверки бота"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Тест бота - Локальный режим</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .test-case { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
            button { margin: 5px; padding: 10px; }
            .response { background: #f5f5f5; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 Тестирование бота (Локальный режим)</h1>
            
            <div class="test-case">
                <h3>Тестовые команды:</h3>
                <button onclick="sendTest('start')">start</button>
                <button onclick="sendTest('расписание')">расписание</button>
                <button onclick="sendTest('проекты')">проекты</button>
                <button onclick="sendTest('деканат')">деканат</button>
                <button onclick="sendTest('помощь')">помощь</button>
                <button onclick="sendTest('test')">неизвестная команда</button>
            </div>
            
            <div class="test-case">
                <h3>История ответов:</h3>
                <button onclick="loadResponses()">Обновить историю</button>
                <button onclick="clearResponses()">Очистить историю</button>
                <div id="responses"></div>
            </div>
            
            <div id="result"></div>
        </div>

        <script>
            async function sendTest(command) {
                const testData = {
                    type: 'message_new',
                    object: {
                        message: {
                            from_id: Math.floor(Math.random() * 10000),
                            text: command,
                            id: Date.now()
                        }
                    }
                };

                try {
                    const response = await fetch('/webhook', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(testData)
                    });
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<div class="response"><strong>Результат:</strong> ${JSON.stringify(result)}</div>`;
                    
                    // Автоматически обновляем историю
                    loadResponses();
                } catch (err) {
                    document.getElementById('result').innerHTML = 
                        `<div class="response" style="color: red;">Ошибка: ${err}</div>`;
                }
            }

            async function loadResponses() {
                try {
                    const response = await fetch('/responses?count=10');
                    const data = await response.json();
                    
                    let html = `<p><strong>Всего ответов:</strong> ${data.total_responses}</p>`;
                    data.last_responses.forEach((resp, index) => {
                        html += `<div class="response">
                            <strong>#${index + 1}</strong> | User: ${resp.user_id} | ${resp.timestamp}<br>
                            <strong>Текст:</strong> ${resp.text.substring(0, 200)}...<br>
                            ${resp.keyboard ? `<strong>Клавиатура:</strong> ${JSON.stringify(resp.keyboard)}` : ''}
                        </div>`;
                    });
                    
                    document.getElementById('responses').innerHTML = html;
                } catch (err) {
                    document.getElementById('responses').innerHTML = `Ошибка загрузки: ${err}`;
                }
            }

            async function clearResponses() {
                try {
                    await fetch('/responses/clear', {method: 'POST'});
                    loadResponses();
                } catch (err) {
                    alert('Ошибка очистки: ' + err);
                }
            }

            // Загружаем историю при старте
            loadResponses();
        </script>
    </body>
    </html>
    """

# API endpoints для мини-приложения
@app.route('/api/schedule')
def api_schedule():
    return jsonify(DEMO_DATA["schedule"])

@app.route('/api/projects')
def api_projects():
    return jsonify(DEMO_DATA["projects"])

@app.route('/api/events')
def api_events():
    return jsonify(DEMO_DATA["events"])

@app.route('/demo')
def demo_page():
    """Демо-страница"""
    return """
    <h1>🎓 Универ-Ассистент - Локальный режим</h1>
    <p>Бот работает в режиме локальной эмуляции</p>
    <p><a href="/test">🧪 Тестовый интерфейс</a></p>
    <p><a href="/responses">📨 История ответов</a></p>
    """

if __name__ == '__main__':
    logger.info(f"🚀 Запуск бота в ЛОКАЛЬНОМ режиме на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)