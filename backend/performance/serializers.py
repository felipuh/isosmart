from rest_framework import serializers
from .models import (
    PerformanceIndicator, Measurement, DataAnalysis,
    InternalAudit, AuditFinding, ManagementReview
)

class PerformanceIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceIndicator
        fields = [
            'id', 'organization_id', 'organization_name', 'code', 'name',
            'description', 'indicator_type', 'measurement_method', 'formula',
            'target_value', 'unit_of_measure', 'frequency',
            'responsible_person_id', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

class MeasurementSerializer(serializers.ModelSerializer):
    indicator_detail = PerformanceIndicatorSerializer(source='indicator', read_only=True)
    
    class Meta:
        model = Measurement
        fields = [
            'id', 'organization_id', 'indicator', 'indicator_detail',
            'measurement_date', 'actual_value', 'target_value', 'variance',
            'variance_percentage', 'status', 'comments', 'measured_by_id',
            'evidence', 'created_at', 'updated_at',
        ]
        read_only_fields = ['variance', 'variance_percentage', 'created_at', 'updated_at']

class DataAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataAnalysis
        fields = [
            'id', 'organization_id', 'title', 'analysis_type',
            'period_start', 'period_end', 'objectives', 'methodology',
            'findings', 'conclusions', 'recommendations', 'analyzed_by_id',
            'status', 'ai_insights', 'ai_predictions', 'ai_anomalies',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

class AuditFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditFinding
        fields = [
            'id', 'organization_id', 'audit', 'finding_number',
            'finding_type', 'clause_reference', 'description', 'evidence',
            'root_cause', 'immediate_action', 'corrective_action',
            'responsible_person_id', 'due_date', 'completion_date',
            'verification_date', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

class InternalAuditSerializer(serializers.ModelSerializer):
    findings = AuditFindingSerializer(many=True, read_only=True)
    findings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InternalAudit
        fields = [
            'id', 'organization_id', 'organization_name', 'audit_code',
            'audit_type', 'title', 'objectives', 'scope', 'criteria',
            'planned_date', 'start_date', 'end_date', 'lead_auditor_id',
            'status', 'audit_report', 'executive_summary', 'findings',
            'findings_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_findings_count(self, obj):
        return obj.findings.count()

class ManagementReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementReview
        fields = [
            'id', 'organization_id', 'organization_name', 'review_code',
            'title', 'scheduled_date', 'actual_date', 'chairperson_id',
            'performance_results', 'customer_feedback', 'process_performance',
            'nc_and_corrective_actions', 'improvement_opportunities',
            'improvement_decisions', 'qms_changes', 'resource_needs',
            'minutes', 'action_items', 'next_review_date', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
