from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from appointments.schedule_views import DayScheduleView
from utils.health import health
from tenants.urls import billing_urlpatterns, clinic_urlpatterns, platform_urlpatterns


def api_root(request):
    return JsonResponse({
        'message': 'Aura Clinic API is running! 🚀',
        'version': '1.0',
        'status': 'online',
        'endpoints': {
            'users':        '/api/users/',
            'patients':     '/api/patients/',
            'documents':    '/api/documents/',
            'treatments':   '/api/treatments/',
            'appointments': '/api/appointments/',
            'leads':        '/api/leads/',
            'dashboard':    '/api/dashboard/',
            'reports':      '/api/reports/',
            'audit':        '/api/audit/',
            'roles':        '/api/users/roles/',
            'rooms':        '/api/rooms/',
            'equipment':    '/api/equipment/',
            'clinic':       '/api/clinic/',
            'inventory':    '/api/inventory/',
            'suppliers':    '/api/suppliers/',
            'purchase_orders': '/api/purchase-orders/',
            'therapist':    '/api/therapist/',
            'packages':     '/api/packages/',
            'courses':      '/api/courses/',
            'ai':           '/api/ai/',
            'payments':     '/api/payments/',
            'schedule_day': '/api/schedule/day/?date=YYYY-MM-DD',
        }
    })

urlpatterns = [
    path('',       api_root),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/clinics/',      include(clinic_urlpatterns)),     # clinic registration (public)
    path('api/platform/',     include(platform_urlpatterns)),   # Super Admin (separate login)
    path('api/billing/',      include(billing_urlpatterns)),    # clinic subscription (Stripe)
    path('api/notifications/', include('notifications.urls')),  # in-app bell
    path('api/invoices/',     include('payments.invoice_urls')),  # invoices (lines, payments, balance)
    path('api/health/',       health),                          # uptime monitor / keep-warm
    path('api/users/',        include('users.urls')),
    path('api/patients/',     include('patients.urls')),
    path('api/documents/',    include('patients.document_urls')),   # patient documents (consents, IDs, lab results...)
    path('api/treatments/',   include('treatments.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/leads/',        include('leads.urls')),
    path('api/dashboard/',    include('dashboard.urls')),
    path('api/reports/',      include('dashboard.report_urls')),   # Reports module (admin)
    path('api/audit/',        include('audit.urls')),              # audit trail (admin, read only)
    path('api/rooms/', include('rooms.urls')),
    path('api/equipment/', include('rooms.equipment_urls')),
    path('api/clinic/', include('clinic.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/suppliers/', include('inventory.supplier_urls')),
    path('api/purchase-orders/', include('inventory.purchase_urls')),
    path('api/therapist/', include('therapist.urls')),
    path('api/packages/', include('packages.urls')),
    path('api/courses/', include('packages.course_urls')),     # treatment courses (Protocol tab)
    path('api/ai/', include('ai_agent.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/schedule/day/', DayScheduleView.as_view()),   # calendar: one day, all staff + rooms
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)