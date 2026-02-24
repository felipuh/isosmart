# operations/views.py
"""
Views for Operations Module
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from core.organization_scoping import OrganizationScopedViewSetMixin
from improvement.services import sync_operations_nc_to_improvement_nc

from .models import (
    OperationalControl,
    CustomerRequirement,
    DesignProject,
    ExternalProvider,
    ProductionControl,
    ProductRelease,
    Nonconformity,
    Disposition
)
from .serializers import (
    OperationalControlSerializer,
    CustomerRequirementSerializer,
    DesignProjectSerializer,
    ExternalProviderSerializer,
    ProductionControlSerializer,
    ProductReleaseSerializer,
    NonconformitySerializer,
    DispositionSerializer
)


class OperationalControlViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Controles Operacionales"""
    queryset = OperationalControl.objects.all()
    serializer_class = OperationalControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'control_type', 'frequency', 'is_active']
    search_fields = ['control_code', 'control_name', 'description', 'related_process']
    ordering_fields = ['control_code', 'control_name', 'created_at']
    ordering = ['control_code']


class CustomerRequirementViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Requisitos del Cliente"""
    queryset = CustomerRequirement.objects.all()
    serializer_class = CustomerRequirementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'requirement_type', 'status', 'is_confirmed', 'can_meet_requirement']
    search_fields = ['requirement_code', 'customer_name', 'requirement_title', 'description']
    ordering_fields = ['communication_date', 'requirement_code', 'created_at']
    ordering = ['-communication_date']
    
    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """Requisitos pendientes de revisión"""
        queryset = self.get_queryset().filter(
            is_reviewed=False,
            status='identified'
        ).order_by('communication_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_confirmation(self, request):
        """Requisitos revisados pero no confirmados con cliente"""
        queryset = self.get_queryset().filter(
            is_reviewed=True,
            is_confirmed=False
        ).order_by('review_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def not_feasible(self, request):
        """Requisitos que no se pueden cumplir"""
        queryset = self.get_queryset().filter(
            can_meet_requirement=False
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DesignProjectViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Proyectos de Diseño y Desarrollo"""
    queryset = DesignProject.objects.all()
    serializer_class = DesignProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'project_type', 'current_stage', 'status', 'is_verified', 'is_validated']
    search_fields = ['project_code', 'project_name', 'description']
    ordering_fields = ['start_date', 'target_completion_date', 'created_at']
    ordering = ['-start_date']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Proyectos activos"""
        queryset = self.get_queryset().filter(
            status='active'
        ).order_by('target_completion_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_verification(self, request):
        """Proyectos pendientes de verificación"""
        queryset = self.get_queryset().filter(
            is_verified=False,
            status='active'
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_validation(self, request):
        """Proyectos verificados pero pendientes de validación"""
        queryset = self.get_queryset().filter(
            is_verified=True,
            is_validated=False,
            status='active'
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ExternalProviderViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Proveedores Externos"""
    queryset = ExternalProvider.objects.all()
    serializer_class = ExternalProviderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'provision_type', 'classification', 'performance_rating', 'is_active']
    search_fields = ['provider_code', 'provider_name', 'contact_person', 'products_services']
    ordering_fields = ['provider_name', 'evaluation_score', 'performance_rating', 'created_at']
    ordering = ['provider_name']
    
    @action(detail=False, methods=['get'])
    def approved(self, request):
        """Proveedores aprobados"""
        queryset = self.get_queryset().filter(
            classification='approved',
            is_active=True
        ).order_by('-evaluation_score')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def evaluation_due(self, request):
        """Proveedores que requieren evaluación"""
        from datetime import date, timedelta
        
        threshold_date = date.today() - timedelta(days=365)  # Sin evaluación en 1 año
        
        queryset = self.get_queryset().filter(
            is_active=True
        ).filter(
            models.Q(last_evaluation_date__lt=threshold_date) | 
            models.Q(last_evaluation_date__isnull=True)
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductionControlViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Controles de Producción"""
    queryset = ProductionControl.objects.all()
    serializer_class = ProductionControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'control_type', 'requires_traceability', 'handles_customer_property', 'is_active']
    search_fields = ['control_code', 'product_service_name', 'description']
    ordering_fields = ['control_code', 'product_service_name', 'created_at']
    ordering = ['control_code']


class ProductReleaseViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Liberación de Productos/Servicios"""
    queryset = ProductRelease.objects.all()
    serializer_class = ProductReleaseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'status', 'verification_performed', 'acceptance_criteria_met']
    search_fields = ['release_code', 'product_service_name', 'batch_lot_number', 'customer_name']
    ordering_fields = ['release_date', 'release_code', 'created_at']
    ordering = ['-release_date']
    
    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Liberaciones pendientes de aprobación"""
        queryset = self.get_queryset().filter(
            status='pending'
        ).order_by('release_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Liberaciones recientes (últimos 30 días)"""
        from datetime import date, timedelta
        
        start_date = date.today() - timedelta(days=30)
        
        queryset = self.get_queryset().filter(
            release_date__gte=start_date
        ).order_by('-release_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class NonconformityViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para No Conformidades"""
    queryset = Nonconformity.objects.all()
    serializer_class = NonconformitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'nc_type', 'severity', 'status', 'detection_stage', 'affects_customer']
    search_fields = ['nc_number', 'title', 'description', 'affected_product_service']
    ordering_fields = ['detection_date', 'nc_number', 'severity', 'created_at']
    ordering = ['-detection_date']

    def perform_create(self, serializer):
        super().perform_create(serializer)
        sync_operations_nc_to_improvement_nc(serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        sync_operations_nc_to_improvement_nc(serializer.instance)

    @action(detail=True, methods=['post'])
    def sync_to_improvement(self, request, pk=None):
        nc = self.get_object()
        linked = sync_operations_nc_to_improvement_nc(nc)
        return Response({
            'success': True,
            'operations_nc': nc.nc_number,
            'improvement_nc': linked.nc_number,
            'improvement_id': linked.id,
        })

    @action(detail=False, methods=['post'])
    def sync_open_to_improvement(self, request):
        queryset = self.get_queryset().filter(status__in=['identified', 'under_review', 'disposition_pending', 'treated'])
        synced = []
        for nc in queryset:
            linked = sync_operations_nc_to_improvement_nc(nc)
            synced.append({'operations_nc': nc.nc_number, 'improvement_nc': linked.nc_number, 'improvement_id': linked.id})
        return Response({'success': True, 'count': len(synced), 'items': synced})
    
    @action(detail=False, methods=['get'])
    def open(self, request):
        """No conformidades abiertas"""
        queryset = self.get_queryset().filter(
            status__in=['identified', 'under_review', 'disposition_pending', 'treated']
        ).order_by('-severity', 'detection_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """No conformidades críticas"""
        queryset = self.get_queryset().filter(
            severity='critical',
            status__in=['identified', 'under_review', 'disposition_pending', 'treated']
        ).order_by('detection_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def customer_impact(self, request):
        """No conformidades que afectan al cliente"""
        queryset = self.get_queryset().filter(
            affects_customer=True
        ).order_by('-detection_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_disposition(self, request):
        """No conformidades sin disposición"""
        queryset = self.get_queryset().filter(
            status='disposition_pending'
        ).order_by('detection_date')
        
        # Filtrar las que no tienen disposition
        ncs_without_disposition = [nc for nc in queryset if not hasattr(nc, 'disposition')]
        
        serializer = self.get_serializer(ncs_without_disposition, many=True)
        return Response(serializer.data)


class DispositionViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    organization_lookup_field = 'nonconformity__organization_id'
    organization_write_field = None
    """ViewSet para Disposiciones"""
    queryset = Disposition.objects.all()
    serializer_class = DispositionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['nonconformity__organization_id', 'disposition_action', 'requires_authorization', 'is_verified', 'is_effective']
    search_fields = ['nonconformity__nc_number', 'action_description']
    ordering_fields = ['created_at', 'implementation_date', 'verification_date']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        organization_id = self.get_organization_id()
        nonconformity = serializer.validated_data.get('nonconformity')
        if nonconformity and nonconformity.organization_id != organization_id:
            raise PermissionDenied('No conformidad fuera de la organización activa')
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def pending_verification(self, request):
        """Disposiciones implementadas pero no verificadas"""
        queryset = self.get_queryset().filter(
            implementation_date__isnull=False,
            is_verified=False
        ).order_by('implementation_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
