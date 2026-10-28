from rest_framework import serializers
from .models import ProcessMap, Process, ProcessInteraction, ProcessActivity


class ProcessActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessActivity
        fields = [
            'id',
            'process',
            'sequence_number',
            'name',
            'description',
            'responsible',
            'estimated_duration',
            'tools_required',
            'created_at',
        ]
        extra_kwargs = {
            'process': {'required': True}
        }


class ProcessSerializer(serializers.ModelSerializer):
    activities = ProcessActivitySerializer(many=True, read_only=True)
    activities_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Process
        fields = [
            'id',
            'process_map',
            'code',
            'name',
            'description',
            'process_type',
            'objective',
            'owner',
            'inputs',
            'outputs',
            'resources',
            'kpis',
            'risks',
            'controls',
            'criticality_score',
            'is_critical',
            'carbon_intensity_category',
            'climate_exposure_level',
            'supply_chain_risk',
            'resilience_score',
            'documented_in',
            'is_active',
            'activities',
            'activities_count',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'process_map': {'required': True}
        }
    
    def get_activities_count(self, obj):
        return obj.activities.count()


class ProcessInteractionSerializer(serializers.ModelSerializer):
    source_process_name = serializers.CharField(
        source='source_process.name',
        read_only=True
    )
    target_process_name = serializers.CharField(
        source='target_process.name',
        read_only=True
    )
    
    class Meta:
        model = ProcessInteraction
        fields = [
            'id',
            'process_map',
            'source_process',
            'source_process_name',
            'target_process',
            'target_process_name',
            'interaction_type',
            'description',
            'exchanged_items',
            'frequency',
            'is_critical',
            'created_at',
        ]
        extra_kwargs = {
            'process_map': {'required': True},
            'source_process': {'required': True},
            'target_process': {'required': True}
        }


class ProcessMapSerializer(serializers.ModelSerializer):
    processes = ProcessSerializer(many=True, read_only=True)
    interactions = ProcessInteractionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProcessMap
        fields = [
            'id',
            'organization_id',
            'title',
            'version',
            'effective_date',
            'total_processes',
            'strategic_count',
            'operational_count',
            'support_count',
            'interaction_analysis',
            'critical_processes',
            'recommendations',
            'status',
            'created_at',
            'updated_at',
            'created_by',
            'scope_definition',
            'processes',
            'interactions',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProcessMapCreateSerializer(serializers.Serializer):
    """Serializer para crear nuevo mapa de procesos"""
    organization_id = serializers.IntegerField(required=False)
    created_by = serializers.CharField(
        max_length=100,
        required=False,
        default="Sistema IA"
    )