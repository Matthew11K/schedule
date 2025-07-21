from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # Главная страница
    path('', views.landing, name='landing'),
    
    # Основные страницы
    path('dashboard/', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule, name='schedule'),
    path('reports/', views.reports, name='reports'),
    
    # Индивидуальные расписания
    path('teacher/<int:teacher_id>/schedule/', views.teacher_schedule, name='teacher_schedule'),
    path('group/<int:group_id>/schedule/', views.group_schedule, name='group_schedule'),
    
    # AJAX endpoints
    path('api/conflicts/check/', views.ConflictCheckView.as_view(), name='check_conflicts'),
    path('modals/event/', views.EventModalView.as_view(), name='event_modal'),
] 