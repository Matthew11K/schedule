# School Schedule - Система управления школьным расписанием

## 📋 Описание

Система управления школьным расписанием, разработанная на Django с использованием PostgreSQL. Поддерживает создание расписаний, управление конфликтами ресурсов, учебными материалами и многое другое.

## 🚀 Быстрый старт

### Требования

- Docker
- Docker Compose
- Make (опционально, для удобства)

### Установка и запуск

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd Schedule
```

2. **Запустите проект:**
```bash
# С использованием Make
make first-run

# Или напрямую через docker-compose
docker-compose build
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

3. **Откройте браузер:**
- Приложение: http://localhost:8000
- API документация: http://localhost:8000/api/docs/
- Админ панель: http://localhost:8000/admin/
- pgAdmin: http://localhost:5050 (admin@admin.com / admin)

## 🛠 Команды разработки

### Основные команды Make

```bash
make help              # Показать все доступные команды
make build             # Собрать Docker образы
make up                # Запустить все сервисы
make down              # Остановить все сервисы
make logs              # Показать логи
make restart           # Перезапустить сервисы
```

### Django команды

```bash
make shell             # Django shell
make bash              # Bash в контейнере
make migrate           # Выполнить миграции
make makemigrations    # Создать миграции
make superuser         # Создать суперпользователя
make test              # Запустить тесты
make check             # Проверить конфигурацию
```

### Команды без Make

```bash
# Запуск сервисов
docker-compose up -d

# Django команды
docker-compose exec web python manage.py [command]

# Просмотр логов
docker-compose logs -f web
```

## 📊 Структура проекта

```
Schedule/
├── core/              # Основные модели (Subsidiary, Subject, Course, etc.)
├── groups/            # Группы и студенты
├── schedule/          # Расписание и события
├── learning/          # Учебные материалы и программы
├── rules/             # Правила и ограничения
├── school_schedule/   # Настройки Django
├── static/            # Статические файлы
├── media/             # Медиа файлы
├── templates/         # Шаблоны
└── logs/              # Логи приложения
```

## 🗄 Архитектура базы данных

Проект использует PostgreSQL с следующими основными сущностями:

- **Subsidiary** - Филиал школы
- **Subject** - Предмет
- **Level** - Ступень обучения
- **Course** - Курс
- **Package** - Пакет курсов
- **Group** - Класс/группа
- **SchedulePlan** - План расписания
- **ScheduledEvent** - Запланированное событие
- **LearningMaterial** - Учебные материалы

## 🔧 Настройки

### Переменные окружения

Создайте файл `env_settings.py` для локальных настроек:

```python
# База данных
DATABASE_CONFIG = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'school_schedule',
    'USER': 'postgres',
    'PASSWORD': 'postgres',
    'HOST': 'db',
    'PORT': '5432',
}

# Django настройки
DEBUG = True
SECRET_KEY = 'your-secret-key-here'
```

### Docker окружение

Основные настройки в `docker-compose.yml`:

- **web**: Django приложение (порт 8000)
- **db**: PostgreSQL база данных (порт 5432)
- **pgadmin**: Веб-интерфейс для PostgreSQL (порт 5050)

## 🧪 Тестирование

```bash
# Запуск всех тестов
make test

# Или через pytest
make pytest

# Конкретное приложение
docker-compose exec web python manage.py test core
```

## 📚 API

Документация API доступна по адресам:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Основные эндпоинты:

- `/api/core/` - Основные модели
- `/api/groups/` - Группы и студенты  
- `/api/schedule/` - Расписание
- `/api/learning/` - Учебные материалы
- `/api/rules/` - Правила и ограничения

## 🔍 Отладка

### Просмотр логов

```bash
# Все сервисы
make logs

# Только Django
make logs-web

# Только PostgreSQL
make logs-db
```

### Подключение к базе данных

```bash
# Через pgAdmin: http://localhost:5050
# Или напрямую через psql
docker-compose exec db psql -U postgres -d school_schedule
```

## 🚧 Разработка

### Добавление новых моделей

1. Создайте модели в соответствующем приложении
2. Создайте миграции: `make makemigrations`
3. Примените миграции: `make migrate`

### Структура приложений

- **core**: Основная логика и модели
- **groups**: Управление группами и студентами
- **schedule**: Система расписания
- **learning**: Учебные материалы
- **rules**: Правила и ограничения