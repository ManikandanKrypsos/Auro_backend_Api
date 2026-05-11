from django.urls import path
from .views import (
    PackageListView,
    PackageDetailView,
    PackageStatusView,
    PackageScheduleSessionView,
)

urlpatterns = [
    path('',                              PackageListView.as_view()),           # GET, POST
    path('<int:pk>/',                     PackageDetailView.as_view()),         # GET, PATCH
    path('<int:pk>/status/',              PackageStatusView.as_view()),         # PATCH
    path('<int:pk>/schedule-session/',    PackageScheduleSessionView.as_view()),# POST
]