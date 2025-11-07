// Конфигурация
const CONFIG = {
    API_BASE_URL: 'https://your-bot-name.onrender.com', // Замените на ваш Render URL
    GITHUB_PAGES_URL: 'https://artemfair5-design.github.io/university-assistant-bot'
};

// State приложения
let state = {
    currentUser: 'Иван Иванов',
    currentTab: 'schedule',
    scheduleData: {},
    projectsData: []
};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

function initApp() {
    // Установка имени пользователя
    document.getElementById('userName').textContent = state.currentUser;
    
    // Инициализация табов
    initTabs();
    
    // Загрузка данных
    loadSchedule();
    loadProjects();
    
    // Инициализация модального окна
    initModal();
    
    // Инициализация обработчиков сервисов
    initServices();
}

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Обновляем активные кнопки
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Показываем соответствующий контент
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabName).classList.add('active');
            
            state.currentTab = tabName;
        });
    });
}

function initModal() {
    const modal = document.getElementById('modal');
    const closeBtn = document.querySelector('.close');
    const confirmBtn = document.getElementById('modal-confirm');
    
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    confirmBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        showNotification('Запрос отправлен успешно!', 'success');
    });
    
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

function showModal(title, text, confirmCallback = null) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-text').textContent = text;
    
    const confirmBtn = document.getElementById('modal-confirm');
    if (confirmCallback) {
        confirmBtn.onclick = confirmCallback;
    }
    
    document.getElementById('modal').style.display = 'block';
}

function initServices() {
    const serviceButtons = document.querySelectorAll('.btn-service');
    
    serviceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const serviceCard = this.closest('.service-card');
            const serviceType = serviceCard.getAttribute('data-service');
            
            let title, text;
            
            switch(serviceType) {
                case 'reference':
                    title = 'Заказ справки об обучении';
                    text = 'Вы уверены, что хотите заказать справку об обучении? Справка будет готова в течение 3 рабочих дней.';
                    break;
                case 'academic_leave':
                    title = 'Заявление на академический отпуск';
                    text = 'Подача заявления на академический отпуск требует подтверждения от куратора. Продолжить?';
                    break;
                case 'transfer':
                    title = 'Заявление на перевод';
                    text = 'Для перевода на другую специальность требуется согласование с обоими деканатами. Продолжить?';
                    break;
            }
            
            showModal(title, text, function() {
                // Здесь можно добавить API вызов
                showNotification('Заявление отправлено на рассмотрение', 'success');
            });
        });
    });
}

// Загрузка данных
async function loadSchedule() {
    try {
        showLoading('schedule-list');
        
        // В реальном приложении здесь будет fetch к API
        // const response = await fetch(`${CONFIG.API_BASE_URL}/api/schedule`);
        // const data = await response.json();
        
        // Имитация API ответа
        const data = {
            today: [
                {
                    time: "09:00-10:30",
                    subject: "Математический анализ",
                    room: "310",
                    teacher: "проф. Иванов"
                },
                {
                    time: "11:00-12:30", 
                    subject: "Программирование",
                    room: "415",
                    teacher: "доц. Петрова"
                },
                {
                    time: "14:00-15:30",
                    subject: "Иностранный язык", 
                    room: "201",
                    teacher: "ст. преп. Сидорова"
                }
            ]
        };
        
        state.scheduleData = data;
        renderSchedule('today');
        
        // Инициализация переключения дат
        initDateSelector();
        
    } catch (error) {
        console.error('Ошибка загрузки расписания:', error);
        showNotification('Ошибка загрузки расписания', 'error');
    }
}

async function loadProjects() {
    try {
        showLoading('projects-list');
        
        // Имитация API ответа
        const data = [
            {
                id: 1,
                title: "Разработка мобильного приложения",
                needs: "2 backend, 1 frontend, 1 дизайнер",
                deadline: "2 месяца",
                curator: "проф. Иванов",
                status: "active"
            },
            {
                id: 2,
                title: "Исследование AI в образовании",
                needs: "аналитики, исследователи", 
                deadline: "3 месяца",
                curator: "доц. Петрова",
                status: "active"
            }
        ];
        
        state.projectsData = data;
        renderProjects();
        
    } catch (error) {
        console.error('Ошибка загрузки проектов:', error);
        showNotification('Ошибка загрузки проектов', 'error');
    }
}

// Рендеринг данных
function renderSchedule(dateType) {
    const container = document.getElementById('schedule-list');
    const schedule = state.scheduleData[dateType] || [];
    
    if (schedule.length === 0) {
        container.innerHTML = '<div class="no-data">Нет занятий на выбранную дату</div>';
        return;
    }
    
    container.innerHTML = schedule.map(item => `
        <div class="schedule-item">
            <div class="schedule-time">${item.time}</div>
            <div class="schedule-details">
                <div class="schedule-subject">${item.subject}</div>
                <div class="schedule-meta">
                    Аудитория: ${item.room} | Преподаватель: ${item.teacher}
                </div>
            </div>
        </div>
    `).join('');
}

function renderProjects() {
    const container = document.getElementById('projects-list');
    const projects = state.projectsData;
    
    container.innerHTML = projects.map(project => `
        <div class="project-card">
            <h3>${project.title}</h3>
            <div class="project-meta">
                <p><strong>Требуются:</strong> ${project.needs}</p>
                <p><strong>Срок:</strong> ${project.deadline}</p>
                <p><strong>Куратор:</strong> ${project.curator}</p>
            </div>
            <button class="btn-primary" onclick="joinProject(${project.id})">
                Присоединиться к проекту
            </button>
        </div>
    `).join('');
}

function initDateSelector() {
    const dateButtons = document.querySelectorAll('.date-btn');
    
    dateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const dateType = this.getAttribute('data-date');
            
            dateButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            renderSchedule(dateType);
        });
    });
}

// Действия пользователя
function joinProject(projectId) {
    showModal(
        'Присоединение к проекту',
        'Вы уверены, что хотите присоединиться к этому проекту? С вами свяжется куратор для уточнения деталей.',
        function() {
            showNotification('Заявка отправлена! Ожидайте ответа от куратора.', 'success');
        }
    );
}

// Вспомогательные функции
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '<div class="loading">Загрузка...</div>';
}

function showNotification(message, type = 'info') {
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Стили для уведомления
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1001;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Удаляем уведомление через 3 секунды
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Стили для анимации
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .loading {
        text-align: center;
        padding: 2rem;
        color: #666;
    }
    
    .no-data {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-style: italic;
    }
    
    .notification-success { background: #4CAF50; }
    .notification-error { background: #f44336; }
    .notification-info { background: #2196F3; }
`;
document.head.appendChild(style);