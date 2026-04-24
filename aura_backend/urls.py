from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        'message': 'Aura Clinic API is running! 🚀',
        'version': '1.0',
        'status': 'online',
        'endpoints': {
            'users':        '/api/users/',
            'patients':     '/api/patients/',
            'treatments':   '/api/treatments/',
            'appointments': '/api/appointments/',
            'leads':        '/api/leads/',
            'dashboard':    '/api/dashboard/',
            'roles':        '/api/users/roles/',
        }
    })

urlpatterns = [
    path('',       api_root),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/users/',        include('users.urls')),
    path('api/patients/',     include('patients.urls')),
    path('api/treatments/',   include('treatments.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/leads/',        include('leads.urls')),
    path('api/dashboard/',    include('dashboard.urls')),
    path('api/rooms/', include('rooms.urls')),
]