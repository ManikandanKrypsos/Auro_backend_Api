from django.urls import path
from .views import (
    DashboardOverviewView,
    BestServicesView,
    StaffPerformanceView,
    RevenueChartView,
    RebookingRateView,
)

urlpatterns = [
    path('',                  DashboardOverviewView.as_view()),
    path('best-services/',    BestServicesView.as_view()),
    path('staff-performance/', StaffPerformanceView.as_view()),
    path('revenue-chart/',    RevenueChartView.as_view()),
    path('rebooking-rate/',   RebookingRateView.as_view()),
]