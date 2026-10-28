# improvement/views.py
"""
Views for Improvement Module
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from core.organization_scoping import OrganizationScopedViewSetMixin
from ai_modules.improvement.improvement_engine import ImprovementAIService

from .models import Nonconformity, CorrectiveAction, ContinualImprovement
from .serializers import (
    NonconformitySerializer,
    CorrectiveActionSerializer,
    ContinualImprovementSerializer
)


class NonconformityViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para No Conformidades"""
    queryset = Nonconformity.objects.all()
    serializer_class = NonconformitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'source', 'severity', 'status']
    search_fields = ['nc_number', 'title', 'description']
    ordering_fields = ['detection_date', 'created_at', 'severity']
    ordering = ['-detection_date']

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Estadisticas de no conformidades"""
        queryset = self.get_queryset()
        stats = {
            'total': queryset.count(),
            'open': queryset.filter(status='open').count(),
            'closed': queryset.filter(status='closed').count(),
            'critical': queryset.filter(severity='critical').count(),
            'major': queryset.filter(severity='major').count(),
            'minor': queryset.filter(severity='minor').count(),
            'by_source': {},
        }

        for source, _ in Nonconformity.SOURCE_CHOICES:
            stats['by_source'][source] = queryset.filter(source=source).count()

        return Response(stats)


class CorrectiveActionViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Acciones Correctivas"""
    queryset = CorrectiveAction.objects.all()
    serializer_class = CorrectiveActionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'action_type', 'status', 'is_effective']
    search_fields = ['action_number', 'action_description', 'root_cause_identified']
    ordering_fields = ['created_at', 'planned_completion_date']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Acciones vencidas"""
        from datetime import date

        queryset = self.get_queryset().filter(
            planned_completion_date__lt=date.today(),
            status__in=['planned', 'in_progress']
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ContinualImprovementViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Mejora Continua"""
    queryset = ContinualImprovement.objects.all()
    serializer_class = ContinualImprovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'improvement_type', 'priority', 'status']
    search_fields = ['initiative_number', 'title', 'description']
    ordering_fields = ['priority', 'proposed_date', 'created_at']
    ordering = ['-priority', '-created_at']

    @action(detail=False, methods=['get'])
    def active_initiatives(self, request):
        """Iniciativas activas"""
        queryset = self.get_queryset().filter(
            status__in=['approved', 'in_progress', 'implemented', 'measuring_results']
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def improvement_cockpit_kpis(request):
    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    nc_qs = Nonconformity.objects.filter(organization_id=organization_id)
    actions_qs = CorrectiveAction.objects.filter(organization_id=organization_id)
    initiatives_qs = ContinualImprovement.objects.filter(organization_id=organization_id)

    kpis = {
        'nonconformities': {
            'total': nc_qs.count(),
            'open': nc_qs.filter(status='open').count(),
            'critical': nc_qs.filter(severity='critical').count(),
        },
        'corrective_actions': {
            'total': actions_qs.count(),
            'overdue': actions_qs.filter(status__in=['planned', 'in_progress']).count(),
            'effective': actions_qs.filter(is_effective=True).count(),
        },
        'improvements': {
            'total': initiatives_qs.count(),
            'active': initiatives_qs.filter(status__in=['approved', 'in_progress', 'implemented', 'measuring_results']).count(),
            'successful': initiatives_qs.filter(status='successful').count(),
        },
    }

    service = ImprovementAIService()
    ai_result = service.process({'operation': 'cockpit_summary', 'kpis': kpis})
    return Response({'organization_id': int(organization_id), 'kpis': kpis, 'ai': ai_result})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def improvement_ai_root_cause(request):
    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    nonconformities = Nonconformity.objects.filter(organization_id=organization_id).order_by('-detection_date')[:100]
    payload = {
        'operation': 'root_cause_intelligence',
        'nonconformities': [
            {
                'id': item.id,
                'nc_number': item.nc_number,
                'source': item.source,
            }
            for item in nonconformities
        ],
    }
    service = ImprovementAIService()
    return Response(service.process(payload))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def improvement_ai_corrective_tracker(request):
    from datetime import date

    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    actions = CorrectiveAction.objects.filter(organization_id=organization_id).order_by('-created_at')[:100]
    payload = {
        'operation': 'corrective_tracker',
        'actions': [
            {
                'id': item.id,
                'action_number': item.action_number,
                'status': item.status,
                'completion_percentage': item.completion_percentage,
                'is_overdue': bool(item.planned_completion_date and item.planned_completion_date < date.today() and item.status in ['planned', 'in_progress']),
            }
            for item in actions
        ],
    }
    service = ImprovementAIService()
    return Response(service.process(payload))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def improvement_ai_continual_optimizer(request):
    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    initiatives = ContinualImprovement.objects.filter(organization_id=organization_id).order_by('-created_at')[:100]
    payload = {
        'operation': 'continual_optimizer',
        'initiatives': [
            {
                'id': item.id,
                'initiative_number': item.initiative_number,
                'priority': item.priority,
                'status': item.status,
            }
            for item in initiatives
        ],
    }
    service = ImprovementAIService()
    return Response(service.process(payload))
