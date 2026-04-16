from rest_framework import serializers
from .models import Patient

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

    def to_representation(self, instance):
        """Make response match Flutter's PatientModel field names."""
        data = super().to_representation(instance)
        # Flutter expects 'bloodType' not 'blood_type'
        data['bloodType']        = data.pop('blood_type')
        data['skinType']         = data.pop('skin_type')
        data['marketingSource']  = data.pop('marketing_source')
        data['createdAt']        = data.pop('created_at')
        return data

def to_internal_value(self, data):
    """Accept both camelCase and snake_case from Flutter."""
    # ✅ Fixed: copy data first to avoid mutating QueryDict
    data = data.copy()
    if 'bloodType' in data:
        data['blood_type'] = data.pop('bloodType')
    if 'skinType' in data:
        data['skin_type'] = data.pop('skinType')
    if 'marketingSource' in data:
        data['marketing_source'] = data.pop('marketingSource')
    return super().to_internal_value(data)