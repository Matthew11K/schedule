/**
 * Главный JavaScript файл для системы управления расписанием
 */

// Файл app.js загружен успешно

// Локальные библиотеки загружены - проверки не нужны
window.hasFullCalendar = true;
window.hasAxios = true;

// Глобальные переменные
let calendar = null;
let currentFilters = {
    groups: [],
    teachers: [],
    subjects: [],
    rooms: []
};
let authToken = null;

// Класс для работы с API
class ScheduleAPI {
    constructor() {
        this.baseURL = window.API_BASE_URL;
        this.csrfToken = window.CSRF_TOKEN;
        this.setupAxios();
    }

    setupAxios() {
        // Настройка axios для работы с Django
        axios.defaults.headers.common['X-CSRFToken'] = this.csrfToken;
        
        // Интерцептор для обработки ошибок
        axios.interceptors.response.use(
            response => response,
            error => {
                if (error.response?.status === 401) {
                    this.handleAuthError();
                }
                return Promise.reject(error);
            }
        );
    }

    handleAuthError() {
        showToast('Ошибка аутентификации. Пожалуйста, войдите в систему.', 'error');
        window.location.href = '/admin/login/';
    }

    async authenticate(username, password) {
        try {
            const response = await axios.post('auth/token/', {
                username,
                password
            });
            
            authToken = response.data.access;
            axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
            localStorage.setItem('authToken', authToken);
            
            return true;
        } catch (error) {
            console.error('Authentication error:', error);
            return false;
        }
    }

    // Методы для работы с расписанием
    async getScheduledEvents(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.start_date) params.append('start_date', filters.start_date);
            if (filters.end_date) params.append('end_date', filters.end_date);
            if (filters.plan) params.append('plan', filters.plan);
            if (filters.teacher) params.append('teacher', filters.teacher);
            if (filters.group) params.append('group', filters.group);
            if (filters.room) params.append('room', filters.room);
            
            const response = await axios.get(`scheduled-events/?${params}`);
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching events:', error);
            throw error;
        }
    }

    async createScheduledEvent(eventData) {
        try {
            const response = await axios.post('scheduled-events/', eventData);
            return response.data;
        } catch (error) {
            console.error('Error creating event:', error);
            throw error;
        }
    }

    async updateScheduledEvent(eventId, eventData) {
        try {
            const response = await axios.put(`scheduled-events/${eventId}/`, eventData);
            return response.data;
        } catch (error) {
            console.error('Error updating event:', error);
            throw error;
        }
    }

    async deleteScheduledEvent(eventId) {
        try {
            await axios.delete(`scheduled-events/${eventId}/`);
            return true;
        } catch (error) {
            console.error('Error deleting event:', error);
            throw error;
        }
    }

    // Методы для получения справочников
    async getTeachers() {
        try {
            const response = await axios.get('teachers/');
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching teachers:', error);
            throw error;
        }
    }

    async getGroups() {
        try {
            const response = await axios.get('groups/');
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching groups:', error);
            throw error;
        }
    }

    async getSubjects() {
        try {
            const response = await axios.get('subjects/');
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching subjects:', error);
            throw error;
        }
    }

    async getRooms() {
        try {
            const response = await axios.get('rooms/');
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching rooms:', error);
            throw error;
        }
    }

    async getSubsidiaries() {
        try {
            const response = await axios.get('subsidiaries/');
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching subsidiaries:', error);
            throw error;
        }
    }

    async getSchedulePlans() {
        try {
            const response = await axios.get('schedule-plans/');
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching schedule plans:', error);
            throw error;
        }
    }

    async getConflicts(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.plan) params.append('plan', filters.plan);
            if (filters.resolved !== undefined) params.append('resolved', filters.resolved);
            if (filters.type) params.append('type', filters.type);
            
            const response = await axios.get(`conflicts/?${params}`);
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching conflicts:', error);
            throw error;
        }
    }

    async getGroupCourses() {
        try {
            const response = await axios.get('group-courses/');
            return response.data.results || response.data;
        } catch (error) {
            console.error('Error fetching group courses:', error);
            throw error;
        }
    }

    // Методы для работы с конфликтами
    async checkConflicts(planId) {
        try {
            const response = await axios.post(`schedule-plans/${planId}/check_conflicts/`);
            return response.data;
        } catch (error) {
            console.error('Error checking conflicts:', error);
            throw error;
        }
    }

    async resolveConflicts(planId) {
        try {
            const response = await axios.post(`schedule-plans/${planId}/resolve_conflicts/`);
            return response.data;
        } catch (error) {
            console.error('Error resolving conflicts:', error);
            throw error;
        }
    }
}

// Инициализация API
const api = new ScheduleAPI();

// Утилиты
function showLoading(show = true) {
    // Функция заглушена - индикатор загрузки удален для предотвращения блокировки интерфейса
    // console.log('Loading:', show);
}

function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toastId = 'toast-' + Date.now();
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';

    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass}" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: duration });
    toast.show();

    // Удаляем toast после скрытия
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function formatDateTime(dateTime) {
    return new Date(dateTime).toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTime(dateTime) {
    return new Date(dateTime).toLocaleString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getSubjectColor(subjectName) {
    const colors = {
        'Математика': 'event-math',
        'Русский язык': 'event-russian',
        'Английский язык': 'event-english',
        'Физика': 'event-science',
        'Химия': 'event-science',
        'Биология': 'event-science',
        'История': 'event-history',
        'География': 'event-geography',
        'Изобразительное искусство': 'event-art',
        'Физическая культура': 'event-pe'
    };
    
    return colors[subjectName] || 'event-math';
}

// Класс для управления календарем
class ScheduleCalendar {
    constructor(containerId) {
        this.containerId = containerId;
        this.calendar = null;
        this.events = [];
        this.init();
    }

    init() {
        const calendarEl = document.getElementById(this.containerId);
        if (!calendarEl) return;

        this.calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'timeGridWeek',
            locale: 'ru',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            height: 'auto',
            slotMinTime: '08:00:00',
            slotMaxTime: '20:00:00',
            slotDuration: '00:30:00',
            allDaySlot: false,
            weekends: false,
            selectable: true,
            selectMirror: true,
            editable: true,
            droppable: true,
            eventResizableFromStart: true,
            
            // События календаря
            select: this.handleSelect.bind(this),
            eventClick: this.handleEventClick.bind(this),
            eventDrop: this.handleEventDrop.bind(this),
            eventResize: this.handleEventResize.bind(this),
            drop: this.handleDrop.bind(this),
            
            // Загрузка событий
            events: this.loadEvents.bind(this),
            

            
            // Индикатор загрузки отключен - события загружаются быстро
            // loading: function(isLoading) {
            //     showLoading(isLoading);
            // },
            
            // Настройка отображения событий
            eventContent: this.renderEventContent.bind(this),
            
            // Настройка бизнес-часов
            businessHours: {
                daysOfWeek: [1, 2, 3, 4, 5, 6], // Понедельник - Суббота
                startTime: '08:00',
                endTime: '18:00'
            }
        });

        this.calendar.render();
        

    }

    async loadEvents(info, successCallback, failureCallback) {
        try {
            const filters = {
                start_date: info.startStr.split('T')[0],
                end_date: info.endStr.split('T')[0],
                ...this.getActiveFilters()
            };
            
            const events = await api.getScheduledEvents(filters);
            const formattedEvents = this.formatEventsForCalendar(events);
            
            this.events = events;
            successCallback(formattedEvents);
            
        } catch (error) {
            console.error('Error loading events:', error);
            failureCallback(error);
            showToast('Ошибка загрузки событий', 'error');
        }
    }

    formatEventsForCalendar(events) {
        return events.map(event => {
            try {
                // Создаем правильные локальные даты
                const eventDate = event.specific_date || event.weekday;
                // Используем формат который FullCalendar понимает как локальное время
                const startDateTime = `${eventDate}T${event.start_time}`;
                const endDateTime = `${eventDate}T${event.end_time}`;
                
                const subjectColor = this.getSubjectColor(event.group_course?.course?.subject?.name || '');
                
                return {
                    id: event.id,
                    title: this.getEventTitle(event),
                    start: startDateTime,
                    end: endDateTime,
                    backgroundColor: this.getEventColor(event),
                    borderColor: this.getEventBorderColor(event),
                    textColor: this.getEventTextColor(event),
                    extendedProps: {
                        originalEvent: event,
                        groupName: event.group_course?.group?.name || '',
                        teacherName: event.group_course?.teacher?.user || '',
                        roomName: event.room?.name || '',
                        subjectName: event.group_course?.course?.subject?.name || '',
                        duration: event.duration_minutes,
                        hasConflicts: false // Это будет заполняться из API конфликтов
                    },
                    className: subjectColor
                };
                
            } catch (error) {
                console.error('Error formatting event:', event, error);
                throw error;
            }
        });
    }

    getEventTitle(event) {
        // Используем topic как основное название события
        const topic = event.topic || 'Урок';
        const group = event.group_course?.group?.name || '';
        const room = event.room?.name || '';
        
        return `${topic}\n${group}\n${room}`;
    }

    getEventColor(event) {
        // Базовые цвета будут применяться через CSS классы
        return null;
    }

    getEventBorderColor(event) {
        return null;
    }

    getEventTextColor(event) {
        return null;
    }

    getSubjectColor(subjectName) {
        // Генерируем цвет на основе названия предмета
        const colors = [
            'subject-math', 'subject-physics', 'subject-chemistry',
            'subject-biology', 'subject-history', 'subject-geography',
            'subject-literature', 'subject-language', 'subject-art'
        ];
        
        if (!subjectName) return 'subject-default';
        
        // Простой хеш для консистентности цветов
        let hash = 0;
        for (let i = 0; i < subjectName.length; i++) {
            hash = subjectName.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        return colors[Math.abs(hash) % colors.length];
    }

    getActiveFilters() {
        const filters = {};
        
        // Собираем активные фильтры из UI
        const groupFilters = document.querySelectorAll('input[name="group-filter"]:checked');
        const teacherFilters = document.querySelectorAll('input[name="teacher-filter"]:checked');
        const subjectFilters = document.querySelectorAll('input[name="subject-filter"]:checked');
        const roomFilters = document.querySelectorAll('input[name="room-filter"]:checked');
        
        if (groupFilters.length > 0) {
            filters.groups = Array.from(groupFilters).map(cb => cb.value);
        }
        
        return filters;
    }

    async handleSelect(selectInfo) {
        // Открываем модальное окно для создания нового события
        this.openEventModal(null, {
            start: selectInfo.start,
            end: selectInfo.end
        });
        
        this.calendar.unselect();
    }

    async handleEventClick(clickInfo) {
        // Открываем модальное окно для редактирования события
        const event = clickInfo.event.extendedProps.originalEvent;
        this.openEventModal(event);
    }

    async handleEventDrop(dropInfo) {
        try {
            showLoading(true);
            
            const event = dropInfo.event.extendedProps.originalEvent;
            const newStart = dropInfo.event.start;
            
            const updatedEvent = {
                ...event,
                datetime: newStart.toISOString()
            };
            
            await api.updateScheduledEvent(event.id, updatedEvent);
            showToast('Событие успешно перемещено', 'success');
            
        } catch (error) {
            console.error('Error moving event:', error);
            showToast('Ошибка перемещения события', 'error');
            dropInfo.revert();
        } finally {
            showLoading(false);
        }
    }

    async handleEventResize(resizeInfo) {
        try {
            showLoading(true);
            
            const event = resizeInfo.event.extendedProps.originalEvent;
            const newEnd = resizeInfo.event.end;
            const newStart = resizeInfo.event.start;
            const newDuration = Math.round((newEnd - newStart) / 60000);
            
            const updatedEvent = {
                ...event,
                datetime: newStart.toISOString(),
                duration: newDuration
            };
            
            await api.updateScheduledEvent(event.id, updatedEvent);
            showToast('Продолжительность события изменена', 'success');
            
        } catch (error) {
            console.error('Error resizing event:', error);
            showToast('Ошибка изменения продолжительности', 'error');
            resizeInfo.revert();
        } finally {
            showLoading(false);
        }
    }

    handleDrop(dropInfo) {
        // Обработка перетаскивания внешних элементов
        console.log('External drop:', dropInfo);
    }

    renderEventContent(eventInfo) {
        const event = eventInfo.event;
        const props = event.extendedProps;
        
        return {
            html: `
                <div class="fc-event-main-frame">
                    <div class="fc-event-title-container">
                        <div class="fc-event-title fc-sticky">
                            <strong>${props.subjectName}</strong>
                        </div>
                    </div>
                    <div class="fc-event-time">
                        ${formatTime(event.start)} - ${formatTime(event.end)}
                    </div>
                    <div class="fc-event-group">
                        ${props.groupName}
                    </div>
                    <div class="fc-event-room">
                        <i class="bi bi-geo-alt"></i> ${props.roomName}
                    </div>
                    ${props.hasConflicts ? '<span class="conflict-indicator"></span>' : ''}
                </div>
            `
        };
    }

    openEventModal(event = null, selectInfo = null) {
        // Эта функция будет реализована в следующем шаге
        console.log('Opening event modal:', event, selectInfo);
    }

    refresh() {
        if (this.calendar) {
            this.calendar.refetchEvents();
        } else if (this.isFallback) {
            // В fallback режиме загружаем события вручную
            this.loadEventsForFallback();
        }
    }

    async loadEventsForFallback() {
        try {
            const eventsList = document.getElementById('events-list');
            if (eventsList) {
                eventsList.innerHTML = `
                    <div class="text-center p-3">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Загрузка...</span>
                        </div>
                        <p class="mt-2">Загрузка событий...</p>
                    </div>
                `;
            }

            const response = await window.axios.get('scheduled-events/');
            this.events = this.formatEventsForCalendar(response.data.results || []);
            this.renderFallbackEvents();
        } catch (error) {
            console.error('Ошибка загрузки событий:', error);
            const eventsList = document.getElementById('events-list');
            if (eventsList) {
                eventsList.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i>
                        Ошибка загрузки событий: ${error.message}
                    </div>
                `;
            }
        }
    }

    changeView(viewName) {
        if (this.calendar) {
            this.calendar.changeView(viewName);
        } else {
            // Fallback - просто обновляем отображение
            this.renderFallbackEvents();
        }
    }

    // Fallback методы для работы без FullCalendar
    initFallbackCalendar(calendarEl) {
        console.warn('FullCalendar недоступен, используем простое отображение');
        calendarEl.innerHTML = `
            <div class="fallback-calendar">
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i>
                    Календарная библиотека недоступна. Показываем события списком.
                </div>
                <div class="calendar-header">
                    <h5>Расписание событий</h5>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.scheduleCalendar.refresh()">
                        <i class="bi bi-arrow-clockwise"></i> Обновить
                    </button>
                </div>
                <div id="events-list" class="events-list">
                    <div class="text-center p-3">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Загрузка...</span>
                        </div>
                        <p class="mt-2">Загрузка событий...</p>
                    </div>
                </div>
            </div>
        `;
        this.isFallback = true;
    }

    renderFallbackEvents() {
        if (!this.isFallback) return;
        
        const eventsList = document.getElementById('events-list');
        if (!eventsList) return;

        if (this.events.length === 0) {
            eventsList.innerHTML = `
                <div class="text-center p-3">
                    <i class="bi bi-calendar-x fs-1 text-muted"></i>
                    <p class="text-muted mt-2">Нет событий для отображения</p>
                </div>
            `;
            return;
        }

        const eventsHtml = this.events.map(event => `
            <div class="card mb-2">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title mb-1">${event.title || 'Без названия'}</h6>
                            <small class="text-muted">
                                <i class="bi bi-clock"></i> ${event.start} - ${event.end}
                            </small>
                        </div>
                        <span class="badge bg-primary">${event.extendedProps?.subject || 'Предмет'}</span>
                    </div>
                    ${event.extendedProps?.room ? `<p class="mb-1"><i class="bi bi-geo-alt"></i> ${event.extendedProps.room}</p>` : ''}
                    ${event.extendedProps?.teacher ? `<p class="mb-0"><i class="bi bi-person"></i> ${event.extendedProps.teacher}</p>` : ''}
                </div>
            </div>
        `).join('');

        eventsList.innerHTML = eventsHtml;
    }
}



// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    
    // Проверяем, есть ли сохраненный токен
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
        authToken = savedToken;
        axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
    }
    
    // Инициализируем календарь если есть контейнер
    const calendarContainer = document.getElementById('calendar');
    if (calendarContainer) {
        window.scheduleCalendar = new ScheduleCalendar('calendar');
        // Убеждаемся что индикатор загрузки отключен после создания календаря
        setTimeout(() => showLoading(false), 100);
    }
    
    // Инициализируем обработчики фильтров
    initializeFilters();
    
    // Инициализируем другие компоненты
    initializeToolbar();
    initializeModals();
    

});

function initializeFilters() {
    console.log('🔧 Initializing filters...');
    
    // Обработчики для фильтров
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[name$="-filter"]')) {
            console.log(`🔄 Filter changed: ${e.target.name} = ${e.target.checked}`);
            if (window.scheduleCalendar) {
                window.scheduleCalendar.refresh();
            }
        }
    });
    
    // Кнопка "Проверить конфликты"
    const checkConflictsBtn = document.getElementById('checkConflictsBtn');
    if (checkConflictsBtn) {
        checkConflictsBtn.addEventListener('click', async function() {
            console.log('🔍 Check conflicts button clicked');
            try {
                showToast('Проверка конфликтов...', 'info');
                
                // Используем простой эндпоинт проверки конфликтов
                const response = await fetch('/api/v1/check_conflicts/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    }
                });
                
                console.log('📡 Conflicts API response:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                console.log('📊 Conflicts data:', data);
                
                if (data.conflicts && data.conflicts.length > 0) {
                    showToast(`Найдено конфликтов: ${data.conflicts.length}`, 'warning');
                } else {
                    showToast('Конфликтов не найдено', 'success');
                }
                
            } catch (error) {
                console.error('❌ Error checking conflicts:', error);
                showToast('Ошибка при проверке конфликтов', 'error');
            }
        });
        console.log('✅ Check conflicts button handler added');
    }
    
    // Кнопка "Создать урок"
    const createLessonBtn = document.getElementById('createLessonBtn');
    if (createLessonBtn) {
        createLessonBtn.addEventListener('click', function() {
            console.log('📝 Create lesson button clicked');
            const modal = new bootstrap.Modal(document.getElementById('eventModal'));
            modal.show();
        });
        console.log('✅ Create lesson button handler added');
    }
}

// Функция для получения CSRF токена
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

function initializeToolbar() {
    // Обработчики для кнопок тулбара
    document.addEventListener('click', function(e) {
        if (e.target.matches('.btn-view-change')) {
            const view = e.target.dataset.view;
            if (window.scheduleCalendar && view) {
                window.scheduleCalendar.changeView(view);
                
                // Обновляем активную кнопку
                document.querySelectorAll('.btn-view-change').forEach(btn => {
                    btn.classList.remove('active');
                });
                e.target.classList.add('active');
            }
        }
    });
}

function initializeModals() {
    // Инициализация модальных окон будет добавлена в следующем шаге
}

// Экспорт для использования в других файлах
window.ScheduleAPI = ScheduleAPI;
window.ScheduleCalendar = ScheduleCalendar;
window.api = api;
window.showToast = showToast;
window.showLoading = showLoading;
 