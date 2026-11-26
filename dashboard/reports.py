"""
Reports module (admin only). Shared filters on every endpoint:

  ?date_from=YYYY-MM-DD &date_to=YYYY-MM-DD   inclusive, clinic local time (defaults per endpoint)
  ?staff_id=      only appointments of this professional
  ?treatment_id=  only appointments of this treatment
  ?group_by=week|month   (trend endpoints; weeks start on Monday)

GET /api/reports/revenue-by-treatment/   every treatment's revenue in the range (default: this month)
GET /api/reports/average-ticket/         avg charged per completed appointment (default: this month)
GET /api/reports/appointment-outcomes/   completed / cancelled / no-show per period (default: last 6 months)
GET /api/reports/patient-retention/      new vs returning patients per period (default: last 6 months)

Money follows the dashboard: revenue = money received (payments minus refunds, by paid date),
attributed to a treatment / professional through the invoice's appointment.
"""
import datetime
from collections import defaultdict

from django.db.models import Count, Min, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.models import Appointment
from payments.metrics import in_dates, month_bounds, payments_between, signed_amount
from users.permissions import IsAdmin
from utils.api_errors import validation_error

MAX_PERIODS = 60


def _trend(current, previous):
    from .views import _calc_trend
    return _calc_trend(current, previous)


def _filters(request, default_from):
    """Returns (params dict, error_response)."""
    p, errors = request.query_params, {}
    today = timezone.localdate()
    out = {}
    for f, default in (('date_from', default_from), ('date_to', today)):
        if p.get(f):
            d = parse_date(p[f])
            if not d:
                errors[f] = 'Use YYYY-MM-DD.'
            out[f] = d
        else:
            out[f] = default
    for f in ('staff_id', 'treatment_id'):
        v = p.get(f)
        if v in (None, ''):
            out[f] = None
        elif not str(v).isdigit():
            errors[f] = 'Must be a whole number.'
        else:
            out[f] = int(v)
    if not errors and out['date_from'] > out['date_to']:
        errors['date_from'] = 'Must be on or before date_to.'
    if errors:
        return None, validation_error(errors)
    return out, None


def _appts(f):
    qs = in_dates(Appointment.objects.all(), f['date_from'], f['date_to'])
    if f['staff_id']:
        qs = qs.filter(staff_id=f['staff_id'])
    if f['treatment_id']:
        qs = qs.filter(treatment_id=f['treatment_id'])
    return qs


def _echo(f, **extra):
    return {'date_from': str(f['date_from']), 'date_to': str(f['date_to']),
            'staff_id': f['staff_id'], 'treatment_id': f['treatment_id'], **extra}


def _previous(f):
    days = (f['date_to'] - f['date_from']).days + 1
    end = f['date_from'] - datetime.timedelta(days=1)
    return dict(f, date_from=end - datetime.timedelta(days=days - 1), date_to=end)


# ── periods ──────────────────────────────────────────────────────────────────

def _group_by(request):
    g = request.query_params.get('group_by', 'month')
    return g if g in ('week', 'month') else None


def _default_trend_start(group_by):
    today = timezone.localdate()
    if group_by == 'week':
        return today - datetime.timedelta(days=today.weekday() + 7 * 11)          # 12 weeks incl. this one
    first = today.replace(day=1)
    for _ in range(5):                                                           # 6 months incl. this one
        first = (first - datetime.timedelta(days=1)).replace(day=1)
    return first


def _periods(start, end, group_by):
    """[(key, label, period_start, period_end)] covering [start, end], clipped to the range."""
    out = []
    if group_by == 'week':
        cur = start - datetime.timedelta(days=start.weekday())
        while cur <= end:
            iso = cur.isocalendar()
            out.append((cur, f'{iso[0]}-W{iso[1]:02d}', max(cur, start), min(cur + datetime.timedelta(days=6), end)))
            cur += datetime.timedelta(days=7)
    else:
        cur = start.replace(day=1)
        while cur <= end:
            first, last = month_bounds(cur)
            out.append((first, first.strftime('%Y-%m'), max(first, start), min(last, end)))
            cur = last + datetime.timedelta(days=1)
    return out


def _key(d, group_by):
    return d - datetime.timedelta(days=d.weekday()) if group_by == 'week' else d.replace(day=1)


def _trend_setup(request):
    group_by = _group_by(request)
    if not group_by:
        return None, None, validation_error({'group_by': 'Use week or month.'})
    f, bad = _filters(request, _default_trend_start(group_by))
    if bad:
        return None, None, bad
    periods = _periods(f['date_from'], f['date_to'], group_by)
    if len(periods) > MAX_PERIODS:
        return None, None, validation_error({'date_from': f'At most {MAX_PERIODS} {group_by}s per request.'})
    return f, (group_by, periods), None


# ── 1. revenue by treatment ──────────────────────────────────────────────────

class RevenueByTreatmentView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from treatments.models import Treatment
        today = timezone.localdate()
        f, bad = _filters(request, today.replace(day=1))
        if bad:
            return bad
        pays = payments_between(f['date_from'], f['date_to'], f['staff_id'], f['treatment_id'])
        revenue = {r['invoice__appointment__treatment_id']: float(r['t'] or 0)
                   for r in pays.values('invoice__appointment__treatment_id').annotate(t=Sum(signed_amount()))}
        appts = _appts(f).exclude(status='cancelled')
        counts = {r['treatment_id']: r for r in appts.values('treatment_id').annotate(
            bookings=Count('id'), completed=Count('id', filter=Q(status='completed')))}
        treatments = Treatment.objects.all().order_by('name')
        if f['treatment_id']:
            treatments = treatments.filter(pk=f['treatment_id'])
        rows = []
        for t in treatments:
            c = counts.get(t.id, {})
            rows.append({'treatment_id': t.id, 'name': t.name, 'category': t.category,
                         'bookings': c.get('bookings', 0), 'completed': c.get('completed', 0),
                         'revenue': round(revenue.get(t.id, 0.0), 2)})
        other = round(revenue.get(None, 0.0), 2)        # standalone invoices / appointments without a treatment
        total = round(sum(r['revenue'] for r in rows) + other, 2)
        for r in rows:
            r['share_pct'] = round(r['revenue'] / total * 100, 1) if total else 0.0
            r['avg_per_completed'] = round(r['revenue'] / r['completed'], 2) if r['completed'] else None
        rows.sort(key=lambda r: (-r['revenue'], -r['bookings'], r['name']))
        return Response(_echo(f, total_revenue=total, other_revenue=other,
                              other_share_pct=round(other / total * 100, 1) if total else 0.0,
                              treatments=rows))


# ── 2. average ticket ────────────────────────────────────────────────────────

def _ticket(f):
    from payments.models import Invoice
    invs = (Invoice.objects.filter(appointment__in=_appts(f).filter(status='completed'))
            .exclude(status='void').values_list('total', 'credited'))
    amounts = [float((t or 0) - (c or 0)) for t, c in invs]
    paid = [a for a in amounts if a > 0]                 # €0 = package sessions / free sessions
    return {
        'completed_appointments': len(amounts),
        'charged_appointments': len(paid),
        'excluded_zero_value': len(amounts) - len(paid),
        'total_charged': round(sum(paid), 2),
        'average_ticket': round(sum(paid) / len(paid), 2) if paid else 0.0,
    }


class AverageTicketView(APIView):
    """
    average_ticket = what was charged (invoice total minus credits) per completed appointment in the range,
    by appointment date. €0 sessions (package sessions, free sessions) are left out of the average and
    counted in excluded_zero_value. previous = the same-length period just before, for the trend.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        f, bad = _filters(request, today.replace(day=1))
        if bad:
            return bad
        cur, prev = _ticket(f), _ticket(_previous(f))
        return Response(_echo(f, **cur,
                              previous={'date_from': str(_previous(f)['date_from']), 'date_to': str(_previous(f)['date_to']),
                                        **prev},
                              trend=_trend(cur['average_ticket'], prev['average_ticket'])))


# ── 3. appointment outcomes over time ────────────────────────────────────────

class AppointmentOutcomesView(APIView):
    permission_classes = [IsAdmin]
    STATUSES = ('completed', 'cancelled', 'no_show', 'upcoming', 'in_session')

    def get(self, request):
        f, setup, bad = _trend_setup(request)
        if bad:
            return bad
        group_by, periods = setup
        buckets = defaultdict(lambda: dict.fromkeys(self.STATUSES, 0))
        for dt, status in _appts(f).values_list('date_time', 'status'):
            buckets[_key(timezone.localtime(dt).date(), group_by)][status] += 1
        series, totals = [], dict.fromkeys(self.STATUSES, 0)
        for key, label, start, end in periods:
            b = buckets[key]
            total = sum(b.values())
            done = b['completed'] + b['cancelled'] + b['no_show']
            for s in self.STATUSES:
                totals[s] += b[s]
            series.append({'period': label, 'start': str(start), 'end': str(end),
                           'completed': b['completed'], 'cancelled': b['cancelled'], 'no_show': b['no_show'],
                           'scheduled': b['upcoming'] + b['in_session'], 'total': total,
                           'completion_rate': round(b['completed'] / done * 100, 1) if done else None,
                           'cancellation_rate': round(b['cancelled'] / total * 100, 1) if total else None,
                           'no_show_rate': round(b['no_show'] / total * 100, 1) if total else None})
        all_total = sum(totals.values())
        return Response(_echo(f, group_by=group_by, series=series, totals={
            'completed': totals['completed'], 'cancelled': totals['cancelled'], 'no_show': totals['no_show'],
            'scheduled': totals['upcoming'] + totals['in_session'], 'total': all_total}))


# ── 4. patient retention over time ───────────────────────────────────────────

class PatientRetentionView(APIView):
    """
    Per period, from completed appointments (with the staff / treatment filters):
      active    — distinct patients with a completed visit in the period
      new       — of those, patients whose first-ever completed visit is in the period
      returning — of those, patients who had a completed visit before the period
      retention_rate = returning / active
    registered — patient records created in the period (not affected by staff / treatment).
    vip        — active patients whose category is VIP now (the category has no history).
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        from patients.models import Patient
        f, setup, bad = _trend_setup(request)
        if bad:
            return bad
        group_by, periods = setup
        visits = list(_appts(f).filter(status='completed').values_list('patient_id', 'date_time'))
        ids = {pid for pid, _ in visits}
        first_visit = {r['patient_id']: timezone.localtime(r['first']).date() for r in
                       Appointment.objects.filter(status='completed', patient_id__in=ids)
                       .values('patient_id').annotate(first=Min('date_time'))}
        vip = set(Patient.objects.filter(pk__in=ids, category='VIP').values_list('pk', flat=True))
        active = defaultdict(set)
        for pid, dt in visits:
            active[_key(timezone.localtime(dt).date(), group_by)].add(pid)
        registered = defaultdict(int)
        for dt in Patient.objects.filter(
                created_at__gte=_day(f['date_from']), created_at__lt=_day(f['date_to'] + datetime.timedelta(days=1))
        ).values_list('created_at', flat=True):
            registered[_key(timezone.localtime(dt).date(), group_by)] += 1
        series = []
        tot_new = tot_ret = 0
        all_active = set()
        for key, label, start, end in periods:
            pats = active[key]
            new = {p for p in pats if first_visit.get(p) and first_visit[p] >= key}
            ret = pats - new
            tot_new += len(new)
            tot_ret += len(ret)
            all_active |= pats
            series.append({'period': label, 'start': str(start), 'end': str(end),
                           'active': len(pats), 'new': len(new), 'returning': len(ret),
                           'retention_rate': round(len(ret) / len(pats) * 100, 1) if pats else None,
                           'vip': len(pats & vip), 'registered': registered[key]})
        return Response(_echo(f, group_by=group_by, series=series, totals={
            'unique_active': len(all_active), 'new': tot_new, 'returning_visits': tot_ret,
            'registered': sum(s['registered'] for s in series)}))


def _day(d):
    from payments.metrics import day_start
    return day_start(d)
