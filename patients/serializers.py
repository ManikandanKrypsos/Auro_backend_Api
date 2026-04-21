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
    age = serializers.SerializerMethodField()  # 👈 calculated field

    class Meta:
        model  = Patient
        fields = '__all__'
        read_only_fields = ['patient_id', 'id']

    def get_age(self, obj):
        """Calculate age from dob"""
        if not obj.dob:
            return None
        today = timezone.localdate()
        age = today.year - obj.dob.year
        # Check if birthday has passed this year
        if (today.month, today.day) < (obj.dob.month, obj.dob.day):
            age -= 1
        return age

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 👈 Replace numeric id with Aura patient_id
        data.pop('id')
        data['id'] = data.pop('patient_id')

        # camelCase for Flutter
        data['bloodType']       = data.pop('blood_type')
        data['skinType']        = data.pop('skin_type')
        data['createdAt']       = data.pop('created_at')

        # marketing source with id and label
        marketing_id = data.pop('marketing_source')
        data['marketingSource'] = {
            'id':    marketing_id,
            'label': MARKETING_SOURCE_MAP.get(marketing_id, 'Other')
        } if marketing_id else None

        return data

    def to_internal_value(self, data):
        data = data.copy()
        if 'bloodType' in data:
            data['blood_type'] = data.pop('bloodType')
        if 'skinType' in data:
            data['skin_type'] = data.pop('skinType')
        if 'marketingSource' in data:
            data['marketing_source'] = data.pop('marketingSource')
        return super().to_internal_value(data)