from django.urls import path
from .views import (
    InventoryMetaView, InventoryListView,
    InventoryDetailView, StockMovementListView,
)

urlpatterns = [
    path('',                      InventoryListView.as_view()),        # GET, POST
    path('meta/',                 InventoryMetaView.as_view()),        # GET dropdown options
    path('<int:pk>/',             InventoryDetailView.as_view()),      # GET, PATCH, DELETE
    path('<int:pk>/movements/',   StockMovementListView.as_view()),    # GET, POST
]