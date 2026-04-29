from django.urls import path
from .views import (
    TreatmentListView, TreatmentDetailView, TreatmentMetaView,
    PricePlanListView, PricePlanDetailView,
    ContraindicationView,
)

urlpatterns = [
    path('',                                                TreatmentListView.as_view()),
    path('meta/',                                           TreatmentMetaView.as_view()),
    path('<int:pk>/',                                       TreatmentDetailView.as_view()),
    path('<int:pk>/price-plans/',                           PricePlanListView.as_view()),
    path('<int:pk>/price-plans/<int:plan_id>/',             PricePlanDetailView.as_view()),
    path('<int:pk>/contraindications/',                     ContraindicationView.as_view()),
]