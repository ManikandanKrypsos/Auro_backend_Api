from django.urls import path

from .course_views import (
    CourseDetailView, CourseListView, CoursePlanDetailView, CoursePlanGenerateView, CoursePlanView,
    CourseProgressDetailView, CourseProgressView, CourseResetProtocolView,
)

urlpatterns = [
    path('',                                   CourseListView.as_view()),            # GET, POST
    path('<int:pk>/',                          CourseDetailView.as_view()),          # GET, PATCH, DELETE
    path('<int:pk>/reset-protocol/',           CourseResetProtocolView.as_view()),   # POST
    path('<int:pk>/progress/',                 CourseProgressView.as_view()),        # POST
    path('<int:pk>/progress/<int:entry_id>/',  CourseProgressDetailView.as_view()),  # PATCH, DELETE
    path('<int:pk>/plan/',                     CoursePlanView.as_view()),            # POST
    path('<int:pk>/plan/generate/',            CoursePlanGenerateView.as_view()),    # POST
    path('<int:pk>/plan/<int:plan_id>/',       CoursePlanDetailView.as_view()),      # PATCH, DELETE
]
