"""
Административный интерфейс для основных моделей системы.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Subsidiary, Subject, Level, Course, Package, PackageCourse,
    Teacher, Room
)


@admin.register(Subsidiary)
class SubsidiaryAdmin(admin.ModelAdmin):
    """Админка для филиалов."""
    
    list_display = ['name', 'short_name', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'short_name', 'address', 'phone', 'email']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'short_name', 'address']
        }),
        ('Контактная информация', {
            'fields': ['phone', 'email']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Админка для предметов."""
    
    list_display = ['name', 'short_name', 'code', 'subsidiary', 'is_active', 'teachers_count', 'courses_count']
    list_filter = ['subsidiary', 'is_active', 'created_at']
    search_fields = ['name', 'short_name', 'code', 'subsidiary__name']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['subsidiary']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'short_name', 'code', 'subsidiary', 'description']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def teachers_count(self, obj):
        """Количество учителей, преподающих предмет."""
        return obj.teachers.count()
    teachers_count.short_description = 'Учителей'
    
    def courses_count(self, obj):
        """Количество курсов по предмету."""
        return obj.courses.count()
    courses_count.short_description = 'Курсов'
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related('subsidiary')


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    """Админка для ступеней."""
    
    list_display = ['name', 'short_name', 'subsidiary', 'order', 'is_active', 'courses_count', 'groups_count']
    list_filter = ['subsidiary', 'is_active', 'created_at']
    search_fields = ['name', 'short_name', 'subsidiary__name']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['subsidiary', 'order']
    autocomplete_fields = ['subsidiary']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'short_name', 'subsidiary', 'order', 'description']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def courses_count(self, obj):
        """Количество курсов на ступени."""
        return obj.courses.count()
    courses_count.short_description = 'Курсов'
    
    def groups_count(self, obj):
        """Количество групп на ступени."""
        return obj.groups.count()
    groups_count.short_description = 'Групп'
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related('subsidiary')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Админка для курсов."""
    
    list_display = ['name', 'short_name', 'subject', 'level', 'duration_hours', 
                   'lesson_duration_minutes', 'is_active', 'groups_count']
    list_filter = ['subject', 'level', 'is_active', 'created_at']
    search_fields = ['name', 'short_name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['subject', 'level']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'short_name', 'subject', 'level']
        }),
        ('Параметры курса', {
            'fields': ['duration_hours', 'lesson_duration_minutes', 'description']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def groups_count(self, obj):
        """Количество групп, изучающих курс."""
        return obj.group_courses.count()
    groups_count.short_description = 'Групп'


class PackageCourseInline(admin.TabularInline):
    """Инлайн для курсов в пакете."""
    
    model = PackageCourse
    extra = 1
    fields = ['course', 'hours_per_week', 'is_required', 'order']
    autocomplete_fields = ['course']


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """Админка для пакетов курсов."""
    
    list_display = ['name', 'level', 'courses_count', 'groups_count', 'is_active']
    list_filter = ['level', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PackageCourseInline]
    autocomplete_fields = ['level']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'level', 'description']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def courses_count(self, obj):
        """Количество курсов в пакете."""
        return obj.courses.count()
    courses_count.short_description = 'Курсов'
    
    def groups_count(self, obj):
        """Количество групп, использующих пакет."""
        return obj.groups.count()
    groups_count.short_description = 'Групп'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Админка для учителей."""
    
    list_display = ['full_name', 'employee_id', 'subsidiary', 'subjects_list', 
                   'max_hours_per_week', 'groups_count', 'is_active']
    list_filter = ['subsidiary', 'subjects', 'is_active', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id', 'phone']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['subjects']
    autocomplete_fields = ['user', 'subsidiary']
    
    fieldsets = [
        ('Пользователь', {
            'fields': ['user']
        }),
        ('Основная информация', {
            'fields': ['employee_id', 'subsidiary', 'subjects']
        }),
        ('Контактная информация', {
            'fields': ['phone']
        }),
        ('Рабочие параметры', {
            'fields': ['max_hours_per_week']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def subjects_list(self, obj):
        """Список предметов, которые преподаёт учитель."""
        subjects = obj.subjects.all()[:3]  # Показываем только первые 3
        if subjects:
            result = ', '.join([s.short_name for s in subjects])
            if obj.subjects.count() > 3:
                result += f' (и ещё {obj.subjects.count() - 3})'
            return result
        return 'Нет предметов'
    subjects_list.short_description = 'Предметы'
    
    def groups_count(self, obj):
        """Количество групп у учителя."""
        return obj.group_courses.count()
    groups_count.short_description = 'Групп'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Админка для кабинетов."""
    
    list_display = ['name', 'subsidiary', 'capacity', 'subjects_list', 'is_active']
    list_filter = ['subsidiary', 'subjects', 'is_active', 'created_at']
    search_fields = ['name', 'equipment']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['subjects']
    autocomplete_fields = ['subsidiary']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'subsidiary', 'capacity']
        }),
        ('Характеристики', {
            'fields': ['equipment', 'subjects']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def subjects_list(self, obj):
        """Список предметов для кабинета."""
        subjects = obj.subjects.all()[:3]  # Показываем только первые 3
        if subjects:
            result = ', '.join([s.short_name for s in subjects])
            if obj.subjects.count() > 3:
                result += f' (и ещё {obj.subjects.count() - 3})'
            return result
        return 'Универсальный'
    subjects_list.short_description = 'Предметы'


# Настройка заголовков админки
admin.site.site_header = "Система управления расписанием"
admin.site.site_title = "Админ-панель"
admin.site.index_title = "Управление школьным расписанием"
