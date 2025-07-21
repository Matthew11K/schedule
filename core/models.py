"""
Основные модели системы управления расписанием.

Этот модуль содержит основные модели для работы с филиалами,
предметами, ступенями, курсами и другими базовыми сущностями.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Subsidiary(models.Model):
    """Филиал школы."""
    
    name = models.CharField(
        max_length=200,
        verbose_name='Название филиала',
        help_text='Полное название филиала'
    )
    short_name = models.CharField(
        max_length=50,
        verbose_name='Краткое название',
        help_text='Краткое обозначение филиала'
    )
    address = models.TextField(
        verbose_name='Адрес',
        help_text='Полный адрес филиала'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон',
        help_text='Контактный телефон'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email',
        help_text='Контактный email'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Филиал активен и используется'
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
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Subject(models.Model):
    """Предмет обучения."""
    
    name = models.CharField(
        max_length=200,
        verbose_name='Название предмета',
        help_text='Полное название предмета'
    )
    short_name = models.CharField(
        max_length=50,
        verbose_name='Краткое название',
        help_text='Краткое обозначение предмета'
    )
    code = models.CharField(
        max_length=20,
        verbose_name='Код предмета',
        help_text='Уникальный код предмета'
    )
    subsidiary = models.ForeignKey(
        'Subsidiary',
        on_delete=models.CASCADE,
        related_name='subjects',
        verbose_name='Филиал',
        help_text='Филиал, в котором преподается предмет'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание предмета'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Предмет активен и используется'
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
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        ordering = ['subsidiary', 'name']
        unique_together = ['subsidiary', 'code']
    
    def __str__(self):
        return f"{self.subsidiary.short_name} - {self.name}"


class Level(models.Model):
    """Ступень обучения."""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Название ступени',
        help_text='Название ступени обучения'
    )
    short_name = models.CharField(
        max_length=20,
        verbose_name='Краткое название',
        help_text='Краткое обозначение ступени'
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name='levels',
        verbose_name='Филиал',
        help_text='Филиал, в котором действует ступень'
    )
    order = models.PositiveIntegerField(
        verbose_name='Порядок',
        help_text='Порядок следования ступени'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание ступени'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Ступень активна и используется'
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
        verbose_name = 'Ступень'
        verbose_name_plural = 'Ступени'
        ordering = ['subsidiary', 'order']
        unique_together = ['subsidiary', 'order']
    
    def __str__(self):
        return f"{self.subsidiary.short_name} - {self.name}"


class Course(models.Model):
    """Курс обучения."""
    
    name = models.CharField(
        max_length=200,
        verbose_name='Название курса',
        help_text='Полное название курса'
    )
    short_name = models.CharField(
        max_length=50,
        verbose_name='Краткое название',
        help_text='Краткое обозначение курса'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='Предмет',
        help_text='Предмет, к которому относится курс'
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='Ступень',
        help_text='Ступень обучения'
    )
    duration_hours = models.PositiveIntegerField(
        verbose_name='Продолжительность (часы)',
        help_text='Общая продолжительность курса в академических часах'
    )
    lesson_duration_minutes = models.PositiveIntegerField(
        default=45,
        validators=[MinValueValidator(15), MaxValueValidator(180)],
        verbose_name='Длительность урока (минуты)',
        help_text='Стандартная длительность урока в минутах'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание курса'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Курс активен и используется'
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
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['level__order', 'subject__name', 'name']
    
    def __str__(self):
        return f"{self.subject.short_name} - {self.name} ({self.level.short_name})"


class Package(models.Model):
    """Типовой пакет курсов."""
    
    name = models.CharField(
        max_length=200,
        verbose_name='Название пакета',
        help_text='Название типового пакета курсов'
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='packages',
        verbose_name='Ступень',
        help_text='Ступень обучения'
    )
    courses = models.ManyToManyField(
        Course,
        through='PackageCourse',
        verbose_name='Курсы',
        help_text='Курсы, входящие в пакет'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание пакета'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Пакет активен и используется'
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
        verbose_name = 'Пакет курсов'
        verbose_name_plural = 'Пакеты курсов'
        ordering = ['level__order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.level.short_name})"


class PackageCourse(models.Model):
    """Промежуточная модель для связи пакета и курса."""
    
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        verbose_name='Пакет'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='Курс'
    )
    hours_per_week = models.PositiveIntegerField(
        default=1,
        verbose_name='Часов в неделю',
        help_text='Количество часов в неделю для данного курса'
    )
    is_required = models.BooleanField(
        default=True,
        verbose_name='Обязательный',
        help_text='Курс обязателен для изучения'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок',
        help_text='Порядок следования курса в пакете'
    )
    
    class Meta:
        verbose_name = 'Курс в пакете'
        verbose_name_plural = 'Курсы в пакетах'
        unique_together = ['package', 'course']
        ordering = ['package', 'order']
    
    def __str__(self):
        return f"{self.package.name} - {self.course.name}"


class Teacher(models.Model):
    """Учитель/преподаватель."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        help_text='Связанный пользователь системы'
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name='teachers',
        verbose_name='Филиал',
        help_text='Основной филиал работы'
    )
    subjects = models.ManyToManyField(
        Subject,
        related_name='teachers',
        verbose_name='Предметы',
        help_text='Предметы, которые преподаёт учитель'
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Табельный номер',
        help_text='Уникальный табельный номер сотрудника'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон',
        help_text='Контактный телефон'
    )
    max_hours_per_week = models.PositiveIntegerField(
        default=40,
        verbose_name='Максимум часов в неделю',
        help_text='Максимальная учебная нагрузка в неделю'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Учитель активен и может вести занятия'
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
        verbose_name = 'Учитель'
        verbose_name_plural = 'Учителя'
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"
    
    @property
    def full_name(self):
        """Полное имя учителя."""
        return f"{self.user.last_name} {self.user.first_name}"


class Room(models.Model):
    """Кабинет/аудитория."""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Название кабинета',
        help_text='Название или номер кабинета'
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name='Филиал',
        help_text='Филиал, в котором находится кабинет'
    )
    capacity = models.PositiveIntegerField(
        verbose_name='Вместимость',
        help_text='Максимальное количество учащихся'
    )
    equipment = models.TextField(
        blank=True,
        verbose_name='Оборудование',
        help_text='Описание доступного оборудования'
    )
    subjects = models.ManyToManyField(
        Subject,
        blank=True,
        related_name='rooms',
        verbose_name='Предметы',
        help_text='Предметы, для которых подходит кабинет'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Кабинет активен и может использоваться'
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
        verbose_name = 'Кабинет'
        verbose_name_plural = 'Кабинеты'
        ordering = ['subsidiary__name', 'name']
        unique_together = ['subsidiary', 'name']
    
    def __str__(self):
        return f"{self.subsidiary.short_name} - {self.name}"
