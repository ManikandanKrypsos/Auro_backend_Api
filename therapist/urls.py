from django.urls import path
from .views import (
    TherapistAppointmentsView,
    TherapistTodayView,
    TherapistPatientsView,
    TherapistScheduleView,
)

urlpatterns = [
    path('appointments/', TherapistAppointmentsView.as_view()),  # GET all appointments
    path('today/',        TherapistTodayView.as_view()),         # GET today's summary
    path('patients/',     TherapistPatientsView.as_view()),      # GET only their patients
    path('schedule/',     TherapistScheduleView.as_view()),      # GET schedule by date range
]