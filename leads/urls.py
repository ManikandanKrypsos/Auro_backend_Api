from django.urls import path
from .views import (
    LeadMetaView, LeadStatsView, LeadPipelineView,
    LeadListView, LeadDetailView,
    LeadStageView, LeadActivityView, LeadConvertView,
)

urlpatterns = [
    path('',                        LeadListView.as_view()),      # GET, POST
    path('meta/',                   LeadMetaView.as_view()),      # GET dropdown options
    path('stats/',                  LeadStatsView.as_view()),     # GET pipeline stats
    path('pipeline/',               LeadPipelineView.as_view()),  # GET kanban board
    path('<int:pk>/',               LeadDetailView.as_view()),    # GET, PATCH, DELETE
    path('<int:pk>/stage/',         LeadStageView.as_view()),     # PATCH move stage
    path('<int:pk>/activity/',      LeadActivityView.as_view()),  # GET, POST
    path('<int:pk>/convert/',       LeadConvertView.as_view()),   # POST convert to patient
]