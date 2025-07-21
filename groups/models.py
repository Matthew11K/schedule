"""
Модели для работы с группами и студентами.

Этот модуль содержит модели для управления группами (классами),
студентами и связями между группами и курсами.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator

from core.models import Subsidiary, Level, Course, Package, Teacher


class Group(models.Model):
    """Группа/класс учащихся."""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Название группы',
        help_text='Название группы или класса'
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='Филиал',
        help_text='Филиал, в котором обучается группа'
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='Ступень',
        help_text='Ступень обучения группы'
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='groups',
        verbose_name='Пакет курсов',
        help_text='Типовой пакет курсов для группы'
    )
    max_students = models.PositiveIntegerField(
        default=25,
        verbose_name='Максимум студентов',
        help_text='Максимальное количество студентов в группе'
    )
    start_date = models.DateField(
        verbose_name='Дата начала обучения',
        help_text='Дата начала обучения группы'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания обучения',
        help_text='Плановая дата окончания обучения'
    )
    curator = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curated_groups',
        verbose_name='Куратор',
        help_text='Куратор группы'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна',
        help_text='Группа активна и обучается'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создана'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлена'
    )
    
    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['subsidiary__name', 'level__order', 'name']
        unique_together = ['subsidiary', 'name']
    
    def __str__(self):
        return f"{self.subsidiary.short_name} - {self.name}"
    
    @property
    def current_students_count(self):
        """Текущее количество студентов в группе."""
        return self.students.filter(is_active=True).count()
    
    @property
    def is_full(self):
        """Проверка, заполнена ли группа."""
        return self.current_students_count >= self.max_students


class GroupCourse(models.Model):
    """Курс, назначенный группе."""
    
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='group_courses',
        verbose_name='Группа',
        help_text='Группа, которая изучает курс'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='group_courses',
        verbose_name='Курс',
        help_text='Изучаемый курс'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name='group_courses',
        verbose_name='Преподаватель',
        help_text='Преподаватель, ведущий курс'
    )
    hours_per_week = models.PositiveIntegerField(
        default=1,
        verbose_name='Часов в неделю',
        help_text='Количество академических часов в неделю'
    )
    total_hours = models.PositiveIntegerField(
        verbose_name='Общее количество часов',
        help_text='Общее количество часов курса для группы'
    )
    start_date = models.DateField(
        verbose_name='Дата начала',
        help_text='Дата начала изучения курса'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания',
        help_text='Плановая дата окончания курса'
    )
    completed_hours = models.PositiveIntegerField(
        default=0,
        verbose_name='Пройдено часов',
        help_text='Количество пройденных часов'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Курс активен для группы'
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
        verbose_name = 'Курс группы'
        verbose_name_plural = 'Курсы групп'
        ordering = ['group', 'course__subject__name', 'course__name']
        unique_together = ['group', 'course']
    
    def __str__(self):
        return f"{self.group.name} - {self.course.name}"
    
    @property
    def progress_percentage(self):
        """Процент выполнения курса."""
        if self.total_hours == 0:
            return 0
        return min(100, (self.completed_hours / self.total_hours) * 100)
    
    @property
    def is_completed(self):
        """Проверка, завершён ли курс."""
        return self.completed_hours >= self.total_hours


class Student(models.Model):
    """Студент/ученик."""
    
    # Валидатор для номера телефона
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Пользователь',
        help_text='Связанный пользователь системы (опционально)'
    )
    student_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Номер студента',
        help_text='Уникальный номер студента'
    )
    first_name = models.CharField(
        max_length=100,
        verbose_name='Имя',
        help_text='Имя студента'
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='Фамилия',
        help_text='Фамилия студента'
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отчество',
        help_text='Отчество студента'
    )
    date_of_birth = models.DateField(
        verbose_name='Дата рождения',
        help_text='Дата рождения студента'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email',
        help_text='Электронная почта студента'
    )
    phone = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        verbose_name='Телефон',
        help_text='Контактный телефон'
    )
    groups = models.ManyToManyField(
        Group,
        related_name='students',
        blank=True,
        verbose_name='Группы',
        help_text='Группы, в которых обучается студент'
    )
    parent_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='ФИО родителя',
        help_text='Полное имя родителя/законного представителя'
    )
    parent_phone = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        verbose_name='Телефон родителя',
        help_text='Контактный телефон родителя'
    )
    parent_email = models.EmailField(
        blank=True,
        verbose_name='Email родителя',
        help_text='Электронная почта родителя'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Адрес',
        help_text='Домашний адрес'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
        help_text='Дополнительные заметки о студенте'
    )
    enrollment_date = models.DateField(
        verbose_name='Дата зачисления',
        help_text='Дата зачисления в школу'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Студент активен и обучается'
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
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
    @property
    def full_name(self):
        """Полное имя студента."""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)
    
    @property
    def short_name(self):
        """Краткое имя студента."""
        return f"{self.last_name} {self.first_name}"
    
    @property
    def age(self):
        """Возраст студента."""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Lesson(models.Model):
    """Урок из календарно-тематического планирования (КТП)."""
    
    order = models.PositiveIntegerField(
        verbose_name='Порядковый номер',
        help_text='Порядковый номер урока в рамках курса группы'
    )
    group_course = models.ForeignKey(
        GroupCourse,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс группы',
        help_text='Курс группы, к которому относится урок'
    )
    event = models.OneToOneField(
        'schedule.Event',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson',
        verbose_name='Проведённое событие',
        help_text='Связанное проведённое событие (когда урок состоялся)'
    )
    title = models.CharField(
        max_length=300,
        verbose_name='Название урока',
        help_text='Название или тема урока'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Подробное описание урока'
    )
    planned_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Планируемая дата',
        help_text='Планируемая дата проведения урока'
    )
    is_conducted = models.BooleanField(
        default=False,
        verbose_name='Проведён',
        help_text='Урок проведён (связан с Event)'
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
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['group_course', 'order']
        unique_together = ['group_course', 'order']
    
    def __str__(self):
        return f"{self.group_course} - Урок #{self.order}: {self.title}"
    
    def save(self, *args, **kwargs):
        """Автоматическое обновление статуса проведения."""
        self.is_conducted = self.event is not None
        super().save(*args, **kwargs)
    
    @property
    def status(self):
        """Статус урока."""
        if self.is_conducted:
            return 'Проведён'
        elif self.planned_date:
            from datetime import date
            if self.planned_date < date.today():
                return 'Просрочен'
            elif self.planned_date == date.today():
                return 'Сегодня'
            else:
                return 'Запланирован'
        else:
            return 'Не запланирован'


class LessonTheme(models.Model):
    """Связь урока с темами из учебной программы (many-to-many через промежуточную таблицу)."""
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='lesson_themes',
        verbose_name='Урок'
    )
    curriculum_node = models.ForeignKey(
        'learning.CurriculumNode',
        on_delete=models.CASCADE,
        related_name='lesson_themes',
        verbose_name='Узел программы'
    )
    is_primary = models.BooleanField(
        default=True,
        verbose_name='Основная тема',
        help_text='Является ли тема основной для урока'
    )
    coverage_percentage = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Процент покрытия',
        help_text='Процент темы, который покрывается в этом уроке'
    )
    
    class Meta:
        verbose_name = 'Тема урока'
        verbose_name_plural = 'Темы уроков'
        unique_together = ['lesson', 'curriculum_node']
    
    def __str__(self):
        return f"{self.lesson.title} → {self.curriculum_node.name}"
