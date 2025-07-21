"""
Модели для системы учебных материалов и программ.

Этот модуль содержит модели для управления учебными материалами,
их структурой, учебными программами и связями с курсами.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from pathlib import Path

from core.models import Subsidiary, Subject
from groups.models import GroupCourse


class LearningMaterialCollection(models.Model):
    """Коллекция учебных материалов."""
    
    name = models.CharField(
        max_length=200,
        verbose_name='Название коллекции',
        help_text='Название коллекции учебных материалов'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='material_collections',
        verbose_name='Предмет',
        help_text='Предмет, к которому относится коллекция'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание коллекции'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна',
        help_text='Коллекция активна и используется'
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
        verbose_name = 'Коллекция материалов'
        verbose_name_plural = 'Коллекции материалов'
        ordering = ['subject', 'name']
    
    def __str__(self):
        return f"{self.subject.name} - {self.name}"
    
    @property
    def materials_count(self):
        """Количество материалов в коллекции."""
        return self.nodes.aggregate(
            count=models.Count('materials', distinct=True)
        )['count'] or 0


class LearningMaterial(models.Model):
    """Учебный материал."""
    
    MATERIAL_TYPE_CHOICES = [
        ('document', 'Документ'),
        ('video', 'Видео'),
        ('audio', 'Аудио'),
        ('image', 'Изображение'),
        ('presentation', 'Презентация'),
        ('interactive', 'Интерактивный материал'),
        ('link', 'Ссылка'),
        ('text', 'Текстовый материал'),
    ]
    
    name = models.CharField(
        max_length=300,
        verbose_name='Название материала',
        help_text='Название учебного материала'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание содержания материала'
    )
    material_type = models.CharField(
        max_length=15,
        choices=MATERIAL_TYPE_CHOICES,
        verbose_name='Тип материала',
        help_text='Тип учебного материала'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='learning_materials',
        verbose_name='Предмет',
        help_text='Предмет, к которому относится материал'
    )
    file = models.FileField(
        upload_to='learning_materials/',
        null=True,
        blank=True,
        verbose_name='Файл',
        help_text='Файл материала'
    )
    external_url = models.URLField(
        blank=True,
        verbose_name='Внешняя ссылка',
        help_text='Ссылка на внешний ресурс'
    )
    content = models.TextField(
        blank=True,
        verbose_name='Текстовое содержание',
        help_text='Текстовое содержание материала (для типа "текст")'
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Размер файла (байты)',
        help_text='Размер файла в байтах'
    )
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        verbose_name='Длительность (минуты)',
        help_text='Длительность материала в минутах (для видео/аудио)'
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Теги',
        help_text='Теги для поиска и группировки (через запятую)'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Публичный',
        help_text='Материал доступен для всех'
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='created_materials',
        verbose_name='Создан пользователем',
        help_text='Пользователь, создавший материал'
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
        verbose_name = 'Учебный материал'
        verbose_name_plural = 'Учебные материалы'
        ordering = ['subject', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_material_type_display()})"
    
    def clean(self):
        """Валидация модели."""
        # Проверка обязательности поля в зависимости от типа материала
        if self.material_type == 'link' and not self.external_url:
            raise ValidationError('Для материала типа "Ссылка" обязательно указание URL')
        
        if self.material_type == 'text' and not self.content:
            raise ValidationError('Для материала типа "Текст" обязательно указание содержания')
        
        if self.material_type in ['document', 'video', 'audio', 'image', 'presentation'] and not self.file:
            raise ValidationError(f'Для материала типа "{self.get_material_type_display()}" обязательно прикрепление файла')
    
    @property
    def file_size_display(self):
        """Отображение размера файла в удобном формате."""
        if not self.file_size:
            return '-'
        
        if self.file_size < 1024:
            return f"{self.file_size} Б"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size // 1024} КБ"
        else:
            return f"{self.file_size // (1024 * 1024)} МБ"
    
    @property
    def tags_list(self):
        """Список тегов."""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()] if self.tags else []


class LearningMaterialNode(models.Model):
    """Узел в структуре учебных материалов."""
    
    collection = models.ForeignKey(
        LearningMaterialCollection,
        on_delete=models.CASCADE,
        related_name='nodes',
        verbose_name='Коллекция',
        help_text='Коллекция, к которой относится узел'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название узла',
        help_text='Название узла в структуре материалов'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание содержания узла'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительский узел',
        help_text='Родительский узел в иерархии'
    )
    materials = models.ManyToManyField(
        LearningMaterial,
        blank=True,
        related_name='nodes',
        verbose_name='Материалы',
        help_text='Учебные материалы в этом узле'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок',
        help_text='Порядок отображения среди соседних узлов'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Узел активен и отображается'
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
        verbose_name = 'Узел материалов'
        verbose_name_plural = 'Узлы материалов'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Валидация модели."""
        # Проверка на цикличность
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError('Обнаружена цикличность в структуре узлов')
                current = current.parent
    
    @property
    def level(self):
        """Уровень вложенности узла."""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level
    
    @property
    def full_path(self):
        """Полный путь до узла."""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' / '.join(path)


class Curriculum(models.Model):
    """Учебная программа."""
    
    name = models.CharField(
        max_length=300,
        verbose_name='Название программы',
        help_text='Название учебной программы'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание программы и её целей'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='curricula',
        verbose_name='Предмет',
        help_text='Предмет, к которому относится программа'
    )
    version = models.CharField(
        max_length=50,
        default='1.0',
        verbose_name='Версия',
        help_text='Версия программы'
    )
    total_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        verbose_name='Общее количество часов',
        help_text='Общее количество академических часов'
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Начальный'),
            ('intermediate', 'Средний'),
            ('advanced', 'Продвинутый'),
            ('expert', 'Экспертный'),
        ],
        default='beginner',
        verbose_name='Уровень сложности',
        help_text='Уровень сложности программы'
    )
    is_template = models.BooleanField(
        default=False,
        verbose_name='Шаблон',
        help_text='Программа является шаблоном для создания других программ'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна',
        help_text='Программа активна и используется'
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='created_curricula',
        verbose_name='Создан пользователем',
        help_text='Пользователь, создавший программу'
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
        verbose_name = 'Учебная программа'
        verbose_name_plural = 'Учебные программы'
        ordering = ['subject', 'name']
        unique_together = ['name', 'subject', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.subject.name})"


class CurriculumNode(models.Model):
    """Узел в структуре учебной программы."""
    
    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name='nodes',
        verbose_name='Учебная программа',
        help_text='Программа, к которой относится узел'
    )
    name = models.CharField(
        max_length=300,
        verbose_name='Название узла',
        help_text='Название узла программы (тема, раздел, урок)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Описание содержания узла'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительский узел',
        help_text='Родительский узел в иерархии программы'
    )
    node_type = models.CharField(
        max_length=20,
        choices=[
            ('module', 'Модуль'),
            ('chapter', 'Глава'),
            ('topic', 'Тема'),
            ('lesson', 'Урок'),
        ],
        default='lesson',
        verbose_name='Тип узла',
        help_text='Тип узла в структуре программы'
    )
    estimated_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Планируемые часы',
        help_text='Количество часов для изучения этого узла'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок',
        help_text='Порядок изучения среди соседних узлов'
    )
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name='Обязательный',
        help_text='Узел обязателен для изучения'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Узел активен в программе'
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
        verbose_name = 'Узел программы'
        verbose_name_plural = 'Узлы программы'
        ordering = ['curriculum', 'order', 'name']
        unique_together = ['curriculum', 'name', 'parent']
    
    def __str__(self):
        return f"{self.curriculum.name} / {self.name}"
    
    def clean(self):
        """Валидация модели."""
        # Проверка на цикличность
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError('Обнаружена цикличность в структуре программы')
                current = current.parent
        
        # Проверка принадлежности к той же программе
        if self.parent and self.parent.curriculum != self.curriculum:
            raise ValidationError('Родительский узел должен принадлежать той же программе')
    
    @property
    def level(self):
        """Уровень вложенности узла."""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level
    
    @property
    def full_path(self):
        """Полный путь до узла в программе."""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' / '.join(path)


class CurriculumNodeMaterial(models.Model):
    """Связь узла программы с учебными материалами."""
    
    curriculum_node = models.ForeignKey(
        CurriculumNode,
        on_delete=models.CASCADE,
        related_name='node_materials',
        verbose_name='Узел программы',
        help_text='Узел программы'
    )
    learning_material = models.ForeignKey(
        LearningMaterial,
        on_delete=models.CASCADE,
        related_name='curriculum_links',
        verbose_name='Учебный материал',
        help_text='Связанный учебный материал'
    )
    material_type = models.CharField(
        max_length=20,
        choices=[
            ('required', 'Обязательный'),
            ('recommended', 'Рекомендуемый'),
            ('supplementary', 'Дополнительный'),
            ('assessment', 'Контрольный'),
        ],
        default='required',
        verbose_name='Тип материала',
        help_text='Тип использования материала в узле'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок',
        help_text='Порядок изучения материала в узле'
    )
    estimated_time_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(480)],
        verbose_name='Планируемое время (минуты)',
        help_text='Планируемое время работы с материалом'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
        help_text='Примечания по использованию материала'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создана'
    )
    
    class Meta:
        verbose_name = 'Материал узла программы'
        verbose_name_plural = 'Материалы узлов программы'
        ordering = ['curriculum_node', 'order', 'material_type']
        unique_together = ['curriculum_node', 'learning_material']
    
    def __str__(self):
        return f"{self.curriculum_node.name} → {self.learning_material.name}"


class GroupCourseCurriculum(models.Model):
    """Связь курса группы с учебной программой."""
    
    group_course = models.ForeignKey(
        GroupCourse,
        on_delete=models.CASCADE,
        related_name='curricula',
        verbose_name='Курс группы',
        help_text='Курс группы'
    )
    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name='group_courses',
        verbose_name='Учебная программа',
        help_text='Учебная программа'
    )
    start_date = models.DateField(
        verbose_name='Дата начала',
        help_text='Дата начала изучения программы'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания',
        help_text='Планируемая дата окончания программы'
    )
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Прогресс (%)',
        help_text='Процент выполнения программы'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна',
        help_text='Программа активна для группы'
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
        verbose_name = 'Программа курса группы'
        verbose_name_plural = 'Программы курсов групп'
        ordering = ['group_course', 'start_date']
        unique_together = ['group_course', 'curriculum']
    
    def __str__(self):
        return f"{self.group_course} → {self.curriculum.name}"
    
    def clean(self):
        """Валидация модели."""
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('Дата начала должна быть меньше даты окончания')
        
        # Проверка соответствия предмета
        if self.curriculum.subject != self.group_course.course.subject:
            raise ValidationError('Предмет программы должен соответствовать предмету курса')
    
    @property
    def duration_days(self):
        """Длительность изучения программы в днях."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0
    
    @property
    def is_completed(self):
        """Проверка завершённости программы."""
        return self.progress_percentage >= 100
