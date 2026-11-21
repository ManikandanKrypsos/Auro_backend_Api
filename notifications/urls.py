from django.urls import path
from . import views as v

urlpatterns = [
    path('',                v.NotificationListView.as_view()),   # GET (paginated, includes unread_count)
    path('unread-count/',   v.UnreadCountView.as_view()),        # GET — cheap, for the badge
    path('mark-all-read/',  v.MarkAllReadView.as_view()),        # POST
    path('preferences/',    v.PreferencesView.as_view()),        # GET, PATCH
    path('<int:pk>/',       v.NotificationDetailView.as_view()), # PATCH {is_read}
]
