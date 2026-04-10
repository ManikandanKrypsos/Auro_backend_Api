from django.urls import path
from .views import RegisterView, LoginView, MeView, UserListView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('me/', MeView.as_view()),
    path('staff/', UserListView.as_view()),  # Admin only
]