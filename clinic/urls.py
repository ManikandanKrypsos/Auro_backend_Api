from django.urls import path
from .views import (
    ClinicHoursView, ClinicHoursDayView,
    PlannedClosureListView, PlannedClosureDetailView,
)

urlpatterns = [
    # Clinic Hours
    path('hours/',             ClinicHoursView.as_view()),        # GET, POST (bulk)
    path('hours/<str:day>/',   ClinicHoursDayView.as_view()),     # PATCH single day

    # Planned Closures
    path('closures/',          PlannedClosureListView.as_view()),  # GET, POST
    path('closures/<int:pk>/', PlannedClosureDetailView.as_view()),# GET, PATCH, DELETE
]