from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.organization_scoping import OrganizationScopedViewSetMixin
from improvement.services import (
    sync_finding_to_improvement_nc,
    sync_management_review_to_continual_improvement,
)
from ai_modules.performance.performance_engine import PerformanceAIService
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_cockpit_kpis(request):
    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    indicators_qs = PerformanceIndicator.objects.filter(organization_id=organization_id)
    measurements_qs = Measurement.objects.filter(organization_id=organization_id)
    audits_qs = InternalAudit.objects.filter(organization_id=organization_id)
    findings_qs = AuditFinding.objects.filter(organization_id=organization_id)
    reviews_qs = ManagementReview.objects.filter(organization_id=organization_id)

    kpis = {
        'indicators': {
            'total': indicators_qs.count(),
            'active': indicators_qs.filter(status='active').count(),
        },
        'measurements': {
            'total': measurements_qs.count(),
            'on_target': measurements_qs.filter(status='on_target').count(),
            'needs_attention': measurements_qs.filter(status='needs_attention').count(),
        },
        'audits': {
            'total': audits_qs.count(),
            'planned': audits_qs.filter(status='planned').count(),
            'in_progress': audits_qs.filter(status='in_progress').count(),
        },
        'findings': {
            'total': findings_qs.count(),
            'open': findings_qs.filter(status='open').count(),
            'major_nc': findings_qs.filter(finding_type='nc_major').count(),
        },
        'reviews': {
            'total': reviews_qs.count(),
            'scheduled': reviews_qs.filter(status='scheduled').count(),
        },
    }

    service = PerformanceAIService()
    ai_result = service.process({'operation': 'cockpit_summary', 'kpis': kpis})
    return Response({'organization_id': int(organization_id), 'kpis': kpis, 'ai': ai_result})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def performance_ai_indicator_drift(request):
    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    measurements = Measurement.objects.filter(organization_id=organization_id).order_by('-measurement_date')[:100]
    payload = {
        'operation': 'indicator_drift',
        'measurements': [
            {
                'id': item.id,
                'status': item.status,
            }
            for item in measurements
        ],
    }
    service = PerformanceAIService()
    return Response(service.process(payload))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def performance_ai_audit_assistant(request):
    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    findings = AuditFinding.objects.filter(organization_id=organization_id).order_by('-created_at')[:100]
    payload = {
        'operation': 'audit_assistant',
        'findings': [
            {
                'id': item.id,
                'finding_number': item.finding_number,
                'finding_type': item.finding_type,
                'status': item.status,
            }
            for item in findings
        ],
    }
    service = PerformanceAIService()
    return Response(service.process(payload))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def performance_ai_executive_brief(request):
    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    reviews = ManagementReview.objects.filter(organization_id=organization_id).order_by('-scheduled_date')[:50]
    payload = {
        'operation': 'executive_review_brief',
        'reviews': [
            {
                'id': item.id,
                'review_code': item.review_code,
                'status': item.status,
            }
            for item in reviews
        ],
    }
    service = PerformanceAIService()
    return Response(service.process(payload))
