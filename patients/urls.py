from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, MarketingSourceListView, PatientVIPView

router = DefaultRouter()
router.register(r'', PatientViewSet, basename='patient')

urlpatterns = [
    path('marketing-sources/', MarketingSourceListView.as_view()),
    path('<str:pk>/vip/',      PatientVIPView.as_view()),   # PATCH mark/unmark VIP
    path('', include(router.urls)),
]