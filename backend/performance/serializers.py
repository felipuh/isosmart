from rest_framework import serializers
from .models import (
    PerformanceIndicator, Measurement, DataAnalysis,
    InternalAudit, AuditFinding, ManagementReview
)

class PerformanceIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceIndicator
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class MeasurementSerializer(serializers.ModelSerializer):
    indicator_detail = PerformanceIndicatorSerializer(source='indicator', read_only=True)
    
    class Meta:
        model = Measurement
        fields = '__all__'
        read_only_fields = ['variance', 'variance_percentage', 'created_at', 'updated_at']

class DataAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataAnalysis
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AuditFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditFinding
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class InternalAuditSerializer(serializers.ModelSerializer):
    findings = AuditFindingSerializer(many=True, read_only=True)
    findings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InternalAudit
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_findings_count(self, obj):
        return obj.findings.count()

class ManagementReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementReview
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
