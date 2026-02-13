# improvement/views.py
"""
Views for Improvement Module
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Nonconformity, CorrectiveAction, ContinualImprovement
from .serializers import (
    NonconformitySerializer,
    CorrectiveActionSerializer,
    ContinualImprovementSerializer
)


class NonconformityViewSet(viewsets.ModelViewSet):
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
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(organization_id=organization_id)
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


class CorrectiveActionViewSet(viewsets.ModelViewSet):
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

        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(
            organization_id=organization_id,
            planned_completion_date__lt=date.today(),
            status__in=['planned', 'in_progress']
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ContinualImprovementViewSet(viewsets.ModelViewSet):
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
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(
            organization_id=organization_id,
            status__in=['approved', 'in_progress', 'implemented', 'measuring_results']
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
