from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/patients/', include('patients.urls')),
    path('api/treatments/', include('treatments.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/leads/', include('leads.urls')),
    path('api/dashboard/', include('dashboard.urls')),
]