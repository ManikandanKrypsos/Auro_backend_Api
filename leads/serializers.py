from rest_framework import serializers
from .models import Lead, LeadActivity

class LeadActivitySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = LeadActivity
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']

class LeadSerializer(serializers.ModelSerializer):
    activities = LeadActivitySerializer(many=True, read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    days_in_stage = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = '__all__'

    def get_days_in_stage(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.updated_at
        return delta.days


class LeadStageUpdateSerializer(serializers.Serializer):
    stage = serializers.ChoiceField(choices=Lead.STAGE_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)