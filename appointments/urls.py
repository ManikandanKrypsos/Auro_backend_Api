from django.urls import path
from .views import (
    AppointmentListView, AppointmentDetailView,
    AppointmentStatusView, AppointmentArrivalView,
    AppointmentConsentView, AvailableSlotsView,
    TodayAppointmentsView, CalendarView,
    AppointmentMetaView,
)

urlpatterns = [
    path('',                            AppointmentListView.as_view()),    # GET, POST
    path('meta/',                       AppointmentMetaView.as_view()),    # GET dropdown options
    path('today/',                      TodayAppointmentsView.as_view()),  # GET
    path('calendar/',                   CalendarView.as_view()),           # GET
    path('available-slots/',            AvailableSlotsView.as_view()),     # GET
    path('<int:pk>/',                   AppointmentDetailView.as_view()),  # GET, PATCH, DELETE
    path('<int:pk>/status/',            AppointmentStatusView.as_view()),  # PATCH
    path('<int:pk>/arrived/',           AppointmentArrivalView.as_view()), # PATCH
    path('<int:pk>/consent/',           AppointmentConsentView.as_view()), # PATCH
]