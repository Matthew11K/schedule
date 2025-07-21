# Фронтенд интерфейс системы управления расписанием

## Технологический стек

### Основные технологии
- **Bootstrap 5.3** - CSS фреймворк для адаптивного дизайна
- **FullCalendar.js 6.1.8** - календарный компонент с drag-and-drop
- **Django Templates** - серверное рендеринг шаблонов
- **HTMX 1.9.6** - динамические обновления без перезагрузки страницы
- **Axios 1.5.0** - HTTP клиент для работы с API

### Дополнительные библиотеки
- **Bootstrap Icons** - иконки интерфейса
- **SortableJS** - drag-and-drop функциональность
- **FullCalendar Russian locale** - русская локализация календаря

## Структура приложения

```
frontend/
├── templates/frontend/
│   ├── base.html              # Базовый шаблон
│   ├── landing.html           # Посадочная страница
│   ├── dashboard.html         # Панель планирования
│   ├── schedule.html          # Календарное расписание
│   └── reports.html           # Отчеты и аналитика
├── static/frontend/
│   ├── css/
│   │   └── style.css         # Кастомные стили
│   ├── js/
│   │   └── app.js           # Основная JavaScript логика
│   └── img/                 # Изображения
├── views.py                 # Views для страниц
└── urls.py                  # URL маршруты
```

## Основные страницы

### 1. Посадочная страница (`/`)
- Общее описание системы
- Основные возможности
- Статистика системы
- Ссылки для входа в систему

**URL**: `http://localhost:8000/`

### 2. Панель планирования (`/dashboard/`)
- Боковая панель с фильтрами
- Календарный интерфейс FullCalendar
- Быстрые действия (создание урока, проверка конфликтов)
- Статистика в реальном времени

**URL**: `http://localhost:8000/dashboard/`

**Основные функции**:
- Фильтрация по группам, предметам, преподавателям, кабинетам
- Создание и редактирование уроков
- Проверка конфликтов в расписании
- Автоматическое разрешение конфликтов

### 3. Календарное расписание (`/schedule/`)
- Полноэкранный календарь
- Расширенные фильтры и настройки
- Экспорт в различные форматы
- Детальная статистика

**URL**: `http://localhost:8000/schedule/`

**Представления календаря**:
- Недельный вид (по умолчанию)
- Дневной вид
- Месячный вид

### 4. Отчеты (`/reports/`)
- Статистические карточки
- Заглушки для будущих отчетов
- Аналитика использования ресурсов

**URL**: `http://localhost:8000/reports/`

## JavaScript архитектура

### Основные классы

#### `ScheduleAPI`
Класс для работы с REST API:

```javascript
const api = new ScheduleAPI();

// Основные методы
await api.getScheduledEvents(filters)
await api.createScheduledEvent(eventData)
await api.updateScheduledEvent(eventId, eventData)
await api.deleteScheduledEvent(eventId)
await api.getTeachers()
await api.getGroups()
await api.getSubjects()
await api.getRooms()
await api.checkConflicts(planId)
await api.resolveConflicts(planId)
```

#### `ScheduleCalendar`
Класс для управления календарем:

```javascript
const calendar = new ScheduleCalendar('calendar');

// Основные методы
calendar.refresh()
calendar.changeView('timeGridWeek')
calendar.openEventModal(event)
```

### Утилиты

```javascript
// Показать/скрыть индикатор загрузки
showLoading(true/false)

// Показать уведомление
showToast('Сообщение', 'success|error|warning|info')

// Форматирование времени
formatDateTime(dateTime)
formatTime(dateTime)
```

## CSS кастомизация

### CSS переменные
```css
:root {
    --primary-color: #0d6efd;
    --secondary-color: #6c757d;
    --success-color: #198754;
    --info-color: #0dcaf0;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --sidebar-width: 300px;
    --calendar-height: calc(100vh - 120px);
}
```

### Основные CSS классы

#### Календарь
- `.calendar-container` - контейнер календаря
- `.fc-event` - события календаря
- `.event-math`, `.event-russian`, etc. - цвета предметов
- `.conflict-indicator` - индикатор конфликта

#### Фильтры
- `.sidebar` - боковая панель
- `.filter-group` - группа фильтров
- `.filter-checkbox` - чекбокс фильтра
- `.class-indicator` - цветовой индикатор

#### Компоненты
- `.loading-overlay` - оверлей загрузки
- `.draggable-item` - перетаскиваемый элемент
- `.drop-zone` - зона для сброса

## Интеграция с API

### Аутентификация
Система поддерживает JWT аутентификацию:

```javascript
// Автоматическое добавление токена
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// Обработка ошибок аутентификации
axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            // Перенаправление на страницу входа
        }
        return Promise.reject(error);
    }
);
```

### Работа с событиями
```javascript
// Загрузка событий календаря
const events = await api.getScheduledEvents({
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    teacher: teacherId,
    group: groupId
});

// Создание нового события
const newEvent = await api.createScheduledEvent({
    group_course_id: 1,
    teacher_id: 2,
    room_id: 3,
    datetime: '2024-01-15T10:00:00',
    duration: 45
});
```

## Drag-and-Drop функциональность

### FullCalendar настройки
```javascript
{
    selectable: true,
    selectMirror: true,
    editable: true,
    droppable: true,
    eventResizableFromStart: true,
    
    // Обработчики событий
    select: handleSelect,
    eventClick: handleEventClick,
    eventDrop: handleEventDrop,
    eventResize: handleEventResize
}
```

### Внешние drag-and-drop элементы
```javascript
// Создание перетаскиваемых элементов
new Sortable(element, {
    group: 'calendar',
    animation: 150,
    onEnd: function(evt) {
        // Обработка завершения перетаскивания
    }
});
```

## Responsive дизайн

### Брейкпоинты
- **Desktop**: >= 768px - полный интерфейс
- **Mobile**: < 768px - адаптированный интерфейс

### Мобильные адаптации
```css
@media (max-width: 768px) {
    .sidebar {
        position: fixed;
        left: -var(--sidebar-width);
        transition: left 0.3s ease;
    }
    
    .sidebar.show {
        left: 0;
    }
    
    .fc-header-toolbar {
        flex-direction: column;
    }
}
```

## Модальные окна

### Создание/редактирование события
```javascript
function openEventModal(event = null) {
    const modal = new bootstrap.Modal(document.getElementById('eventModal'));
    
    // Динамическая загрузка содержимого
    fetch(`/modals/event/?event_id=${event ? event.id : ''}`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('eventModalBody').innerHTML = html;
        });
    
    modal.show();
}
```

### Отображение конфликтов
```javascript
function showConflictsModal(conflicts) {
    const modal = new bootstrap.Modal(document.getElementById('conflictsModal'));
    
    // Формирование списка конфликтов
    let html = '<div class="list-group">';
    conflicts.forEach(conflict => {
        html += `<div class="list-group-item">...</div>`;
    });
    html += '</div>';
    
    modal.show();
}
```

## Фильтрация и поиск

### Боковая панель фильтров
```javascript
// Загрузка данных для фильтров
async function loadFilterData() {
    const [groups, subjects, teachers, rooms] = await Promise.all([
        api.getGroups(),
        api.getSubjects(),
        api.getTeachers(),
        api.getRooms()
    ]);
    
    populateGroupFilters(groups);
    populateSubjectFilters(subjects);
    // ...
}

// Применение фильтров
document.addEventListener('change', function(e) {
    if (e.target.matches('input[name$="-filter"]')) {
        if (window.scheduleCalendar) {
            window.scheduleCalendar.refresh();
        }
    }
});
```

## Обработка ошибок

### Глобальная обработка
```javascript
// Toast уведомления
function showToast(message, type = 'info') {
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}

// Axios interceptors
axios.interceptors.response.use(
    response => response,
    error => {
        console.error('API Error:', error);
        showToast('Произошла ошибка', 'error');
        return Promise.reject(error);
    }
);
```

## Производительность

### Оптимизации
1. **Lazy loading** - динамическая загрузка модальных окон
2. **Debouncing** - задержка при фильтрации
3. **Caching** - кэширование API запросов
4. **Pagination** - пагинация больших списков

### CDN ресурсы
Все внешние библиотеки загружаются через CDN:
- Bootstrap CSS/JS
- FullCalendar
- Bootstrap Icons
- HTMX
- SortableJS
- Axios

## Безопасность

### CSRF защита
```javascript
// Автоматическое добавление CSRF токена
axios.defaults.headers.common['X-CSRFToken'] = window.CSRF_TOKEN;
```

### Валидация форм
```javascript
// Клиентская валидация
function validateEventForm(formData) {
    const required = ['group_course_id', 'teacher_id', 'room_id', 'datetime'];
    
    for (const field of required) {
        if (!formData.get(field)) {
            throw new Error(`Поле ${field} обязательно для заполнения`);
        }
    }
}
```

## Расширение функциональности

### Добавление новых страниц
1. Создать шаблон в `templates/frontend/`
2. Добавить view в `views.py`
3. Зарегистрировать URL в `urls.py`
4. Добавить в навигацию

### Кастомизация календаря
```javascript
// Добавление новых представлений
calendar.setOption('headerToolbar', {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay,customView'
});

// Кастомные рендереры событий
eventContent: function(eventInfo) {
    return {
        html: `<div class="custom-event">...</div>`
    };
}
```

## Развертывание

### Статические файлы
```bash
python manage.py collectstatic
```

### Минификация (в продакшн)
Рекомендуется использовать:
- CSS минификацию
- JavaScript bundling
- Image optimization
- CDN для статики

## Troubleshooting

### Общие проблемы

1. **Календарь не загружается**
   - Проверить подключение к API
   - Убедиться в корректности токена аутентификации

2. **Drag-and-drop не работает**
   - Проверить настройки FullCalendar
   - Убедиться в загрузке SortableJS

3. **Фильтры не применяются**
   - Проверить обработчики событий
   - Убедиться в корректности API запросов

### Отладка
```javascript
// Включение debug режима
window.DEBUG = true;

// Логирование API запросов
axios.interceptors.request.use(config => {
    if (window.DEBUG) {
        console.log('API Request:', config);
    }
    return config;
});
```
