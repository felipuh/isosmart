# resources/views.py
"""
Views for Resources Module
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from core.organization_scoping import OrganizationScopedViewSetMixin

from .models import (
    Resource,
    Infrastructure,
    WorkEnvironment,
    Competence,
    Training,
    Awareness,
    Communication
)
from .serializers import (
    ResourceSerializer,
    InfrastructureSerializer,
    WorkEnvironmentSerializer,
    CompetenceSerializer,
    TrainingSerializer,
    AwarenessSerializer,
    CommunicationSerializer
)


class ResourceViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Recursos"""
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'resource_type', 'status', 'is_active']
    search_fields = ['name', 'code', 'description', 'location']
    ordering_fields = ['name', 'resource_type', 'created_at']
    ordering = ['resource_type', 'name']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Recursos agrupados por tipo"""
        resources = self.get_queryset().filter(is_active=True)
        
        result = {}
        for resource_type, _ in Resource.RESOURCE_TYPE_CHOICES:
            result[resource_type] = ResourceSerializer(
                resources.filter(resource_type=resource_type),
                many=True
            ).data
        
        return Response(result)


class InfrastructureViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Infraestructura"""
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'infrastructure_type', 'status', 'is_active']
    search_fields = ['name', 'code', 'description', 'location']
    ordering_fields = ['name', 'next_maintenance_date', 'created_at']
    ordering = ['infrastructure_type', 'name']
    
    @action(detail=False, methods=['get'])
    def maintenance_due(self, request):
        """Infraestructura con mantenimiento próximo"""
        from datetime import date, timedelta

        days = int(request.query_params.get('days', 30))

        future_date = date.today() + timedelta(days=days)

        queryset = self.get_queryset().filter(
            is_active=True,
            next_maintenance_date__lte=future_date,
            next_maintenance_date__gte=date.today()
        ).order_by('next_maintenance_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class WorkEnvironmentViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Ambientes de Trabajo"""
    queryset = WorkEnvironment.objects.all()
    serializer_class = WorkEnvironmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'overall_condition', 'is_active']
    search_fields = ['area_name', 'location', 'description']
    ordering_fields = ['area_name', 'last_evaluation_date', 'created_at']
    ordering = ['area_name']


class CompetenceViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Competencias"""
    queryset = Competence.objects.all()
    serializer_class = CompetenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'user', 'required_level', 'current_level', 'needs_improvement', 'is_active']
    search_fields = ['competence_name', 'position', 'user__username', 'user__email']
    ordering_fields = ['user', 'competence_name', 'created_at']
    ordering = ['user', 'competence_name']
    
    @action(detail=False, methods=['get'])
    def gaps(self, request):
        """Competencias con brecha (gap)"""
        queryset = self.get_queryset().filter(
            is_active=True
        )
        
        # Filtrar aquellos con brecha
        gaps = [comp for comp in queryset if comp.has_gap]
        
        serializer = self.get_serializer(gaps, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Competencias agrupadas por usuario"""
        user_id = request.query_params.get('user_id')

        queryset = self.get_queryset().filter(
            user_id=user_id,
            is_active=True
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TrainingViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Capacitaciones"""
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'training_type', 'status']
    search_fields = ['title', 'code', 'description', 'instructor']
    ordering_fields = ['start_date', 'title', 'created_at']
    ordering = ['-start_date']
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Capacitaciones próximas"""
        from datetime import date

        queryset = self.get_queryset().filter(
            start_date__gte=date.today(),
            status__in=['planned', 'in_progress']
        ).order_by('start_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Agregar participante a capacitación"""
        training = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            training.participants.add(user)
            return Response({'status': 'Participante agregado'})
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class AwarenessViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Actividades de Conciencia"""
    queryset = Awareness.objects.all()
    serializer_class = AwarenessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'awareness_type', 'method']
    search_fields = ['activity_name', 'description', 'target_audience']
    ordering_fields = ['date', 'activity_name', 'created_at']
    ordering = ['-date']
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Agregar participante a actividad"""
        activity = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            activity.participants.add(user)
            return Response({'status': 'Participante agregado'})
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class CommunicationViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Comunicaciones"""
    queryset = Communication.objects.all()
    serializer_class = CommunicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'communication_type', 'method', 'frequency', 'status', 'is_active']
    search_fields = ['title', 'description', 'content_summary', 'target_audience']
    ordering_fields = ['scheduled_date', 'title', 'created_at']
    ordering = ['-scheduled_date']
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Comunicaciones pendientes"""

        queryset = self.get_queryset().filter(
            status='planned',
            is_active=True
        ).order_by('scheduled_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
