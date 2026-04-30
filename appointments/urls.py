from django.urls import path
from .views import (
    AppointmentListView, AppointmentDetailView,
    AppointmentStatusView, AppointmentArrivalView,
    AppointmentConsentView, AvailableSlotsView,
    TodayAppointmentsView, CalendarView,
)

urlpatterns = [
    # Core CRUD
    path('',                            AppointmentListView.as_view()),    # GET, POST
    path('<int:pk>/',                   AppointmentDetailView.as_view()),  # GET, PATCH, DELETE

    # Actions
    path('<int:pk>/status/',            AppointmentStatusView.as_view()),  # PATCH
    path('<int:pk>/arrived/',           AppointmentArrivalView.as_view()), # PATCH
    path('<int:pk>/consent/',           AppointmentConsentView.as_view()), # PATCH

    # Calendar & Availability
    path('today/',                      TodayAppointmentsView.as_view()),  # GET
    path('calendar/',                   CalendarView.as_view()),           # GET
    path('available-slots/',            AvailableSlotsView.as_view()),     # GET
]