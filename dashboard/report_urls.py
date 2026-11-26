from django.urls import path

from .reports import AppointmentOutcomesView, AverageTicketView, PatientRetentionView, RevenueByTreatmentView

urlpatterns = [
    path('revenue-by-treatment/', RevenueByTreatmentView.as_view()),
    path('average-ticket/',       AverageTicketView.as_view()),
    path('appointment-outcomes/', AppointmentOutcomesView.as_view()),
    path('patient-retention/',    PatientRetentionView.as_view()),
]
