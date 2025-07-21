from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path, include

from . import views

# Создаем роутер для API
router = DefaultRouter()

# Регистрируем ViewSets для core моделей
router.register(r'subsidiaries', views.SubsidiaryViewSet)
router.register(r'subjects', views.SubjectViewSet)
router.register(r'levels', views.LevelViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'packages', views.PackageViewSet)
router.register(r'teachers', views.TeacherViewSet)
router.register(r'rooms', views.RoomViewSet)

# Регистрируем ViewSets для groups моделей
router.register(r'groups', views.GroupViewSet)
router.register(r'group-courses', views.GroupCourseViewSet)
router.register(r'students', views.StudentViewSet)

# Регистрируем ViewSets для schedule моделей
router.register(r'schedule-plans', views.SchedulePlanViewSet)
router.register(r'scheduled-events', views.ScheduledEventViewSet)
router.register(r'scheduled-event-cancellations', views.ScheduledEventCancellationViewSet)
router.register(r'events', views.EventViewSet)

# Регистрируем ViewSets для learning моделей
router.register(r'learning-materials', views.LearningMaterialViewSet)
router.register(r'learning-material-nodes', views.LearningMaterialNodeViewSet)
router.register(r'curricula', views.CurriculumViewSet)
router.register(r'curriculum-nodes', views.CurriculumNodeViewSet)
router.register(r'curriculum-node-materials', views.CurriculumNodeMaterialViewSet)
router.register(r'group-course-curricula', views.GroupCourseCurriculumViewSet)

# Регистрируем ViewSets для rules моделей
router.register(r'working-period-rules', views.WorkingPeriodRuleViewSet)
router.register(r'teacher-availability-periods', views.TeacherAvailabilityPeriodViewSet)
router.register(r'time-slots', views.TimeSlotViewSet)
router.register(r'room-availability-rules', views.RoomAvailabilityRuleViewSet)
router.register(r'conflict-types', views.ConflictTypeViewSet)
router.register(r'conflicts', views.ConflictViewSet)

# Регистрируем ViewSets для пользователей
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # JWT аутентификация
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Простая проверка конфликтов
    path('check_conflicts/', views.check_conflicts_simple, name='check_conflicts_simple'),
    
    # API endpoints
    path('', include(router.urls)),
    
    # Browsable API (для разработки)
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
] 