from django.urls import path

from .views import AuditActionsView, AuditListView

urlpatterns = [
    path('',          AuditListView.as_view()),     # GET
    path('actions/',  AuditActionsView.as_view()),  # GET
]
