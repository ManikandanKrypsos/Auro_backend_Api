from django.urls import path
from .views import TreatmentListView, TreatmentDetailView, TreatmentMetaView

urlpatterns = [
    path('',          TreatmentListView.as_view()),    # GET, POST
    path('meta/',     TreatmentMetaView.as_view()),    # GET dropdown options
    path('<int:pk>/', TreatmentDetailView.as_view()),  # GET, PATCH, PUT, DELETE
]