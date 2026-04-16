from rest_framework import serializers
from .models import Lead, LeadActivity

class LeadActivitySerializer(serializers.ModelSerializer):
    # ✅ Fixed: use email as fallback if username is empty
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeadActivity
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.username or obj.created_by.email
        return None

class LeadSerializer(serializers.ModelSerializer):
    activities       = LeadActivitySerializer(many=True, read_only=True)
    # ✅ Fixed: use email as fallback
    assigned_to_name = serializers.SerializerMethodField()
    days_in_stage    = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = '__all__'

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.username or obj.assigned_to.email
        return None

    def get_days_in_stage(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.updated_at
        return delta.days

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['createdAt']     = data.pop('created_at')
        data['updatedAt']     = data.pop('updated_at')
        data['assignedTo']    = data.pop('assigned_to')
        data['lastContacted'] = data.pop('last_contacted')
        return data


class LeadStageUpdateSerializer(serializers.Serializer):
    stage = serializers.ChoiceField(choices=Lead.STAGE_CHOICES)
    note  = serializers.CharField(required=False, allow_blank=True)