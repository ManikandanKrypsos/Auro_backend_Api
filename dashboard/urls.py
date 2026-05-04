from django.urls import path
from .views import (
    ReceptionDashboardView,
    DashboardOverviewView,
    BestServicesView,
    StaffPerformanceView,
    RevenueChartView,
    RebookingRateView,
)

urlpatterns = [
    path('',                   DashboardOverviewView.as_view()),   # Admin dashboard
    path('reception/',         ReceptionDashboardView.as_view()),  # Reception dashboard
    path('best-services/',     BestServicesView.as_view()),
    path('staff-performance/', StaffPerformanceView.as_view()),
    path('revenue-chart/',     RevenueChartView.as_view()),
    path('rebooking-rate/',    RebookingRateView.as_view()),
]