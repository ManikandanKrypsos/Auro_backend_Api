"""
Single definition of money used by the dashboard and the payments screen, so both always agree.

Revenue (received) = payments minus refunds whose paid date is in the period (clinic local time).
                     Partial payments count when they arrive; refunds count when they are made.
Outstanding        = balance still due on open / partially paid invoices issued in the period.
Staff / treatment  = through the invoice's appointment (standalone invoices only count in totals).

paid_total() / billable() are the old appointment-based rule, kept for anything not yet moved.
"""
import datetime
from django.db.models import Sum
from django.utils import timezone


def billable(qs):
    """Appointments that count for money: drop cancelled appointments that were never paid."""
    return qs.exclude(status='cancelled', payment_status='pending')


def paid_total(qs):
    """Collected revenue for a queryset of appointments."""
    return round(float(
        billable(qs).filter(payment_status='paid').aggregate(t=Sum('payment_amount'))['t'] or 0
    ), 2)


def day_start(d):
    """Timezone-aware 00:00 (clinic local time) of a date."""
    return timezone.make_aware(datetime.datetime.combine(d, datetime.time.min))


def in_dates(qs, start, end):
    """Filter appointments whose local date is within [start, end] (inclusive). None = open."""
    if start:
        qs = qs.filter(date_time__gte=day_start(start))
    if end:
        qs = qs.filter(date_time__lt=day_start(end + datetime.timedelta(days=1)))
    return qs


def month_bounds(d):
    """First and last day of d's calendar month."""
    first = d.replace(day=1)
    nxt   = datetime.date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    return first, nxt - datetime.timedelta(days=1)


# ── Money received (payments) ─────────────────────────────────────────────────

def payments_between(start, end, staff_id=None, treatment_id=None):
    """Payment rows (payments and refunds) whose local paid date is within [start, end]. None = open."""
    from .models import Payment
    qs = Payment.objects.all()
    if start:
        qs = qs.filter(paid_at__gte=day_start(start))
    if end:
        qs = qs.filter(paid_at__lt=day_start(end + datetime.timedelta(days=1)))
    if staff_id is not None:
        qs = qs.filter(invoice__appointment__staff_id=staff_id)
    if treatment_id is not None:
        qs = qs.filter(invoice__appointment__treatment_id=treatment_id)
    return qs



def signed_amount():
    """+amount for payments, -amount for refunds (for aggregate())."""
    from django.db.models import Case, DecimalField, F, When
    return Case(When(kind='refund', then=-F('amount')), default=F('amount'),
                output_field=DecimalField(max_digits=12, decimal_places=2))


def received_total(start, end, staff_id=None, treatment_id=None):
    qs = payments_between(start, end, staff_id, treatment_id)
    return round(float(qs.aggregate(t=Sum(signed_amount()))['t'] or 0), 2)


def received_by(start, end, field):
    """{value_of_field: net received} — e.g. field='invoice__appointment__treatment_id'."""
    rows = payments_between(start, end).values(field).annotate(t=Sum(signed_amount()))
    return {r[field]: round(float(r['t'] or 0), 2) for r in rows}


def outstanding_total(start, end, staff_id=None):
    from .models import Invoice
    qs = Invoice.objects.filter(status__in=['open', 'partially_paid'])
    if start:
        qs = qs.filter(issue_date__gte=start)
    if end:
        qs = qs.filter(issue_date__lte=end)
    if staff_id is not None:
        qs = qs.filter(appointment__staff_id=staff_id)
    return round(float(qs.aggregate(t=Sum('balance_due'))['t'] or 0), 2)
