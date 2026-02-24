from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.organization_scoping import OrganizationScopedViewSetMixin
from improvement.services import (
    sync_finding_to_improvement_nc,
    sync_management_review_to_continual_improvement,
)
from .models import (
    PerformanceIndicator, Measurement, DataAnalysis,
    InternalAudit, AuditFinding, ManagementReview
)
from .serializers import (
    PerformanceIndicatorSerializer, MeasurementSerializer, DataAnalysisSerializer,
    InternalAuditSerializer, AuditFindingSerializer, ManagementReviewSerializer
)

class PerformanceIndicatorViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = PerformanceIndicator.objects.all()
    serializer_class = PerformanceIndicatorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['indicator_type', 'frequency', 'status', 'organization_id']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['created_at', 'name', 'target_value']
    ordering = ['-created_at']
    
class MeasurementViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['indicator', 'status', 'organization_id', 'measurement_date']
    search_fields = ['comments']
    ordering_fields = ['measurement_date', 'actual_value']
    ordering = ['-measurement_date']
    
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

class DataAnalysisViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = DataAnalysis.objects.all()
    serializer_class = DataAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['analysis_type', 'status', 'organization_id']
    search_fields = ['title', 'objectives', 'findings']
    ordering_fields = ['created_at', 'period_start']
    ordering = ['-created_at']
    
class InternalAuditViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = InternalAudit.objects.all()
    serializer_class = InternalAuditSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['audit_type', 'status', 'organization_id']
    search_fields = ['audit_code', 'title', 'objectives']
    ordering_fields = ['planned_date', 'created_at']
    ordering = ['-planned_date']
    
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

class AuditFindingViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AuditFinding.objects.all()
    serializer_class = AuditFindingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['audit', 'finding_type', 'status', 'organization_id']
    search_fields = ['finding_number', 'description', 'clause_reference']
    ordering_fields = ['created_at', 'due_date']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        super().perform_create(serializer)
        sync_finding_to_improvement_nc(serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        sync_finding_to_improvement_nc(serializer.instance)

class ManagementReviewViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = ManagementReview.objects.all()
    serializer_class = ManagementReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'organization_id']
    search_fields = ['review_code', 'title']
    ordering_fields = ['scheduled_date', 'created_at']
    ordering = ['-scheduled_date']
    
    def perform_create(self, serializer):
        super().perform_create(serializer)
        sync_management_review_to_continual_improvement(serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        sync_management_review_to_continual_improvement(serializer.instance)
