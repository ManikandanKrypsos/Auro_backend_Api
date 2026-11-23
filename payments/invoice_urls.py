from django.urls import path
from . import invoice_views as v

urlpatterns = [
    path('',                                       v.InvoiceListView.as_view()),        # GET, POST
    path('settings/',                              v.InvoiceSettingsView.as_view()),    # GET, PATCH
    path('ageing/',                                v.AgeingReportView.as_view()),       # GET outstanding by days overdue
    path('for-appointment/<int:appointment_id>/',  v.AppointmentInvoiceView.as_view()), # GET
    path('<int:pk>/',                              v.InvoiceDetailNewView.as_view()),   # GET, PATCH
    path('<int:pk>/void/',                         v.InvoiceVoidView.as_view()),        # POST
]
