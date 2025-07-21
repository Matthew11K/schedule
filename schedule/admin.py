"""
Административный интерфейс для приложения расписания.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    SchedulePlan, ScheduledEvent, ScheduledEventCancellation, 
    Event, StudentPresence
)


@admin.register(SchedulePlan)
class SchedulePlanAdmin(admin.ModelAdmin):
    """Административный интерфейс для планов расписания."""
    
    list_display = [
        'name', 'subsidiary', 'start_date', 'end_date', 
        'duration_days', 'is_active', 'is_current'
    ]
    list_filter = ['subsidiary', 'is_active', 'start_date']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    date_hierarchy = 'start_date'
    ordering = ['-start_date', 'name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'subsidiary', 'description')
        }),
        ('Период действия', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'duration_days']
    
    def duration_days(self, obj):
        """Отображение продолжительности плана."""
        return f"{obj.duration_days} дней"
    duration_days.short_description = 'Продолжительность'
    
    def is_current(self, obj):
        """Отображение актуальности плана."""
        if obj.is_current:
            return format_html('<span style="color: green;">✓ Текущий</span>')
        return format_html('<span style="color: gray;">Неактуальный</span>')
    is_current.short_description = 'Актуальность'


class ScheduledEventCancellationInline(admin.TabularInline):
    """Инлайн для отмен событий."""
    
    model = ScheduledEventCancellation
    extra = 0
    fields = [
        'cancellation_type', 'cancellation_date', 'start_date', 
        'end_date', 'reason', 'created_by'
    ]
    readonly_fields = ['created_by']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(ScheduledEvent)
class ScheduledEventAdmin(admin.ModelAdmin):
    """Административный интерфейс для запланированных событий."""
    
    list_display = [
        'group_course', 'group', 'teachers_display', 'room', 'event_type',
        'weekday_display', 'time_display', 'academic_hours', 'duration_minutes', 'is_active'
    ]
    list_filter = [
        'event_type', 'weekday', 'is_active', 'schedule_plan__subsidiary',
        'group_course__course__subject', 'group', 'teachers'
    ]
    search_fields = [
        'group_course__group__name', 'group_course__course__name',
        'group__name', 'teachers__user__first_name', 'teachers__user__last_name', 'topic'
    ]
    list_editable = ['is_active']
    ordering = ['schedule_plan', 'weekday', 'start_time']
    filter_horizontal = ['teachers']
    autocomplete_fields = ['schedule_plan', 'group', 'group_course', 'room']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('schedule_plan', 'group', 'group_course', 'teachers', 'room')
        }),
        ('Расписание', {
            'fields': (
                'event_type', 'weekday', 'specific_date',
                'start_time', 'end_time', 'duration_minutes', 'academic_hours'
            )
        }),
        ('Детали', {
            'fields': ('topic', 'notes', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ScheduledEventCancellationInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'schedule_plan', 'group', 'group_course__group', 'group_course__course', 'room'
        ).prefetch_related('teachers__user')
    
    def teachers_display(self, obj):
        """Отображение списка преподавателей."""
        teachers = obj.teachers.all()[:3]  # Показываем только первых 3
        if teachers:
            result = ', '.join([teacher.full_name for teacher in teachers])
            if obj.teachers.count() > 3:
                result += f' (и ещё {obj.teachers.count() - 3})'
            return result
        return 'Нет преподавателей'
    teachers_display.short_description = 'Преподаватели'
    
    def weekday_display(self, obj):
        """Отображение дня недели."""
        if obj.event_type == 'weekly' and obj.weekday is not None:
            return dict(obj.WEEKDAY_CHOICES)[obj.weekday]
        elif obj.event_type == 'single' and obj.specific_date:
            return obj.specific_date.strftime('%d.%m.%Y')
        return '-'
    weekday_display.short_description = 'День'
    
    def time_display(self, obj):
        """Отображение времени события."""
        return f"{obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')}"
    time_display.short_description = 'Время'


@admin.register(ScheduledEventCancellation)
class ScheduledEventCancellationAdmin(admin.ModelAdmin):
    """Административный интерфейс для отмен событий."""
    
    list_display = [
        'scheduled_event', 'cancellation_type', 'date_display',
        'reason_short', 'created_by', 'created_at'
    ]
    list_filter = ['cancellation_type', 'created_at', 'scheduled_event__schedule_plan__subsidiary']
    search_fields = ['reason', 'scheduled_event__group_course__group__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('scheduled_event', 'cancellation_type', 'reason')
        }),
        ('Даты отмены', {
            'fields': ('cancellation_date', 'start_date', 'end_date')
        }),
        ('Дополнительно', {
            'fields': ('replacement_event', 'created_by')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'scheduled_event__group_course__group',
            'scheduled_event__group_course__course',
            'created_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Автоматическое заполнение создателя отмены."""
        if not change:  # Только при создании
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def date_display(self, obj):
        """Отображение даты отмены."""
        if obj.cancellation_type == 'single':
            return obj.cancellation_date.strftime('%d.%m.%Y') if obj.cancellation_date else '-'
        elif obj.cancellation_type == 'period':
            start = obj.start_date.strftime('%d.%m.%Y') if obj.start_date else '?'
            end = obj.end_date.strftime('%d.%m.%Y') if obj.end_date else '?'
            return f"{start} - {end}"
        return 'Постоянно'
    date_display.short_description = 'Дата отмены'
    
    def reason_short(self, obj):
        """Краткая причина отмены."""
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Причина'


class StudentPresenceInline(admin.TabularInline):
    """Инлайн для присутствия студентов."""
    
    model = StudentPresence
    extra = 0
    fields = ['student', 'status', 'arrival_time', 'leave_time', 'excuse_reason']
    autocomplete_fields = ['student']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Административный интерфейс для проведённых событий."""
    
    list_display = [
        'group_display', 'date', 'time_display', 'teacher',
        'room', 'status', 'attendance_count', 'duration_minutes'
    ]
    list_filter = [
        'status', 'date', 'scheduled_event__schedule_plan__subsidiary',
        'scheduled_event__group_course__course__subject', 'teacher'
    ]
    search_fields = [
        'scheduled_event__group_course__group__name',
        'scheduled_event__group_course__course__name',
        'teacher__first_name', 'teacher__last_name', 'topic'
    ]
    date_hierarchy = 'date'
    ordering = ['-date', '-start_time']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('scheduled_event', 'date', 'teacher', 'room', 'status')
        }),
        ('Время проведения', {
            'fields': ('start_time', 'end_time')
        }),
        ('Содержание занятия', {
            'fields': ('topic', 'homework', 'notes')
        }),
        ('Статистика', {
            'fields': ('attendance_count',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'duration_minutes']
    inlines = [StudentPresenceInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'scheduled_event__group_course__group',
            'scheduled_event__group_course__course',
            'teacher', 'room'
        )
    
    def group_display(self, obj):
        """Отображение группы и курса."""
        return str(obj.scheduled_event.group_course)
    group_display.short_description = 'Группа/Курс'
    
    def time_display(self, obj):
        """Отображение времени события."""
        return f"{obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')}"
    time_display.short_description = 'Время'
    
    def duration_minutes(self, obj):
        """Отображение продолжительности."""
        return f"{obj.duration_minutes} мин"
    duration_minutes.short_description = 'Продолжительность'


@admin.register(StudentPresence)
class StudentPresenceAdmin(admin.ModelAdmin):
    """Административный интерфейс для присутствия студентов."""
    
    list_display = [
        'student', 'event_display', 'status', 'arrival_time',
        'leave_time', 'is_present'
    ]
    list_filter = [
        'status', 'event__date', 'event__scheduled_event__schedule_plan__subsidiary',
        'student__groups'
    ]
    search_fields = [
        'student__first_name', 'student__last_name',
        'event__scheduled_event__group_course__group__name'
    ]
    ordering = ['-event__date', 'student__last_name', 'student__first_name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('event', 'student', 'status')
        }),
        ('Временные отметки', {
            'fields': ('arrival_time', 'leave_time')
        }),
        ('Дополнительно', {
            'fields': ('excuse_reason', 'notes')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['student']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'event__scheduled_event__group_course__group',
            'event__scheduled_event__group_course__course'
        )
    
    def event_display(self, obj):
        """Отображение события."""
        return f"{obj.event.group} - {obj.event.date.strftime('%d.%m.%Y')}"
    event_display.short_description = 'Событие'
    
    def is_present(self, obj):
        """Отображение присутствия."""
        if obj.is_present:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    is_present.short_description = 'Присутствовал'
