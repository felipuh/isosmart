from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Count
from authentication.models import UserProfile
from core.organization_scoping import OrganizationScopedViewSetMixin

from .models import ScopeDefinition, ProcessScope, LocationScope
from .serializers import (
    ScopeDefinitionSerializer,
    ScopeDefinitionCreateSerializer,
    ProcessScopeSerializer,
    LocationScopeSerializer
)
from .services.scope_analyzer import ScopeAnalyzer

import logging

logger = logging.getLogger(__name__)


def _parse_org_id(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError({'organization_id': 'organization_id invalido'})


def _allowed_org_ids_for_request(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return set()
    if user.is_superuser:
        return None
    return set(
        UserProfile.objects.filter(user=user, is_active=True).values_list('organization_id', flat=True)
    )


def _resolve_scoped_org_id(request):
    query_org_id = _parse_org_id(
        request.query_params.get('organization_id')
        or request.query_params.get('organization')
        or request.data.get('organization_id')
        or request.data.get('organization')
    )
    token_org_id = _parse_org_id(getattr(request, 'organization_id', None))

    if query_org_id and token_org_id and query_org_id != token_org_id:
        raise PermissionDenied('organization_id no coincide con el token activo')

    organization_id = query_org_id or token_org_id
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    allowed_org_ids = _allowed_org_ids_for_request(request)
    if allowed_org_ids is not None and organization_id not in allowed_org_ids:
        raise PermissionDenied('No autorizado para esta organizacion')

    return organization_id


class ScopeDefinitionViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de definiciones de alcance
    """
    queryset = ScopeDefinition.objects.all().order_by('-created_at')
    serializer_class = ScopeDefinitionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por estado si se especifica"""
        queryset = super().get_queryset()
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprobar una definición de alcance"""
        try:
            scope = self.get_object()
            scope.status = 'approved'
            scope.save()
            
            logger.info(f"Alcance aprobado: {scope.title} (ID: {scope.id})")
            
            serializer = self.get_serializer(scope)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error aprobando alcance: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activar una definición de alcance (solo una activa a la vez)"""
        try:
            scope = self.get_object()
            
            # Desactivar todas las demás
            ScopeDefinition.objects.filter(
                status='active',
                organization_id=scope.organization_id
            ).exclude(id=scope.id).update(status='superseded')
            
            # Activar esta
            scope.status = 'active'
            scope.save()
            
            logger.info(f"Alcance activado: {scope.title} (ID: {scope.id})")
            
            serializer = self.get_serializer(scope)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error activando alcance: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Obtener la definición de alcance activa"""
        try:
            scope = self.get_queryset().filter(status='active').first()
            
            if not scope:
                return Response(
                    {'message': 'No hay alcance activo'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(scope)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo alcance activo: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de alcances"""
        try:
            scoped = self.get_queryset()
            total = scoped.count()
            by_status = scoped.values('status').annotate(
                count=Count('id')
            )
            
            active_scope = scoped.filter(status='active').first()
            
            stats = {
                'total_definitions': total,
                'by_status': {item['status']: item['count'] for item in by_status},
                'active_scope': {
                    'id': active_scope.id if active_scope else None,
                    'title': active_scope.title if active_scope else None,
                    'version': active_scope.version if active_scope else None,
                    'products_count': active_scope.total_products if active_scope else 0,
                    'coverage': active_scope.coverage_score if active_scope else 0
                } if active_scope else None
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_scope_analysis(request):
    """
    Ejecutar análisis de alcance con IA
    """
    try:
        logger.info("Iniciando análisis de alcance...")
        
        # Validar datos de entrada
        serializer = ScopeDefinitionCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ejecutar análisis
        organization_id = _resolve_scoped_org_id(request)
        analyzer = ScopeAnalyzer()
        payload = dict(serializer.validated_data)
        payload['organization_id'] = organization_id
        result = analyzer.process(data=payload)
        
        logger.info(f"Análisis de alcance completado: {result.get('status')}")
        
        if result.get('status') == 'completed':
            return Response({
                'status': 'success',
                'message': 'Análisis de alcance completado',
                'scope_id': result.get('scope_id'),
                'scope_statement': result.get('scope_statement'),
                'products_count': result.get('products_count'),
                'exclusions_count': result.get('exclusions_count'),
                'coverage_score': result.get('coverage_score'),
                'boundaries': result.get('boundaries'),
                'requirements': result.get('requirements'),
                'recommendations': result.get('recommendations')
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': result.get('message', result.get('error'))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except (ValidationError, PermissionDenied):
        raise
    except Exception as e:
        logger.error(f"Error en análisis de alcance: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_scope(request):
    """
    Obtener la última definición de alcance
    """
    try:
        organization_id = _resolve_scoped_org_id(request)
        latest = ScopeDefinition.objects.filter(organization_id=organization_id).order_by('-created_at').first()
        
        if not latest:
            return Response({
                'status': 'no_data',
                'message': 'No hay definiciones de alcance disponibles'
            })
        
        serializer = ScopeDefinitionSerializer(latest)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
        
    except (ValidationError, PermissionDenied):
        raise
    except Exception as e:
        logger.error(f"Error obteniendo último alcance: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scope_statement(request):
    """
    Obtener la declaración de alcance más reciente
    """
    try:
        organization_id = _resolve_scoped_org_id(request)
        latest = ScopeDefinition.objects.filter(organization_id=organization_id).order_by('-created_at').first()

        if not latest:
            return Response({
                'status': 'no_data',
                'message': 'No hay definiciones de alcance disponibles'
            })

        return Response({
            'status': 'success',
            'scope_id': latest.id,
            'title': latest.title,
            'version': latest.version,
            'scope_statement': latest.scope_statement or ''
        })

    except (ValidationError, PermissionDenied):
        raise
    except Exception as e:
        logger.error(f"Error obteniendo declaración de alcance: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_scope_audit(request):
    """
    Ejecutar auditoría básica del alcance (validaciones mínimas)
    """
    try:
        organization_id = _resolve_scoped_org_id(request)
        latest = ScopeDefinition.objects.filter(organization_id=organization_id).order_by('-created_at').first()

        if not latest:
            return Response({
                'status': 'no_data',
                'message': 'No hay definiciones de alcance disponibles'
            })

        issues = []
        if not latest.scope_statement:
            issues.append('Falta la declaración de alcance.')
        if not latest.products_services:
            issues.append('No se han definido productos o servicios.')
        if not latest.organizational_boundaries:
            issues.append('No se han definido límites organizacionales.')
        if not latest.applicable_requirements:
            issues.append('No se han definido requisitos aplicables.')

        score = max(0, 100 - (len(issues) * 20))

        return Response({
            'status': 'success',
            'scope_id': latest.id,
            'score': score,
            'issues': issues
        })

    except (ValidationError, PermissionDenied):
        raise
    except Exception as e:
        logger.error(f"Error en auditoría de alcance: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessScopeViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de procesos en alcance
    """
    organization_lookup_field = 'scope_definition__organization_id'
    organization_write_field = None
    queryset = ProcessScope.objects.all()
    serializer_class = ProcessScopeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por definición de alcance si se especifica"""
        queryset = super().get_queryset()
        
        scope_id = self.request.query_params.get('scope_id', None)
        if scope_id:
            queryset = queryset.filter(scope_definition_id=scope_id)
        
        return queryset

    def perform_create(self, serializer):
        organization_id = self.get_organization_id()
        scope_definition = serializer.validated_data.get('scope_definition')
        if scope_definition and scope_definition.organization_id != organization_id:
            raise PermissionDenied('La definicion de alcance no pertenece a la organizacion activa')
        serializer.save()

    def perform_update(self, serializer):
        organization_id = self.get_organization_id()
        scope_definition = serializer.validated_data.get('scope_definition') or getattr(serializer.instance, 'scope_definition', None)
        if scope_definition and scope_definition.organization_id != organization_id:
            raise PermissionDenied('No puede mover registros fuera de la organizacion activa')
        serializer.save()


class LocationScopeViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de ubicaciones en alcance
    """
    organization_lookup_field = 'scope_definition__organization_id'
    organization_write_field = None
    queryset = LocationScope.objects.all()
    serializer_class = LocationScopeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por definición de alcance si se especifica"""
        queryset = super().get_queryset()
        
        scope_id = self.request.query_params.get('scope_id', None)
        if scope_id:
            queryset = queryset.filter(scope_definition_id=scope_id)
        
        return queryset

    def perform_create(self, serializer):
        organization_id = self.get_organization_id()
        scope_definition = serializer.validated_data.get('scope_definition')
        if scope_definition and scope_definition.organization_id != organization_id:
            raise PermissionDenied('La definicion de alcance no pertenece a la organizacion activa')
        serializer.save()

    def perform_update(self, serializer):
        organization_id = self.get_organization_id()
        scope_definition = serializer.validated_data.get('scope_definition') or getattr(serializer.instance, 'scope_definition', None)
        if scope_definition and scope_definition.organization_id != organization_id:
            raise PermissionDenied('No puede mover registros fuera de la organizacion activa')
        serializer.save()