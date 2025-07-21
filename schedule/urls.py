from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'schedule-plans', views.SchedulePlanViewSet)
# router.register(r'scheduled-events', views.ScheduledEventViewSet)
# router.register(r'events', views.EventViewSet)
# router.register(r'lessons', views.LessonViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 