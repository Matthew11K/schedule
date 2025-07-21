"""
Модели для работы с расписанием.

Этот модуль содержит модели для управления планами расписания,
событиями, отменами и фактическими занятиями.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, time

from core.models import Subsidiary, Teacher, Room
from groups.models import Group, GroupCourse, Student


class SchedulePlan(models.Model):
    """План расписания."""
    
    name = models.CharField(
        max_length=200,
        verbose_name='Название плана',
        help_text='Название плана расписания'
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name='schedule_plans',
        verbose_name='Филиал',
        help_text='Филиал, для которого создан план'
    )
    start_date = models.DateField(
        verbose_name='Дата начала',
        help_text='Дата начала действия плана'
    )
    end_date = models.DateField(
        verbose_name='Дата окончания',
        help_text='Дата окончания действия плана'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание плана расписания'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='План активен и используется'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлён'
    )
    
    class Meta:
        verbose_name = 'План расписания'
        verbose_name_plural = 'Планы расписания'
        ordering = ['-start_date', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.subsidiary.short_name})"
    
    def clean(self):
        """Валидация модели."""
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('Дата начала должна быть меньше даты окончания')
    
    @property
    def duration_days(self):
        """Длительность плана в днях."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0
    
    @property
    def is_current(self):
        """Проверка, является ли план текущим."""
        from datetime import date
        today = date.today()
        return self.start_date <= today <= self.end_date if self.start_date and self.end_date else False


class ScheduledEvent(models.Model):
    """Запланированное событие в расписании."""
    
    EVENT_TYPE_CHOICES = [
        ('weekly', 'Еженедельное'),
        ('single', 'Разовое'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]
    
    schedule_plan = models.ForeignKey(
        SchedulePlan,
        on_delete=models.CASCADE,
        related_name='scheduled_events',
        verbose_name='План расписания',
        help_text='План расписания, к которому относится событие'
    )
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='scheduled_events',
        verbose_name='Группа',
        help_text='Группа, участвующая в событии'
    )
    group_course = models.ForeignKey(
        GroupCourse,
        on_delete=models.CASCADE,
        related_name='scheduled_events',
        verbose_name='Курс группы',
        help_text='Курс группы для события'
    )
    teachers = models.ManyToManyField(
        Teacher,
        related_name='scheduled_events',
        verbose_name='Преподаватели',
        help_text='Преподаватели, ведущие событие'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name='scheduled_events',
        verbose_name='Кабинет',
        help_text='Кабинет для проведения события'
    )
    event_type = models.CharField(
        max_length=10,
        choices=EVENT_TYPE_CHOICES,
        default='weekly',
        verbose_name='Тип события',
        help_text='Тип события: еженедельное или разовое'
    )
    
    # Для еженедельных событий
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        null=True,
        blank=True,
        verbose_name='День недели',
        help_text='День недели для еженедельных событий'
    )
    
    # Для разовых событий
    specific_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Конкретная дата',
        help_text='Конкретная дата для разовых событий'
    )
    
    start_time = models.TimeField(
        verbose_name='Время начала',
        help_text='Время начала события'
    )
    end_time = models.TimeField(
        verbose_name='Время окончания',
        help_text='Время окончания события'
    )
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(300)],
        verbose_name='Продолжительность (минуты)',
        help_text='Продолжительность события в минутах'
    )
    academic_hours = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Академические часы',
        help_text='Количество академических часов события'
    )
    topic = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Тема занятия',
        help_text='Тема или название занятия'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
        help_text='Дополнительные примечания к событию'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно',
        help_text='Событие активно и будет выполняться'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )
    
    class Meta:
        verbose_name = 'Запланированное событие'
        verbose_name_plural = 'Запланированные события'
        ordering = ['schedule_plan', 'weekday', 'start_time']
    
    def __str__(self):
        event_time = f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        if self.event_type == 'weekly':
            day_name = dict(self.WEEKDAY_CHOICES)[self.weekday] if self.weekday is not None else "?"
            return f"{self.group_course} - {day_name} {event_time}"
        else:
            date_str = self.specific_date.strftime('%d.%m.%Y') if self.specific_date else "?"
            return f"{self.group_course} - {date_str} {event_time}"
    
    def clean(self):
        """Валидация модели."""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Время начала должно быть меньше времени окончания')
        
        if self.event_type == 'weekly' and self.weekday is None:
            raise ValidationError('Для еженедельных событий обязательно указание дня недели')
        
        if self.event_type == 'single' and self.specific_date is None:
            raise ValidationError('Для разовых событий обязательно указание конкретной даты')
        
        # Проверка взаимоисключающих полей
        if self.weekday is not None and self.specific_date is not None:
            raise ValidationError('Нельзя одновременно указывать день недели и конкретную дату')
        
        if self.event_type == 'weekly' and self.specific_date is not None:
            raise ValidationError('Для еженедельных событий нельзя указывать конкретную дату')
        
        if self.event_type == 'single' and self.weekday is not None:
            raise ValidationError('Для разовых событий нельзя указывать день недели')
        
        # Проверка соответствия группы и курса группы
        if self.group_course and self.group and self.group_course.group != self.group:
            raise ValidationError('Группа должна соответствовать группе в курсе группы')
        
        # Проверка продолжительности
        if self.start_time and self.end_time:
            calculated_duration = (
                datetime.combine(datetime.today(), self.end_time) - 
                datetime.combine(datetime.today(), self.start_time)
            ).total_seconds() / 60
            
            if abs(calculated_duration - self.duration_minutes) > 1:  # Разрешаем погрешность в 1 минуту
                raise ValidationError(
                    f'Продолжительность ({self.duration_minutes} мин) не соответствует '
                    f'времени начала и окончания ({calculated_duration:.0f} мин)'
                )
    
    def save(self, *args, **kwargs):
        """Автоматический расчёт продолжительности при сохранении."""
        if self.start_time and self.end_time and not self.duration_minutes:
            duration = (
                datetime.combine(datetime.today(), self.end_time) - 
                datetime.combine(datetime.today(), self.start_time)
            ).total_seconds() / 60
            self.duration_minutes = int(duration)
        
        super().save(*args, **kwargs)


class ScheduledEventCancellation(models.Model):
    """Отмена запланированного события."""
    
    CANCELLATION_TYPE_CHOICES = [
        ('single', 'Разовая отмена'),
        ('period', 'Отмена на период'),
        ('permanent', 'Постоянная отмена'),
    ]
    
    scheduled_event = models.ForeignKey(
        ScheduledEvent,
        on_delete=models.CASCADE,
        related_name='cancellations',
        verbose_name='Запланированное событие',
        help_text='Событие, которое отменяется'
    )
    cancellation_type = models.CharField(
        max_length=10,
        choices=CANCELLATION_TYPE_CHOICES,
        default='single',
        verbose_name='Тип отмены',
        help_text='Тип отмены события'
    )
    
    # Для разовой отмены
    cancellation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата отмены',
        help_text='Конкретная дата отмены для разового события'
    )
    
    # Для отмены на период
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата начала отмены',
        help_text='Дата начала периода отмены'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания отмены',
        help_text='Дата окончания периода отмены'
    )
    
    reason = models.CharField(
        max_length=500,
        verbose_name='Причина отмены',
        help_text='Причина отмены события'
    )
    replacement_event = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replaces',
        verbose_name='Замещающее событие',
        help_text='Событие, которое заменяет отменённое'
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        verbose_name='Создано пользователем',
        help_text='Пользователь, создавший отмену'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    
    class Meta:
        verbose_name = 'Отмена события'
        verbose_name_plural = 'Отмены событий'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.cancellation_type == 'single':
            date_str = self.cancellation_date.strftime('%d.%m.%Y') if self.cancellation_date else "?"
            return f"Отмена {self.scheduled_event} на {date_str}"
        elif self.cancellation_type == 'period':
            start_str = self.start_date.strftime('%d.%m.%Y') if self.start_date else "?"
            end_str = self.end_date.strftime('%d.%m.%Y') if self.end_date else "?"
            return f"Отмена {self.scheduled_event} с {start_str} по {end_str}"
        else:
            return f"Постоянная отмена {self.scheduled_event}"
    
    def clean(self):
        """Валидация модели."""
        if self.cancellation_type == 'single' and not self.cancellation_date:
            raise ValidationError('Для разовой отмены обязательно указание даты')
        
        if self.cancellation_type == 'period':
            if not self.start_date or not self.end_date:
                raise ValidationError('Для отмены на период обязательно указание начальной и конечной даты')
            if self.start_date >= self.end_date:
                raise ValidationError('Дата начала должна быть меньше даты окончания')


class Event(models.Model):
    """Состоявшееся событие (фактическое занятие)."""
    
    STATUS_CHOICES = [
        ('completed', 'Проведено'),
        ('cancelled', 'Отменено'),
        ('postponed', 'Перенесено'),
        ('partial', 'Частично проведено'),
    ]
    
    scheduled_event = models.ForeignKey(
        ScheduledEvent,
        on_delete=models.CASCADE,
        related_name='actual_events',
        verbose_name='Запланированное событие',
        help_text='Связанное запланированное событие'
    )
    date = models.DateField(
        verbose_name='Дата проведения',
        help_text='Фактическая дата проведения события'
    )
    start_time = models.TimeField(
        verbose_name='Время начала',
        help_text='Фактическое время начала'
    )
    end_time = models.TimeField(
        verbose_name='Время окончания',
        help_text='Фактическое время окончания'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name='conducted_events',
        verbose_name='Преподаватель',
        help_text='Фактический преподаватель'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name='conducted_events',
        verbose_name='Кабинет',
        help_text='Фактический кабинет'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name='Статус',
        help_text='Статус проведения события'
    )
    topic = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Фактическая тема',
        help_text='Фактическая тема проведённого занятия'
    )
    homework = models.TextField(
        blank=True,
        verbose_name='Домашнее задание',
        help_text='Заданное домашнее задание'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
        help_text='Примечания о проведённом занятии'
    )
    attendance_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество присутствующих',
        help_text='Количество присутствующих студентов'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )
    
    class Meta:
        verbose_name = 'Проведённое событие'
        verbose_name_plural = 'Проведённые события'
        ordering = ['-date', '-start_time']
        unique_together = ['scheduled_event', 'date']
    
    def __str__(self):
        return f"{self.scheduled_event.group_course} - {self.date.strftime('%d.%m.%Y')}"
    
    def clean(self):
        """Валидация модели."""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Время начала должно быть меньше времени окончания')
    
    @property
    def duration_minutes(self):
        """Фактическая продолжительность события в минутах."""
        if self.start_time and self.end_time:
            duration = (
                datetime.combine(datetime.today(), self.end_time) - 
                datetime.combine(datetime.today(), self.start_time)
            ).total_seconds() / 60
            return int(duration)
        return 0
    
    @property
    def group(self):
        """Группа события."""
        return self.scheduled_event.group_course.group
    
    @property
    def course(self):
        """Курс события."""
        return self.scheduled_event.group_course.course


class StudentPresence(models.Model):
    """Присутствие студента на занятии."""
    
    PRESENCE_STATUS_CHOICES = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
        ('early_leave', 'Ушёл раньше'),
        ('excused', 'Отсутствовал по уважительной причине'),
    ]
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='student_presences',
        verbose_name='Событие',
        help_text='Проведённое событие'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='presences',
        verbose_name='Студент',
        help_text='Студент'
    )
    status = models.CharField(
        max_length=15,
        choices=PRESENCE_STATUS_CHOICES,
        default='present',
        verbose_name='Статус присутствия',
        help_text='Статус присутствия студента'
    )
    arrival_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время прихода',
        help_text='Фактическое время прихода (для опоздавших)'
    )
    leave_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время ухода',
        help_text='Фактическое время ухода (для ушедших раньше)'
    )
    excuse_reason = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Причина отсутствия',
        help_text='Причина отсутствия или опоздания'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
        help_text='Дополнительные примечания'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )
    
    class Meta:
        verbose_name = 'Присутствие студента'
        verbose_name_plural = 'Присутствие студентов'
        ordering = ['event', 'student__last_name', 'student__first_name']
        unique_together = ['event', 'student']
    
    def __str__(self):
        status_display = dict(self.PRESENCE_STATUS_CHOICES)[self.status]
        return f"{self.student.short_name} - {status_display}"
    
    @property
    def is_present(self):
        """Проверка, присутствовал ли студент."""
        return self.status in ['present', 'late', 'early_leave']
    
    @property
    def is_late(self):
        """Проверка, опоздал ли студент."""
        return self.status == 'late' and self.arrival_time and self.arrival_time > self.event.start_time
