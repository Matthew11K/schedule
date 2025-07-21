"""
Административный интерфейс для приложения учебных материалов.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    LearningMaterialCollection, LearningMaterial, LearningMaterialNode, Curriculum, 
    CurriculumNode, CurriculumNodeMaterial, GroupCourseCurriculum
)


class LearningMaterialNodeInline(admin.TabularInline):
    """Инлайн для узлов коллекции."""
    
    model = LearningMaterialNode
    extra = 1
    fields = ['name', 'description', 'parent', 'order', 'is_active']
    show_change_link = True


@admin.register(LearningMaterialCollection)
class LearningMaterialCollectionAdmin(admin.ModelAdmin):
    """Административный интерфейс для коллекций учебных материалов."""
    
    list_display = ['name', 'subject', 'materials_count', 'is_active', 'created_at']
    list_filter = ['subject', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'subject__name']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'materials_count']
    inlines = [LearningMaterialNodeInline]
    autocomplete_fields = ['subject']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'subject', 'description')
        }),
        ('Статистика', {
            'fields': ('materials_count',)
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subject')


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    """Административный интерфейс для учебных материалов."""
    
    list_display = [
        'name', 'material_type', 'subject', 'file_size_display',
        'duration_minutes', 'is_public', 'created_by', 'created_at'
    ]
    list_filter = [
        'material_type', 'subject', 'is_public', 'created_by',
        'created_at'
    ]
    search_fields = [
        'name', 'description', 'tags', 'content'
    ]
    list_editable = ['is_public']
    ordering = ['subject', 'name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'material_type', 'subject')
        }),
        ('Содержание', {
            'fields': ('file', 'external_url', 'content')
        }),
        ('Метаданные', {
            'fields': (
                'file_size', 'duration_minutes', 'tags', 'is_public'
            )
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'file_size_display']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'subject', 'created_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Автоматическое заполнение создателя материала."""
        if not change:  # Только при создании
            obj.created_by = request.user
        
        # Автоматическое определение размера файла
        if obj.file and hasattr(obj.file, 'size'):
            obj.file_size = obj.file.size
        
        super().save_model(request, obj, form, change)
    
    def file_size_display(self, obj):
        """Отображение размера файла."""
        return obj.file_size_display
    file_size_display.short_description = 'Размер файла'


class LearningMaterialInline(admin.TabularInline):
    """Инлайн для материалов в узлах."""
    
    model = LearningMaterialNode.materials.through
    extra = 0
    verbose_name = 'Материал'
    verbose_name_plural = 'Материалы'


@admin.register(LearningMaterialNode)
class LearningMaterialNodeAdmin(admin.ModelAdmin):
    """Административный интерфейс для узлов материалов."""
    
    list_display = [
        'name', 'collection', 'parent', 'level_display', 'materials_count',
        'order', 'is_active'
    ]
    list_filter = ['collection', 'is_active', 'parent']
    search_fields = ['name', 'description', 'collection__name']
    list_editable = ['order', 'is_active']
    ordering = ['collection', 'order', 'name']
    autocomplete_fields = ['collection', 'parent']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('collection', 'name', 'description', 'parent')
        }),
        ('Материалы', {
            'fields': ('materials',)
        }),
        ('Настройки', {
            'fields': ('order', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['materials']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('collection', 'parent')
    
    def level_display(self, obj):
        """Отображение уровня вложенности."""
        return '  ' * obj.level + '├─ ' if obj.level > 0 else ''
    level_display.short_description = 'Уровень'
    
    def materials_count(self, obj):
        """Количество материалов в узле."""
        return obj.materials.count()
    materials_count.short_description = 'Материалов'


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    """Административный интерфейс для учебных программ."""
    
    list_display = [
        'name', 'subject', 'version', 'difficulty_level',
        'total_hours', 'is_template', 'is_active', 'created_by'
    ]
    list_filter = [
        'subject', 'difficulty_level', 'is_template', 'is_active',
        'created_by'
    ]
    search_fields = ['name', 'description']
    list_editable = ['is_template', 'is_active']
    ordering = ['subject', 'name', 'version']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'subject', 'version')
        }),
        ('Параметры программы', {
            'fields': ('total_hours', 'difficulty_level')
        }),
        ('Настройки', {
            'fields': ('is_template', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'subject', 'created_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Автоматическое заполнение создателя программы."""
        if not change:  # Только при создании
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class CurriculumNodeMaterialInline(admin.TabularInline):
    """Инлайн для материалов узла программы."""
    
    model = CurriculumNodeMaterial
    extra = 0
    fields = [
        'learning_material', 'material_type', 'order',
        'estimated_time_minutes', 'notes'
    ]
    autocomplete_fields = ['learning_material']


@admin.register(CurriculumNode)
class CurriculumNodeAdmin(admin.ModelAdmin):
    """Административный интерфейс для узлов программы."""
    
    list_display = [
        'name', 'curriculum', 'node_type', 'parent',
        'estimated_hours', 'order', 'is_mandatory', 'is_active'
    ]
    list_filter = [
        'curriculum', 'node_type', 'is_mandatory', 'is_active',
        'parent'
    ]
    search_fields = ['name', 'description', 'curriculum__name']
    list_editable = ['order', 'is_mandatory', 'is_active']
    ordering = ['curriculum', 'order', 'name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('curriculum', 'name', 'description', 'parent')
        }),
        ('Параметры узла', {
            'fields': ('node_type', 'estimated_hours')
        }),
        ('Настройки', {
            'fields': ('order', 'is_mandatory', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CurriculumNodeMaterialInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'curriculum', 'parent'
        )


@admin.register(CurriculumNodeMaterial)
class CurriculumNodeMaterialAdmin(admin.ModelAdmin):
    """Административный интерфейс для материалов узлов программы."""
    
    list_display = [
        'curriculum_node', 'learning_material', 'material_type',
        'order', 'estimated_time_minutes'
    ]
    list_filter = [
        'material_type', 'curriculum_node__curriculum',
        'learning_material__subject'
    ]
    search_fields = [
        'curriculum_node__name', 'learning_material__name',
        'notes'
    ]
    ordering = ['curriculum_node', 'order', 'material_type']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('curriculum_node', 'learning_material', 'material_type')
        }),
        ('Параметры', {
            'fields': ('order', 'estimated_time_minutes', 'notes')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    autocomplete_fields = ['curriculum_node', 'learning_material']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'curriculum_node__curriculum',
            'learning_material__subject'
        )


@admin.register(GroupCourseCurriculum)
class GroupCourseCurriculumAdmin(admin.ModelAdmin):
    """Административный интерфейс для программ курсов групп."""
    
    list_display = [
        'group_course', 'curriculum', 'start_date', 'end_date',
        'progress_percentage', 'duration_days', 'is_active'
    ]
    list_filter = [
        'is_active', 'start_date', 'curriculum__subject',
        'group_course__group__subsidiary'
    ]
    search_fields = [
        'group_course__group__name', 'curriculum__name'
    ]
    list_editable = ['progress_percentage', 'is_active']
    date_hierarchy = 'start_date'
    ordering = ['-start_date', 'group_course', 'curriculum']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('group_course', 'curriculum')
        }),
        ('Период изучения', {
            'fields': ('start_date', 'end_date')
        }),
        ('Прогресс', {
            'fields': ('progress_percentage', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'duration_days']
    autocomplete_fields = ['group_course', 'curriculum']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'group_course__group__subsidiary',
            'group_course__course__subject',
            'curriculum__subject'
        )
    
    def duration_days(self, obj):
        """Отображение длительности программы."""
        if obj.duration_days > 0:
            return f"{obj.duration_days} дней"
        return '-'
    duration_days.short_description = 'Длительность'



