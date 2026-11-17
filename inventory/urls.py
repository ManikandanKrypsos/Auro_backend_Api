from django.urls import path
from .views import (
    InventoryMetaView, InventoryListView,
    InventoryDetailView, StockMovementListView,
    OutOfStockView, StockCountView,
    ReceiveStockView, AdjustStockView,
)
from .lot_views import ItemLotsView, NearExpiryView, InventorySummaryView

urlpatterns = [
    path('',                      InventoryListView.as_view()),        # GET, POST
    path('meta/',                 InventoryMetaView.as_view()),        # GET dropdown options
    path('out-of-stock/',         OutOfStockView.as_view()),           # GET list
    path('stock-count/',          StockCountView.as_view()),           # GET counts only
    path('summary/',              InventorySummaryView.as_view()),     # GET dashboard KPIs
    path('near-expiry/',          NearExpiryView.as_view()),           # GET ?days=90
    path('<int:pk>/',             InventoryDetailView.as_view()),      # GET, PATCH, DELETE
    path('<int:pk>/movements/',   StockMovementListView.as_view()),    # GET, POST
    path('<int:pk>/receive/',     ReceiveStockView.as_view()),         # POST receive stock
    path('<int:pk>/adjust/',      AdjustStockView.as_view()),          # POST wastage / correction
    path('<int:pk>/lots/',        ItemLotsView.as_view()),             # GET lots of an item
]