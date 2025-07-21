"""
Модели для системы правил и ограничений.

Этот модуль содержит модели для управления правилами работы,
доступности учителей, временными слотами и ограничениями.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import time, date

from core.models import Subsidiary, Teacher, Room


class WorkingPeriodRule(models.Model):
    """Правило рабочего периода."""
    
    RULE_TYPE_CHOICES = [
        ('working_day', 'Рабочий день'),
        ('holiday', 'Праздничный день'),
        ('weekend', 'Выходной день'),
        ('vacation', 'Каникулы'),
        ('special', 'Особый период'),
    ]
    
    RECURRENCE_CHOICES = [
        ('once', 'Однократно'),
        ('daily', 'Ежедневно'),
        ('weekly', 'Еженедельно'),
        ('monthly', 'Ежемесячно'),
        ('yearly', 'Ежегодно'),
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
    
    name = models.CharField(
        max_length=200,
        verbose_name='Название правила',
        help_text='Название правила рабочего периода'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание правила'
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name='working_period_rules',
        null=True,
        blank=True,
        verbose_name='Филиал',
        help_text='Филиал (если не указан, то правило глобальное)'
    )
    rule_type = models.CharField(
        max_length=15,
        choices=RULE_TYPE_CHOICES,
        verbose_name='Тип правила',
        help_text='Тип рабочего периода'
    )
    start_date = models.DateField(
        verbose_name='Дата начала',
        help_text='Дата начала действия правила'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания',
        help_text='Дата окончания действия правила (если не указана, то бессрочно)'
    )
    recurrence = models.CharField(
        max_length=10,
        choices=RECURRENCE_CHOICES,
        default='once',
        verbose_name='Повторение',
        help_text='Тип повторения правила'
    )
    weekdays = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Дни недели',
        help_text='Дни недели для еженедельного повторения (0-6, через запятую)'
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время начала',
        help_text='Время начала рабочего дня (если применимо)'
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время окончания',
        help_text='Время окончания рабочего дня (если применимо)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно',
        help_text='Правило активно и применяется'
    )
    priority = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Приоритет',
        help_text='Приоритет правила (больше число = выше приоритет)'
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
        verbose_name = 'Правило рабочего периода'
        verbose_name_plural = 'Правила рабочих периодов'
        ordering = ['-priority', 'start_date', 'name']
    
    def __str__(self):
        subsidiary_name = self.subsidiary.short_name if self.subsidiary else "Глобальное"
        return f"{self.name} ({subsidiary_name})"
    
    def clean(self):
        """Валидация модели."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Дата начала должна быть меньше или равна дате окончания')
        
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Время начала должно быть меньше времени окончания')
        
        if self.recurrence == 'weekly' and not self.weekdays:
            raise ValidationError('Для еженедельного повторения необходимо указать дни недели')
    
    @property
    def weekdays_list(self):
        """Список дней недели для повторения."""
        if self.weekdays:
            try:
                return [int(day.strip()) for day in self.weekdays.split(',') if day.strip().isdigit()]
            except ValueError:
                return []
        return []
    
    @property
    def duration_hours(self):
        """Продолжительность рабочего дня в часах."""
        if self.start_time and self.end_time:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            return (end - start).total_seconds() / 3600
        return 0


class TeacherAvailabilityPeriod(models.Model):
    """Период доступности учителя."""
    
    AVAILABILITY_TYPE_CHOICES = [
        ('available', 'Доступен'),
        ('unavailable', 'Недоступен'),
        ('preferred', 'Предпочтительное время'),
        ('limited', 'Ограниченная доступность'),
    ]
    
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='availability_periods',
        verbose_name='Учитель',
        help_text='Учитель'
    )
    availability_type = models.CharField(
        max_length=15,
        choices=AVAILABILITY_TYPE_CHOICES,
        verbose_name='Тип доступности',
        help_text='Тип доступности учителя'
    )
    start_date = models.DateField(
        verbose_name='Дата начала',
        help_text='Дата начала периода'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания',
        help_text='Дата окончания периода (если не указана, то постоянно)'
    )
    start_time = models.TimeField(
        verbose_name='Время начала',
        help_text='Время начала доступности в день'
    )
    end_time = models.TimeField(
        verbose_name='Время окончания',
        help_text='Время окончания доступности в день'
    )
    weekdays = models.CharField(
        max_length=20,
        verbose_name='Дни недели',
        help_text='Дни недели (0-6, через запятую). Пустое значение = все дни'
    )
    max_hours_per_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name='Максимум часов в день',
        help_text='Максимальное количество рабочих часов в день'
    )
    max_hours_per_week = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(168)],
        verbose_name='Максимум часов в неделю',
        help_text='Максимальное количество рабочих часов в неделю'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
        help_text='Дополнительные примечания'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Период активен'
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
        verbose_name = 'Период доступности учителя'
        verbose_name_plural = 'Периоды доступности учителей'
        ordering = ['teacher', 'start_date', 'start_time']
    
    def __str__(self):
        period = f"{self.start_date}"
        if self.end_date:
            period += f" - {self.end_date}"
        time_range = f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        return f"{self.teacher.short_name}: {period} {time_range}"
    
    def clean(self):
        """Валидация модели."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Дата начала должна быть меньше или равна дате окончания')
        
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Время начала должно быть меньше времени окончания')
    
    @property
    def weekdays_list(self):
        """Список дней недели."""
        if self.weekdays:
            try:
                return [int(day.strip()) for day in self.weekdays.split(',') if day.strip().isdigit()]
            except ValueError:
                return []
        return list(range(7))  # Все дни недели, если не указано
    
    @property
    def daily_duration_hours(self):
        """Продолжительность доступности в день."""
        if self.start_time and self.end_time:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            return (end - start).total_seconds() / 3600
        return 0


class TimeSlot(models.Model):
    """Временной слот для занятий."""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Название слота',
        help_text='Название временного слота'
    )
    start_time = models.TimeField(
        verbose_name='Время начала',
        help_text='Время начала слота'
    )
    end_time = models.TimeField(
        verbose_name='Время окончания',
        help_text='Время окончания слота'
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name='time_slots',
        null=True,
        blank=True,
        verbose_name='Филиал',
        help_text='Филиал (если не указан, то слот глобальный)'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок',
        help_text='Порядок отображения слота'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Слот активен и может использоваться'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    
    class Meta:
        verbose_name = 'Временной слот'
        verbose_name_plural = 'Временные слоты'
        ordering = ['subsidiary', 'order', 'start_time']
        unique_together = ['start_time', 'end_time', 'subsidiary']
    
    def __str__(self):
        time_range = f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        subsidiary_name = self.subsidiary.short_name if self.subsidiary else "Глобальный"
        return f"{self.name} ({time_range}) - {subsidiary_name}"
    
    def clean(self):
        """Валидация модели."""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Время начала должно быть меньше времени окончания')
    
    @property
    def duration_minutes(self):
        """Продолжительность слота в минутах."""
        if self.start_time and self.end_time:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            return int((end - start).total_seconds() / 60)
        return 0


class RoomAvailabilityRule(models.Model):
    """Правило доступности кабинета."""
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='availability_rules',
        verbose_name='Кабинет',
        help_text='Кабинет'
    )
    start_date = models.DateField(
        verbose_name='Дата начала',
        help_text='Дата начала действия правила'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания',
        help_text='Дата окончания действия правила'
    )
    start_time = models.TimeField(
        verbose_name='Время начала',
        help_text='Время начала доступности кабинета'
    )
    end_time = models.TimeField(
        verbose_name='Время окончания',
        help_text='Время окончания доступности кабинета'
    )
    weekdays = models.CharField(
        max_length=20,
        verbose_name='Дни недели',
        help_text='Дни недели (0-6, через запятую). Пустое значение = все дни'
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name='Доступен',
        help_text='Кабинет доступен в указанное время'
    )
    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Причина',
        help_text='Причина недоступности (если применимо)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно',
        help_text='Правило активно'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    
    class Meta:
        verbose_name = 'Правило доступности кабинета'
        verbose_name_plural = 'Правила доступности кабинетов'
        ordering = ['room', 'start_date', 'start_time']
    
    def __str__(self):
        status = "доступен" if self.is_available else "недоступен"
        period = f"{self.start_date}"
        if self.end_date:
            period += f" - {self.end_date}"
        time_range = f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        return f"{self.room.name} {status}: {period} {time_range}"
    
    def clean(self):
        """Валидация модели."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Дата начала должна быть меньше или равна дате окончания')
        
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Время начала должно быть меньше времени окончания')
    
    @property
    def weekdays_list(self):
        """Список дней недели."""
        if self.weekdays:
            try:
                return [int(day.strip()) for day in self.weekdays.split(',') if day.strip().isdigit()]
            except ValueError:
                return []
        return list(range(7))  # Все дни недели, если не указано


class ConflictType(models.Model):
    """Тип конфликта в расписании."""
    
    SEVERITY_CHOICES = [
        ('low', 'Низкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая'),
        ('critical', 'Критическая'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название типа',
        help_text='Название типа конфликта'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Описание типа конфликта'
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='medium',
        verbose_name='Серьёзность',
        help_text='Уровень серьёзности конфликта'
    )
    is_blocking = models.BooleanField(
        default=False,
        verbose_name='Блокирующий',
        help_text='Конфликт блокирует создание события'
    )
    auto_resolve = models.BooleanField(
        default=False,
        verbose_name='Автоматическое разрешение',
        help_text='Система может автоматически разрешить этот тип конфликта'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Тип конфликта активен'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    
    class Meta:
        verbose_name = 'Тип конфликта'
        verbose_name_plural = 'Типы конфликтов'
        ordering = ['severity', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"


class Conflict(models.Model):
    """Конфликт в расписании."""
    
    STATUS_CHOICES = [
        ('detected', 'Обнаружен'),
        ('acknowledged', 'Принят к сведению'),
        ('in_progress', 'В процессе разрешения'),
        ('resolved', 'Разрешён'),
        ('ignored', 'Игнорирован'),
    ]
    
    conflict_type = models.ForeignKey(
        ConflictType,
        on_delete=models.CASCADE,
        related_name='conflicts',
        verbose_name='Тип конфликта',
        help_text='Тип конфликта'
    )
    # Связь с событием через строку, чтобы избежать циклических импортов
    scheduled_event_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='ID запланированного события',
        help_text='ID запланированного события, с которым связан конфликт'
    )
    description = models.TextField(
        verbose_name='Описание конфликта',
        help_text='Подробное описание конфликта'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='detected',
        verbose_name='Статус',
        help_text='Статус разрешения конфликта'
    )
    detected_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Обнаружен'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Разрешён'
    )
    resolved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_conflicts',
        verbose_name='Разрешён пользователем',
        help_text='Пользователь, разрешивший конфликт'
    )
    resolution_notes = models.TextField(
        blank=True,
        verbose_name='Примечания к разрешению',
        help_text='Примечания о том, как был разрешён конфликт'
    )
    
    class Meta:
        verbose_name = 'Конфликт'
        verbose_name_plural = 'Конфликты'
        ordering = ['-detected_at', 'conflict_type__severity']
    
    def __str__(self):
        return f"{self.conflict_type.name} - {self.get_status_display()}"
    
    @property
    def is_resolved(self):
        """Проверка, разрешён ли конфликт."""
        return self.status in ['resolved', 'ignored']
    
    @property
    def age_hours(self):
        """Возраст конфликта в часах."""
        from django.utils import timezone
        if self.resolved_at:
            return (self.resolved_at - self.detected_at).total_seconds() / 3600
        else:
            return (timezone.now() - self.detected_at).total_seconds() / 3600
