from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from rest_framework.permissions import AllowAny

from core.models import Subsidiary, Subject, Level, Course, Package, Teacher, Room
from groups.models import Group, GroupCourse, Student
from schedule.models import SchedulePlan, ScheduledEvent, ScheduledEventCancellation, Event
from learning.models import (
    LearningMaterial, LearningMaterialNode, Curriculum, 
    CurriculumNode, CurriculumNodeMaterial, GroupCourseCurriculum
)
from rules.models import (
    WorkingPeriodRule, TeacherAvailabilityPeriod, TimeSlot, 
    RoomAvailabilityRule, ConflictType, Conflict
)

from .serializers import (
    SubsidiarySerializer, SubjectSerializer, LevelSerializer, 
    CourseSerializer, PackageSerializer, TeacherSerializer, RoomSerializer,
    GroupSerializer, GroupCourseSerializer, StudentSerializer,
    SchedulePlanSerializer, ScheduledEventSerializer, ScheduledEventCancellationSerializer,
    EventSerializer, LearningMaterialSerializer, LearningMaterialNodeSerializer,
    CurriculumSerializer, CurriculumNodeSerializer, CurriculumNodeMaterialSerializer,
    GroupCourseCurriculumSerializer, WorkingPeriodRuleSerializer,
    TeacherAvailabilityPeriodSerializer, TimeSlotSerializer, RoomAvailabilityRuleSerializer,
    ConflictTypeSerializer, ConflictSerializer, UserSerializer,
    ScheduleViewSerializer, TeacherScheduleSerializer, GroupScheduleSerializer,
    ConflictDetailSerializer
)

from schedule.conflict_detection import ConflictDetector
from schedule.conflict_resolution import ConflictResolver


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# ViewSets для core моделей
class SubsidiaryViewSet(viewsets.ModelViewSet):
    queryset = Subsidiary.objects.all()
    serializer_class = SubsidiarySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination


class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().select_related('subsidiary', 'subject', 'level')
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        subsidiary_id = self.request.query_params.get('subsidiary')
        subject_id = self.request.query_params.get('subject')
        level_id = self.request.query_params.get('level')
        
        if subsidiary_id:
            queryset = queryset.filter(subsidiary=subsidiary_id)
        if subject_id:
            queryset = queryset.filter(subject=subject_id)
        if level_id:
            queryset = queryset.filter(level=level_id)
            
        return queryset


class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all().select_related('subsidiary')
    serializer_class = PackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all().select_related('user', 'subsidiary').prefetch_related('subjects')
    serializer_class = TeacherSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Получить расписание преподавателя"""
        teacher = self.get_object()
        
        # Получаем параметры даты
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        events = ScheduledEvent.objects.filter(teachers=teacher)
        
        if start_date:
            events = events.filter(specific_date__gte=start_date)
        if end_date:
            events = events.filter(specific_date__lte=end_date)
            
        events = events.select_related('group_course', 'room', 'schedule_plan')
        
        serializer = ScheduleViewSerializer(events, many=True)
        return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all().select_related('subsidiary')
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]  # Разрешаем без авторизации для тестирования
    pagination_class = StandardResultsSetPagination


# ViewSets для groups моделей
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().select_related('subsidiary')
    serializer_class = GroupSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Получить расписание группы"""
        group = self.get_object()
        
        # Получаем параметры даты
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        events = ScheduledEvent.objects.filter(group_course__group=group)
        
        if start_date:
            events = events.filter(specific_date__gte=start_date)
        if end_date:
            events = events.filter(specific_date__lte=end_date)
            
        events = events.select_related('group_course', 'room', 'schedule_plan').prefetch_related('teachers')
        
        serializer = ScheduleViewSerializer(events, many=True)
        return Response(serializer.data)


class GroupCourseViewSet(viewsets.ModelViewSet):
    queryset = GroupCourse.objects.all().select_related('group', 'course', 'package', 'teacher')
    serializer_class = GroupCourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().select_related('user').prefetch_related('groups')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


# ViewSets для schedule моделей
class SchedulePlanViewSet(viewsets.ModelViewSet):
    queryset = SchedulePlan.objects.all().select_related('subsidiary')
    serializer_class = SchedulePlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @action(detail=True, methods=['post'])
    def check_conflicts(self, request, pk=None):
        """Проверить конфликты в плане расписания"""
        plan = self.get_object()
        # Обнаруживаем и сохраняем конфликты в базу данных
        from schedule.conflict_detection import detect_and_save_conflicts
        created_conflicts = detect_and_save_conflicts(plan)
        
        # Возвращаем найденные конфликты
        # Получаем события этого плана
        events = plan.scheduled_events.all()
        event_ids = list(events.values_list('id', flat=True))
        
        conflict_serializer = ConflictDetailSerializer(
            Conflict.objects.filter(
                scheduled_event_id__in=event_ids,
                status__in=['detected', 'acknowledged', 'in_progress']
            ),
            many=True
        )
        
        return Response({
            'conflicts_found': len(created_conflicts),
            'conflicts': conflict_serializer.data
        })

    @action(detail=True, methods=['post'])
    def resolve_conflicts(self, request, pk=None):
        """Автоматически разрешить конфликты"""
        plan = self.get_object()
        resolver = ConflictResolver()
        
        # Получаем события этого плана для фильтрации конфликтов
        events = plan.scheduled_events.all()
        event_ids = list(events.values_list('id', flat=True))
        
        conflicts = Conflict.objects.filter(
            scheduled_event_id__in=event_ids,
            status__in=['detected', 'acknowledged', 'in_progress']
        )
        
        results = []
        for conflict in conflicts:
            solutions = resolver.suggest_solutions(conflict)
            result = {
                'conflict_id': conflict.id,
                'solutions': solutions,
                'auto_resolved': False
            }
            
            # Пытаемся автоматически разрешить
            if resolver.can_auto_resolve(conflict):
                success = resolver.auto_resolve_conflict(conflict)
                result['auto_resolved'] = success
            
            results.append(result)
        
        return Response({'results': results})


class ScheduledEventViewSet(viewsets.ModelViewSet):
    queryset = ScheduledEvent.objects.all().select_related('schedule_plan', 'group_course', 'room').prefetch_related('teachers')
    serializer_class = ScheduledEventSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по параметрам
        plan_id = self.request.query_params.get('plan')
        teacher_id = self.request.query_params.get('teacher')
        group_id = self.request.query_params.get('group')
        room_id = self.request.query_params.get('room')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if plan_id:
            queryset = queryset.filter(schedule_plan=plan_id)
        if teacher_id:
            queryset = queryset.filter(teachers=teacher_id)
        if group_id:
            queryset = queryset.filter(group_course__group=group_id)
        if room_id:
            queryset = queryset.filter(room=room_id)
        # Фильтрация по датам только для single событий
        # Weekly события отображаются всегда (логика повторения обрабатывается на фронтенде)
        if start_date or end_date:
            from django.db.models import Q
            date_filter = Q()
            if start_date and end_date:
                # Включаем single события в диапазоне дат И все weekly события
                date_filter = Q(
                    Q(event_type='single', specific_date__range=[start_date, end_date]) |
                    Q(event_type='weekly')
                )
            elif start_date:
                date_filter = Q(
                    Q(event_type='single', specific_date__gte=start_date) |
                    Q(event_type='weekly')
                )
            elif end_date:
                date_filter = Q(
                    Q(event_type='single', specific_date__lte=end_date) |
                    Q(event_type='weekly')
                )
            queryset = queryset.filter(date_filter)
            
        return queryset.order_by('event_type', 'weekday', 'specific_date', 'start_time')


class ScheduledEventCancellationViewSet(viewsets.ModelViewSet):
    queryset = ScheduledEventCancellation.objects.all().select_related('event')
    serializer_class = ScheduledEventCancellationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().select_related('subsidiary')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


# ViewSets для learning моделей
class LearningMaterialViewSet(viewsets.ModelViewSet):
    queryset = LearningMaterial.objects.all()
    serializer_class = LearningMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class LearningMaterialNodeViewSet(viewsets.ModelViewSet):
    queryset = LearningMaterialNode.objects.all().select_related('material', 'parent')
    serializer_class = LearningMaterialNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class CurriculumViewSet(viewsets.ModelViewSet):
    queryset = Curriculum.objects.all()
    serializer_class = CurriculumSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class CurriculumNodeViewSet(viewsets.ModelViewSet):
    queryset = CurriculumNode.objects.all().select_related('curriculum', 'parent')
    serializer_class = CurriculumNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class CurriculumNodeMaterialViewSet(viewsets.ModelViewSet):
    queryset = CurriculumNodeMaterial.objects.all().select_related('curriculum_node', 'material_node')
    serializer_class = CurriculumNodeMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class GroupCourseCurriculumViewSet(viewsets.ModelViewSet):
    queryset = GroupCourseCurriculum.objects.all().select_related('group_course', 'curriculum')
    serializer_class = GroupCourseCurriculumSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


# ViewSets для rules моделей
class WorkingPeriodRuleViewSet(viewsets.ModelViewSet):
    queryset = WorkingPeriodRule.objects.all().select_related('subsidiary')
    serializer_class = WorkingPeriodRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class TeacherAvailabilityPeriodViewSet(viewsets.ModelViewSet):
    queryset = TeacherAvailabilityPeriod.objects.all().select_related('teacher')
    serializer_class = TeacherAvailabilityPeriodSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all().select_related('subsidiary')
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class RoomAvailabilityRuleViewSet(viewsets.ModelViewSet):
    queryset = RoomAvailabilityRule.objects.all().select_related('room')
    serializer_class = RoomAvailabilityRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class ConflictTypeViewSet(viewsets.ModelViewSet):
    queryset = ConflictType.objects.all()
    serializer_class = ConflictTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class ConflictViewSet(viewsets.ModelViewSet):
    queryset = Conflict.objects.all().select_related('conflict_type', 'resolved_by')
    serializer_class = ConflictSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по параметрам
        plan_id = self.request.query_params.get('plan')
        resolved = self.request.query_params.get('resolved')
        conflict_type = self.request.query_params.get('type')
        
        if plan_id:
            # Получаем события указанного плана
            from schedule.models import ScheduledEvent
            event_ids = ScheduledEvent.objects.filter(schedule_plan_id=plan_id).values_list('id', flat=True)
            queryset = queryset.filter(scheduled_event_id__in=event_ids)
        if resolved is not None:
            if resolved.lower() == 'true':
                # Фильтр для разрешенных конфликтов
                queryset = queryset.filter(status__in=['resolved', 'ignored'])
            else:
                # Фильтр для неразрешенных конфликтов
                queryset = queryset.filter(status__in=['detected', 'acknowledged', 'in_progress'])
        if conflict_type:
            queryset = queryset.filter(conflict_type=conflict_type)
            
        return queryset.order_by('-detected_at')

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Разрешить конфликт"""
        conflict = self.get_object()
        resolver = ConflictResolver()
        
        # Получаем предложения по разрешению
        suggestions = resolver.suggest_solutions(conflict)
        
        # Пытаемся автоматически разрешить
        if resolver.can_auto_resolve(conflict):
            success = resolver.auto_resolve_conflict(conflict)
            return Response({
                'resolved': success,
                'suggestions': suggestions
            })
        
        return Response({
            'resolved': False,
            'suggestions': suggestions,
            'message': 'Конфликт требует ручного разрешения'
        })


# ViewSets для пользователей
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


@api_view(['POST'])
@permission_classes([AllowAny])  # Разрешаем без авторизации для тестирования
def check_conflicts_simple(request):
    """
    Простая проверка конфликтов для активного плана расписания.
    POST /api/v1/check_conflicts/
    """
    try:
        # Находим активный план расписания
        plan = SchedulePlan.objects.filter(is_active=True).first()
        if not plan:
            return Response(
                {'error': 'Активный план расписания не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Используем функцию детекции конфликтов
        from schedule.conflict_detection import detect_and_save_conflicts
        conflicts = detect_and_save_conflicts(plan)
        
        return Response({
            'plan_id': plan.id,
            'plan_name': plan.name,
            'conflicts': [
                {
                    'id': conflict.id,
                    'type': conflict.conflict_type.name,
                    'description': conflict.description,
                    'severity': conflict.conflict_type.severity,
                    'scheduled_event_id': conflict.scheduled_event_id,
                } for conflict in conflicts
            ],
            'total_conflicts': len(conflicts)
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
