from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'materials', views.LearningMaterialViewSet)
# router.register(r'collections', views.LearningMaterialCollectionViewSet)
# router.register(r'curriculums', views.CurriculumViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 