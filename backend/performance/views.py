from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    PerformanceIndicator, Measurement, DataAnalysis,
    InternalAudit, AuditFinding, ManagementReview
)
from .serializers import (
    PerformanceIndicatorSerializer, MeasurementSerializer, DataAnalysisSerializer,
    InternalAuditSerializer, AuditFindingSerializer, ManagementReviewSerializer
)

class PerformanceIndicatorViewSet(viewsets.ModelViewSet):
    serializer_class = PerformanceIndicatorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['indicator_type', 'frequency', 'status', 'organization_id']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['created_at', 'name', 'target_value']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return PerformanceIndicator.objects.all()

class MeasurementViewSet(viewsets.ModelViewSet):
    serializer_class = MeasurementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['indicator', 'status', 'organization_id', 'measurement_date']
    search_fields = ['comments']
    ordering_fields = ['measurement_date', 'actual_value']
    ordering = ['-measurement_date']
    
    def get_queryset(self):
        return Measurement.objects.all()
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        measurements = self.get_queryset()
        
        stats = {
            'total_measurements': measurements.count(),
            'on_target': measurements.filter(status='on_target').count(),
            'below_target': measurements.filter(status='below_target').count(),
            'above_target': measurements.filter(status='above_target').count(),
            'needs_attention': measurements.filter(status='needs_attention').count(),
        }
        
        return Response(stats)

class DataAnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = DataAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['analysis_type', 'status', 'organization_id']
    search_fields = ['title', 'objectives', 'findings']
    ordering_fields = ['created_at', 'period_start']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return DataAnalysis.objects.all()

class InternalAuditViewSet(viewsets.ModelViewSet):
    serializer_class = InternalAuditSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['audit_type', 'status', 'organization_id']
    search_fields = ['audit_code', 'title', 'objectives']
    ordering_fields = ['planned_date', 'created_at']
    ordering = ['-planned_date']
    
    def get_queryset(self):
        return InternalAudit.objects.all()
    
    @action(detail=True, methods=['get'])
    def findings_summary(self, request, pk=None):
        """Get findings summary for an audit"""
        audit = self.get_object()
        findings = audit.findings.all()
        
        summary = {
            'total': findings.count(),
            'major_nc': findings.filter(finding_type='nc_major').count(),
            'minor_nc': findings.filter(finding_type='nc_minor').count(),
            'observations': findings.filter(finding_type='observation').count(),
            'opportunities': findings.filter(finding_type='opportunity').count(),
            'conformities': findings.filter(finding_type='conformity').count(),
            'open': findings.filter(status='open').count(),
            'closed': findings.filter(status='closed').count(),
        }
        
        return Response(summary)

class AuditFindingViewSet(viewsets.ModelViewSet):
    serializer_class = AuditFindingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['audit', 'finding_type', 'status', 'organization_id']
    search_fields = ['finding_number', 'description', 'clause_reference']
    ordering_fields = ['created_at', 'due_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return AuditFinding.objects.all()

class ManagementReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ManagementReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'organization_id']
    search_fields = ['review_code', 'title']
    ordering_fields = ['scheduled_date', 'created_at']
    ordering = ['-scheduled_date']
    
    def get_queryset(self):
        return ManagementReview.objects.all()
