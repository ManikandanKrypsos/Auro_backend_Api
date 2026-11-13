"""
Single definition of "revenue" used by the dashboard and the payments screen,
so the numbers on both always reconcile.

Revenue (collected) = sum of payment_amount where payment_status == 'paid'
Pending             = sum of payment_amount where payment_status == 'pending'
Billed              = revenue + pending
Scope               = every appointment except cancelled ones that were never paid
Date                = the appointment's date (clinic local time)
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
