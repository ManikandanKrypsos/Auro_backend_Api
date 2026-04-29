from django.urls import path
from .views import (
    InventoryMetaView, InventoryListView,
    InventoryDetailView, StockMovementListView,
    OutOfStockView,
)

urlpatterns = [
    path('',                      InventoryListView.as_view()),        # GET, POST
    path('meta/',                 InventoryMetaView.as_view()),        # GET dropdown options
    path('out-of-stock/',         OutOfStockView.as_view()),           # GET out of stock
    path('<int:pk>/',             InventoryDetailView.as_view()),      # GET, PATCH, DELETE
    path('<int:pk>/movements/',   StockMovementListView.as_view()),    # GET, POST
]