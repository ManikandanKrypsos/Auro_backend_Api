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
from .invoice_views import (PaymentReceiptView, PaymentRecordDetailView, PaymentRecordListView, PaymentRefundView,
                            ReconcileView, ReconciliationSummaryView)

urlpatterns = [
    path('',                                  PaymentListView.as_view()),   # GET screen list, POST record a payment
    path('records/',                          PaymentRecordListView.as_view()),
    path('records/reconcile/',                ReconcileView.as_view()),        # POST bulk mark / unmark (admin)
    path('reconciliation/',                   ReconciliationSummaryView.as_view()),  # GET per-method totals
    path('records/<int:pk>/',                 PaymentRecordDetailView.as_view()),
    path('records/<int:pk>/refund/',          PaymentRefundView.as_view()),    # POST partial / full refund
    path('records/<int:pk>/receipt/',         PaymentReceiptView.as_view()),   # GET JSON, ?output=pdf
    path('create-checkout-session/',          CreateCheckoutSessionView.as_view()),
    path('create-intent/',                    CreatePaymentIntentView.as_view()),
    path('confirm/',                          ConfirmPaymentView.as_view()),
    path('refund/',                           RefundPaymentView.as_view()),
    path('mark-paid/',                        MarkAsPaidView.as_view()),
    path('webhook/',                          StripeWebhookView.as_view()),
    path('status/<int:appointment_id>/',      PaymentStatusView.as_view()),
    path('invoice/<int:appointment_id>/',     InvoiceDetailView.as_view()),
]