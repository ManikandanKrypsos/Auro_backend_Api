from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,
    MeView, UserListView, RolesListView,
    RefreshTokenView, ForgotPasswordView,
    VerifyOTPView, ResetPasswordView
)

urlpatterns = [
    path('register/',         RegisterView.as_view()),
    path('login/',            LoginView.as_view()),
    path('logout/',           LogoutView.as_view()),
    path('refresh/',          RefreshTokenView.as_view()),
    path('me/',               MeView.as_view()),
    path('staff/',            UserListView.as_view()),
    path('roles/',            RolesListView.as_view()),
    path('forgot-password/',  ForgotPasswordView.as_view()),
    path('verify-otp/',       VerifyOTPView.as_view()),
    path('reset-password/',   ResetPasswordView.as_view()),
]