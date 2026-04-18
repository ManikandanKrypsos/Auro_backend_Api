from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, MarketingSourceListView

router = DefaultRouter()
router.register(r'', PatientViewSet, basename='patient')

urlpatterns = [
    path('marketing-sources/', MarketingSourceListView.as_view()),
    path('', include(router.urls)),
]