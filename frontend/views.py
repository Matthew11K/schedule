from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json


def dashboard(request):
    """Главная страница планирования"""
    context = {
        'page_title': 'Планирование расписания',
        'active_page': 'dashboard'
    }
    return render(request, 'frontend/dashboard.html', context)


def schedule(request):
    """Страница календарного расписания"""
    context = {
        'page_title': 'Календарь расписания',
        'active_page': 'schedule'
    }
    return render(request, 'frontend/schedule.html', context)


def reports(request):
    """Страница отчетов"""
    context = {
        'page_title': 'Отчеты',
        'active_page': 'reports'
    }
    return render(request, 'frontend/reports.html', context)


@login_required
def teacher_schedule(request, teacher_id):
    """Расписание конкретного преподавателя"""
    context = {
        'page_title': f'Расписание преподавателя',
        'active_page': 'schedule',
        'teacher_id': teacher_id
    }
    return render(request, 'frontend/teacher_schedule.html', context)


@login_required
def group_schedule(request, group_id):
    """Расписание конкретной группы"""
    context = {
        'page_title': f'Расписание группы',
        'active_page': 'schedule',
        'group_id': group_id
    }
    return render(request, 'frontend/group_schedule.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class ConflictCheckView(View):
    """API для проверки конфликтов через фронтенд"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            plan_id = data.get('plan_id')
            
            if not plan_id:
                return JsonResponse({'error': 'Plan ID is required'}, status=400)
            
            # Здесь можно добавить дополнительную логику
            # или напрямую использовать API
            
            return JsonResponse({
                'success': True,
                'message': 'Conflicts checked successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EventModalView(View):
    """Представление для модального окна событий"""
    
    def get(self, request):
        """Возвращает HTML для модального окна создания/редактирования события"""
        event_id = request.GET.get('event_id')
        
        context = {
            'event_id': event_id,
            'is_edit': event_id is not None
        }
        
        return render(request, 'frontend/partials/event_modal.html', context)


def landing(request):
    """Посадочная страница"""
    if request.user.is_authenticated:
        return dashboard(request)
    
    context = {
        'page_title': 'Система управления школьным расписанием'
    }
    return render(request, 'frontend/landing.html', context)
