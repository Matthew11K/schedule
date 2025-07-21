from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'groups', views.GroupViewSet)
# router.register(r'group-courses', views.GroupCourseViewSet)
# router.register(r'students', views.StudentViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 