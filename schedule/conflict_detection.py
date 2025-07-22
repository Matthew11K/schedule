"""
Алгоритмы обнаружения конфликтов в расписании.

Этот модуль содержит алгоритмы для обнаружения различных типов конфликтов
в расписании занятий, включая конфликты преподавателей, кабинетов,
превышение нагрузки и нарушение правил работы.
"""

from datetime import datetime, date, time, timedelta
from typing import List, Dict, Tuple, Optional, Set
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import ScheduledEvent, Event, StudentPresence
from core.models import Teacher, Room
from groups.models import GroupCourse, Student
from rules.models import (
    WorkingPeriodRule, TeacherAvailabilityPeriod, 
    RoomAvailabilityRule, ConflictType, Conflict
)


class ConflictDetector:
    """Главный класс для обнаружения конфликтов в расписании."""
    
    def __init__(self):
        """Инициализация детектора конфликтов."""
        self.detected_conflicts = []
    
    def detect_all_conflicts(self, schedule_plan=None) -> List[Dict]:
        """
        Обнаружение всех типов конфликтов в расписании.
        
        Args:
            schedule_plan: План расписания для проверки (если None, проверяются все)
            
        Returns:
            Список обнаруженных конфликтов
        """
        self.detected_conflicts = []
        
        # Получаем события для проверки
        events = ScheduledEvent.objects.filter(is_active=True)
        if schedule_plan:
            events = events.filter(schedule_plan=schedule_plan)
        
        # Запускаем все проверки
        for event in events:
            self._check_teacher_conflicts(event)
            self._check_room_conflicts(event)
            self._check_teacher_availability(event)
            self._check_room_availability(event)
            self._check_working_hours(event)
            self._check_teacher_workload(event)
            self._check_room_capacity(event)
        
        return self.detected_conflicts
    
    def _check_teacher_conflicts(self, event: ScheduledEvent):
        """Проверка конфликтов преподавателя по времени."""
        # Получаем всех преподавателей события
        event_teachers = event.teachers.all()
        
        for teacher in event_teachers:
            # Получаем все события с тем же преподавателем
            conflicting_events = ScheduledEvent.objects.filter(
                teachers=teacher,
                is_active=True
            ).exclude(id=event.id if event.id else 0)
            
            for other_event in conflicting_events:
                if self._events_overlap(event, other_event):
                    conflict = {
                        'type': 'teacher_time_conflict',
                        'severity': 'critical',
                        'event_id': event.id,
                        'description': (
                            f'Преподаватель {teacher.full_name} занят в другом месте: '
                            f'{other_event.group_course} в {other_event.room}'
                        ),
                        'conflicting_event_id': other_event.id,
                        'blocking': True
                    }
                    self.detected_conflicts.append(conflict)
    
    def _check_room_conflicts(self, event: ScheduledEvent):
        """Проверка конфликтов кабинета по времени."""
        # Получаем все события в том же кабинете
        conflicting_events = ScheduledEvent.objects.filter(
            room=event.room,
            is_active=True
        ).exclude(id=event.id if event.id else 0)
        
        for other_event in conflicting_events:
            if self._events_overlap(event, other_event):
                conflict = {
                    'type': 'room_time_conflict',
                    'severity': 'critical',
                    'event_id': event.id,
                    'description': (
                        f'Кабинет {event.room} занят другой группой: '
                        f'{other_event.group_course} с {", ".join([t.full_name for t in other_event.teachers.all()])}'
                    ),
                    'conflicting_event_id': other_event.id,
                    'blocking': True
                }
                self.detected_conflicts.append(conflict)
    
    def _check_teacher_availability(self, event: ScheduledEvent):
        """Проверка доступности преподавателя."""
        # Проверяем доступность для каждого преподавателя
        event_teachers = event.teachers.all()
        
        for teacher in event_teachers:
            availability_periods = TeacherAvailabilityPeriod.objects.filter(
                teacher=teacher,
                is_active=True
            )
            
            is_available = False
            for period in availability_periods:
                if self._event_in_availability_period(event, period):
                    if period.availability_type == 'available':
                        is_available = True
                    elif period.availability_type == 'unavailable':
                        conflict = {
                            'type': 'teacher_unavailable',
                            'severity': 'high',
                            'event_id': event.id,
                            'description': (
                                f'Преподаватель {teacher.full_name} недоступен в это время: '
                                f'{period.notes or "Нет уточнений"}'
                            ),
                            'blocking': False
                        }
                        self.detected_conflicts.append(conflict)
                        break  # Прерываем проверку для этого учителя
            
            if not is_available and availability_periods.exists():
                conflict = {
                    'type': 'teacher_not_in_schedule',
                    'severity': 'medium',
                    'event_id': event.id,
                    'description': (
                        f'Время события не входит в график работы преподавателя {teacher.full_name}'
                    ),
                    'blocking': False
                }
                self.detected_conflicts.append(conflict)
    
    def _check_room_availability(self, event: ScheduledEvent):
        """Проверка доступности кабинета."""
        availability_rules = RoomAvailabilityRule.objects.filter(
            room=event.room,
            is_active=True
        )
        
        for rule in availability_rules:
            if self._event_in_room_rule_period(event, rule):
                if not rule.is_available:
                    conflict = {
                        'type': 'room_unavailable',
                        'severity': 'high',
                        'event_id': event.id,
                        'description': (
                            f'Кабинет {event.room} недоступен: '
                            f'{rule.reason or "Нет уточнений"}'
                        ),
                        'blocking': True
                    }
                    self.detected_conflicts.append(conflict)
    
    def _check_working_hours(self, event: ScheduledEvent):
        """Проверка соответствия рабочему времени."""
        working_rules = WorkingPeriodRule.objects.filter(
            Q(subsidiary=event.schedule_plan.subsidiary) | Q(subsidiary=None),
            is_active=True
        ).order_by('-priority')
        
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
                        'description': (
                            f'Событие запланировано на нерабочее время: {rule.name}'
                        ),
                        'blocking': False
                    }
                    self.detected_conflicts.append(conflict)
                    return
        
        if not is_working_time:
            conflict = {
                'type': 'outside_working_hours',
                'severity': 'medium',
                'event_id': event.id,
                'description': 'Событие запланировано вне рабочих часов',
                'blocking': False
            }
            self.detected_conflicts.append(conflict)
    
    def _check_teacher_workload(self, event: ScheduledEvent):
        """Проверка превышения нагрузки преподавателя."""
        # Проверяем нагрузку для каждого преподавателя
        event_teachers = event.teachers.all()
        
        for teacher in event_teachers:
            # Проверяем недельную нагрузку
            week_start = self._get_week_start_for_event(event)
            week_end = week_start + timedelta(days=6)
            
            weekly_events = ScheduledEvent.objects.filter(
                teachers=teacher,
                schedule_plan=event.schedule_plan,
                is_active=True
            )
            
            # Считаем часы за неделю
            total_weekly_hours = 0
            for weekly_event in weekly_events:
                if self._event_in_date_range(weekly_event, week_start, week_end):
                    total_weekly_hours += weekly_event.duration_minutes / 60
            
            if teacher.max_hours_per_week and total_weekly_hours > teacher.max_hours_per_week:
                conflict = {
                    'type': 'teacher_workload_exceeded',
                    'severity': 'high',
                    'event_id': event.id,
                    'description': (
                        f'Превышена недельная нагрузка преподавателя {teacher.full_name}: '
                        f'{total_weekly_hours:.1f} часов (макс. {teacher.max_hours_per_week})'
                    ),
                    'blocking': False
                }
                self.detected_conflicts.append(conflict)
            
            # Проверяем дневную нагрузку через периоды доступности
            availability_periods = TeacherAvailabilityPeriod.objects.filter(
                teacher=teacher,
                max_hours_per_day__isnull=False,
                is_active=True
            )
        
        for period in availability_periods:
            if self._event_in_availability_period(event, period):
                daily_hours = self._calculate_daily_hours(teacher, event, period)
                if daily_hours > period.max_hours_per_day:
                    conflict = {
                        'type': 'teacher_daily_workload_exceeded',
                        'severity': 'medium',
                        'event_id': event.id,
                        'description': (
                            f'Превышена дневная нагрузка преподавателя {teacher}: '
                            f'{daily_hours:.1f} часов (макс. {period.max_hours_per_day})'
                        ),
                        'blocking': False
                    }
                    self.detected_conflicts.append(conflict)
    
    def _check_room_capacity(self, event: ScheduledEvent):
        """Проверка вместимости кабинета."""
        room = event.room
        group = event.group_course.group
        
        # Подсчитываем активных студентов в группе
        active_students = Student.objects.filter(
            groups=group,
            is_active=True
        ).count()
        
        if room.capacity and active_students > room.capacity:
            conflict = {
                'type': 'room_capacity_exceeded',
                'severity': 'medium',
                'event_id': event.id,
                'description': (
                    f'Превышена вместимость кабинета {room}: '
                    f'{active_students} студентов (макс. {room.capacity})'
                ),
                'blocking': False
            }
            self.detected_conflicts.append(conflict)
    
    def _events_overlap(self, event1: ScheduledEvent, event2: ScheduledEvent) -> bool:
        """Проверка пересечения двух событий по времени."""
        # Если события в разных планах расписания, они не пересекаются
        if event1.schedule_plan != event2.schedule_plan:
            return False
        
        # Проверяем пересечение для еженедельных событий
        if (event1.event_type == 'weekly' and event2.event_type == 'weekly' and
            event1.weekday == event2.weekday):
            return self._time_ranges_overlap(
                event1.start_time, event1.end_time,
                event2.start_time, event2.end_time
            )
        
        # Проверяем пересечение для разовых событий
        if (event1.event_type == 'single' and event2.event_type == 'single' and
            event1.specific_date == event2.specific_date):
            return self._time_ranges_overlap(
                event1.start_time, event1.end_time,
                event2.start_time, event2.end_time
            )
        
        # Проверяем пересечение разового события с еженедельным
        if event1.event_type == 'single' and event2.event_type == 'weekly':
            if event1.specific_date.weekday() == event2.weekday:
                return self._time_ranges_overlap(
                    event1.start_time, event1.end_time,
                    event2.start_time, event2.end_time
                )
        
        if event1.event_type == 'weekly' and event2.event_type == 'single':
            if event2.specific_date.weekday() == event1.weekday:
                return self._time_ranges_overlap(
                    event1.start_time, event1.end_time,
                    event2.start_time, event2.end_time
                )
        
        return False
    
    def _time_ranges_overlap(self, start1: time, end1: time, start2: time, end2: time) -> bool:
        """Проверка пересечения временных интервалов."""
        return start1 < end2 and start2 < end1
    
    def _event_in_availability_period(self, event: ScheduledEvent, period: TeacherAvailabilityPeriod) -> bool:
        """Проверка попадания события в период доступности учителя."""
        # Проверяем даты
        event_date = self._get_event_date_for_check(event)
        if event_date < period.start_date:
            return False
        if period.end_date and event_date > period.end_date:
            return False
        
        # Проверяем день недели
        if period.weekdays:
            allowed_weekdays = [int(d.strip()) for d in period.weekdays.split(',') if d.strip().isdigit()]
            if event_date.weekday() not in allowed_weekdays:
                return False
        
        # Проверяем время
        return self._time_ranges_overlap(
            event.start_time, event.end_time,
            period.start_time, period.end_time
        )
    
    def _event_in_room_rule_period(self, event: ScheduledEvent, rule: RoomAvailabilityRule) -> bool:
        """Проверка попадания события в период правила кабинета."""
        # Проверяем даты
        event_date = self._get_event_date_for_check(event)
        if event_date < rule.start_date:
            return False
        if rule.end_date and event_date > rule.end_date:
            return False
        
        # Проверяем день недели
        if rule.weekdays:
            allowed_weekdays = [int(d.strip()) for d in rule.weekdays.split(',') if d.strip().isdigit()]
            if event_date.weekday() not in allowed_weekdays:
                return False
        
        # Проверяем время
        return self._time_ranges_overlap(
            event.start_time, event.end_time,
            rule.start_time, rule.end_time
        )
    
    def _event_in_working_rule(self, event: ScheduledEvent, rule: WorkingPeriodRule) -> bool:
        """Проверка попадания события в рабочее правило."""
        # Проверяем даты
        event_date = self._get_event_date_for_check(event)
        
        if rule.recurrence == 'once':
            if event_date < rule.start_date:
                return False
            if rule.end_date and event_date > rule.end_date:
                return False
        elif rule.recurrence == 'weekly':
            if rule.weekdays:
                allowed_weekdays = [int(d.strip()) for d in rule.weekdays.split(',') if d.strip().isdigit()]
                if event_date.weekday() not in allowed_weekdays:
                    return False
        
        # Проверяем время если указано
        if rule.start_time and rule.end_time:
            return self._time_ranges_overlap(
                event.start_time, event.end_time,
                rule.start_time, rule.end_time
            )
        
        return True
    
    def _get_event_date_for_check(self, event: ScheduledEvent) -> date:
        """Получение даты события для проверки."""
        if event.event_type == 'single':
            return event.specific_date
        else:
            # Для еженедельных событий используем дату начала плана
            plan_start = event.schedule_plan.start_date
            # Находим первый день с нужным днем недели
            days_ahead = event.weekday - plan_start.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return plan_start + timedelta(days=days_ahead)
    
    def _get_week_start_for_event(self, event: ScheduledEvent) -> date:
        """Получение начала недели для события."""
        event_date = self._get_event_date_for_check(event)
        days_since_monday = event_date.weekday()
        return event_date - timedelta(days=days_since_monday)
    
    def _event_in_date_range(self, event: ScheduledEvent, start_date: date, end_date: date) -> bool:
        """Проверка попадания события в диапазон дат."""
        event_date = self._get_event_date_for_check(event)
        return start_date <= event_date <= end_date
    
    def _calculate_daily_hours(self, teacher: Teacher, event: ScheduledEvent, period: TeacherAvailabilityPeriod) -> float:
        """Расчёт дневной нагрузки преподавателя."""
        event_date = self._get_event_date_for_check(event)
        
        # Получаем все события учителя в этот день
        daily_events = ScheduledEvent.objects.filter(
            teacher=teacher,
            schedule_plan=event.schedule_plan,
            is_active=True
        )
        
        total_hours = 0
        for daily_event in daily_events:
            if self._get_event_date_for_check(daily_event) == event_date:
                total_hours += daily_event.duration_minutes / 60
        
        return total_hours


def create_conflict_from_detection(conflict_data: Dict) -> Conflict:
    """
    Создание записи конфликта в базе данных из результата обнаружения.
    
    Args:
        conflict_data: Данные обнаруженного конфликта
        
    Returns:
        Созданный объект Conflict
    """
    try:
        conflict_type = ConflictType.objects.get(name__icontains=conflict_data['type'])
    except ConflictType.DoesNotExist:
        # Создаём новый тип конфликта если его нет
        conflict_type = ConflictType.objects.create(
            name=conflict_data['type'],
            description=f"Автоматически созданный тип конфликта: {conflict_data['type']}",
            severity=conflict_data.get('severity', 'medium'),
            is_blocking=conflict_data.get('blocking', False),
            auto_resolve=False
        )
    
    return Conflict.objects.create(
        conflict_type=conflict_type,
        scheduled_event_id=conflict_data.get('event_id'),
        description=conflict_data['description'],
        status='detected'
    )


def detect_and_save_conflicts(schedule_plan=None) -> List[Conflict]:
    """
    Обнаружение конфликтов и сохранение их в базе данных.
    
    Args:
        schedule_plan: План расписания для проверки
        
    Returns:
        Список созданных объектов Conflict
    """
    detector = ConflictDetector()
    detected_conflicts = detector.detect_all_conflicts(schedule_plan)
    
    created_conflicts = []
    for conflict_data in detected_conflicts:
        try:
            conflict = create_conflict_from_detection(conflict_data)
            created_conflicts.append(conflict)
        except Exception as e:
            print(f"Ошибка при создании конфликта: {e}")
    
    return created_conflicts 