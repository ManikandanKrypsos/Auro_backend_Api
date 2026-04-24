from django.urls import path
from .views import RoomListView, RoomDetailView, RoomTypesView

urlpatterns = [
    path('',          RoomListView.as_view()),    # GET, POST
    path('types/',    RoomTypesView.as_view()),   # GET room type choices
    path('<int:pk>/', RoomDetailView.as_view()),  # GET, PATCH, PUT, DELETE
]