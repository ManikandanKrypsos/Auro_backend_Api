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
        data = super().to_representation(instance)

        data.pop('id')
        data['id'] = data.pop('patient_id')

        # camelCase for Flutter
        data['bloodType'] = data.pop('blood_type')
        data['skinType']  = data.pop('skin_type')
        data['createdAt'] = data.pop('created_at')

        # marketing source with id and label
        marketing_id = data.pop('marketing_source')
        data['marketingSource'] = {
            'id':    marketing_id,
            'label': MARKETING_SOURCE_MAP.get(marketing_id, 'Other')
        } if marketing_id else None

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
                # If it's a list, take the first non-empty item
                if isinstance(val, list):
                    val = next((v for v in val if v), '')
                # Empty string → remove so field uses model default
                if val == '' or val is None:
                    data.pop(field, None)
                else:
                    data[field] = val

        # Fix image field — if it's a file path or non-URL string, ignore it
        # (actual file upload is handled in the ViewSet)
        if 'image' in data:
            val = data['image']
            if isinstance(val, list):
                val = next((v for v in val if v), '')
            # If not a valid URL, remove it — ViewSet will handle file upload
            if val and not str(val).startswith('http'):
                data.pop('image', None)
            elif not val:
                data.pop('image', None)

        return super().to_internal_value(data)