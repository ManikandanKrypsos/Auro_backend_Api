from rest_framework import serializers
from .models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    staff_name = serializers.CharField(source='staff.username', read_only=True)
    treatment_name = serializers.CharField(source='treatment.name', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'