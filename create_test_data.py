#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных для системы управления расписанием
Запуск: python manage.py shell < create_test_data.py
"""

import os
import sys
import django
from datetime import datetime, time, date
import random

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_schedule.settings')
django.setup()

# Импорты моделей
from django.contrib.auth.models import User
from core.models import Subsidiary, Subject, Level, Course, Teacher, Room
from groups.models import Group, Student, GroupCourse  
from schedule.models import SchedulePlan, ScheduledEvent
from rules.models import ConflictType

def clear_data():
    """Очистка существующих данных"""
    print("🗑️  Очистка существующих данных...")
    ScheduledEvent.objects.all().delete()
    GroupCourse.objects.all().delete()
    Student.objects.all().delete()
    Group.objects.all().delete()
    Course.objects.all().delete()
    Teacher.objects.all().delete()
    Room.objects.all().delete()
    Level.objects.all().delete()
    Subject.objects.all().delete()
    SchedulePlan.objects.all().delete()
    ConflictType.objects.all().delete()
    Subsidiary.objects.all().delete()
    print("✅ Данные очищены")

def create_test_data():
    """Создание всех тестовых данных"""
    print("📊 Создание тестовых данных...")
    
    # 1. Филиал
    print("🏢 Создание филиала...")
    subsidiary = Subsidiary.objects.create(
        name='Основная школа',
        short_name='ОШ',
        address='ул. Школьная, 1',
        phone='+7 (495) 123-45-67',
        email='info@school.edu'
    )
    
    # 2. Предметы  
    print("📚 Создание предметов...")
    subjects_data = [
        ('Математика', 'Мат', 'MATH'),
        ('Русский язык', 'Рус', 'RUS'), 
        ('Английский язык', 'Англ', 'ENG'),
        ('Физика', 'Физ', 'PHYS'),
        ('Химия', 'Хим', 'CHEM'),
        ('Биология', 'Био', 'BIO'),
        ('История', 'Ист', 'HIST'),
        ('География', 'Гео', 'GEO'),
        ('Физкультура', 'ФК', 'PE'),
        ('Информатика', 'Инф', 'IT')
    ]
    
    subjects = []
    for name, short, code in subjects_data:
        subject = Subject.objects.create(
            name=name,
            short_name=short,
            code=code,
            subsidiary=subsidiary,
            description=f'Предмет {name}',
            is_active=True
        )
        subjects.append(subject)
    
    # 3. Ступени
    print("🎯 Создание ступеней...")
    levels = []
    for i in range(5, 10):  # 5-9 классы
        level = Level.objects.create(
            name=f'{i} класс',
            short_name=f'{i}кл',
            subsidiary=subsidiary,
            order=i,
            description=f'Ступень {i} класса',
            is_active=True
        )
        levels.append(level)
    
    # 4. Курсы
    print("📖 Создание курсов...")
    courses = []
    for subject in subjects:
        for level in levels:
            # Не все предметы для всех классов
            if (subject.code == 'PHYS' and level.order < 7) or \
               (subject.code == 'CHEM' and level.order < 8):
                continue
                
            course = Course.objects.create(
                subject=subject,
                level=level,
                name=f'{subject.name} {level.name}',
                description=f'Курс {subject.name} для {level.name}',
                duration_hours=random.randint(60, 120),
                weekly_hours=random.randint(2, 4),
                is_active=True
            )
            courses.append(course)
    
    # 5. Кабинеты
    print("🏫 Создание кабинетов...")
    rooms_data = [
        ('101', 30, 'Математика'),
        ('102', 28, 'Русский язык'),
        ('103', 25, 'Английский язык'), 
        ('201', 32, 'Физика'),
        ('202', 25, 'Химия'),
        ('203', 30, 'Биология'),
        ('301', 35, 'История'),
        ('302', 32, 'География'),
        ('Спортзал', 50, 'Физкультура'),
        ('Компьютерный класс', 24, 'Информатика'),
        ('Актовый зал', 100, None)
    ]
    
    rooms = []
    for name, capacity, subject_name in rooms_data:
        subject = None
        if subject_name:
            subject = next((s for s in subjects if s.name == subject_name), None)
            
        room = Room.objects.create(
            name=name,
            subsidiary=subsidiary,
            capacity=capacity,
            subject=subject,
            description=f'Кабинет {name}',
            is_active=True
        )
        rooms.append(room)
    
    # 6. Учителя
    print("👩‍🏫 Создание учителей...")
    teachers_data = [
        ('Иванова', 'Анна', 'Петровна', ['Математика']),
        ('Петров', 'Сергей', 'Иванович', ['Русский язык']),
        ('Сидорова', 'Мария', 'Александровна', ['Английский язык']),
        ('Козлов', 'Дмитрий', 'Николаевич', ['Физика']),
        ('Морозова', 'Елена', 'Викторовна', ['Химия', 'Биология']),
        ('Волков', 'Алексей', 'Сергеевич', ['История']),
        ('Соколова', 'Ольга', 'Дмитриевна', ['География']),
        ('Новиков', 'Иван', 'Петрович', ['Физкультура']),
        ('Федорова', 'Наталья', 'Александровна', ['Информатика'])
    ]
    
    teachers = []
    for last_name, first_name, middle_name, subject_names in teachers_data:
        # Создаем пользователя
        username = f'{last_name.lower()}.{first_name[0].lower()}'
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=f'{username}@school.edu',
            password='password123'
        )
        
        # Создаем учителя
        teacher = Teacher.objects.create(
            user=user,
            subsidiary=subsidiary,
            employee_id=f'T{len(teachers) + 1:03d}',
            phone=f'+7 (495) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
            max_hours_per_week=random.randint(18, 25),
            is_active=True
        )
        
        # Привязываем предметы
        for subject_name in subject_names:
            subject = next((s for s in subjects if s.name == subject_name), None)
            if subject:
                teacher.subjects.add(subject)
        
        teachers.append(teacher)
    
    # 7. Группы
    print("👥 Создание групп...")
    groups = []
    for level in levels:
        for letter in ['А', 'Б']:
            group = Group.objects.create(
                name=f'{level.order}{letter}',
                subsidiary=subsidiary,
                level=level,
                max_students=random.randint(25, 30),
                start_date=date(2024, 9, 1),
                end_date=date(2025, 5, 31),
                description=f'Класс {level.order}{letter}',
                is_active=True
            )
            groups.append(group)
    
    # 8. Студенты
    print("👨‍🎓 Создание студентов...")
    first_names = ['Александр', 'Максим', 'Артём', 'Михаил', 'Даниил', 'Дмитрий',
                   'Анна', 'Мария', 'Полина', 'Елизавета', 'Екатерина', 'Виктория']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Козлов', 'Морозов', 'Волков',
                  'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Соколов', 'Михайлов']
    
    students = []
    for group in groups:
        num_students = random.randint(20, group.max_students)
        for i in range(num_students):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            student = Student.objects.create(
                student_id=f'S{group.level.order}{group.name[-1]}{i+1:02d}',
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date(2010 + group.level.order, random.randint(1, 12), random.randint(1, 28)),
                enrollment_date=date(2024, 9, 1),
                is_active=True
            )
            student.groups.add(group)
            students.append(student)
    
    # 9. Курсы групп
    print("📝 Создание курсов групп...")
    group_courses = []
    for group in groups:
        level_courses = [c for c in courses if c.level == group.level]
        for course in level_courses:
            # Находим подходящего учителя
            suitable_teachers = [t for t in teachers if course.subject in t.subjects.all()]
            if suitable_teachers:
                teacher = random.choice(suitable_teachers)
                
                group_course = GroupCourse.objects.create(
                    group=group,
                    course=course,
                    teacher=teacher,
                    academic_hours=course.duration_hours,
                    start_date=date(2024, 9, 1),
                    end_date=date(2025, 5, 31),
                    is_active=True
                )
                group_courses.append(group_course)
    
    # 10. План расписания
    print("📅 Создание плана расписания...")
    schedule_plan = SchedulePlan.objects.create(
        name='Основное расписание 2024-2025',
        subsidiary=subsidiary,
        description='Основной план расписания на учебный год',
        start_date=date(2024, 9, 1),
        end_date=date(2025, 5, 31),
        is_active=True
    )
    
    # 11. Типы конфликтов
    print("⚠️ Создание типов конфликтов...")
    conflict_types_data = [
        ('teacher_time_conflict', 'Конфликт времени учителя', 'high'),
        ('room_double_booking', 'Двойное бронирование кабинета', 'high'),
        ('room_capacity_exceeded', 'Превышение вместимости кабинета', 'medium'),
        ('teacher_workload_exceeded', 'Превышение нагрузки учителя', 'low'),
    ]
    
    conflict_types = []
    for code, name, severity in conflict_types_data:
        conflict_type = ConflictType.objects.create(
            code=code,
            name=name,
            description=name,
            severity=severity,
            is_active=True
        )
        conflict_types.append(conflict_type)
    
    # 12. События расписания
    print("📆 Создание событий расписания...")
    weekdays = [0, 1, 2, 3, 4]  # Пн-Пт
    time_slots = [
        (time(8, 30), time(9, 15)),
        (time(9, 25), time(10, 10)),
        (time(10, 30), time(11, 15)),
        (time(11, 25), time(12, 10)),
        (time(12, 30), time(13, 15)),
        (time(13, 25), time(14, 10))
    ]
    
    events = []
    created_events = 0
    for group_course in group_courses[:30]:  # Первые 30 курсов групп
        # Создаем 2-3 урока в неделю
        lessons_per_week = min(3, group_course.course.weekly_hours)
        used_slots = set()
        
        for _ in range(lessons_per_week):
            # Избегаем конфликтов времени
            attempts = 0
            while attempts < 10:
                weekday = random.choice(weekdays)
                start_time, end_time = random.choice(time_slots)
                slot_key = (weekday, start_time)
                
                if slot_key not in used_slots:
                    used_slots.add(slot_key)
                    break
                attempts += 1
            
            if attempts >= 10:
                continue  # Пропускаем если не нашли свободный слот
            
            # Находим подходящий кабинет
            suitable_rooms = [r for r in rooms 
                            if r.subject == group_course.course.subject or r.subject is None]
            room = random.choice(suitable_rooms) if suitable_rooms else random.choice(rooms)
            
            event = ScheduledEvent.objects.create(
                schedule_plan=schedule_plan,
                group_course=group_course,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time,
                room=room,
                duration_minutes=45,
                event_type='lesson',
                topic=f'Урок {group_course.course.subject.name}',
                is_active=True
            )
            
            # Добавляем учителя
            event.teachers.add(group_course.teacher)
            events.append(event)
            created_events += 1
    
    # Финальная статистика
    print("\n" + "="*50)
    print("✅ ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ!")
    print("="*50)
    print(f"🏢 Филиалов: {Subsidiary.objects.count()}")
    print(f"📚 Предметов: {Subject.objects.count()}")
    print(f"🎯 Ступеней: {Level.objects.count()}")
    print(f"📖 Курсов: {Course.objects.count()}")
    print(f"👩‍🏫 Учителей: {Teacher.objects.count()}")
    print(f"🏫 Кабинетов: {Room.objects.count()}")
    print(f"👥 Групп: {Group.objects.count()}")
    print(f"👨‍🎓 Студентов: {Student.objects.count()}")
    print(f"📝 Курсов групп: {GroupCourse.objects.count()}")
    print(f"📅 Планов расписания: {SchedulePlan.objects.count()}")
    print(f"📆 Событий: {ScheduledEvent.objects.count()}")
    print(f"⚠️ Типов конфликтов: {ConflictType.objects.count()}")
    print("="*50)
    print("🎯 Теперь можно тестировать систему!")
    print("🌐 Откройте: http://localhost:8000/dashboard/")
    print("🔧 Админка: http://localhost:8000/admin/ (admin/admin)")
    print("="*50)

if __name__ == "__main__":
    clear_data()
    create_test_data() 