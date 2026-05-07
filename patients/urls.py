from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, MarketingSourceListView, PatientVIPView
from .patient_detail_views import (
    PatientOverviewView, PatientHistoryView,
    PatientNotesView, PatientNoteDetailView,
    PatientPhotosView, PatientConsentView, PatientConsentDetailView,
)

router = DefaultRouter()
router.register(r'', PatientViewSet, basename='patient')

urlpatterns = [
    path('marketing-sources/',                  MarketingSourceListView.as_view()),
    path('<str:pk>/vip/',                       PatientVIPView.as_view()),
    path('<str:pk>/overview/',                  PatientOverviewView.as_view()),
    path('<str:pk>/history/',                   PatientHistoryView.as_view()),
    path('<str:pk>/notes/',                     PatientNotesView.as_view()),
    path('<str:pk>/notes/<int:note_id>/',       PatientNoteDetailView.as_view()),
    path('<str:pk>/photos/',                    PatientPhotosView.as_view()),
    path('<str:pk>/consent/',                   PatientConsentView.as_view()),
    path('<str:pk>/consent/<int:record_id>/',   PatientConsentDetailView.as_view()),
    path('', include(router.urls)),
]