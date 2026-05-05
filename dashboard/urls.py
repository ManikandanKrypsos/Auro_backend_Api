from django.urls import path
from .views import (
    DashboardView,
    ReceptionDashboardView,
    TherapistDashboardView,
    AdminDashboardView,
)

urlpatterns = [
    path('',             DashboardView.as_view()),          # auto-detects role
    path('reception/',   ReceptionDashboardView.as_view()), # force reception view
    path('therapist/',   TherapistDashboardView.as_view()), # force therapist view
    path('admin/',       AdminDashboardView.as_view()),     # force admin view
]