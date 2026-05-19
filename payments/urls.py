from django.urls import path
from .views import (
    CreatePaymentIntentView,
    ConfirmPaymentView,
    RefundPaymentView,
    PaymentStatusView,
    StripeWebhookView,
)

urlpatterns = [
    path('create-intent/', CreatePaymentIntentView.as_view()),
    path('confirm/',        ConfirmPaymentView.as_view()),
    path('refund/',         RefundPaymentView.as_view()),
    path('status/<int:appointment_id>/', PaymentStatusView.as_view()),
    path('webhook/',        StripeWebhookView.as_view()),
]