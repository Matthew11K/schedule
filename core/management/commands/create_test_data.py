from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import datetime, time
import random

from core.models import Subsidiary, Subject, Level, Course, Teacher, Room
from groups.models import Group, Student, GroupCourse
from schedule.models import SchedulePlan, ScheduledEvent
from rules.models import ConflictType


class Command(BaseCommand):
    help = 'Создает тестовые данные для системы управления расписанием'

    def handle(self, *args, **options):
        self.stdout.write('📊 Создание тестовых данных...')
        
        # Создаем данные в правильном порядке
        subsidiary = self.create_subsidiary()
        subjects = self.create_subjects()
        levels = self.create_levels()
        courses = self.create_courses(subjects, levels)
        teachers = self.create_teachers(subsidiary, subjects)
        rooms = self.create_rooms(subsidiary, subjects)
        groups = self.create_groups(subsidiary, levels)
        group_courses = self.create_group_courses(groups, courses, teachers)
        students = self.create_students(groups)
        schedule_plan = self.create_schedule_plan(subsidiary)
        conflict_types = self.create_conflict_types()
        events = self.create_scheduled_events(schedule_plan, group_courses, teachers, rooms)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Успешно создано:\n'
                f'   📚 Предметов: {len(subjects)}\n'
                f'   🎯 Ступеней: {len(levels)}\n'
                f'   📖 Курсов: {len(courses)}\n'
                f'   👩‍🏫 Учителей: {len(teachers)}\n'
                f'   🏫 Кабинетов: {len(rooms)}\n'
                f'   👥 Групп: {len(groups)}\n'
                f'   👨‍🎓 Студентов: {len(students)}\n'
                f'   📅 События: {len(events)}\n'
                f'   ⚠️ Типов конфликтов: {len(conflict_types)}'
            )
        )

    def create_subsidiary(self):
        subsidiary, created = Subsidiary.objects.get_or_create(
            name='Основной филиал',
            defaults={'short_name': 'Центр', 'address': 'ул. Образования, д. 1'}
        )
        return subsidiary

    def create_subjects(self):
        subjects_data = [
            ('Математика', 'MATH'), ('Русский язык', 'RUS'), ('Английский язык', 'ENG'), 
            ('Физика', 'PHYS'), ('Химия', 'CHEM'), ('Биология', 'BIO'), 
            ('История', 'HIST'), ('География', 'GEO'), ('Физическая культура', 'PE'), 
            ('Информатика', 'IT')
        ]
        subjects = []
        subsidiary = Subsidiary.objects.first()
        for name, code in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=name, 
                subsidiary=subsidiary,
                defaults={
                    'description': f'Курс {name.lower()}', 
                    'short_name': name[:10],
                    'code': code
                }
            )
            subjects.append(subject)
        return subjects

    def create_levels(self):
        levels = []
        subsidiary = Subsidiary.objects.first()
        for i in range(5, 10):  # 5-9 классы
            level, created = Level.objects.get_or_create(
                name=f'{i} класс', 
                subsidiary=subsidiary,
                defaults={
                    'description': f'Ступень {i} класса',
                    'short_name': f'{i}кл',
                    'order': i
                }
            )
            levels.append(level)
        return levels

    def create_courses(self, subjects, levels):
        courses = []
        for subject in subjects:
            for level in levels:
                course, created = Course.objects.get_or_create(
                    subject=subject, level=level,
                    defaults={'name': f'{subject.name} {level.name}', 'hours_per_week': random.randint(2, 4)}
                )
                courses.append(course)
        return courses

    def create_teachers(self, subsidiary, subjects):
        teachers_data = [
            ('Иванов', 'Иван', ['Математика']),
            ('Петрова', 'Мария', ['Русский язык']),
            ('Сидоров', 'Петр', ['Физика']),
            ('Козлова', 'Анна', ['Английский язык']),
            ('Морозов', 'Алексей', ['История']),
            ('Волкова', 'Елена', ['Биология', 'Химия']),
            ('Соколов', 'Михаил', ['География']),
            ('Новиков', 'Сергей', ['Физическая культура']),
            ('Федорова', 'Наталья', ['Информатика'])
        ]
        
        teachers = []
        for last_name, first_name, subject_names in teachers_data:
            username = f'{last_name.lower()}.{first_name[0].lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first_name, 'last_name': last_name, 'email': f'{username}@school.ru'}
            )
            
            teacher, created = Teacher.objects.get_or_create(
                user=user,
                defaults={'subsidiary': subsidiary, 'employee_id': f'T{len(teachers) + 1:03d}', 'max_hours_per_week': 25}
            )
            
            if created:
                for subject_name in subject_names:
                    try:
                        subject = Subject.objects.get(name=subject_name)
                        teacher.subjects.add(subject)
                    except Subject.DoesNotExist:
                        continue
            
            teachers.append(teacher)
        return teachers

    def create_rooms(self, subsidiary, subjects):
        rooms_data = [
            ('101', 30, 'Математика'), ('102', 28, 'Русский язык'), ('103', 25, 'Английский язык'),
            ('201', 30, 'Физика'), ('202', 25, 'Химия'), ('203', 28, 'Биология'),
            ('301', 35, 'История'), ('302', 32, 'География'), ('Спортзал', 50, 'Физическая культура'),
            ('Компьютерный класс', 24, 'Информатика'), ('Актовый зал', 100, None)
        ]
        
        rooms = []
        for name, capacity, subject_name in rooms_data:
            subject = None
            if subject_name:
                try:
                    subject = Subject.objects.get(name=subject_name)
                except Subject.DoesNotExist:
                    pass
            
            room, created = Room.objects.get_or_create(
                name=name, subsidiary=subsidiary,
                defaults={'capacity': capacity, 'subject': subject}
            )
            rooms.append(room)
        return rooms

    def create_groups(self, subsidiary, levels):
        groups = []
        for level in levels:
            for letter in ['А', 'Б']:
                group, created = Group.objects.get_or_create(
                    name=f'{level.name[0]}{letter}', subsidiary=subsidiary, level=level,
                    defaults={'max_students': 28}
                )
                groups.append(group)
        return groups

    def create_group_courses(self, groups, courses, teachers):
        group_courses = []
        for group in groups:
            level_courses = [c for c in courses if c.level == group.level]
            for course in level_courses:
                suitable_teachers = [t for t in teachers if course.subject in t.subjects.all()]
                if suitable_teachers:
                    teacher = random.choice(suitable_teachers)
                    group_course, created = GroupCourse.objects.get_or_create(
                        group=group, course=course, teacher=teacher,
                        defaults={'academic_hours': course.hours_per_week * 36, 'is_active': True}
                    )
                    group_courses.append(group_course)
        return group_courses

    def create_students(self, groups):
        students = []
        names = ['Александр Иванов', 'Мария Петрова', 'Максим Сидоров', 'Анна Козлова', 'Дмитрий Морозов']
        for group in groups:
            for i, name in enumerate(names):
                first_name, last_name = name.split()
                student, created = Student.objects.get_or_create(
                    student_id=f'S{group.level.sort_order}{group.name[-1]}{i+1:02d}',
                    defaults={'first_name': first_name, 'last_name': last_name, 
                             'date_of_birth': datetime(2010 + group.level.sort_order, 1, 1).date(),
                             'enrollment_date': datetime(2024, 9, 1).date()}
                )
                if created:
                    student.groups.add(group)
                students.append(student)
        return students

    def create_schedule_plan(self, subsidiary):
        plan, created = SchedulePlan.objects.get_or_create(
            name='Основное расписание 2024-2025', subsidiary=subsidiary,
            defaults={'description': 'Основной план расписания', 'start_date': datetime(2024, 9, 1).date(),
                     'end_date': datetime(2025, 5, 31).date(), 'is_active': True}
        )
        return plan

    def create_conflict_types(self):
        conflict_types_data = [
            ('teacher_time_conflict', 'Конфликт времени учителя'),
            ('room_double_booking', 'Двойное бронирование кабинета'),
            ('room_capacity_exceeded', 'Превышение вместимости'),
            ('teacher_workload_exceeded', 'Превышение нагрузки учителя'),
        ]
        
        conflict_types = []
        for code, name in conflict_types_data:
            conflict_type, created = ConflictType.objects.get_or_create(
                code=code, defaults={'name': name, 'description': name, 'severity': 'high'}
            )
            conflict_types.append(conflict_type)
        return conflict_types

    def create_scheduled_events(self, schedule_plan, group_courses, teachers, rooms):
        events = []
        weekdays = [0, 1, 2, 3, 4]  # Пн-Пт
        time_slots = [(time(8, 30), time(9, 15)), (time(9, 25), time(10, 10)), (time(10, 30), time(11, 15))]
        
        for group_course in group_courses[:15]:  # Создаем события для первых 15 курсов
            weekday = random.choice(weekdays)
            start_time, end_time = random.choice(time_slots)
            suitable_rooms = [r for r in rooms if r.subject == group_course.course.subject or r.subject is None]
            room = random.choice(suitable_rooms) if suitable_rooms else random.choice(rooms)
            
            event, created = ScheduledEvent.objects.get_or_create(
                schedule_plan=schedule_plan, group_course=group_course, weekday=weekday, start_time=start_time,
                defaults={'end_time': end_time, 'room': room, 'duration_minutes': 45, 'event_type': 'lesson',
                         'topic': f'Урок {group_course.course.subject.name}', 'is_active': True}
            )
            
            if created:
                event.teachers.add(group_course.teacher)
            events.append(event)
        return events
