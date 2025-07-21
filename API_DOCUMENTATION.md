# REST API для системы управления школьным расписанием

## Обзор

REST API предоставляет полный функционал для управления системой школьного расписания. API использует JWT аутентификацию и следует REST принципам.

## Базовая конфигурация

- **Base URL**: `http://localhost:8000/api/v1/`
- **Аутентификация**: JWT Token + Session Authentication
- **Формат данных**: JSON
- **Пагинация**: 50 записей на страницу (настраивается через `?page_size=`)

## Аутентификация

### Получение JWT токена

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Ответ:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Обновление токена

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Использование токена

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/v1/teachers/
```

## Основные endpoints

### 1. Справочные данные

#### Филиалы
- **GET** `/subsidiaries/` - Список всех филиалов
- **POST** `/subsidiaries/` - Создать новый филиал
- **GET** `/subsidiaries/{id}/` - Получить конкретный филиал
- **PUT** `/subsidiaries/{id}/` - Обновить филиал
- **DELETE** `/subsidiaries/{id}/` - Удалить филиал

#### Предметы
- **GET** `/subjects/` - Список всех предметов
- **POST** `/subjects/` - Создать новый предмет
- **GET** `/subjects/{id}/` - Получить конкретный предмет
- **PUT** `/subjects/{id}/` - Обновить предмет
- **DELETE** `/subjects/{id}/` - Удалить предмет

#### Уровни
- **GET** `/levels/` - Список всех уровней
- **POST** `/levels/` - Создать новый уровень
- **GET** `/levels/{id}/` - Получить конкретный уровень
- **PUT** `/levels/{id}/` - Обновить уровень
- **DELETE** `/levels/{id}/` - Удалить уровень

#### Курсы
- **GET** `/courses/` - Список всех курсов
- **POST** `/courses/` - Создать новый курс
- **GET** `/courses/{id}/` - Получить конкретный курс
- **PUT** `/courses/{id}/` - Обновить курс
- **DELETE** `/courses/{id}/` - Удалить курс

**Фильтры для курсов:**
- `?subsidiary=<id>` - Фильтр по филиалу
- `?subject=<id>` - Фильтр по предмету
- `?level=<id>` - Фильтр по уровню

#### Пакеты
- **GET** `/packages/` - Список всех пакетов
- **POST** `/packages/` - Создать новый пакет
- **GET** `/packages/{id}/` - Получить конкретный пакет
- **PUT** `/packages/{id}/` - Обновить пакет
- **DELETE** `/packages/{id}/` - Удалить пакет

#### Преподаватели
- **GET** `/teachers/` - Список всех преподавателей
- **POST** `/teachers/` - Создать нового преподавателя
- **GET** `/teachers/{id}/` - Получить конкретного преподавателя
- **PUT** `/teachers/{id}/` - Обновить преподавателя
- **DELETE** `/teachers/{id}/` - Удалить преподавателя
- **GET** `/teachers/{id}/schedule/` - Получить расписание преподавателя

**Параметры для расписания преподавателя:**
- `?start_date=2024-01-01` - Начальная дата
- `?end_date=2024-01-31` - Конечная дата

#### Кабинеты
- **GET** `/rooms/` - Список всех кабинетов
- **POST** `/rooms/` - Создать новый кабинет
- **GET** `/rooms/{id}/` - Получить конкретный кабинет
- **PUT** `/rooms/{id}/` - Обновить кабинет
- **DELETE** `/rooms/{id}/` - Удалить кабинет

### 2. Группы и студенты

#### Группы
- **GET** `/groups/` - Список всех групп
- **POST** `/groups/` - Создать новую группу
- **GET** `/groups/{id}/` - Получить конкретную группу
- **PUT** `/groups/{id}/` - Обновить группу
- **DELETE** `/groups/{id}/` - Удалить группу
- **GET** `/groups/{id}/schedule/` - Получить расписание группы

#### Курсы групп
- **GET** `/group-courses/` - Список всех курсов групп
- **POST** `/group-courses/` - Создать новый курс группы
- **GET** `/group-courses/{id}/` - Получить конкретный курс группы
- **PUT** `/group-courses/{id}/` - Обновить курс группы
- **DELETE** `/group-courses/{id}/` - Удалить курс группы

#### Студенты
- **GET** `/students/` - Список всех студентов
- **POST** `/students/` - Создать нового студента
- **GET** `/students/{id}/` - Получить конкретного студента
- **PUT** `/students/{id}/` - Обновить студента
- **DELETE** `/students/{id}/` - Удалить студента

### 3. Расписание

#### Планы расписания
- **GET** `/schedule-plans/` - Список всех планов расписания
- **POST** `/schedule-plans/` - Создать новый план расписания
- **GET** `/schedule-plans/{id}/` - Получить конкретный план расписания
- **PUT** `/schedule-plans/{id}/` - Обновить план расписания
- **DELETE** `/schedule-plans/{id}/` - Удалить план расписания
- **POST** `/schedule-plans/{id}/check_conflicts/` - Проверить конфликты в плане
- **POST** `/schedule-plans/{id}/resolve_conflicts/` - Разрешить конфликты в плане

#### Запланированные события
- **GET** `/scheduled-events/` - Список всех запланированных событий
- **POST** `/scheduled-events/` - Создать новое событие
- **GET** `/scheduled-events/{id}/` - Получить конкретное событие
- **PUT** `/scheduled-events/{id}/` - Обновить событие
- **DELETE** `/scheduled-events/{id}/` - Удалить событие

**Фильтры для событий:**
- `?plan=<id>` - Фильтр по плану расписания
- `?teacher=<id>` - Фильтр по преподавателю
- `?group=<id>` - Фильтр по группе
- `?room=<id>` - Фильтр по кабинету
- `?start_date=2024-01-01` - Начальная дата
- `?end_date=2024-01-31` - Конечная дата

#### Отмены событий
- **GET** `/scheduled-event-cancellations/` - Список всех отмен событий
- **POST** `/scheduled-event-cancellations/` - Создать новую отмену
- **GET** `/scheduled-event-cancellations/{id}/` - Получить конкретную отмену
- **PUT** `/scheduled-event-cancellations/{id}/` - Обновить отмену
- **DELETE** `/scheduled-event-cancellations/{id}/` - Удалить отмену

#### События
- **GET** `/events/` - Список всех событий
- **POST** `/events/` - Создать новое событие
- **GET** `/events/{id}/` - Получить конкретное событие
- **PUT** `/events/{id}/` - Обновить событие
- **DELETE** `/events/{id}/` - Удалить событие

### 4. Учебные материалы

#### Материалы
- **GET** `/learning-materials/` - Список всех учебных материалов
- **POST** `/learning-materials/` - Создать новый материал
- **GET** `/learning-materials/{id}/` - Получить конкретный материал
- **PUT** `/learning-materials/{id}/` - Обновить материал
- **DELETE** `/learning-materials/{id}/` - Удалить материал

#### Узлы материалов
- **GET** `/learning-material-nodes/` - Список всех узлов материалов
- **POST** `/learning-material-nodes/` - Создать новый узел материала
- **GET** `/learning-material-nodes/{id}/` - Получить конкретный узел материала
- **PUT** `/learning-material-nodes/{id}/` - Обновить узел материала
- **DELETE** `/learning-material-nodes/{id}/` - Удалить узел материала

#### Учебные программы
- **GET** `/curricula/` - Список всех учебных программ
- **POST** `/curricula/` - Создать новую учебную программу
- **GET** `/curricula/{id}/` - Получить конкретную учебную программу
- **PUT** `/curricula/{id}/` - Обновить учебную программу
- **DELETE** `/curricula/{id}/` - Удалить учебную программу

#### Узлы программ
- **GET** `/curriculum-nodes/` - Список всех узлов программ
- **POST** `/curriculum-nodes/` - Создать новый узел программы
- **GET** `/curriculum-nodes/{id}/` - Получить конкретный узел программы
- **PUT** `/curriculum-nodes/{id}/` - Обновить узел программы
- **DELETE** `/curriculum-nodes/{id}/` - Удалить узел программы

#### Связи узлов и материалов
- **GET** `/curriculum-node-materials/` - Список всех связей узлов и материалов
- **POST** `/curriculum-node-materials/` - Создать новую связь
- **GET** `/curriculum-node-materials/{id}/` - Получить конкретную связь
- **PUT** `/curriculum-node-materials/{id}/` - Обновить связь
- **DELETE** `/curriculum-node-materials/{id}/` - Удалить связь

#### Программы курсов групп
- **GET** `/group-course-curricula/` - Список всех программ курсов групп
- **POST** `/group-course-curricula/` - Создать новую программу курса группы
- **GET** `/group-course-curricula/{id}/` - Получить конкретную программу курса группы
- **PUT** `/group-course-curricula/{id}/` - Обновить программу курса группы
- **DELETE** `/group-course-curricula/{id}/` - Удалить программу курса группы

### 5. Правила и ограничения

#### Правила рабочего времени
- **GET** `/working-period-rules/` - Список всех правил рабочего времени
- **POST** `/working-period-rules/` - Создать новое правило рабочего времени
- **GET** `/working-period-rules/{id}/` - Получить конкретное правило рабочего времени
- **PUT** `/working-period-rules/{id}/` - Обновить правило рабочего времени
- **DELETE** `/working-period-rules/{id}/` - Удалить правило рабочего времени

#### Периоды доступности преподавателей
- **GET** `/teacher-availability-periods/` - Список всех периодов доступности преподавателей
- **POST** `/teacher-availability-periods/` - Создать новый период доступности преподавателя
- **GET** `/teacher-availability-periods/{id}/` - Получить конкретный период доступности преподавателя
- **PUT** `/teacher-availability-periods/{id}/` - Обновить период доступности преподавателя
- **DELETE** `/teacher-availability-periods/{id}/` - Удалить период доступности преподавателя

#### Временные слоты
- **GET** `/time-slots/` - Список всех временных слотов
- **POST** `/time-slots/` - Создать новый временной слот
- **GET** `/time-slots/{id}/` - Получить конкретный временной слот
- **PUT** `/time-slots/{id}/` - Обновить временной слот
- **DELETE** `/time-slots/{id}/` - Удалить временной слот

#### Правила доступности кабинетов
- **GET** `/room-availability-rules/` - Список всех правил доступности кабинетов
- **POST** `/room-availability-rules/` - Создать новое правило доступности кабинета
- **GET** `/room-availability-rules/{id}/` - Получить конкретное правило доступности кабинета
- **PUT** `/room-availability-rules/{id}/` - Обновить правило доступности кабинета
- **DELETE** `/room-availability-rules/{id}/` - Удалить правило доступности кабинета

### 6. Конфликты

#### Типы конфликтов
- **GET** `/conflict-types/` - Список всех типов конфликтов
- **POST** `/conflict-types/` - Создать новый тип конфликта
- **GET** `/conflict-types/{id}/` - Получить конкретный тип конфликта
- **PUT** `/conflict-types/{id}/` - Обновить тип конфликта
- **DELETE** `/conflict-types/{id}/` - Удалить тип конфликта

#### Конфликты
- **GET** `/conflicts/` - Список всех конфликтов
- **POST** `/conflicts/` - Создать новый конфликт
- **GET** `/conflicts/{id}/` - Получить конкретный конфликт
- **PUT** `/conflicts/{id}/` - Обновить конфликт
- **DELETE** `/conflicts/{id}/` - Удалить конфликт
- **POST** `/conflicts/{id}/resolve/` - Разрешить конфликт

**Фильтры для конфликтов:**
- `?plan=<id>` - Фильтр по плану расписания
- `?resolved=true/false` - Фильтр по статусу разрешения
- `?type=<id>` - Фильтр по типу конфликта

### 7. Пользователи

#### Пользователи
- **GET** `/users/` - Список всех пользователей
- **POST** `/users/` - Создать нового пользователя
- **GET** `/users/{id}/` - Получить конкретного пользователя
- **PUT** `/users/{id}/` - Обновить пользователя
- **DELETE** `/users/{id}/` - Удалить пользователя

## Примеры использования

### Создание нового преподавателя

```bash
curl -X POST http://localhost:8000/api/v1/teachers/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "phone": "+7(999)123-45-67",
    "subsidiaries": [1, 2],
    "subjects": [1, 2, 3]
  }'
```

### Получение расписания преподавателя за период

```bash
curl -H "Authorization: Bearer <access_token>" \
  "http://localhost:8000/api/v1/teachers/1/schedule/?start_date=2024-01-01&end_date=2024-01-31"
```

### Создание нового события в расписании

```bash
curl -X POST http://localhost:8000/api/v1/scheduled-events/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 1,
    "group_course_id": 1,
    "teacher_id": 1,
    "room_id": 1,
    "datetime": "2024-01-15T10:00:00Z",
    "duration": 60
  }'
```

### Проверка конфликтов в плане расписания

```bash
curl -X POST http://localhost:8000/api/v1/schedule-plans/1/check_conflicts/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json"
```

### Получение нерешенных конфликтов

```bash
curl -H "Authorization: Bearer <access_token>" \
  "http://localhost:8000/api/v1/conflicts/?resolved=false"
```

### Разрешение конфликта

```bash
curl -X POST http://localhost:8000/api/v1/conflicts/1/resolve/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json"
```

## Коды ответов

- **200 OK** - Успешный запрос
- **201 Created** - Ресурс создан
- **204 No Content** - Ресурс удален
- **400 Bad Request** - Некорректные данные
- **401 Unauthorized** - Требуется аутентификация
- **403 Forbidden** - Доступ запрещен
- **404 Not Found** - Ресурс не найден
- **405 Method Not Allowed** - Метод не поддерживается
- **500 Internal Server Error** - Внутренняя ошибка сервера

## Пагинация

Все списки поддерживают пагинацию:

```json
{
  "count": 123,
  "next": "http://localhost:8000/api/v1/teachers/?page=2",
  "previous": null,
  "results": [...]
}
```

## Специальные возможности

### Функции управления конфликтами

API предоставляет расширенные возможности для работы с конфликтами:

1. **Автоматическое обнаружение конфликтов** - система анализирует планы расписания и находит все типы конфликтов
2. **Предложения по разрешению** - для каждого конфликта система предлагает варианты решения
3. **Автоматическое разрешение** - простые конфликты могут быть разрешены автоматически
4. **Подробные отчеты** - полная информация о конфликтах с описанием и рекомендациями

### Фильтрация и поиск

Большинство endpoints поддерживают фильтрацию:

- По датам (`start_date`, `end_date`)
- По связанным объектам (`teacher`, `group`, `room`, `plan`)
- По статусам (`resolved`, `active`)
- По типам (`type`, `level`)

## Документация OpenAPI

Полная интерактивная документация доступна по адресам:

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`