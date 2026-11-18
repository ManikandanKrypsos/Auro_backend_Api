from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,
    MeView, UserListView, RolesListView,
    RefreshTokenView, ForgotPasswordView,
    VerifyOTPView, ResetPasswordView,
    StaffDetailView, StaffTreatmentsView, ChangePasswordView, StaffResetPasswordView,
    WorkingHoursListView, WorkingHoursDetailView,
    BreakTimeListView, BreakTimeDetailView,
    LeaveListView, LeaveDetailView,
)

urlpatterns = [
    # Auth
    path('register/',                   RegisterView.as_view()),
    path('login/',                      LoginView.as_view()),
    path('logout/',                     LogoutView.as_view()),
    path('refresh/',                    RefreshTokenView.as_view()),
    path('me/',                         MeView.as_view()),
    path('roles/',                      RolesListView.as_view()),
    path('forgot-password/',            ForgotPasswordView.as_view()),
    path('verify-otp/',                 VerifyOTPView.as_view()),
    path('reset-password/',             ResetPasswordView.as_view()),

    # Staff CRUD — image upload via multipart/form-data in PATCH
    path('staff/',                      UserListView.as_view()),
    path('staff/<int:pk>/',             StaffDetailView.as_view()),  # GET, PATCH, DELETE
    path('staff/<int:pk>/treatments/',  StaffTreatmentsView.as_view()),  # GET, PATCH {treatment_ids}
    path('staff/<int:pk>/reset-password/', StaffResetPasswordView.as_view()),  # POST new temp password
    path('change-password/',            ChangePasswordView.as_view()),  # POST set own password

    # Working Hours
    path('staff/<int:staff_id>/working-hours/',          WorkingHoursListView.as_view()),
    path('staff/<int:staff_id>/working-hours/<int:pk>/', WorkingHoursDetailView.as_view()),

    # Break Times
    path('staff/<int:staff_id>/break-times/',            BreakTimeListView.as_view()),
    path('staff/<int:staff_id>/break-times/<int:pk>/',   BreakTimeDetailView.as_view()),

    # Leaves
    path('staff/<int:staff_id>/leaves/',                 LeaveListView.as_view()),
    path('staff/<int:staff_id>/leaves/<int:pk>/',        LeaveDetailView.as_view()),
]