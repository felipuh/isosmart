from rest_framework import serializers
from .models import ScopeDefinition, ProcessScope, LocationScope


class LocationScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationScope
        fields = [
            'id',
            'scope_definition',
            'location_name',
            'address',
            'location_type',
            'country',
            'city',
            'activities',
            'employee_count',
            'is_included',
            'created_at',
        ]
        extra_kwargs = {
            'scope_definition': {'required': True}
        }


class ProcessScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessScope
        fields = [
            'id',
            'scope_definition',
            'process_name',
            'process_code',
            'process_type',
            'description',
            'owner',
            'inputs',
            'outputs',
            'kpis',
            'is_included',
            'exclusion_reason',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'scope_definition': {'required': True}
        }


class ScopeDefinitionSerializer(serializers.ModelSerializer):
    locations = LocationScopeSerializer(many=True, read_only=True)
    processes = ProcessScopeSerializer(many=True, read_only=True)
    
    total_products_count = serializers.IntegerField(
        source='total_products',
        read_only=True
    )
    total_exclusions_count = serializers.IntegerField(
        source='total_exclusions',
        read_only=True
    )
    coverage_percentage = serializers.FloatField(
        source='coverage_score',
        read_only=True
    )
    
    class Meta:
        model = ScopeDefinition
        fields = [
            'id',
            'organization_id',
            'title',
            'version',
            'effective_date',
            'organizational_boundaries',
            'products_services',
            'applicable_requirements',
            'environmental_criteria',
            'climate_readiness_score',
            'digital_readiness_score',
            'exclusions',
            'scope_statement',
            'coverage_analysis',
            'status',
            'created_at',
            'updated_at',
            'created_by',
            'locations',
            'processes',
            'total_products_count',
            'total_exclusions_count',
            'coverage_percentage',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScopeDefinitionCreateSerializer(serializers.Serializer):
    """Serializer para crear nueva definición de alcance"""
    organization_id = serializers.IntegerField(required=False)
    products_services = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        help_text="Lista de productos y servicios"
    )
    has_design = serializers.BooleanField(
        default=False,
        help_text="¿La organización realiza diseño y desarrollo?"
    )
    created_by = serializers.CharField(
        max_length=100,
        required=False,
        default="Sistema IA"
    )