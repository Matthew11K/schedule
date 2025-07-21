"""
Команда для создания тестовых событий в календаре
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from schedule.models import ScheduledEvent, SchedulePlan
from groups.models import Group, GroupCourse
from core.models import Teacher, Room


class Command(BaseCommand):
    help = 'Создает тестовые события для календаря'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых событий...')

        # Получаем существующие данные
        group = Group.objects.first()
        group_course = GroupCourse.objects.first()
        teacher = Teacher.objects.first()
        room = Room.objects.first()
        plan = SchedulePlan.objects.first()

        if not all([group, group_course, teacher, room, plan]):
            self.stdout.write(
                self.style.ERROR('Необходимо сначала создать группы, курсы, учителей и кабинеты')
            )
            return

        # Создаем события на эту неделю
        events = [
            {
                'topic': 'Математика - Алгебра',
                'specific_date': date(2025, 7, 21),
                'start_time': time(9, 0),
                'end_time': time(10, 30),
                'duration_minutes': 90,
            },
            {
                'topic': 'Русский язык - Сочинение',
                'specific_date': date(2025, 7, 21),
                'start_time': time(11, 0),
                'end_time': time(12, 30),
                'duration_minutes': 90,
            },
            {
                'topic': 'Физика - Лабораторная работа',
                'specific_date': date(2025, 7, 22),
                'start_time': time(10, 0),
                'end_time': time(12, 0),
                'duration_minutes': 120,
            },
            {
                'topic': 'Химия - Практикум',
                'specific_date': date(2025, 7, 23),
                'start_time': time(9, 30),
                'end_time': time(11, 0),
                'duration_minutes': 90,
            },
            {
                'topic': 'История - Контрольная работа',
                'specific_date': date(2025, 7, 24),
                'start_time': time(11, 0),
                'end_time': time(12, 0),
                'duration_minutes': 60,
            },
            {
                'topic': 'Английский язык - Говорение',
                'specific_date': date(2025, 7, 25),
                'start_time': time(10, 30),
                'end_time': time(12, 0),
                'duration_minutes': 90,
            },
        ]

        created_count = 0
        for event_data in events:
            # Проверяем, не существует ли уже такое событие
            existing = ScheduledEvent.objects.filter(
                specific_date=event_data['specific_date'],
                start_time=event_data['start_time'],
                group=group
            ).first()
            
            if not existing:
                event = ScheduledEvent.objects.create(
                    topic=event_data['topic'],
                    event_type='single',  # Разовое событие
                    specific_date=event_data['specific_date'],
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    duration_minutes=event_data['duration_minutes'],
                    academic_hours=2,
                    group=group,
                    group_course=group_course,
                    room=room,
                    schedule_plan=plan,
                    is_active=True
                )
                # Добавляем преподавателя (ManyToMany)
                event.teachers.add(teacher)
                created_count += 1
                self.stdout.write(f'✅ Создано: {event.topic} - {event.specific_date} {event.start_time}')
            else:
                self.stdout.write(f'⚠️ Уже существует: {event_data["topic"]}')

        self.stdout.write(
            self.style.SUCCESS(f'Создано {created_count} новых событий!')
        ) 