from django.urls import path
from .views import (
    LeadMetaView, LeadStatsView, LeadPipelineView,
    LeadListView, LeadDetailView,
    LeadStageView, LeadActivityView, LeadConvertView,
    LeadHistoryView, LeadNotesView, LeadTasksView, LeadTaskDetailView, LeadAssigneesView,
)

urlpatterns = [
    path('',                        LeadListView.as_view()),      # GET, POST
    path('meta/',                   LeadMetaView.as_view()),      # GET dropdown options
    path('stats/',                  LeadStatsView.as_view()),     # GET pipeline stats
    path('pipeline/',               LeadPipelineView.as_view()),  # GET kanban board
    path('assignees/',              LeadAssigneesView.as_view()), # GET who a lead can be assigned to
    path('<int:pk>/',               LeadDetailView.as_view()),    # GET, PATCH, DELETE
    path('<int:pk>/stage/',         LeadStageView.as_view()),     # PATCH move stage
    path('<int:pk>/activity/',      LeadActivityView.as_view()),  # GET, POST
    path('<int:pk>/convert/',       LeadConvertView.as_view()),   # POST convert to patient (stores the link)
    path('<int:pk>/history/',       LeadHistoryView.as_view()),   # GET full activity log
    path('<int:pk>/notes/',         LeadNotesView.as_view()),     # GET, POST
    path('<int:pk>/tasks/',         LeadTasksView.as_view()),     # GET, POST
    path('<int:pk>/tasks/<int:task_id>/', LeadTaskDetailView.as_view()),  # PATCH, DELETE
]