"""
Административный интерфейс для моделей групп и студентов.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Group, GroupCourse, Student, Lesson, LessonTheme


class GroupCourseInline(admin.TabularInline):
    """Инлайн для курсов группы."""
    
    model = GroupCourse
    extra = 1
    fields = ['course', 'teacher', 'hours_per_week', 'total_hours', 
             'start_date', 'end_date', 'completed_hours', 'is_active']
    autocomplete_fields = ['course', 'teacher']
    readonly_fields = ['progress_percentage']
    
    def progress_percentage(self, obj):
        """Процент выполнения курса."""
        if obj.id:
            return f"{obj.progress_percentage:.1f}%"
        return "-"
    progress_percentage.short_description = 'Прогресс'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Админка для групп."""
    
    list_display = ['name', 'subsidiary', 'level', 'current_students_count', 
                   'max_students', 'is_full_display', 'curator', 'is_active']
    list_filter = ['subsidiary', 'level', 'is_active', 'start_date', 'created_at']
    search_fields = ['name', 'curator__user__first_name', 'curator__user__last_name']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'current_students_count']
    date_hierarchy = 'start_date'
    inlines = [GroupCourseInline]
    autocomplete_fields = ['subsidiary', 'level', 'package', 'curator']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'subsidiary', 'level', 'package']
        }),
        ('Параметры группы', {
            'fields': ['max_students', 'current_students_count', 'curator']
        }),
        ('Даты', {
            'fields': ['start_date', 'end_date']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def is_full_display(self, obj):
        """Отображение заполненности группы."""
        if obj.is_full:
            return format_html('<span style="color: red;">Заполнена</span>')
        return format_html('<span style="color: green;">Есть места</span>')
    is_full_display.short_description = 'Заполненность'
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related(
            'subsidiary', 'level', 'package', 'curator__user'
        )


@admin.register(GroupCourse)
class GroupCourseAdmin(admin.ModelAdmin):
    """Админка для курсов групп."""
    
    list_display = ['group', 'course', 'teacher', 'hours_per_week', 'total_hours', 
                   'completed_hours', 'progress_display', 'is_active']
    list_filter = ['group__subsidiary', 'course__subject', 'course__level', 
                  'teacher', 'is_active', 'start_date']
    search_fields = ['group__name', 'course__name', 'teacher__user__first_name', 
                    'teacher__user__last_name']
    list_editable = ['is_active', 'completed_hours']
    readonly_fields = ['created_at', 'updated_at', 'progress_percentage']
    date_hierarchy = 'start_date'
    autocomplete_fields = ['group', 'course', 'teacher']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['group', 'course', 'teacher']
        }),
        ('Параметры курса', {
            'fields': ['hours_per_week', 'total_hours', 'completed_hours', 'progress_percentage']
        }),
        ('Даты', {
            'fields': ['start_date', 'end_date']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def progress_display(self, obj):
        """Отображение прогресса курса."""
        progress = obj.progress_percentage
        if progress == 100:
            color = 'green'
        elif progress >= 75:
            color = 'orange'
        elif progress >= 50:
            color = 'blue'
        else:
            color = 'red'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{:.1f}%</div></div>',
            progress, color, progress
        )
    progress_display.short_description = 'Прогресс'
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related(
            'group__subsidiary', 'course__subject', 'course__level', 'teacher__user'
        )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Админка для студентов."""
    
    list_display = ['full_name', 'student_id', 'groups_display', 'age', 'phone', 
                   'parent_name', 'parent_phone', 'is_active']
    list_filter = ['groups__subsidiary', 'groups__level', 'groups', 'is_active', 
                  'enrollment_date', 'created_at']
    search_fields = ['first_name', 'last_name', 'middle_name', 'student_id', 
                    'phone', 'email', 'parent_name', 'parent_phone']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'age']
    date_hierarchy = 'enrollment_date'
    autocomplete_fields = ['user']
    filter_horizontal = ['groups']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['user', 'student_id', 'groups']
        }),
        ('Персональные данные', {
            'fields': ['first_name', 'last_name', 'middle_name', 'date_of_birth', 'age']
        }),
        ('Контактная информация', {
            'fields': ['email', 'phone', 'address']
        }),
        ('Родители/опекуны', {
            'fields': ['parent_name', 'parent_phone', 'parent_email']
        }),
        ('Учёба', {
            'fields': ['enrollment_date', 'notes']
        }),
        ('Статус', {
            'fields': ['is_active']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related('user').prefetch_related(
            'groups__subsidiary', 'groups__level'
        )
    
    def groups_display(self, obj):
        """Отображение групп студента."""
        groups = obj.groups.all()[:3]  # Показываем только первые 3
        if groups:
            result = ', '.join([f"{group.subsidiary.short_name}-{group.name}" for group in groups])
            if obj.groups.count() > 3:
                result += f' (и ещё {obj.groups.count() - 3})'
            return result
        return 'Нет групп'
    groups_display.short_description = 'Группы'
    
    # Дополнительные действия
    actions = ['activate_students', 'deactivate_students']
    
    def activate_students(self, request, queryset):
        """Активировать выбранных студентов."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'Активировано {count} студентов.')
    activate_students.short_description = 'Активировать выбранных студентов'
    
    def deactivate_students(self, request, queryset):
        """Деактивировать выбранных студентов."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано {count} студентов.')
    deactivate_students.short_description = 'Деактивировать выбранных студентов'


class LessonThemeInline(admin.TabularInline):
    """Инлайн для тем урока."""
    
    model = LessonTheme
    extra = 1
    fields = ['curriculum_node', 'is_primary', 'coverage_percentage']
    autocomplete_fields = ['curriculum_node']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Админка для уроков."""
    
    list_display = ['title', 'group_course', 'order', 'planned_date', 
                   'status_display', 'is_conducted', 'event_link']
    list_filter = ['group_course__group__subsidiary', 'group_course__course__subject', 
                  'group_course__group', 'is_conducted', 'planned_date', 'created_at']
    search_fields = ['title', 'description', 'group_course__group__name', 
                    'group_course__course__name']
    list_editable = ['planned_date']
    readonly_fields = ['created_at', 'updated_at', 'is_conducted', 'status']
    date_hierarchy = 'planned_date'
    inlines = [LessonThemeInline]
    autocomplete_fields = ['group_course', 'event']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['group_course', 'order', 'title']
        }),
        ('Содержание', {
            'fields': ['description']
        }),
        ('Планирование', {
            'fields': ['planned_date', 'event']
        }),
        ('Статус', {
            'fields': ['is_conducted', 'status']
        }),
        ('Служебная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def status_display(self, obj):
        """Отображение статуса урока с цветом."""
        status = obj.status
        if status == 'Проведён':
            color = 'green'
        elif status == 'Просрочен':
            color = 'red'
        elif status == 'Сегодня':
            color = 'orange'
        elif status == 'Запланирован':
            color = 'blue'
        else:
            color = 'gray'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    status_display.short_description = 'Статус'
    
    def event_link(self, obj):
        """Ссылка на связанное событие."""
        if obj.event:
            url = reverse('admin:schedule_event_change', args=[obj.event.id])
            return format_html('<a href="{}">Событие #{}</a>', url, obj.event.id)
        return '-'
    event_link.short_description = 'Событие'
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related(
            'group_course__group__subsidiary', 
            'group_course__course__subject',
            'event'
        )
    
    # Дополнительные действия
    actions = ['mark_as_conducted', 'set_planned_date_today']
    
    def mark_as_conducted(self, request, queryset):
        """Отметить как проведённые (только если есть связанное событие)."""
        count = 0
        for lesson in queryset:
            if lesson.event:
                lesson.is_conducted = True
                lesson.save()
                count += 1
        self.message_user(request, f'Отмечено как проведённые {count} уроков.')
    mark_as_conducted.short_description = 'Отметить как проведённые (с событием)'
    
    def set_planned_date_today(self, request, queryset):
        """Установить планируемую дату на сегодня."""
        from datetime import date
        count = queryset.update(planned_date=date.today())
        self.message_user(request, f'Установлена планируемая дата для {count} уроков.')
    set_planned_date_today.short_description = 'Установить дату на сегодня'


@admin.register(LessonTheme)
class LessonThemeAdmin(admin.ModelAdmin):
    """Админка для тем уроков."""
    
    list_display = ['lesson', 'curriculum_node', 'is_primary', 'coverage_percentage']
    list_filter = ['is_primary', 'lesson__group_course__course__subject',
                  'lesson__group_course__group']
    search_fields = ['lesson__title', 'curriculum_node__name', 
                    'lesson__group_course__group__name']
    list_editable = ['is_primary', 'coverage_percentage']
    autocomplete_fields = ['lesson', 'curriculum_node']
    
    fieldsets = [
        ('Связи', {
            'fields': ['lesson', 'curriculum_node']
        }),
        ('Параметры', {
            'fields': ['is_primary', 'coverage_percentage']
        })
    ]
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related(
            'lesson__group_course__group',
            'lesson__group_course__course',
            'curriculum_node__curriculum'
        )
