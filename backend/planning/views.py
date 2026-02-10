# planning/views.py
"""
Views for Planning Module
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    RiskOpportunity,
    QualityObjective,
    ObjectiveAction,
    ChangeControl
)
from .serializers import (
    RiskOpportunitySerializer,
    QualityObjectiveSerializer,
    ObjectiveActionSerializer,
    ChangeControlSerializer
)


class RiskOpportunityViewSet(viewsets.ModelViewSet):
    """ViewSet para Riesgos y Oportunidades"""
    queryset = RiskOpportunity.objects.all()
    serializer_class = RiskOpportunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'item_type', 'category', 'status', 'context', 'is_active']
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['risk_level', 'opportunity_score', 'created_at', 'review_date']
    ordering = ['-risk_level', '-opportunity_score']
    
    @action(detail=False, methods=['get'])
    def risks(self, request):
        """Solo riesgos"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            item_type='risk',
            is_active=True
        ).order_by('-risk_level')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def opportunities(self, request):
        """Solo oportunidades"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            item_type='opportunity',
            is_active=True
        ).order_by('-opportunity_score')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        """Riesgos de alta prioridad (nivel >= 15)"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            item_type='risk',
            risk_level__gte=15,
            is_active=True
        ).order_by('-risk_level')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class QualityObjectiveViewSet(viewsets.ModelViewSet):
    """ViewSet para Objetivos de Calidad"""
    queryset = QualityObjective.objects.all()
    serializer_class = QualityObjectiveSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'status', 'alignment', 'is_active']
    search_fields = ['code', 'title', 'description', 'metric']
    ordering_fields = ['target_date', 'progress_percentage', 'created_at']
    ordering = ['-target_date']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Objetivos activos"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            status='in_progress',
            is_active=True
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def smart_compliant(self, request):
        """Objetivos que cumplen SMART"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            is_specific=True,
            is_measurable=True,
            is_achievable=True,
            is_relevant=True,
            is_time_bound=True,
            is_active=True
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def at_risk(self, request):
        """Objetivos en riesgo (progreso < 50% y fecha meta cercana)"""
        from datetime import date, timedelta
        
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        threshold_date = date.today() + timedelta(days=30)
        
        queryset = self.queryset.filter(
            organization_id=organization_id,
            status='in_progress',
            progress_percentage__lt=50,
            target_date__lte=threshold_date,
            is_active=True
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ObjectiveActionViewSet(viewsets.ModelViewSet):
    """ViewSet para Acciones de Objetivos"""
    queryset = ObjectiveAction.objects.all()
    serializer_class = ObjectiveActionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'objective', 'status', 'responsible']
    search_fields = ['description', 'what_will_be_done']
    ordering_fields = ['due_date', 'progress_percentage', 'created_at']
    ordering = ['objective', 'action_number']
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Acciones vencidas"""
        from datetime import date
        
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            due_date__lt=date.today(),
            status__in=['planned', 'in_progress']
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChangeControlViewSet(viewsets.ModelViewSet):
    """ViewSet para Control de Cambios"""
    queryset = ChangeControl.objects.all()
    serializer_class = ChangeControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'status', 'change_type', 'urgency', 'reason']
    search_fields = ['change_number', 'title', 'description']
    ordering_fields = ['planned_date', 'urgency', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprobar cambio"""
        change = self.get_object()
        change.approve(request.user)
        return Response({'status': 'Cambio aprobado'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechazar cambio"""
        change = self.get_object()
        comments = request.data.get('comments', '')
        change.reject(request.user, comments)
        return Response({'status': 'Cambio rechazado'})
    
    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Cambios pendientes de aprobación"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            status__in=['submitted', 'under_review']
        ).order_by('urgency', 'planned_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
