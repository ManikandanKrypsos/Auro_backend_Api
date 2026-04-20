from rest_framework import serializers
from .models import Patient, MARKETING_SOURCE_CHOICES

MARKETING_SOURCE_MAP = {
    1: 'Instagram',
    2: 'Website',
    3: 'Walk-in',
    4: 'Referral',
    5: 'WhatsApp',
    6: 'Other',
}

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Patient
        fields = '__all__'
        read_only_fields = ['patient_id', 'id']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 👈 Replace numeric id with patientId (Aura1, Aura2...)
        data.pop('id')                              # remove numeric id
        data['id'] = data.pop('patient_id')         # make patientId the main id

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