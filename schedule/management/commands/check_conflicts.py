"""
Django команда для проверки конфликтов в расписании.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from schedule.models import SchedulePlan, ScheduledEvent
from schedule.conflict_detection import ConflictDetector, detect_and_save_conflicts
from schedule.conflict_resolution import ConflictResolver, auto_resolve_conflicts
from rules.models import Conflict


class Command(BaseCommand):
    """Команда для проверки и разрешения конфликтов в расписании."""
    
    help = 'Проверка конфликтов в расписании и предложение решений'
    
    def add_arguments(self, parser):
        """Добавление аргументов команды."""
        parser.add_argument(
            '--plan-id',
            type=int,
            help='ID плана расписания для проверки (если не указан, проверяются все планы)'
        )
        parser.add_argument(
            '--auto-resolve',
            action='store_true',
            help='Автоматически разрешить конфликты, которые можно разрешить автоматически'
        )
        parser.add_argument(
            '--suggest-solutions',
            action='store_true',
            help='Показать предложения по разрешению для обнаруженных конфликтов'
        )
        parser.add_argument(
            '--clear-old',
            action='store_true',
            help='Очистить старые разрешённые конфликты (старше 30 дней)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Подробный вывод информации'
        )
    
    def handle(self, *args, **options):
        """Основная логика команды."""
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS('=== ПРОВЕРКА КОНФЛИКТОВ В РАСПИСАНИИ ===\n')
            )
        
        # Получаем план расписания для проверки
        schedule_plan = None
        if options['plan_id']:
            try:
                schedule_plan = SchedulePlan.objects.get(id=options['plan_id'])
                if verbose:
                    self.stdout.write(f"Проверка плана: {schedule_plan}")
            except SchedulePlan.DoesNotExist:
                raise CommandError(f'План расписания с ID {options["plan_id"]} не найден')
        elif verbose:
            self.stdout.write("Проверка всех активных планов расписания")
        
        # Очистка старых конфликтов
        if options['clear_old']:
            self._clear_old_conflicts(verbose)
        
        # Обнаружение новых конфликтов
        self._detect_conflicts(schedule_plan, verbose)
        
        # Автоматическое разрешение
        if options['auto_resolve']:
            self._auto_resolve_conflicts(schedule_plan, verbose)
        
        # Предложения решений
        if options['suggest_solutions']:
            self._suggest_solutions(schedule_plan, verbose)
        
        # Итоговая статистика
        self._show_summary(schedule_plan, verbose)
    
    def _clear_old_conflicts(self, verbose: bool):
        """Очистка старых разрешённых конфликтов."""
        if verbose:
            self.stdout.write("\n--- Очистка старых конфликтов ---")
        
        old_date = timezone.now() - timezone.timedelta(days=30)
        old_conflicts = Conflict.objects.filter(
            status__in=['resolved', 'ignored'],
            resolved_at__lt=old_date
        )
        
        count = old_conflicts.count()
        old_conflicts.delete()
        
        if verbose:
            self.stdout.write(f"Удалено старых конфликтов: {count}")
    
    def _detect_conflicts(self, schedule_plan, verbose: bool):
        """Обнаружение новых конфликтов."""
        if verbose:
            self.stdout.write("\n--- Обнаружение конфликтов ---")
        
        # Удаляем необработанные конфликты для повторной проверки
        if schedule_plan:
            event_ids = ScheduledEvent.objects.filter(
                schedule_plan=schedule_plan
            ).values_list('id', flat=True)
            Conflict.objects.filter(
                scheduled_event_id__in=event_ids,
                status='detected'
            ).delete()
        else:
            Conflict.objects.filter(status='detected').delete()
        
        # Обнаруживаем новые конфликты
        created_conflicts = detect_and_save_conflicts(schedule_plan)
        
        if verbose:
            self.stdout.write(f"Обнаружено новых конфликтов: {len(created_conflicts)}")
            
            # Группируем по типам
            conflict_types = {}
            for conflict in created_conflicts:
                conflict_type = conflict.conflict_type.name
                if conflict_type not in conflict_types:
                    conflict_types[conflict_type] = 0
                conflict_types[conflict_type] += 1
            
            for conflict_type, count in conflict_types.items():
                self.stdout.write(f"  - {conflict_type}: {count}")
    
    def _auto_resolve_conflicts(self, schedule_plan, verbose: bool):
        """Автоматическое разрешение конфликтов."""
        if verbose:
            self.stdout.write("\n--- Автоматическое разрешение ---")
        
        stats = auto_resolve_conflicts(schedule_plan)
        
        if verbose:
            self.stdout.write(f"Всего конфликтов для автоматического разрешения: {stats['total_conflicts']}")
            self.stdout.write(f"Автоматически разрешено: {stats['auto_resolved']}")
            self.stdout.write(f"Требует ручного вмешательства: {stats['manual_required']}")
            self.stdout.write(f"Не удалось разрешить: {stats['failed_to_resolve']}")
    
    def _suggest_solutions(self, schedule_plan, verbose: bool):
        """Предложения решений для нерешённых конфликтов."""
        if verbose:
            self.stdout.write("\n--- Предложения решений ---")
        
        # Получаем нерешённые конфликты
        conflicts = Conflict.objects.filter(status='detected')
        
        if schedule_plan:
            event_ids = ScheduledEvent.objects.filter(
                schedule_plan=schedule_plan
            ).values_list('id', flat=True)
            conflicts = conflicts.filter(scheduled_event_id__in=event_ids)
        
        resolver = ConflictResolver()
        
        for conflict in conflicts[:10]:  # Ограничиваем вывод первыми 10
            if verbose:
                self.stdout.write(f"\nКонфликт #{conflict.id}: {conflict.conflict_type.name}")
                self.stdout.write(f"Описание: {conflict.description}")
            
            suggestions = resolver.suggest_solutions(conflict)
            
            if suggestions:
                if verbose:
                    self.stdout.write("Предложения:")
                    for i, suggestion in enumerate(suggestions[:3], 1):
                        priority_color = {
                            'high': self.style.ERROR,
                            'medium': self.style.WARNING,
                            'low': self.style.NOTICE
                        }.get(suggestion.get('priority', 'low'), self.style.NOTICE)
                        
                        self.stdout.write(
                            f"  {i}. {priority_color(suggestion['description'])} "
                            f"(приоритет: {suggestion.get('priority', 'низкий')})"
                        )
            else:
                if verbose:
                    self.stdout.write("  Автоматические решения не найдены")
    
    def _show_summary(self, schedule_plan, verbose: bool):
        """Отображение итоговой статистики."""
        if verbose:
            self.stdout.write("\n--- Итоговая статистика ---")
        
        # Получаем статистику конфликтов
        all_conflicts = Conflict.objects.all()
        if schedule_plan:
            event_ids = ScheduledEvent.objects.filter(
                schedule_plan=schedule_plan
            ).values_list('id', flat=True)
            all_conflicts = all_conflicts.filter(scheduled_event_id__in=event_ids)
        
        total = all_conflicts.count()
        detected = all_conflicts.filter(status='detected').count()
        resolved = all_conflicts.filter(status='resolved').count()
        ignored = all_conflicts.filter(status='ignored').count()
        
        # Статистика по критичности
        critical = all_conflicts.filter(conflict_type__severity='critical').count()
        high = all_conflicts.filter(conflict_type__severity='high').count()
        medium = all_conflicts.filter(conflict_type__severity='medium').count()
        low = all_conflicts.filter(conflict_type__severity='low').count()
        
        if verbose:
            self.stdout.write(f"Всего конфликтов: {total}")
            self.stdout.write(f"  - Обнаружено: {detected}")
            self.stdout.write(f"  - Разрешено: {resolved}")
            self.stdout.write(f"  - Игнорировано: {ignored}")
            self.stdout.write(f"\nПо критичности:")
            self.stdout.write(f"  - Критические: {critical}")
            self.stdout.write(f"  - Высокие: {high}")
            self.stdout.write(f"  - Средние: {medium}")
            self.stdout.write(f"  - Низкие: {low}")
        else:
            # Краткий вывод
            if detected > 0:
                self.stdout.write(
                    self.style.WARNING(f"Обнаружено {detected} активных конфликтов")
                )
                if critical > 0:
                    self.stdout.write(
                        self.style.ERROR(f"Из них {critical} критических!")
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS("Активных конфликтов не обнаружено")
                )
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS('\n=== ПРОВЕРКА ЗАВЕРШЕНА ===')
            ) 