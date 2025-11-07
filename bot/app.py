from flask import Flask, request, jsonify, render_template
import requests
import json
import os

app = Flask(__name__)

# Конфигурация MAX
MAX_TOKEN = "f9LHodD0cOJBJLYDixtV3RsHw4y35JeYVSFSTTalbyYsr6QB1T06ejZ0S_-Z2Ctnhvze3dV9OgzBzOzltVr6"
MAX_API_URL = "https://api.max.ru"

class MaxBot:
    def __init__(self, token, api_url):
        self.token = token
        self.api_url = api_url
    
    def send_message(self, user_id, text, keyboard=None):
        """Отправка сообщения пользователю"""
        url = f"{self.api_url}/v1/messages.send"
        payload = {
            "access_token": self.token,
            "user_id": user_id,
            "message": text
        }
        if keyboard:
            payload["keyboard"] = keyboard
        
        try:
            response = requests.post(url, json=payload)
            return response.json()
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            return None
    
    def get_main_menu(self):
        """Главное меню бота"""
        return {
            "inline": False,
            "buttons": [
                [
                    {
                        "text": "📅 Расписание",
                        "color": "primary"
                    },
                    {
                        "text": "📝 Проекты", 
                        "color": "primary"
                    }
                ],
                [
                    {
                        "text": "🎓 Деканат",
                        "color": "secondary"
                    },
                    {
                        "text": "📚 Библиотека",
                        "color": "secondary"
                    }
                ],
                [
                    {
                        "text": "🎭 Мероприятия",
                        "color": "positive"
                    },
                    {
                        "text": "ℹ️ Помощь",
                        "color": "negative"
                    }
                ]
            ]
        }

# Создаем экземпляр бота
bot = MaxBot(MAX_TOKEN, MAX_API_URL)

@app.route('/')
def index():
    return "Чат-бот Универ-Ассистент работает!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхука от MAX"""
    data = request.json
    
    if data['type'] == 'message_new':
        user_id = data['object']['message']['from_id']
        text = data['object']['message']['text'].lower()
        
        # Обработка команд
        if text in ['start', 'начать', 'меню']:
            welcome_text = """🎓 Добро пожаловать в Универ-Ассистент MAX!

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

🚀 *1. Разработка мобильного приложения*
   - Требуются: 2 backend, 1 frontend, 1 дизайнер
   - Дедлайн: 2 месяца
   - Куратор: проф. Иванов

🔬 *2. Исследование AI в образовании*
   - Требуются: аналитики, исследователи
   - Дедлайн: 3 месяца  
   - Куратор: доц. Петрова

📊 *3. Анализ больших данных*
   - Требуются: data scientist, Python разработчики
   - Дедлайн: 4 месяца
   - Куратор: проф. Сидоров

📱 Чтобы присоединиться к проекту, откройте мини-приложение:"""
            
            # Клавиатура с кнопкой мини-приложения
            projects_keyboard = {
                "inline": False,
                "buttons": [
                    [
                        {
                            "text": "📱 Открыть проекты",
                            "color": "primary",
                            "app_id": 1
                        }
                    ],
                    [
                        {
                            "text": "📅 Расписание",
                            "color": "secondary"
                        },
                        {
                            "text": "🎓 Деканат", 
                            "color": "secondary"
                        }
                    ]
                ]
            }
            bot.send_message(user_id, projects_text, projects_keyboard)
            
        elif 'деканат' in text:
            deanery_text = """🎓 *Сервисы деканата:*

• 📄 Заказать справку об обучении
• 📝 Заявление на академический отпуск
• 🔄 Вопрос по переводу 
• 💰 Оплата обучения
• 📞 Контакты деканата

📱 Для оформления документов откройте мини-приложение:"""
            
            deanery_keyboard = {
                "inline": False,
                "buttons": [
                    [
                        {
                            "text": "📱 Документы деканата",
                            "color": "primary", 
                            "app_id": 1
                        }
                    ],
                    [
                        {
                            "text": "📅 Расписание",
                            "color": "secondary"
                        },
                        {
                            "text": "📝 Проекты",
                            "color": "secondary"
                        }
                    ]
                ]
            }
            bot.send_message(user_id, deanery_text, deanery_keyboard)
            
        elif 'библиотека' in text:
            library_text = """📚 *Электронная библиотека:*

• 🔍 Поиск литературы
• 📖 Электронные учебники
• 📚 Заказ книг
• ⏱ Продление срока

Доступно в мини-приложении:"""
            
            library_keyboard = {
                "inline": False,
                "buttons": [
                    [
                        {
                            "text": "📱 Открыть библиотеку",
                            "color": "primary",
                            "app_id": 1
                        }
                    ],
                    [
                        {
                            "text": "📅 Расписание", 
                            "color": "secondary"
                        },
                        {
                            "text": "🎭 Мероприятия",
                            "color": "secondary"
                        }
                    ]
                ]
            }
            bot.send_message(user_id, library_text, library_keyboard)
            
        elif 'мероприятия' in text or 'события' in text:
            events_text = """🎭 *Ближайшие мероприятия:*

*25.10* - День открытых дверей (18:00, актовый зал)
*27.10* - Хакатон по веб-разработке (10:00, ауд. 500)
*29.10* - Встреча с IT-компаниями (16:00, конференц-зал)
*01.11* - Научный семинар по AI (14:00, ауд. 320)

📱 Для регистрации откройте мини-приложение:"""
            
            events_keyboard = {
                "inline": False,
                "buttons": [
                    [
                        {
                            "text": "📱 Календарь мероприятий", 
                            "color": "primary",
                            "app_id": 1
                        }
                    ],
                    [
                        {
                            "text": "📅 Расписание",
                            "color": "secondary"
                        },
                        {
                            "text": "📝 Проекты",
                            "color": "secondary" 
                        }
                    ]
                ]
            }
            bot.send_message(user_id, events_text, events_keyboard)
            
        elif 'помощь' in text:
            help_text = """ℹ️ *Помощь по боту Универ-Ассистент*

*Основные разделы:*
📅 *Расписание* - актуальное расписание занятий
📝 *Проекты* - проектная деятельность и исследовательская работа
🎓 *Деканат* - справки, документы, академические вопросы
📚 *Библиотека* - электронные ресурсы и заказ книг
🎭 *Мероприятия* - события и внеучебная деятельность

*Техническая поддержка:*
📧 Email: support@university.ru
📞 Телефон: +7 (495) 123-45-67
🕒 Время работы: 9:00-18:00"""
            bot.send_message(user_id, help_text, bot.get_main_menu())
            
        else:
            # Ответ на неизвестную команду
            unknown_text = "🤔 Не понял вашу команду. Используйте кнопки меню или напишите 'помощь'."
            bot.send_message(user_id, unknown_text, bot.get_main_menu())
    
    return jsonify({'status': 'ok'})

# Мини-приложение
@app.route('/app')
def mini_app():
    return render_template('app.html')

@app.route('/api/schedule')
def api_schedule():
    """API для получения расписания"""
    schedule = {
        "today": [
            {"time": "09:00-10:30", "subject": "Математический анализ", "room": "310"},
            {"time": "11:00-12:30", "subject": "Программирование", "room": "415"},
            {"time": "14:00-15:30", "subject": "Иностранный язык", "room": "201"}
        ],
        "tomorrow": [
            {"time": "10:00-11:30", "subject": "Физика", "room": "305"},
            {"time": "12:00-13:30", "subject": "Веб-разработка", "room": "420"}
        ]
    }
    return jsonify(schedule)

@app.route('/api/projects')
def api_projects():
    """API для получения проектов"""
    projects = [
        {
            "id": 1,
            "title": "Разработка мобильного приложения",
            "needs": "2 backend, 1 frontend, 1 дизайнер",
            "deadline": "2 месяца",
            "curator": "проф. Иванов"
        },
        {
            "id": 2, 
            "title": "Исследование AI в образовании",
            "needs": "аналитики, исследователи",
            "deadline": "3 месяца",
            "curator": "доц. Петрова"
        }
    ]
    return jsonify(projects)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)