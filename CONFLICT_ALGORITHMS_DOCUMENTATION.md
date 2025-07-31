# 📋 Документация по алгоритмам обнаружения и решения конфликтов

## 🎯 Обзор системы

Система управления расписанием включает в себя комплексные алгоритмы для **обнаружения** и **автоматического разрешения** конфликтов в расписании занятий. Алгоритмы работают в двух основных направлениях:

1. **🔍 Обнаружение конфликтов** - выявление различных типов нарушений в расписании
2. **🛠️ Разрешение конфликтов** - предложение и применение решений для устранения конфликтов

---

## 📁 Структура файлов

### Основные модули:
- **`schedule/conflict_detection.py`** - Алгоритмы обнаружения конфликтов
- **`schedule/conflict_resolution.py`** - Алгоритмы разрешения конфликтов  
- **`rules/models.py`** - Модели для хранения конфликтов и правил
- **`schedule/management/commands/check_conflicts.py`** - CLI команда для проверки

### Модели данных:
- **`ConflictType`** - Типы конфликтов с уровнями критичности
- **`Conflict`** - Конкретные экземпляры конфликтов
- **`WorkingPeriodRule`** - Правила рабочих периодов
- **`TeacherAvailabilityPeriod`** - Периоды доступности преподавателей
- **`RoomAvailabilityRule`** - Правила доступности кабинетов
- **`TimeSlot`** - Временные слоты для занятий

---

## 🔍 Алгоритмы обнаружения конфликтов

### Класс `ConflictDetector`

Основной класс для обнаружения всех типов конфликтов в расписании.

#### Метод `detect_all_conflicts(schedule_plan=None)`

**Назначение:** Обнаружение всех типов конфликтов в расписании

**Алгоритм:**
1. Получение всех активных событий из базы данных
2. Фильтрация по плану расписания (если указан)
3. Последовательная проверка каждого события по всем типам конфликтов
4. Возврат списка обнаруженных конфликтов

**Типы проверяемых конфликтов:**
- Конфликты времени преподавателя
- Конфликты времени кабинета  
- Недоступность преподавателя
- Недоступность кабинета
- Нарушение рабочих часов
- Превышение нагрузки преподавателя
- Превышение вместимости кабинета

---

### 1. Конфликты времени преподавателя (`_check_teacher_conflicts`)

**Описание:** Обнаружение случаев, когда один преподаватель назначен на несколько событий одновременно.

**Алгоритм:**
```python
def _check_teacher_conflicts(self, event: ScheduledEvent):
    # 1. Получение всех преподавателей события
    event_teachers = event.teachers.all()
    
    # 2. Для каждого преподавателя поиск пересекающихся событий
    for teacher in event_teachers:
        conflicting_events = ScheduledEvent.objects.filter(
            teachers=teacher,
            is_active=True
        ).exclude(id=event.id)
        
        # 3. Проверка пересечения по времени
        for other_event in conflicting_events:
            if self._events_overlap(event, other_event):
                # 4. Создание конфликта
                conflict = {
                    'type': 'teacher_time_conflict',
                    'severity': 'critical',
                    'event_id': event.id,
                    'description': f'Преподаватель {teacher.full_name} занят в другом месте',
                    'conflicting_event_id': other_event.id,
                    'blocking': True
                }
```

**Критичность:** `critical` - блокирующий конфликт

---

### 2. Конфликты времени кабинета (`_check_room_conflicts`)

**Описание:** Обнаружение случаев, когда один кабинет занят несколькими группами одновременно.

**Алгоритм:**
```python
def _check_room_conflicts(self, event: ScheduledEvent):
    # 1. Поиск всех событий в том же кабинете
    conflicting_events = ScheduledEvent.objects.filter(
        room=event.room,
        is_active=True
    ).exclude(id=event.id)
    
    # 2. Проверка пересечения по времени
    for other_event in conflicting_events:
        if self._events_overlap(event, other_event):
            conflict = {
                'type': 'room_time_conflict',
                'severity': 'critical',
                'event_id': event.id,
                'description': f'Кабинет {event.room} занят другой группой',
                'conflicting_event_id': other_event.id,
                'blocking': True
            }
```

**Критичность:** `critical` - блокирующий конфликт

---

### 3. Проверка доступности преподавателя (`_check_teacher_availability`)

**Описание:** Проверка соответствия событий периодам доступности преподавателей.

**Алгоритм:**
```python
def _check_teacher_availability(self, event: ScheduledEvent):
    # 1. Получение периодов доступности для каждого преподавателя
    for teacher in event.teachers.all():
        availability_periods = TeacherAvailabilityPeriod.objects.filter(
            teacher=teacher,
            is_active=True
        )
        
        # 2. Проверка попадания события в периоды доступности
        is_available = False
        for period in availability_periods:
            if self._event_in_availability_period(event, period):
                if period.availability_type == 'available':
                    is_available = True
                elif period.availability_type == 'unavailable':
                    # Создание конфликта недоступности
                    conflict = {
                        'type': 'teacher_unavailable',
                        'severity': 'high',
                        'event_id': event.id,
                        'description': f'Преподаватель {teacher.full_name} недоступен',
                        'blocking': False
                    }
```

**Критичность:** `high` - высокий приоритет

---

### 4. Проверка доступности кабинета (`_check_room_availability`)

**Описание:** Проверка соответствия событий правилам доступности кабинетов.

**Алгоритм:**
```python
def _check_room_availability(self, event: ScheduledEvent):
    # 1. Получение правил доступности кабинета
    availability_rules = RoomAvailabilityRule.objects.filter(
        room=event.room,
        is_active=True
    )
    
    # 2. Проверка каждого правила
    for rule in availability_rules:
        if self._event_in_room_rule_period(event, rule):
            if not rule.is_available:
                conflict = {
                    'type': 'room_unavailable',
                    'severity': 'high',
                    'event_id': event.id,
                    'description': f'Кабинет {event.room} недоступен: {rule.reason}',
                    'blocking': True
                }
```

**Критичность:** `high` - высокий приоритет

---

### 5. Проверка рабочих часов (`_check_working_hours`)

**Описание:** Проверка соответствия событий правилам рабочих периодов.

**Алгоритм:**
```python
def _check_working_hours(self, event: ScheduledEvent):
    # 1. Получение правил рабочих периодов
    working_rules = WorkingPeriodRule.objects.filter(
        Q(subsidiary=event.schedule_plan.subsidiary) | Q(subsidiary=None),
        is_active=True
    ).order_by('-priority')
    
    # 2. Проверка каждого правила
    is_working_time = False
    for rule in working_rules:
        if self._event_in_working_rule(event, rule):
            if rule.rule_type == 'working_day':
                is_working_time = True
                break
            elif rule.rule_type in ['holiday', 'weekend', 'vacation']:
                conflict = {
                    'type': 'non_working_time',
                    'severity': 'medium',
                    'event_id': event.id,
                    'description': f'Событие запланировано на нерабочее время: {rule.name}',
                    'blocking': False
                }
```

**Критичность:** `medium` - средний приоритет

---

### 6. Проверка нагрузки преподавателя (`_check_teacher_workload`)

**Описание:** Проверка превышения максимальной нагрузки преподавателей.

**Алгоритм:**
```python
def _check_teacher_workload(self, event: ScheduledEvent):
    # 1. Получение периодов доступности с ограничениями нагрузки
    for teacher in event.teachers.all():
        availability_periods = TeacherAvailabilityPeriod.objects.filter(
            teacher=teacher,
            is_active=True,
            max_hours_per_day__isnull=False
        )
        
        # 2. Расчёт дневной нагрузки
        for period in availability_periods:
            if self._event_in_availability_period(event, period):
                daily_hours = self._calculate_daily_hours(teacher, event, period)
                if daily_hours > period.max_hours_per_day:
                    conflict = {
                        'type': 'teacher_daily_workload_exceeded',
                        'severity': 'medium',
                        'event_id': event.id,
                        'description': f'Превышена дневная нагрузка преподавателя {teacher}',
                        'blocking': False
                    }
```

**Критичность:** `medium` - средний приоритет

---

### 7. Проверка вместимости кабинета (`_check_room_capacity`)

**Описание:** Проверка превышения вместимости кабинета количеством студентов.

**Алгоритм:**
```python
def _check_room_capacity(self, event: ScheduledEvent):
    # 1. Получение кабинета и группы
    room = event.room
    group = event.group_course.group
    
    # 2. Подсчёт активных студентов в группе
    active_students = Student.objects.filter(
        groups=group,
        is_active=True
    ).count()
    
    # 3. Проверка вместимости
    if room.capacity and active_students > room.capacity:
        conflict = {
            'type': 'room_capacity_exceeded',
            'severity': 'medium',
            'event_id': event.id,
            'description': f'Превышена вместимость кабинета {room}',
            'blocking': False
        }
```

**Критичность:** `medium` - средний приоритет

---

## 🔧 Вспомогательные алгоритмы

### Проверка пересечения событий (`_events_overlap`)

**Назначение:** Определение пересечения двух событий по времени.

**Алгоритм:**
```python
def _events_overlap(self, event1: ScheduledEvent, event2: ScheduledEvent) -> bool:
    # 1. Проверка планов расписания
    if event1.schedule_plan != event2.schedule_plan:
        return False
    
    # 2. Проверка еженедельных событий
    if (event1.event_type == 'weekly' and event2.event_type == 'weekly' and
        event1.weekday == event2.weekday):
        return self._time_ranges_overlap(
            event1.start_time, event1.end_time,
            event2.start_time, event2.end_time
        )
    
    # 3. Проверка разовых событий
    if (event1.event_type == 'single' and event2.event_type == 'single' and
        event1.specific_date == event2.specific_date):
        return self._time_ranges_overlap(
            event1.start_time, event1.end_time,
            event2.start_time, event2.end_time
        )
    
    # 4. Проверка смешанных типов событий
    # ... логика для пересечения еженедельных и разовых событий
```

### Проверка пересечения временных диапазонов (`_time_ranges_overlap`)

**Назначение:** Определение пересечения двух временных диапазонов.

**Алгоритм:**
```python
def _time_ranges_overlap(self, start1: time, end1: time, start2: time, end2: time) -> bool:
    return start1 < end2 and start2 < end1
```

---

## 🛠️ Алгоритмы разрешения конфликтов

### Класс `ConflictResolver`

Основной класс для предложения и применения решений конфликтов.

#### Метод `suggest_solutions(conflict: Conflict)`

**Назначение:** Генерация предложений по разрешению конкретного конфликта.

**Алгоритм:**
1. Определение типа конфликта
2. Вызов соответствующего метода предложения решений
3. Возврат списка предложений с приоритетами

**Типы решений:**
- Изменение времени события
- Замена преподавателя
- Замена кабинета
- Изменение группы
- Игнорирование конфликта

---

### 1. Решения для конфликтов времени преподавателя

**Метод:** `_suggest_teacher_time_solutions`

**Предложения:**
1. **Перенос времени** - поиск свободного времени для того же преподавателя
2. **Замена преподавателя** - поиск альтернативных преподавателей
3. **Изменение дня недели** - перенос на другой день

**Алгоритм:**
```python
def _suggest_teacher_time_solutions(self, event: ScheduledEvent, conflict: Conflict):
    # 1. Поиск свободного времени для преподавателя
    free_slots = self._find_free_teacher_slots(primary_teacher, event.schedule_plan)
    for slot in free_slots[:3]:
        self.suggestions.append({
            'type': 'reschedule_time',
            'description': f'Перенести на {self._format_time_slot(slot)}',
            'action': 'change_time',
            'new_time': slot,
            'priority': 'high'
        })
    
    # 2. Поиск альтернативных преподавателей
    alternative_teachers = self._find_alternative_teachers(event)
    for teacher in alternative_teachers[:2]:
        self.suggestions.append({
            'type': 'change_teacher',
            'description': f'Заменить преподавателя на {teacher}',
            'action': 'change_teacher',
            'new_teacher_id': teacher.id,
            'priority': 'medium'
        })
```

---

### 2. Решения для конфликтов времени кабинета

**Метод:** `_suggest_room_time_solutions`

**Предложения:**
1. **Замена кабинета** - поиск свободных кабинетов
2. **Перенос времени** - поиск времени, когда кабинет свободен
3. **Объединение групп** - если кабинеты позволяют

**Алгоритм:**
```python
def _suggest_room_time_solutions(self, event: ScheduledEvent, conflict: Conflict):
    # 1. Поиск свободных кабинетов
    alternative_rooms = self._find_alternative_rooms(event)
    for room in alternative_rooms[:3]:
        self.suggestions.append({
            'type': 'change_room',
            'description': f'Переместить в кабинет {room}',
            'action': 'change_room',
            'new_room_id': room.id,
            'priority': 'high'
        })
    
    # 2. Поиск свободного времени для кабинета
    free_slots = self._find_free_room_slots(event.room, event.schedule_plan)
    for slot in free_slots[:2]:
        self.suggestions.append({
            'type': 'reschedule_time',
            'description': f'Перенести кабинет на {self._format_time_slot(slot)}',
            'action': 'change_time',
            'new_time': slot,
            'priority': 'medium'
        })
```

---

### 3. Решения для превышения нагрузки

**Метод:** `_suggest_workload_solutions`

**Предложения:**
1. **Перераспределение нагрузки** - поиск преподавателей с меньшей нагрузкой
2. **Изменение времени** - перенос на менее загруженные дни
3. **Разделение групп** - если позволяет кадровый состав

**Алгоритм:**
```python
def _suggest_workload_solutions(self, event: ScheduledEvent, conflict: Conflict):
    # 1. Поиск преподавателей с меньшей нагрузкой
    teachers_with_lower_workload = self._find_teachers_with_lower_workload(event)
    for teacher in teachers_with_lower_workload[:2]:
        self.suggestions.append({
            'type': 'change_teacher',
            'description': f'Передать преподавателю {teacher} (меньшая нагрузка)',
            'action': 'change_teacher',
            'new_teacher_id': teacher.id,
            'priority': 'medium'
        })
    
    # 2. Поиск альтернативных временных слотов
    alternative_times = self._find_alternative_week_times(event)
    for time_slot in alternative_times[:2]:
        self.suggestions.append({
            'type': 'reschedule_time',
            'description': f'Перенести на {self._format_time_slot(time_slot)}',
            'action': 'change_time',
            'new_time': time_slot,
            'priority': 'low'
        })
```

---

## 🔄 Автоматическое разрешение конфликтов

### Функция `auto_resolve_conflicts`

**Назначение:** Автоматическое применение решений для конфликтов, которые можно разрешить автоматически.

**Алгоритм:**
```python
def auto_resolve_conflicts(schedule_plan: SchedulePlan = None) -> Dict[str, int]:
    # 1. Получение конфликтов для автоматического разрешения
    conflicts = Conflict.objects.filter(
        status='detected',
        conflict_type__auto_resolve=True
    )
    
    # 2. Фильтрация по плану расписания
    if schedule_plan:
        event_ids = ScheduledEvent.objects.filter(
            schedule_plan=schedule_plan
        ).values_list('id', flat=True)
        conflicts = conflicts.filter(scheduled_event_id__in=event_ids)
    
    # 3. Обработка каждого конфликта
    for conflict in conflicts:
        # Получение предложений
        suggestions = resolver.suggest_solutions(conflict)
        
        # Применение решения с высоким приоритетом
        high_priority_suggestions = [s for s in suggestions if s.get('priority') == 'high']
        if high_priority_suggestions:
            suggestion = high_priority_suggestions[0]
            if apply_conflict_solution(conflict, suggestion):
                conflict.status = 'resolved'
                conflict.resolved_at = timezone.now()
                conflict.save()
```

### Функция `apply_conflict_solution`

**Назначение:** Применение конкретного решения к конфликту.

**Поддерживаемые действия:**
1. **`change_time`** - изменение времени события
2. **`change_teacher`** - замена преподавателя
3. **`change_room`** - замена кабинета

**Алгоритм:**
```python
def apply_conflict_solution(conflict: Conflict, suggestion: Dict) -> bool:
    event = ScheduledEvent.objects.get(id=conflict.scheduled_event_id)
    action = suggestion.get('action')
    
    if action == 'change_time':
        new_time = suggestion.get('new_time')
        if new_time:
            event.weekday = new_time['weekday']
            event.start_time = new_time['start_time']
            event.end_time = new_time['end_time']
            event.save()
            return True
    
    elif action == 'change_teacher':
        new_teacher_id = suggestion.get('new_teacher_id')
        if new_teacher_id:
            new_teacher = Teacher.objects.get(id=new_teacher_id)
            event.teachers.clear()
            event.teachers.add(new_teacher)
            return True
    
    elif action == 'change_room':
        new_room_id = suggestion.get('new_room_id')
        if new_room_id:
            new_room = Room.objects.get(id=new_room_id)
            event.room = new_room
            event.save()
            return True
    
    return False
```

---

## 📊 Модели данных

### ConflictType (Тип конфликта)

**Поля:**
- `name` - Название типа конфликта
- `description` - Описание типа
- `severity` - Уровень критичности (low/medium/high/critical)
- `is_blocking` - Блокирует ли создание события
- `auto_resolve` - Можно ли разрешить автоматически
- `is_active` - Активен ли тип

### Conflict (Конфликт)

**Поля:**
- `conflict_type` - Связь с типом конфликта
- `scheduled_event_id` - ID связанного события
- `description` - Описание конфликта
- `status` - Статус (detected/acknowledged/in_progress/resolved/ignored)
- `detected_at` - Время обнаружения
- `resolved_at` - Время разрешения
- `resolved_by` - Кто разрешил
- `resolution_notes` - Примечания к разрешению

### WorkingPeriodRule (Правило рабочего периода)

**Поля:**
- `rule_type` - Тип правила (working_day/holiday/weekend/vacation/special)
- `recurrence` - Повторение (once/daily/weekly/monthly/yearly)
- `start_date` / `end_date` - Период действия
- `weekdays` - Дни недели для еженедельного повторения
- `start_time` / `end_time` - Время действия
- `priority` - Приоритет правила

### TeacherAvailabilityPeriod (Период доступности преподавателя)

**Поля:**
- `teacher` - Преподаватель
- `availability_type` - Тип доступности (available/unavailable/preferred/limited)
- `start_date` / `end_date` - Период действия
- `start_time` / `end_time` - Время доступности
- `weekdays` - Дни недели
- `max_hours_per_day` - Максимум часов в день
- `max_hours_per_week` - Максимум часов в неделю

### RoomAvailabilityRule (Правило доступности кабинета)

**Поля:**
- `room` - Кабинет
- `start_date` / `end_date` - Период действия
- `start_time` / `end_time` - Время доступности
- `weekdays` - Дни недели
- `is_available` - Доступен ли кабинет
- `reason` - Причина недоступности

---

## 🚀 Использование системы

### 1. Обнаружение конфликтов

```python
from schedule.conflict_detection import detect_and_save_conflicts

# Обнаружение конфликтов для всех планов
conflicts = detect_and_save_conflicts()

# Обнаружение конфликтов для конкретного плана
from schedule.models import SchedulePlan
plan = SchedulePlan.objects.get(id=1)
conflicts = detect_and_save_conflicts(plan)
```

### 2. Предложение решений

```python
from schedule.conflict_resolution import ConflictResolver
from rules.models import Conflict

resolver = ConflictResolver()
conflict = Conflict.objects.get(id=1)
suggestions = resolver.suggest_solutions(conflict)

for suggestion in suggestions:
    print(f"{suggestion['description']} (приоритет: {suggestion['priority']})")
```

### 3. Автоматическое разрешение

```python
from schedule.conflict_resolution import auto_resolve_conflicts

# Автоматическое разрешение всех конфликтов
stats = auto_resolve_conflicts()
print(f"Разрешено: {stats['auto_resolved']}")
print(f"Требует ручного вмешательства: {stats['manual_required']}")
```

### 4. CLI команда

```bash
# Проверка всех конфликтов
python manage.py check_conflicts --verbose

# Проверка конкретного плана
python manage.py check_conflicts --plan-id 1 --verbose

# Автоматическое разрешение
python manage.py check_conflicts --auto-resolve --verbose

# Предложения решений
python manage.py check_conflicts --suggest-solutions --verbose

# Очистка старых конфликтов
python manage.py check_conflicts --clear-old --verbose
```

---

## 🔧 Настройка и кастомизация

### Добавление нового типа конфликта:

1. Создать запись в `ConflictType`
2. Добавить метод обнаружения в `ConflictDetector`
3. Добавить метод разрешения в `ConflictResolver`
4. Обновить документацию

### Настройка правил:

1. **Рабочие периоды** - настройка праздников и выходных
2. **Доступность преподавателей** - графики работы
3. **Доступность кабинетов** - ремонты и техническое обслуживание
4. **Временные слоты** - структура учебного дня

---