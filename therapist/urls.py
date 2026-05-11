from django.urls import path
from .views import (
    TherapistAppointmentsView,
    TherapistTodayView,
    TherapistPatientsView,
    TherapistScheduleView,
    TherapistProductUsageView,
)
from .session_views import (
    SessionDetailView,
    SessionStartView,
    SessionCompleteView,
    SessionNoteUpdateView,
)

urlpatterns = [
    path('appointments/',               TherapistAppointmentsView.as_view()),
    path('today/',                      TherapistTodayView.as_view()),
    path('patients/',                   TherapistPatientsView.as_view()),
    path('schedule/',                   TherapistScheduleView.as_view()),
    path('products/use/',               TherapistProductUsageView.as_view()),
    path('sessions/<int:pk>/',          SessionDetailView.as_view()),
    path('sessions/<int:pk>/start/',    SessionStartView.as_view()),
    path('sessions/<int:pk>/complete/', SessionCompleteView.as_view()),
    path('sessions/<int:pk>/note/',     SessionNoteUpdateView.as_view()),
]