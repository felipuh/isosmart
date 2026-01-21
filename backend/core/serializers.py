from rest_framework import serializers
from .models import RiskMatrix, QualityObjective, Document


class RiskMatrixSerializer(serializers.ModelSerializer):
    source_module_display = serializers.CharField(source='get_source_module_display', read_only=True)
    probability_display = serializers.CharField(source='get_probability_display', read_only=True)
    impact_display = serializers.CharField(source='get_impact_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = RiskMatrix
        fields = [
            'id',
            'source_module',
            'source_module_display',
            'source_id',
            'risk_description',
            'risk_category',
            'probability',
            'probability_display',
            'impact',
            'impact_display',
            'risk_level',
            'risk_level_display',
            'mitigation_actions',
            'responsible',
            'iso_clause',
            'status',
            'status_display',
            'detection_date',
            'deadline',
            'process_id',
        ]
        read_only_fields = ['id', 'detection_date']


class QualityObjectiveSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = QualityObjective
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.ChoiceField(choices=Document.TYPE_CHOICES)
    file = serializers.FileField()
    source = serializers.CharField(max_length=255, required=False, default='Sistema')
