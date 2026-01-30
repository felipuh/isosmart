from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Count

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


class ScopeDefinitionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de definiciones de alcance
    """
    queryset = ScopeDefinition.objects.all().order_by('-created_at')
    serializer_class = ScopeDefinitionSerializer
    
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
            ScopeDefinition.objects.filter(status='active').update(status='superseded')
            
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
            scope = ScopeDefinition.objects.filter(status='active').first()
            
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
            total = ScopeDefinition.objects.count()
            by_status = ScopeDefinition.objects.values('status').annotate(
                count=Count('id')
            )
            
            active_scope = ScopeDefinition.objects.filter(status='active').first()
            
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
        analyzer = ScopeAnalyzer()
        result = analyzer.process(data=serializer.validated_data)
        
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
            
    except Exception as e:
        logger.error(f"Error en análisis de alcance: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_latest_scope(request):
    """
    Obtener la última definición de alcance
    """
    try:
        # ⭐ CORREGIDO: usar created_at del modelo ScopeDefinition (que SÍ existe)
        latest = ScopeDefinition.objects.order_by('-created_at').first()
        
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
        
    except Exception as e:
        logger.error(f"Error obteniendo último alcance: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_scope_statement(request):
    """
    Obtener la declaración de alcance más reciente
    """
    try:
        latest = ScopeDefinition.objects.order_by('-created_at').first()

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

    except Exception as e:
        logger.error(f"Error obteniendo declaración de alcance: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def run_scope_audit(request):
    """
    Ejecutar auditoría básica del alcance (validaciones mínimas)
    """
    try:
        latest = ScopeDefinition.objects.order_by('-created_at').first()

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

    except Exception as e:
        logger.error(f"Error en auditoría de alcance: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessScopeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de procesos en alcance
    """
    queryset = ProcessScope.objects.all()
    serializer_class = ProcessScopeSerializer
    
    def get_queryset(self):
        """Filtrar por definición de alcance si se especifica"""
        queryset = super().get_queryset()
        
        scope_id = self.request.query_params.get('scope_id', None)
        if scope_id:
            queryset = queryset.filter(scope_definition_id=scope_id)
        
        return queryset


class LocationScopeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de ubicaciones en alcance
    """
    queryset = LocationScope.objects.all()
    serializer_class = LocationScopeSerializer
    
    def get_queryset(self):
        """Filtrar por definición de alcance si se especifica"""
        queryset = super().get_queryset()
        
        scope_id = self.request.query_params.get('scope_id', None)
        if scope_id:
            queryset = queryset.filter(scope_definition_id=scope_id)
        
        return queryset