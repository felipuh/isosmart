# operations/views.py
"""
Views for Operations Module
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

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


class OperationalControlViewSet(viewsets.ModelViewSet):
    """ViewSet para Controles Operacionales"""
    queryset = OperationalControl.objects.all()
    serializer_class = OperationalControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'control_type', 'frequency', 'is_active']
    search_fields = ['control_code', 'control_name', 'description', 'related_process']
    ordering_fields = ['control_code', 'control_name', 'created_at']
    ordering = ['control_code']


class CustomerRequirementViewSet(viewsets.ModelViewSet):
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
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            is_reviewed=False,
            status='identified'
        ).order_by('communication_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_confirmation(self, request):
        """Requisitos revisados pero no confirmados con cliente"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            is_reviewed=True,
            is_confirmed=False
        ).order_by('review_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def not_feasible(self, request):
        """Requisitos que no se pueden cumplir"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            can_meet_requirement=False
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DesignProjectViewSet(viewsets.ModelViewSet):
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
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            status='active'
        ).order_by('target_completion_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_verification(self, request):
        """Proyectos pendientes de verificación"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            is_verified=False,
            status='active'
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_validation(self, request):
        """Proyectos verificados pero pendientes de validación"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            is_verified=True,
            is_validated=False,
            status='active'
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ExternalProviderViewSet(viewsets.ModelViewSet):
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
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            classification='approved',
            is_active=True
        ).order_by('-evaluation_score')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def evaluation_due(self, request):
        """Proveedores que requieren evaluación"""
        from datetime import date, timedelta
        
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        threshold_date = date.today() - timedelta(days=365)  # Sin evaluación en 1 año
        
        queryset = self.queryset.filter(
            organization_id=organization_id,
            is_active=True
        ).filter(
            models.Q(last_evaluation_date__lt=threshold_date) | 
            models.Q(last_evaluation_date__isnull=True)
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductionControlViewSet(viewsets.ModelViewSet):
    """ViewSet para Controles de Producción"""
    queryset = ProductionControl.objects.all()
    serializer_class = ProductionControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'control_type', 'requires_traceability', 'handles_customer_property', 'is_active']
    search_fields = ['control_code', 'product_service_name', 'description']
    ordering_fields = ['control_code', 'product_service_name', 'created_at']
    ordering = ['control_code']


class ProductReleaseViewSet(viewsets.ModelViewSet):
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
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            status='pending'
        ).order_by('release_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Liberaciones recientes (últimos 30 días)"""
        from datetime import date, timedelta
        
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        start_date = date.today() - timedelta(days=30)
        
        queryset = self.queryset.filter(
            organization_id=organization_id,
            release_date__gte=start_date
        ).order_by('-release_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class NonconformityViewSet(viewsets.ModelViewSet):
    """ViewSet para No Conformidades"""
    queryset = Nonconformity.objects.all()
    serializer_class = NonconformitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'nc_type', 'severity', 'status', 'detection_stage', 'affects_customer']
    search_fields = ['nc_number', 'title', 'description', 'affected_product_service']
    ordering_fields = ['detection_date', 'nc_number', 'severity', 'created_at']
    ordering = ['-detection_date']
    
    @action(detail=False, methods=['get'])
    def open(self, request):
        """No conformidades abiertas"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            status__in=['identified', 'under_review', 'disposition_pending', 'treated']
        ).order_by('-severity', 'detection_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """No conformidades críticas"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            severity='critical',
            status__in=['identified', 'under_review', 'disposition_pending', 'treated']
        ).order_by('detection_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def customer_impact(self, request):
        """No conformidades que afectan al cliente"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            affects_customer=True
        ).order_by('-detection_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_disposition(self, request):
        """No conformidades sin disposición"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            organization_id=organization_id,
            status='disposition_pending'
        ).order_by('detection_date')
        
        # Filtrar las que no tienen disposition
        ncs_without_disposition = [nc for nc in queryset if not hasattr(nc, 'disposition')]
        
        serializer = self.get_serializer(ncs_without_disposition, many=True)
        return Response(serializer.data)


class DispositionViewSet(viewsets.ModelViewSet):
    """ViewSet para Disposiciones"""
    queryset = Disposition.objects.all()
    serializer_class = DispositionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['nonconformity__organization_id', 'disposition_action', 'requires_authorization', 'is_verified', 'is_effective']
    search_fields = ['nonconformity__nc_number', 'action_description']
    ordering_fields = ['created_at', 'implementation_date', 'verification_date']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def pending_verification(self, request):
        """Disposiciones implementadas pero no verificadas"""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(
            nonconformity__organization_id=organization_id,
            implementation_date__isnull=False,
            is_verified=False
        ).order_by('implementation_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
