from django.urls import path
from . import views as v

clinic_urlpatterns = [
    path('register/', v.ClinicRegisterView.as_view()),                      # POST (public)
]

platform_urlpatterns = [
    path('login/',                       v.PlatformLoginView.as_view()),        # POST
    path('me/',                          v.PlatformMeView.as_view()),           # GET
    path('clinics/',                     v.PlatformClinicListView.as_view()),   # GET
    path('clinics/<int:pk>/',            v.PlatformClinicDetailView.as_view()), # GET
    path('clinics/<int:pk>/status/',     v.PlatformClinicStatusView.as_view()), # POST activate / suspend
]
