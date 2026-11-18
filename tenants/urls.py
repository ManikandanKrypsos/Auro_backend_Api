from django.urls import path
from . import billing_views as bv
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
    path('clinics/<int:pk>/billing/',    v.PlatformClinicBillingView.as_view()), # PATCH plan / trial / status override
    path('plans/',                       v.PlatformPlanListView.as_view()),     # GET, POST
    path('plans/<int:pk>/',              v.PlatformPlanDetailView.as_view()),   # PATCH
]

billing_urlpatterns = [
    path('plans/',     bv.PlanListView.as_view()),        # GET (public)
    path('status/',    bv.BillingStatusView.as_view()),   # GET
    path('add-card/',  bv.AddCardView.as_view()),         # POST (clinic admin)
    path('webhook/',   bv.BillingWebhookView.as_view()),  # POST (Stripe)
]
