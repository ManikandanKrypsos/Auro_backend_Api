from django.urls import path
from .views import (
    InventoryMetaView, InventoryListView,
    InventoryDetailView, StockMovementListView,
    OutOfStockView, StockCountView,
    ReceiveStockView, AdjustStockView,
)

urlpatterns = [
    path('',                      InventoryListView.as_view()),        # GET, POST
    path('meta/',                 InventoryMetaView.as_view()),        # GET dropdown options
    path('out-of-stock/',         OutOfStockView.as_view()),           # GET list
    path('stock-count/',          StockCountView.as_view()),           # GET counts only
    path('<int:pk>/',             InventoryDetailView.as_view()),      # GET, PATCH, DELETE
    path('<int:pk>/movements/',   StockMovementListView.as_view()),    # GET, POST
    path('<int:pk>/receive/',     ReceiveStockView.as_view()),         # POST receive stock
    path('<int:pk>/adjust/',      AdjustStockView.as_view()),          # POST wastage / correction
]