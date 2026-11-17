from django.urls import path
from .views import SupplierListView, SupplierDetailView

urlpatterns = [
    path('',          SupplierListView.as_view()),     # GET, POST
    path('<int:pk>/', SupplierDetailView.as_view()),   # GET, PATCH, DELETE
]
