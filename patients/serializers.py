from rest_framework import serializers
from .models import Patient, MARKETING_SOURCE_CHOICES
from django.utils import timezone

MARKETING_SOURCE_MAP = {
    1: 'Instagram',
    2: 'Website',
    3: 'Walk-in',
    4: 'Referral',
    5: 'WhatsApp',
    6: 'Other',
}

class PatientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model  = Patient
        fields = '__all__'
        read_only_fields = ['patient_id', 'id']

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
        appts = Appointment.objects.filter(
            patient=instance,
            status='completed'
        ).order_by('-date_time')

        # Total visits (completed appointments)
        data['visits'] = appts.count()

        # Last visit date and treatment
        last_appt = appts.select_related('treatment').first()
        if last_appt and last_appt.date_time:
            from django.utils import timezone as tz
            dt = tz.localtime(last_appt.date_time) if tz.is_aware(last_appt.date_time) else last_appt.date_time
            data['last_visit'] = {
                'date':      str(dt.date()),
                'treatment': last_appt.treatment.name if last_appt.treatment else None,
            }
        else:
            data['last_visit'] = {'date': None, 'treatment': None}

        # Total money spent (sum of payment_amount for paid completed appointments)
        total = appts.filter(
            payment_status='paid'
        ).aggregate(total=Sum('payment_amount'))['total'] or 0
        data['total_spent'] = float(total)

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