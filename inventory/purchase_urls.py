from django.urls import path
from .purchase_views import PurchaseOrderListView, PurchaseOrderDetailView, PurchaseOrderReceiveView

urlpatterns = [
    path('',                  PurchaseOrderListView.as_view()),     # GET, POST
    path('<int:pk>/',         PurchaseOrderDetailView.as_view()),   # GET, PATCH
    path('<int:pk>/receive/', PurchaseOrderReceiveView.as_view()),  # POST (partial receipts)
]
