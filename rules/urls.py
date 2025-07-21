from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'working-periods', views.WorkingPeriodRuleViewSet)
# router.register(r'teacher-availability', views.TeacherAvailabilityPeriodViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 