"""
Invoices and payments.

One invoice per appointment (created automatically) or standalone (e.g. a product sale).
An invoice has line items; payments (and refunds) are separate records against it, so an
invoice can be paid in several parts. Prices are tax-inclusive: tax is the part of each line
total that is tax, at the line's own rate.
"""
from django.conf import settings
from django.db import models

from tenants.managers import TenantManager


class Invoice(models.Model):
    STATUS_CHOICES = (
        ('open',           'Open'),             # nothing paid yet
        ('partially_paid', 'Partially paid'),
        ('paid',           'Paid'),
        ('refunded',       'Refunded'),         # everything paid was refunded
        ('void',           'Void'),             # cancelled, nothing owed
        ('no_charge',      'No charge'),        # total 0 (e.g. a package session)
    )

    clinic         = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                                       related_name='invoices')
    objects        = TenantManager()

    invoice_number = models.CharField(max_length=30)               # INV-2026-0042, per clinic
    patient        = models.ForeignKey('patients.Patient', on_delete=models.PROTECT, null=True, blank=True,
                                       related_name='invoices')
    appointment    = models.OneToOneField('appointments.Appointment', on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='invoice')
    issue_date     = models.DateField()
    due_date       = models.DateField()
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    voided_automatically = models.BooleanField(default=False)    # voided because the appointment was cancelled
    notes          = models.TextField(blank=True)

    # Kept up to date from lines and payments (see payments.invoicing.recalc)
    subtotal       = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # total minus tax
    tax_amount     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid    = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # payments minus refunds
    balance_due    = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_index=True)

    created_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                       blank=True, related_name='+')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-id']
        constraints = [models.UniqueConstraint(fields=['clinic', 'invoice_number'],
                                               name='invoice_number_unique_per_clinic')]

    def __str__(self):
        return self.invoice_number


class InvoiceLine(models.Model):
    objects    = TenantManager.via('invoice__clinic_id')()

    invoice    = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    position   = models.PositiveSmallIntegerField(default=0)
    description = models.CharField(max_length=255)
    treatment  = models.ForeignKey('treatments.Treatment', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+')
    product    = models.ForeignKey('inventory.InventoryItem', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+')
    quantity   = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)            # tax included
    tax_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percent
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0) # quantity × unit_price
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0) # the tax inside line_total
    from_appointment = models.BooleanField(default=False)                         # the automatic appointment line

    class Meta:
        ordering = ['position', 'id']


class Payment(models.Model):
    METHOD_CHOICES = (
        ('cash',     'Cash'),
        ('card',     'Card (in person)'),
        ('transfer', 'Bank transfer'),
        ('online',   'Online (Stripe)'),
        ('other',    'Other'),
    )
    KIND_CHOICES = (('payment', 'Payment'), ('refund', 'Refund'))

    clinic     = models.ForeignKey('tenants.Clinic', on_delete=models.PROTECT, null=True, blank=True,
                                   related_name='payments')
    objects    = TenantManager()

    invoice    = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    kind       = models.CharField(max_length=10, choices=KIND_CHOICES, default='payment')
    amount     = models.DecimalField(max_digits=12, decimal_places=2)            # always positive
    method     = models.CharField(max_length=20, choices=METHOD_CHOICES)
    paid_at    = models.DateTimeField(db_index=True)                              # when the money moved
    reference  = models.CharField(max_length=120, blank=True)                     # card slip, transfer ref, pi_…
    note       = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at', '-id']


class InvoiceCounter(models.Model):
    """Last invoice number used per clinic and year (INV-<year>-<n>)."""
    clinic = models.ForeignKey('tenants.Clinic', on_delete=models.CASCADE, related_name='+')
    year   = models.PositiveSmallIntegerField()
    last   = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['clinic', 'year'], name='invoice_counter_unique')]
