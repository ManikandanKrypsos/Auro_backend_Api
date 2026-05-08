from django.urls import path
from .views import (
    TherapistAppointmentsView,
    TherapistTodayView,
    TherapistPatientsView,
    TherapistScheduleView,
)
from .session_views import (
    SessionDetailView,
    SessionStartView,
    SessionCompleteView,
    SessionNoteUpdateView,
)

urlpatterns = [
    path('appointments/',              TherapistAppointmentsView.as_view()),  # GET all appointments
    path('today/',                     TherapistTodayView.as_view()),         # GET today summary
    path('patients/',                  TherapistPatientsView.as_view()),      # GET only their patients
    path('schedule/',                  TherapistScheduleView.as_view()),      # GET schedule by date range
    path('sessions/<int:pk>/',         SessionDetailView.as_view()),          # GET full session detail
    path('sessions/<int:pk>/start/',   SessionStartView.as_view()),           # PATCH start session
    path('sessions/<int:pk>/complete/', SessionCompleteView.as_view()),       # POST complete session
    path('sessions/<int:pk>/note/',    SessionNoteUpdateView.as_view()),      # PATCH update note
]