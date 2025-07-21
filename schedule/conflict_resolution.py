"""
Модуль для управления и разрешения конфликтов в расписании.

Содержит функции для анализа конфликтов, предложения решений
и автоматического разрешения некоторых типов конфликтов.
"""

from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
from django.db.models import Q
from django.utils import timezone

from .models import ScheduledEvent, SchedulePlan
from core.models import Teacher, Room
from groups.models import GroupCourse
from rules.models import (
    WorkingPeriodRule, TeacherAvailabilityPeriod,
    RoomAvailabilityRule, ConflictType, Conflict, TimeSlot
)


class ConflictResolver:
    """Класс для разрешения конфликтов в расписании."""
    
    def __init__(self):
        """Инициализация резолвера конфликтов."""
        self.suggestions = []
    
    def suggest_solutions(self, conflict: Conflict) -> List[Dict]:
        """
        Предложение решений для конфликта.
        
        Args:
            conflict: Объект конфликта для разрешения
            
        Returns:
            Список предложений по разрешению
        """
        self.suggestions = []
        
        if not conflict.scheduled_event_id:
            return self.suggestions
        
        try:
            event = ScheduledEvent.objects.get(id=conflict.scheduled_event_id)
        except ScheduledEvent.DoesNotExist:
            return self.suggestions
        
        conflict_type = conflict.conflict_type.name.lower()
        
        if 'teacher' in conflict_type and 'time' in conflict_type:
            self._suggest_teacher_time_solutions(event, conflict)
        elif 'room' in conflict_type and 'time' in conflict_type:
            self._suggest_room_time_solutions(event, conflict)
        elif 'teacher_unavailable' in conflict_type:
            self._suggest_teacher_availability_solutions(event, conflict)
        elif 'room_unavailable' in conflict_type:
            self._suggest_room_availability_solutions(event, conflict)
        elif 'workload' in conflict_type:
            self._suggest_workload_solutions(event, conflict)
        elif 'capacity' in conflict_type:
            self._suggest_capacity_solutions(event, conflict)
        elif 'working' in conflict_type:
            self._suggest_working_time_solutions(event, conflict)
        
        return self.suggestions
    
    def _suggest_teacher_time_solutions(self, event: ScheduledEvent, conflict: Conflict):
        """Предложения для конфликтов времени преподавателя."""
        # Получаем первого преподавателя для поиска решений
        event_teachers = event.teachers.all()
        if not event_teachers:
            return
        
        primary_teacher = event_teachers.first()
        
        # 1. Найти свободное время для того же преподавателя
        free_slots = self._find_free_teacher_slots(primary_teacher, event.schedule_plan)
        for slot in free_slots[:3]:  # Ограничиваем 3 предложениями
            self.suggestions.append({
                'type': 'reschedule_time',
                'description': f'Перенести на {self._format_time_slot(slot)}',
                'action': 'change_time',
                'new_time': slot,
                'priority': 'high'
            })
        
        # 2. Найти альтернативных преподавателей
        alternative_teachers = self._find_alternative_teachers(event)
        for teacher in alternative_teachers[:2]:
            self.suggestions.append({
                'type': 'change_teacher',
                'description': f'Заменить преподавателя на {teacher}',
                'action': 'change_teacher',
                'new_teacher_id': teacher.id,
                'priority': 'medium'
            })
    
    def _suggest_room_time_solutions(self, event: ScheduledEvent, conflict: Conflict):
        """Предложения для конфликтов времени кабинета."""
        # 1. Найти свободные кабинеты в то же время
        alternative_rooms = self._find_alternative_rooms(event)
        for room in alternative_rooms[:3]:
            self.suggestions.append({
                'type': 'change_room',
                'description': f'Перенести в кабинет {room}',
                'action': 'change_room',
                'new_room_id': room.id,
                'priority': 'high'
            })
        
        # 2. Найти свободное время для того же кабинета
        free_slots = self._find_free_room_slots(event.room, event.schedule_plan)
        for slot in free_slots[:2]:
            self.suggestions.append({
                'type': 'reschedule_time',
                'description': f'Перенести на {self._format_time_slot(slot)}',
                'action': 'change_time',
                'new_time': slot,
                'priority': 'medium'
            })
    
    def _suggest_teacher_availability_solutions(self, event: ScheduledEvent, conflict: Conflict):
        """Предложения для недоступности преподавателя."""
        # Получаем первого преподавателя для поиска решений
        event_teachers = event.teachers.all()
        if not event_teachers:
            return
            
        primary_teacher = event_teachers.first()
        
        # Найти время когда преподаватель доступен
        available_slots = self._find_teacher_available_slots(primary_teacher, event.schedule_plan)
        for slot in available_slots[:3]:
            self.suggestions.append({
                'type': 'reschedule_to_available_time',
                'description': f'Перенести на доступное время: {self._format_time_slot(slot)}',
                'action': 'change_time',
                'new_time': slot,
                'priority': 'high'
            })
        
        # Альтернативные преподаватели
        alternative_teachers = self._find_alternative_teachers(event)
        for teacher in alternative_teachers[:2]:
            self.suggestions.append({
                'type': 'change_teacher',
                'description': f'Заменить преподавателя на {teacher}',
                'action': 'change_teacher',
                'new_teacher_id': teacher.id,
                'priority': 'medium'
            })
    
    def _suggest_room_availability_solutions(self, event: ScheduledEvent, conflict: Conflict):
        """Предложения для недоступности кабинета."""
        # Альтернативные кабинеты
        alternative_rooms = self._find_alternative_rooms(event)
        for room in alternative_rooms[:3]:
            self.suggestions.append({
                'type': 'change_room',
                'description': f'Перенести в доступный кабинет {room}',
                'action': 'change_room',
                'new_room_id': room.id,
                'priority': 'high'
            })
    
    def _suggest_workload_solutions(self, event: ScheduledEvent, conflict: Conflict):
        """Предложения для превышения нагрузки."""
        # Альтернативные преподаватели с меньшей нагрузкой
        alternative_teachers = self._find_teachers_with_lower_workload(event)
        for teacher in alternative_teachers[:2]:
            self.suggestions.append({
                'type': 'change_teacher_workload',
                'description': f'Заменить преподавателя на {teacher} (меньше нагрузка)',
                'action': 'change_teacher',
                'new_teacher_id': teacher.id,
                'priority': 'medium'
            })
        
        # Перенос на другое время в пределах недели
        alternative_times = self._find_alternative_week_times(event)
        for time_slot in alternative_times[:2]:
            self.suggestions.append({
                'type': 'redistribute_workload',
                'description': f'Перенести на {self._format_time_slot(time_slot)}',
                'action': 'change_time',
                'new_time': time_slot,
                'priority': 'low'
            })
    
    def _suggest_capacity_solutions(self, event: ScheduledEvent, conflict: Conflict):
        """Предложения для превышения вместимости."""
        # Большие кабинеты
        larger_rooms = self._find_larger_rooms(event)
        for room in larger_rooms[:3]:
            self.suggestions.append({
                'type': 'change_to_larger_room',
                'description': f'Перенести в кабинет большей вместимости: {room}',
                'action': 'change_room',
                'new_room_id': room.id,
                'priority': 'high'
            })
        
        # Разделение группы
        if event.group_course.group.students.filter(is_active=True).count() > 10:
            self.suggestions.append({
                'type': 'split_group',
                'description': 'Рассмотреть разделение группы на подгруппы',
                'action': 'manual_intervention',
                'priority': 'low'
            })
    
    def _suggest_working_time_solutions(self, event: ScheduledEvent, conflict: Conflict):
        """Предложения для нарушения рабочего времени."""
        # Перенос в рабочее время
        working_slots = self._find_working_time_slots(event.schedule_plan)
        for slot in working_slots[:3]:
            self.suggestions.append({
                'type': 'move_to_working_time',
                'description': f'Перенести в рабочее время: {self._format_time_slot(slot)}',
                'action': 'change_time',
                'new_time': slot,
                'priority': 'high'
            })
    
    def _find_working_time_slots(self, schedule_plan: SchedulePlan) -> List[Dict]:
        """Поиск слотов в рабочее время."""
        working_slots = []
        time_slots = TimeSlot.objects.filter(
            Q(subsidiary=schedule_plan.subsidiary) | Q(subsidiary=None),
            is_active=True
        ).order_by('order')
        
        # Получаем рабочие дни из правил
        working_rules = WorkingPeriodRule.objects.filter(
            Q(subsidiary=schedule_plan.subsidiary) | Q(subsidiary=None),
            rule_type='working_day',
            is_active=True
        )
        
        for weekday in range(5):  # Пн-Пт (обычно рабочие дни)
            for time_slot in time_slots:
                # Проверяем, попадает ли слот в рабочее время
                is_working_time = False
                for rule in working_rules:
                    if self._time_slot_in_working_rule(weekday, time_slot, rule):
                        is_working_time = True
                        break
                
                if is_working_time:
                    working_slots.append({
                        'weekday': weekday,
                        'start_time': time_slot.start_time,
                        'end_time': time_slot.end_time,
                        'time_slot_name': time_slot.name
                    })
        
        return working_slots[:10]
    
    def _find_teacher_available_slots(self, teacher: Teacher, schedule_plan: SchedulePlan) -> List[Dict]:
        """Поиск слотов когда преподаватель доступен."""
        available_slots = []
        
        # Получаем периоды доступности преподавателя
        availability_periods = TeacherAvailabilityPeriod.objects.filter(
            teacher=teacher,
            availability_type='available',
            is_active=True
        )
        
        if not availability_periods.exists():
            return available_slots
        
        time_slots = TimeSlot.objects.filter(
            Q(subsidiary=schedule_plan.subsidiary) | Q(subsidiary=None),
            is_active=True
        ).order_by('order')
        
        for period in availability_periods:
            weekdays = period.weekdays_list if period.weekdays else list(range(7))
            
            for weekday in weekdays:
                for time_slot in time_slots:
                    # Проверяем пересечение времени
                    if (time_slot.start_time < period.end_time and 
                        time_slot.end_time > period.start_time):
                        # Проверяем свободен ли преподаватель
                        if self._is_teacher_free_at_time(teacher, schedule_plan, weekday, time_slot):
                            available_slots.append({
                                'weekday': weekday,
                                'start_time': time_slot.start_time,
                                'end_time': time_slot.end_time,
                                'time_slot_name': time_slot.name
                            })
        
        return available_slots[:10]
    
    def _find_teachers_with_lower_workload(self, event: ScheduledEvent) -> List[Teacher]:
        """Поиск преподавателей с меньшей нагрузкой."""
        subject = event.group_course.course.subject
        
        # Получаем текущих преподавателей события
        current_teacher_ids = event.teachers.values_list('id', flat=True)
        
        # Получаем всех преподавателей предмета
        teachers = Teacher.objects.filter(
            subjects=subject,
            subsidiary=event.schedule_plan.subsidiary,
            is_active=True
        ).exclude(id__in=current_teacher_ids)
        
        # Сортируем по нагрузке (упрощенно - по количеству событий)
        teachers_with_workload = []
        for teacher in teachers:
            workload = ScheduledEvent.objects.filter(
                teachers=teacher,
                schedule_plan=event.schedule_plan,
                is_active=True
            ).count()
            teachers_with_workload.append((teacher, workload))
        
        # Сортируем по возрастанию нагрузки
        teachers_with_workload.sort(key=lambda x: x[1])
        
        return [teacher for teacher, workload in teachers_with_workload[:3]]
    
    def _find_alternative_week_times(self, event: ScheduledEvent) -> List[Dict]:
        """Поиск альтернативного времени в пределах недели."""
        alternative_times = []
        
        time_slots = TimeSlot.objects.filter(
            Q(subsidiary=event.schedule_plan.subsidiary) | Q(subsidiary=None),
            is_active=True
        ).order_by('order')
        
        for weekday in range(5):  # Пн-Пт
            if weekday == event.weekday:
                continue  # Пропускаем тот же день
            
            for time_slot in time_slots:
                # Проверяем доступность всех преподавателей и кабинета
                all_teachers_free = True
                for teacher in event.teachers.all():
                    if not self._is_teacher_free_at_time(teacher, event.schedule_plan, weekday, time_slot):
                        all_teachers_free = False
                        break
                
                if (all_teachers_free and
                    self._is_room_free_at_time(event.room, event.schedule_plan, weekday, time_slot)):
                    alternative_times.append({
                        'weekday': weekday,
                        'start_time': time_slot.start_time,
                        'end_time': time_slot.end_time,
                        'time_slot_name': time_slot.name
                    })
        
        return alternative_times[:5]
    
    def _time_slot_in_working_rule(self, weekday: int, time_slot: TimeSlot, rule: WorkingPeriodRule) -> bool:
        """Проверка попадания временного слота в рабочее правило."""
        # Проверяем день недели
        if rule.weekdays:
            allowed_weekdays = [int(d.strip()) for d in rule.weekdays.split(',') if d.strip().isdigit()]
            if weekday not in allowed_weekdays:
                return False
        
        # Проверяем время
        if rule.start_time and rule.end_time:
            return (time_slot.start_time < rule.end_time and 
                   time_slot.end_time > rule.start_time)
        
        return True
    
    def _find_free_teacher_slots(self, teacher: Teacher, schedule_plan: SchedulePlan) -> List[Dict]:
        """Поиск свободных слотов для преподавателя."""
        free_slots = []
        time_slots = TimeSlot.objects.filter(
            Q(subsidiary=schedule_plan.subsidiary) | Q(subsidiary=None),
            is_active=True
        ).order_by('order')
        
        # Проверяем каждый временной слот на каждый день недели
        for weekday in range(5):  # Пн-Пт
            for time_slot in time_slots:
                if self._is_teacher_free_at_time(teacher, schedule_plan, weekday, time_slot):
                    free_slots.append({
                        'weekday': weekday,
                        'start_time': time_slot.start_time,
                        'end_time': time_slot.end_time,
                        'time_slot_name': time_slot.name
                    })
        
        return free_slots[:10]  # Ограничиваем результат
    
    def _find_free_room_slots(self, room: Room, schedule_plan: SchedulePlan) -> List[Dict]:
        """Поиск свободных слотов для кабинета."""
        free_slots = []
        time_slots = TimeSlot.objects.filter(
            Q(subsidiary=room.subsidiary) | Q(subsidiary=None),
            is_active=True
        ).order_by('order')
        
        for weekday in range(5):  # Пн-Пт
            for time_slot in time_slots:
                if self._is_room_free_at_time(room, schedule_plan, weekday, time_slot):
                    free_slots.append({
                        'weekday': weekday,
                        'start_time': time_slot.start_time,
                        'end_time': time_slot.end_time,
                        'time_slot_name': time_slot.name
                    })
        
        return free_slots[:10]
    
    def _find_alternative_teachers(self, event: ScheduledEvent) -> List[Teacher]:
        """Поиск альтернативных преподавателей."""
        # Ищем преподавателей того же предмета
        subject = event.group_course.course.subject
        current_teacher_ids = event.teachers.values_list('id', flat=True)
        
        alternative_teachers = Teacher.objects.filter(
            subjects=subject,
            subsidiary=event.schedule_plan.subsidiary,
            is_active=True
        ).exclude(id__in=current_teacher_ids)
        
        # Фильтруем тех, кто свободен в это время
        free_teachers = []
        for teacher in alternative_teachers:
            if self._is_teacher_free_for_event(teacher, event):
                free_teachers.append(teacher)
        
        return free_teachers[:5]
    
    def _find_alternative_rooms(self, event: ScheduledEvent) -> List[Room]:
        """Поиск альтернативных кабинетов."""
        # Получаем тип кабинета для предмета
        subject = event.group_course.course.subject
        
        alternative_rooms = Room.objects.filter(
            subsidiary=event.schedule_plan.subsidiary,
            is_active=True
        ).exclude(id=event.room.id)
        
        # Фильтруем по вместимости
        group_size = event.group_course.group.students.filter(is_active=True).count()
        suitable_rooms = alternative_rooms.filter(
            Q(capacity__gte=group_size) | Q(capacity__isnull=True)
        )
        
        # Проверяем доступность
        free_rooms = []
        for room in suitable_rooms:
            if self._is_room_free_for_event(room, event):
                free_rooms.append(room)
        
        return free_rooms[:5]
    
    def _find_larger_rooms(self, event: ScheduledEvent) -> List[Room]:
        """Поиск кабинетов большей вместимости."""
        current_capacity = event.room.capacity or 0
        group_size = event.group_course.group.students.filter(is_active=True).count()
        
        larger_rooms = Room.objects.filter(
            subsidiary=event.schedule_plan.subsidiary,
            capacity__gt=max(current_capacity, group_size),
            is_active=True
        ).exclude(id=event.room.id).order_by('capacity')
        
        # Проверяем доступность
        free_rooms = []
        for room in larger_rooms:
            if self._is_room_free_for_event(room, event):
                free_rooms.append(room)
        
        return free_rooms[:3]
    
    def _is_teacher_free_at_time(self, teacher: Teacher, schedule_plan: SchedulePlan, 
                                weekday: int, time_slot: TimeSlot) -> bool:
        """Проверка свободен ли преподаватель в указанное время."""
        conflicting_events = ScheduledEvent.objects.filter(
            teacher=teacher,
            schedule_plan=schedule_plan,
            event_type='weekly',
            weekday=weekday,
            is_active=True
        )
        
        for event in conflicting_events:
            if (event.start_time < time_slot.end_time and 
                event.end_time > time_slot.start_time):
                return False
        
        return True
    
    def _is_room_free_at_time(self, room: Room, schedule_plan: SchedulePlan,
                             weekday: int, time_slot: TimeSlot) -> bool:
        """Проверка свободен ли кабинет в указанное время."""
        conflicting_events = ScheduledEvent.objects.filter(
            room=room,
            schedule_plan=schedule_plan,
            event_type='weekly',
            weekday=weekday,
            is_active=True
        )
        
        for event in conflicting_events:
            if (event.start_time < time_slot.end_time and 
                event.end_time > time_slot.start_time):
                return False
        
        return True
    
    def _is_teacher_free_for_event(self, teacher: Teacher, event: ScheduledEvent) -> bool:
        """Проверка свободен ли преподаватель для конкретного события."""
        if event.event_type == 'weekly':
            return self._is_teacher_free_at_time(teacher, event.schedule_plan, event.weekday, 
                                               type('TimeSlot', (), {'start_time': event.start_time, 
                                                                   'end_time': event.end_time})())
        else:
            # Для разовых событий проверяем конкретную дату
            conflicting_events = ScheduledEvent.objects.filter(
                teacher=teacher,
                event_type='single',
                specific_date=event.specific_date,
                is_active=True
            )
            
            for conf_event in conflicting_events:
                if (event.start_time < conf_event.end_time and 
                    event.end_time > conf_event.start_time):
                    return False
            
            return True
    
    def _is_room_free_for_event(self, room: Room, event: ScheduledEvent) -> bool:
        """Проверка свободен ли кабинет для конкретного события."""
        if event.event_type == 'weekly':
            return self._is_room_free_at_time(room, event.schedule_plan, event.weekday,
                                            type('TimeSlot', (), {'start_time': event.start_time,
                                                                'end_time': event.end_time})())
        else:
            conflicting_events = ScheduledEvent.objects.filter(
                room=room,
                event_type='single',
                specific_date=event.specific_date,
                is_active=True
            )
            
            for conf_event in conflicting_events:
                if (event.start_time < conf_event.end_time and 
                    event.end_time > conf_event.start_time):
                    return False
            
            return True
    
    def _format_time_slot(self, slot: Dict) -> str:
        """Форматирование временного слота для отображения."""
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        weekday_name = weekdays[slot['weekday']]
        time_range = f"{slot['start_time'].strftime('%H:%M')}-{slot['end_time'].strftime('%H:%M')}"
        
        if 'time_slot_name' in slot:
            return f"{weekday_name}, {slot['time_slot_name']} ({time_range})"
        else:
            return f"{weekday_name}, {time_range}"


def auto_resolve_conflicts(schedule_plan: SchedulePlan = None) -> Dict[str, int]:
    """
    Автоматическое разрешение конфликтов, которые можно разрешить автоматически.
    
    Args:
        schedule_plan: План расписания для обработки
        
    Returns:
        Статистика разрешённых конфликтов
    """
    stats = {
        'total_conflicts': 0,
        'auto_resolved': 0,
        'manual_required': 0,
        'failed_to_resolve': 0
    }
    
    # Получаем конфликты для автоматического разрешения
    conflicts = Conflict.objects.filter(
        status='detected',
        conflict_type__auto_resolve=True
    )
    
    if schedule_plan:
        # Фильтруем по плану расписания через события
        event_ids = ScheduledEvent.objects.filter(
            schedule_plan=schedule_plan
        ).values_list('id', flat=True)
        conflicts = conflicts.filter(scheduled_event_id__in=event_ids)
    
    stats['total_conflicts'] = conflicts.count()
    
    resolver = ConflictResolver()
    
    for conflict in conflicts:
        try:
            # Получаем предложения по разрешению
            suggestions = resolver.suggest_solutions(conflict)
            
            # Пытаемся применить первое предложение с высоким приоритетом
            high_priority_suggestions = [s for s in suggestions if s.get('priority') == 'high']
            
            if high_priority_suggestions:
                suggestion = high_priority_suggestions[0]
                if apply_conflict_solution(conflict, suggestion):
                    conflict.status = 'resolved'
                    conflict.resolved_at = timezone.now()
                    conflict.resolution_notes = f"Автоматически разрешено: {suggestion['description']}"
                    conflict.save()
                    stats['auto_resolved'] += 1
                else:
                    stats['failed_to_resolve'] += 1
            else:
                stats['manual_required'] += 1
        
        except Exception as e:
            print(f"Ошибка при автоматическом разрешении конфликта {conflict.id}: {e}")
            stats['failed_to_resolve'] += 1
    
    return stats


def apply_conflict_solution(conflict: Conflict, suggestion: Dict) -> bool:
    """
    Применение предложенного решения конфликта.
    
    Args:
        conflict: Конфликт для разрешения
        suggestion: Предложение по разрешению
        
    Returns:
        True если решение применено успешно
    """
    try:
        if not conflict.scheduled_event_id:
            return False
        
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
                try:
                    new_teacher = Teacher.objects.get(id=new_teacher_id)
                    # Заменяем всех преподавателей на одного нового
                    event.teachers.clear()
                    event.teachers.add(new_teacher)
                    return True
                except Teacher.DoesNotExist:
                    return False
        
        elif action == 'change_room':
            new_room_id = suggestion.get('new_room_id')
            if new_room_id:
                try:
                    new_room = Room.objects.get(id=new_room_id)
                    event.room = new_room
                    event.save()
                    return True
                except Room.DoesNotExist:
                    return False
        
        return False
    
    except Exception as e:
        print(f"Ошибка при применении решения: {e}")
        return False 