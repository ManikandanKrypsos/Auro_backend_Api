from django.urls import path

from .document_views import DocumentCountsView, DocumentDetailView, DocumentListView, DocumentTypesView

urlpatterns = [
    path('',          DocumentListView.as_view()),     # GET (queue), POST (upload)
    path('counts/',   DocumentCountsView.as_view()),   # GET
    path('types/',    DocumentTypesView.as_view()),    # GET
    path('<int:pk>/', DocumentDetailView.as_view()),   # GET, PATCH, DELETE
]
