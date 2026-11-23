from django.urls import path
from .views import (
    PaymentListView,
    CreateCheckoutSessionView,
    CreatePaymentIntentView,
    ConfirmPaymentView,
    RefundPaymentView,
    PaymentStatusView,
    InvoiceDetailView,
    MarkAsPaidView,
    StripeWebhookView,
)
from .invoice_views import PaymentRecordDetailView, PaymentRecordListView

urlpatterns = [
    path('',                                  PaymentListView.as_view()),   # GET screen list, POST record a payment
    path('records/',                          PaymentRecordListView.as_view()),
    path('records/<int:pk>/',                 PaymentRecordDetailView.as_view()),
    path('create-checkout-session/',          CreateCheckoutSessionView.as_view()),
    path('create-intent/',                    CreatePaymentIntentView.as_view()),
    path('confirm/',                          ConfirmPaymentView.as_view()),
    path('refund/',                           RefundPaymentView.as_view()),
    path('mark-paid/',                        MarkAsPaidView.as_view()),
    path('webhook/',                          StripeWebhookView.as_view()),
    path('status/<int:appointment_id>/',      PaymentStatusView.as_view()),
    path('invoice/<int:appointment_id>/',     InvoiceDetailView.as_view()),
]