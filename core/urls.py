from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'subsidiaries', views.SubsidiaryViewSet)
# router.register(r'subjects', views.SubjectViewSet)
# router.register(r'levels', views.LevelViewSet)
# router.register(r'courses', views.CourseViewSet)
# router.register(r'packages', views.PackageViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 