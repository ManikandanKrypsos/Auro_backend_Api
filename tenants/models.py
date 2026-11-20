from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Plan(models.Model):
    """A subscription plan. Billing happens in Stripe against stripe_price_id."""
    INTERVAL_CHOICES = (('month', 'Monthly'), ('year', 'Yearly'))

    name            = models.CharField(max_length=80)
    price           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency        = models.CharField(max_length=3, default='eur')
    interval        = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default='month')
    stripe_price_id = models.CharField(max_length=100, blank=True)
    stripe_product_id = models.CharField(max_length=100, blank=True)
    limits          = models.JSONField(default=dict, blank=True)   # not enforced yet
    is_active       = models.BooleanField(default=True)            # offered to new clinics
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price', 'id']

    def __str__(self):
        return self.name


class Clinic(models.Model):
    STATUS_CHOICES = (('active', 'Active'), ('suspended', 'Suspended'))
    SUBSCRIPTION_CHOICES = (
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past due'),
        ('canceled', 'Canceled'),
        ('trial_expired', 'Trial expired'),
    )

    name             = models.CharField(max_length=150)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    suspended_at     = models.DateTimeField(null=True, blank=True)
    suspended_reason = models.CharField(max_length=255, blank=True)

    # Billing (Stripe is the source of truth; these mirror it via the webhook)
    plan                   = models.ForeignKey(Plan, on_delete=models.PROTECT, null=True, blank=True, related_name='clinics')
    subscription_status    = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default='trialing', db_index=True)
    trial_end              = models.DateTimeField(null=True, blank=True)
    stripe_customer_id     = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, db_index=True)
    current_period_end     = models.DateTimeField(null=True, blank=True)
    past_due_since         = models.DateTimeField(null=True, blank=True)
    grace_until            = models.DateTimeField(null=True, blank=True)
    canceled_at            = models.DateTimeField(null=True, blank=True)
    card_brand             = models.CharField(max_length=20, blank=True)
    card_last4             = models.CharField(max_length=4, blank=True)
    card_exp_month         = models.PositiveSmallIntegerField(null=True, blank=True)
    card_exp_year          = models.PositiveSmallIntegerField(null=True, blank=True)
    cancel_at_period_end   = models.BooleanField(default=False)            # canceled in the portal, ends at current_period_end
    last_billing_event_at  = models.DateTimeField(null=True, blank=True)   # ignores out-of-order webhooks

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return self.status == 'active'


class PlatformAdmin(models.Model):
    """Super Admin of the SaaS platform — not a clinic user, has its own login."""
    name       = models.CharField(max_length=150)
    email      = models.EmailField(unique=True)
    password   = models.CharField(max_length=128)
    is_active  = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw):
        self.password = make_password(raw)

    def check_password(self, raw):
        return check_password(raw, self.password)

    def __str__(self):
        return self.email
