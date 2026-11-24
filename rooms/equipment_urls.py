from django.urls import path

from .equipment_views import EquipmentDetailView, EquipmentListView, EquipmentStatusesView

urlpatterns = [
    path('',          EquipmentListView.as_view()),      # GET, POST
    path('statuses/', EquipmentStatusesView.as_view()),  # GET status choices
    path('<int:pk>/', EquipmentDetailView.as_view()),    # GET, PATCH, PUT, DELETE
]
