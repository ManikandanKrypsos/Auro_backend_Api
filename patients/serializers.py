from rest_framework import serializers
from .models import Patient, MARKETING_SOURCE_CHOICES
import datetime
from django.utils import timezone

MARKETING_SOURCE_MAP = {
    1: 'Instagram',
    2: 'Website',
    3: 'Walk-in',
    4: 'Referral',
    5: 'WhatsApp',
    6: 'Other',
}

# A patient is "inactive" with no completed visit in this many days
# (same 30-day rule the AI agent uses for "inactive patients").
INACTIVE_AFTER_DAYS = 30


def patient_status(instance, last_visit_date, next_appointment_date):
    """
    vip      → category is VIP
    active   → completed visit in the last 30 days, an upcoming appointment,
               or registered in the last 30 days
    inactive → everything else
    """
    if instance.category == 'VIP':
        return 'vip'
    cutoff = timezone.localdate() - datetime.timedelta(days=INACTIVE_AFTER_DAYS)
    if next_appointment_date:
        return 'active'
    if last_visit_date and last_visit_date >= cutoff:
        return 'active'
    if instance.created_at and timezone.localtime(instance.created_at).date() >= cutoff:
        return 'active'
    return 'inactive'


def with_visit_stats(queryset):
    """Annotates visits / last visit / next appointment / total spent in the same query as the patients."""
    from django.db.models import Count, Max, Min, OuterRef, Q, Subquery, Sum
    from appointments.models import Appointment
    now = timezone.now()
    last_treatment = (Appointment.objects.model._base_manager
                      .filter(patient=OuterRef('pk'), status='completed')
                      .order_by('-date_time', '-id').values('treatment__name')[:1])
    return queryset.annotate(
        _visits=Count('appointments', filter=Q(appointments__status='completed'), distinct=True),
        _last_visit_at=Max('appointments__date_time', filter=Q(appointments__status='completed')),
        _next_appointment_at=Min('appointments__date_time',
                                 filter=Q(appointments__status='upcoming', appointments__date_time__gte=now)),
        _total_spent=Sum('appointments__payment_amount',
                         filter=Q(appointments__status='completed', appointments__payment_status='paid')),
        _last_visit_treatment=Subquery(last_treatment),
    )


def visit_stats(instance):
    """The stats for one patient: from the annotations when present, otherwise from the database."""
    if hasattr(instance, '_visits'):
        return {
            'visits': instance._visits, 'last_visit_at': instance._last_visit_at,
            'last_visit_treatment': instance._last_visit_treatment,
            'next_appointment_at': instance._next_appointment_at, 'total_spent': instance._total_spent,
        }
    from django.db.models import Sum
    from appointments.models import Appointment
    appts = Appointment.objects.filter(patient=instance, status='completed').order_by('-date_time', '-id')
    last = appts.select_related('treatment').first()
    return {
        'visits': appts.count(),
        'last_visit_at': last.date_time if last else None,
        'last_visit_treatment': last.treatment.name if last and last.treatment else None,
        'next_appointment_at': Appointment.objects.filter(
            patient=instance, status='upcoming', date_time__gte=timezone.now(),
        ).order_by('date_time').values_list('date_time', flat=True).first(),
        'total_spent': appts.filter(payment_status='paid').aggregate(t=Sum('payment_amount'))['t'],
    }


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model  = Patient
        fields = '__all__'
        read_only_fields = ['patient_id', 'id', 'created_by', 'clinic']

    def get_age(self, obj):
        if not obj.dob:
            return None
        today = timezone.localdate()
        age = today.year - obj.dob.year
        if (today.month, today.day) < (obj.dob.month, obj.dob.day):
            age -= 1
        return age

    def to_representation(self, instance):
        from django.db.models import Sum
        from appointments.models import Appointment

        data = super().to_representation(instance)

        # Replace numeric id with Aura patient_id
        data.pop('id')
        data['id'] = data.pop('patient_id')

        # camelCase for Flutter
        data['bloodType'] = data.pop('blood_type')
        data['skinType']  = data.pop('skin_type')
        data['createdAt'] = data.pop('created_at')

        # Marketing source with id and label
        marketing_id = data.pop('marketing_source')
        data['marketingSource'] = {
            'id':    marketing_id,
            'label': MARKETING_SOURCE_MAP.get(marketing_id, 'Other')
        } if marketing_id else None

        # ── Real stats calculated from appointments ────────────────────────
        # The list queryset precomputes these (with_visit_stats) so a page costs one query, not 4 per row.
        stats = visit_stats(instance)
        data['visits'] = stats['visits']

        last_at = stats['last_visit_at']
        if last_at:
            data['last_visit'] = {
                'date':      str(timezone.localtime(last_at).date() if timezone.is_aware(last_at) else last_at.date()),
                'treatment': stats['last_visit_treatment'],
            }
        else:
            data['last_visit'] = {'date': None, 'treatment': None}

        next_at = stats['next_appointment_at']
        next_date = timezone.localtime(next_at).date() if next_at else None
        data['next_appointment'] = str(next_date) if next_date else None

        # Badge status: active / inactive / vip
        last_date = timezone.localtime(last_at).date() if last_at else None
        data['status'] = patient_status(instance, last_date, next_date)

        # Total money spent (sum of payment_amount for paid completed appointments)
        data['total_spent'] = float(stats['total_spent'] or 0)

        return data

    def to_internal_value(self, data):
        data = data.copy()

        # camelCase → snake_case
        if 'bloodType' in data:
            data['blood_type'] = data.pop('bloodType')
        if 'skinType' in data:
            data['skin_type'] = data.pop('skinType')
        if 'marketingSource' in data:
            data['marketing_source'] = data.pop('marketingSource')

        # Fix Flutter sending [''] instead of '' or null for choice fields
        for field in ['blood_type', 'skin_type', 'gender', 'category']:
            if field in data:
                val = data[field]
                if isinstance(val, list):
                    val = next((v for v in val if v), '')
                if val == '' or val is None:
                    data.pop(field, None)
                else:
                    data[field] = val

        # Fix image field
        if 'image' in data:
            val = data['image']
            if isinstance(val, list):
                val = next((v for v in val if v), '')
            if val and not str(val).startswith('http'):
                data.pop('image', None)
            elif not val:
                data.pop('image', None)

        return super().to_internal_value(data)