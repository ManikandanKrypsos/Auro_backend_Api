from django.urls import path
from .views import (
    TherapistAppointmentsView,
    TherapistTodayView,
    TherapistPatientsView,
    TherapistPatientsByCategoryView,
    TherapistScheduleView,
)

urlpatterns = [
    path('appointments/',          TherapistAppointmentsView.as_view()),       # GET all appointments
    path('today/',                 TherapistTodayView.as_view()),               # GET today's summary
    path('patients/',              TherapistPatientsView.as_view()),            # GET only their patients
    path('patients/vip-returning/', TherapistPatientsByCategoryView.as_view()), # GET VIP & Returning patients
    path('schedule/',              TherapistScheduleView.as_view()),            # GET schedule by date range
]