"""
Административный интерфейс для приложения правил и ограничений.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    WorkingPeriodRule, TeacherAvailabilityPeriod, TimeSlot,
    RoomAvailabilityRule, ConflictType, Conflict
)


@admin.register(WorkingPeriodRule)
class WorkingPeriodRuleAdmin(admin.ModelAdmin):
    """Административный интерфейс для правил рабочих периодов."""
    
    list_display = [
        'name', 'rule_type', 'subsidiary', 'start_date', 'end_date',
        'recurrence', 'priority', 'is_active'
    ]
    list_filter = [
        'rule_type', 'subsidiary', 'recurrence', 'is_active',
        'start_date'
    ]
    search_fields = ['name', 'description']
    list_editable = ['priority', 'is_active']
    date_hierarchy = 'start_date'
    ordering = ['-priority', 'start_date', 'name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'subsidiary', 'rule_type')
        }),
        ('Период действия', {
            'fields': ('start_date', 'end_date', 'recurrence', 'weekdays')
        }),
        ('Время работы', {
            'fields': ('start_time', 'end_time')
        }),
        ('Настройки', {
            'fields': ('priority', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subsidiary')


class TeacherAvailabilityPeriodInline(admin.TabularInline):
    """Инлайн для периодов доступности учителя."""
    
    model = TeacherAvailabilityPeriod
    extra = 0
    fields = [
        'availability_type', 'start_date', 'end_date',
        'start_time', 'end_time', 'weekdays', 'is_active'
    ]


@admin.register(TeacherAvailabilityPeriod)
class TeacherAvailabilityPeriodAdmin(admin.ModelAdmin):
    """Административный интерфейс для периодов доступности учителей."""
    
    list_display = [
        'teacher', 'availability_type', 'start_date', 'end_date',
        'time_display', 'weekdays_display', 'max_hours_per_day', 'is_active'
    ]
    list_filter = [
        'availability_type', 'is_active', 'start_date',
        'teacher__subsidiary'
    ]
    search_fields = [
        'teacher__first_name', 'teacher__last_name', 'notes'
    ]
    list_editable = ['is_active']
    date_hierarchy = 'start_date'
    ordering = ['teacher', 'start_date', 'start_time']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('teacher', 'availability_type')
        }),
        ('Период', {
            'fields': ('start_date', 'end_date')
        }),
        ('Время работы', {
            'fields': ('start_time', 'end_time', 'weekdays')
        }),
        ('Ограничения', {
            'fields': ('max_hours_per_day', 'max_hours_per_week')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['teacher']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'teacher__subsidiary'
        )
    
    def time_display(self, obj):
        """Отображение времени доступности."""
        return f"{obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')}"
    time_display.short_description = 'Время'
    
    def weekdays_display(self, obj):
        """Отображение дней недели."""
        weekdays_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        if obj.weekdays:
            try:
                days = [int(d.strip()) for d in obj.weekdays.split(',') if d.strip().isdigit()]
                return ', '.join([weekdays_names[d] for d in days if 0 <= d <= 6])
            except (ValueError, IndexError):
                return obj.weekdays
        return 'Все дни'
    weekdays_display.short_description = 'Дни недели'


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """Административный интерфейс для временных слотов."""
    
    list_display = [
        'name', 'subsidiary', 'time_display', 'duration_minutes',
        'order', 'is_active'
    ]
    list_filter = ['subsidiary', 'is_active']
    search_fields = ['name']
    list_editable = ['order', 'is_active']
    ordering = ['subsidiary', 'order', 'start_time']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'subsidiary')
        }),
        ('Время', {
            'fields': ('start_time', 'end_time')
        }),
        ('Настройки', {
            'fields': ('order', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'duration_minutes']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subsidiary')
    
    def time_display(self, obj):
        """Отображение времени слота."""
        return f"{obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')}"
    time_display.short_description = 'Время'
    
    def duration_minutes(self, obj):
        """Отображение продолжительности."""
        return f"{obj.duration_minutes} мин"
    duration_minutes.short_description = 'Продолжительность'


@admin.register(RoomAvailabilityRule)
class RoomAvailabilityRuleAdmin(admin.ModelAdmin):
    """Административный интерфейс для правил доступности кабинетов."""
    
    list_display = [
        'room', 'is_available', 'start_date', 'end_date',
        'time_display', 'weekdays_display', 'reason_short', 'is_active'
    ]
    list_filter = [
        'is_available', 'is_active', 'start_date',
        'room__subsidiary'
    ]
    search_fields = [
        'room__name', 'reason'
    ]
    list_editable = ['is_active']
    date_hierarchy = 'start_date'
    ordering = ['room', 'start_date', 'start_time']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('room', 'is_available', 'reason')
        }),
        ('Период', {
            'fields': ('start_date', 'end_date')
        }),
        ('Время', {
            'fields': ('start_time', 'end_time', 'weekdays')
        }),
        ('Настройки', {
            'fields': ('is_active',)
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    autocomplete_fields = ['room']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'room__subsidiary'
        )
    
    def time_display(self, obj):
        """Отображение времени."""
        return f"{obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')}"
    time_display.short_description = 'Время'
    
    def weekdays_display(self, obj):
        """Отображение дней недели."""
        weekdays_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        if obj.weekdays:
            try:
                days = [int(d.strip()) for d in obj.weekdays.split(',') if d.strip().isdigit()]
                return ', '.join([weekdays_names[d] for d in days if 0 <= d <= 6])
            except (ValueError, IndexError):
                return obj.weekdays
        return 'Все дни'
    weekdays_display.short_description = 'Дни недели'
    
    def reason_short(self, obj):
        """Краткая причина."""
        if obj.reason:
            return obj.reason[:30] + '...' if len(obj.reason) > 30 else obj.reason
        return '-'
    reason_short.short_description = 'Причина'


@admin.register(ConflictType)
class ConflictTypeAdmin(admin.ModelAdmin):
    """Административный интерфейс для типов конфликтов."""
    
    list_display = [
        'name', 'severity', 'is_blocking', 'auto_resolve',
        'conflicts_count', 'is_active'
    ]
    list_filter = ['severity', 'is_blocking', 'auto_resolve', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_blocking', 'auto_resolve', 'is_active']
    ordering = ['severity', 'name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description')
        }),
        ('Параметры', {
            'fields': ('severity', 'is_blocking', 'auto_resolve')
        }),
        ('Настройки', {
            'fields': ('is_active',)
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def conflicts_count(self, obj):
        """Количество конфликтов этого типа."""
        count = obj.conflicts.count()
        if count > 0:
            url = reverse('admin:rules_conflict_changelist') + f'?conflict_type={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return 0
    conflicts_count.short_description = 'Конфликтов'


@admin.register(Conflict)
class ConflictAdmin(admin.ModelAdmin):
    """Административный интерфейс для конфликтов."""
    
    list_display = [
        'conflict_type', 'status', 'scheduled_event_id',
        'description_short', 'detected_at', 'age_display', 'resolved_by'
    ]
    list_filter = [
        'status', 'conflict_type', 'detected_at', 'resolved_by'
    ]
    search_fields = ['description', 'resolution_notes']
    list_editable = ['status']
    date_hierarchy = 'detected_at'
    ordering = ['-detected_at', 'conflict_type__severity']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('conflict_type', 'scheduled_event_id', 'description')
        }),
        ('Статус', {
            'fields': ('status', 'resolved_by', 'resolution_notes')
        }),
        ('Время', {
            'fields': ('detected_at', 'resolved_at')
        }),
    )
    
    readonly_fields = ['detected_at']
    autocomplete_fields = ['resolved_by']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conflict_type', 'resolved_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Автоматическое заполнение разрешителя конфликта."""
        if change and obj.status in ['resolved', 'ignored'] and not obj.resolved_by:
            obj.resolved_by = request.user
            from django.utils import timezone
            if not obj.resolved_at:
                obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def description_short(self, obj):
        """Краткое описание конфликта."""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Описание'
    
    def age_display(self, obj):
        """Отображение возраста конфликта."""
        hours = obj.age_hours
        if hours < 1:
            return f"{int(hours * 60)} мин"
        elif hours < 24:
            return f"{int(hours)} ч"
        else:
            return f"{int(hours / 24)} дн"
    age_display.short_description = 'Возраст'
    
    actions = ['mark_as_resolved', 'mark_as_ignored']
    
    def mark_as_resolved(self, request, queryset):
        """Действие для отметки конфликтов как разрешённых."""
        from django.utils import timezone
        count = 0
        for conflict in queryset:
            if conflict.status != 'resolved':
                conflict.status = 'resolved'
                conflict.resolved_by = request.user
                conflict.resolved_at = timezone.now()
                conflict.save()
                count += 1
        
        self.message_user(
            request,
            f'Отмечено как разрешённых: {count} конфликтов.'
        )
    mark_as_resolved.short_description = 'Отметить как разрешённые'
    
    def mark_as_ignored(self, request, queryset):
        """Действие для отметки конфликтов как игнорируемых."""
        from django.utils import timezone
        count = 0
        for conflict in queryset:
            if conflict.status != 'ignored':
                conflict.status = 'ignored'
                conflict.resolved_by = request.user
                conflict.resolved_at = timezone.now()
                conflict.save()
                count += 1
        
        self.message_user(
            request,
            f'Отмечено как игнорируемых: {count} конфликтов.'
        )
    mark_as_ignored.short_description = 'Отметить как игнорируемые'
