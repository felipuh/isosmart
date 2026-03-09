from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Count
from authentication.models import UserProfile
from core.organization_scoping import OrganizationScopedViewSetMixin

from .models import ProcessMap, Process, ProcessInteraction, ProcessActivity
from .serializers import (
    ProcessMapSerializer,
    ProcessMapCreateSerializer,
    ProcessSerializer,
    ProcessInteractionSerializer,
    ProcessActivitySerializer
)
from .services.process_analyzer import ProcessAnalyzer

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


class ProcessMapViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de mapas de procesos
    """
    queryset = ProcessMap.objects.all().order_by('-created_at')
    serializer_class = ProcessMapSerializer
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
        """Aprobar un mapa de procesos"""
        try:
            process_map = self.get_object()
            process_map.status = 'approved'
            process_map.save()
            
            logger.info(f"Mapa de procesos aprobado: {process_map.title} (ID: {process_map.id})")
            
            serializer = self.get_serializer(process_map)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error aprobando mapa: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activar un mapa de procesos (solo uno activo a la vez)"""
        try:
            process_map = self.get_object()
            
            # Desactivar todos los demás
            ProcessMap.objects.filter(
                status='active',
                organization_id=process_map.organization_id
            ).exclude(id=process_map.id).update(status='approved')
            
            # Activar este
            process_map.status = 'active'
            process_map.save()
            
            logger.info(f"Mapa de procesos activado: {process_map.title} (ID: {process_map.id})")
            
            serializer = self.get_serializer(process_map)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error activando mapa: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Obtener el mapa de procesos activo"""
        try:
            process_map = self.get_queryset().filter(status='active').first()
            
            if not process_map:
                return Response(
                    {'message': 'No hay mapa de procesos activo'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(process_map)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo mapa activo: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de mapas de procesos"""
        try:
            scoped = self.get_queryset()
            total = scoped.count()
            by_status = scoped.values('status').annotate(
                count=Count('id')
            )
            
            active_map = scoped.filter(status='active').first()
            
            stats = {
                'total_maps': total,
                'by_status': {item['status']: item['count'] for item in by_status},
                'active_map': {
                    'id': active_map.id if active_map else None,
                    'title': active_map.title if active_map else None,
                    'version': active_map.version if active_map else None,
                    'total_processes': active_map.total_processes if active_map else 0,
                    'critical_processes': len(active_map.critical_processes) if active_map else 0
                } if active_map else None
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def diagram(self, request, pk=None):
        """Obtener datos del diagrama de procesos"""
        try:
            process_map = self.get_object()
            
            return Response({
                'status': 'success',
                'diagram_data': process_map.interaction_analysis
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo diagrama: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de procesos individuales
    """
    organization_lookup_field = 'process_map__organization_id'
    organization_write_field = None
    queryset = Process.objects.all().select_related('process_map')
    serializer_class = ProcessSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por mapa o tipo si se especifica"""
        queryset = super().get_queryset()
        
        map_id = self.request.query_params.get('map_id', None)
        if map_id:
            queryset = queryset.filter(process_map_id=map_id)
        
        process_type = self.request.query_params.get('type', None)
        if process_type:
            queryset = queryset.filter(process_type=process_type)
        
        only_critical = self.request.query_params.get('critical', None)
        if only_critical == 'true':
            queryset = queryset.filter(is_critical=True)
        
        return queryset

    def perform_create(self, serializer):
        organization_id = self.get_organization_id()
        process_map = serializer.validated_data.get('process_map')
        if process_map and process_map.organization_id != organization_id:
            raise PermissionDenied('El mapa no pertenece a la organizacion activa')
        serializer.save()

    def perform_update(self, serializer):
        organization_id = self.get_organization_id()
        process_map = serializer.validated_data.get('process_map') or getattr(serializer.instance, 'process_map', None)
        if process_map and process_map.organization_id != organization_id:
            raise PermissionDenied('No puede mover procesos fuera de la organizacion activa')
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Obtener procesos agrupados por tipo"""
        try:
            map_id = request.query_params.get('map_id')
            
            queryset = self.get_queryset()
            if map_id:
                queryset = queryset.filter(process_map_id=map_id)
            
            by_type = {
                'strategic': ProcessSerializer(
                    queryset.filter(process_type='strategic'), 
                    many=True
                ).data,
                'operational': ProcessSerializer(
                    queryset.filter(process_type='operational'), 
                    many=True
                ).data,
                'support': ProcessSerializer(
                    queryset.filter(process_type='support'), 
                    many=True
                ).data,
            }
            
            return Response(by_type)
            
        except Exception as e:
            logger.error(f"Error agrupando procesos: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessInteractionViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de interacciones entre procesos
    """
    organization_lookup_field = 'process_map__organization_id'
    organization_write_field = None
    queryset = ProcessInteraction.objects.all().select_related(
        'source_process', 
        'target_process'
    )
    serializer_class = ProcessInteractionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por mapa si se especifica"""
        queryset = super().get_queryset()
        
        map_id = self.request.query_params.get('map_id', None)
        if map_id:
            queryset = queryset.filter(process_map_id=map_id)
        
        return queryset

    def perform_create(self, serializer):
        organization_id = self.get_organization_id()
        process_map = serializer.validated_data.get('process_map')
        source_process = serializer.validated_data.get('source_process')
        target_process = serializer.validated_data.get('target_process')

        if process_map and process_map.organization_id != organization_id:
            raise PermissionDenied('El mapa no pertenece a la organizacion activa')

        if source_process and process_map and source_process.process_map_id != process_map.id:
            raise ValidationError({'source_process': 'Debe pertenecer al mapa seleccionado'})
        if target_process and process_map and target_process.process_map_id != process_map.id:
            raise ValidationError({'target_process': 'Debe pertenecer al mapa seleccionado'})

        serializer.save()

    def perform_update(self, serializer):
        organization_id = self.get_organization_id()
        process_map = serializer.validated_data.get('process_map') or getattr(serializer.instance, 'process_map', None)
        source_process = serializer.validated_data.get('source_process') or getattr(serializer.instance, 'source_process', None)
        target_process = serializer.validated_data.get('target_process') or getattr(serializer.instance, 'target_process', None)

        if process_map and process_map.organization_id != organization_id:
            raise PermissionDenied('No puede mover interacciones fuera de la organizacion activa')

        if source_process and process_map and source_process.process_map_id != process_map.id:
            raise ValidationError({'source_process': 'Debe pertenecer al mapa seleccionado'})
        if target_process and process_map and target_process.process_map_id != process_map.id:
            raise ValidationError({'target_process': 'Debe pertenecer al mapa seleccionado'})

        serializer.save()


class ProcessActivityViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de actividades de procesos
    """
    organization_lookup_field = 'process__process_map__organization_id'
    organization_write_field = None
    queryset = ProcessActivity.objects.all().select_related('process')
    serializer_class = ProcessActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por proceso si se especifica"""
        queryset = super().get_queryset()
        
        process_id = self.request.query_params.get('process_id', None)
        if process_id:
            queryset = queryset.filter(process_id=process_id)
        
        return queryset

    def perform_create(self, serializer):
        organization_id = self.get_organization_id()
        process = serializer.validated_data.get('process')
        if process and process.process_map.organization_id != organization_id:
            raise PermissionDenied('El proceso no pertenece a la organizacion activa')
        serializer.save()

    def perform_update(self, serializer):
        organization_id = self.get_organization_id()
        process = serializer.validated_data.get('process') or getattr(serializer.instance, 'process', None)
        if process and process.process_map.organization_id != organization_id:
            raise PermissionDenied('No puede mover actividades fuera de la organizacion activa')
        serializer.save()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_process_mapping(request):
    """
    Ejecutar mapeo de procesos con IA
    """
    try:
        logger.info("Iniciando mapeo de procesos...")
        
        # Validar datos de entrada
        serializer = ProcessMapCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ejecutar análisis
        organization_id = _resolve_scoped_org_id(request)
        analyzer = ProcessAnalyzer()
        payload = dict(serializer.validated_data)
        payload['organization_id'] = organization_id
        result = analyzer.process(data=payload)
        
        logger.info(f"Mapeo de procesos completado: {result.get('status')}")
        
        if result.get('status') == 'completed':
            return Response({
                'status': 'success',
                'message': 'Mapeo de procesos completado',
                'process_map_id': result.get('process_map_id'),
                'total_processes': result.get('total_processes'),
                'strategic_count': result.get('strategic_count'),
                'operational_count': result.get('operational_count'),
                'support_count': result.get('support_count'),
                'total_interactions': result.get('total_interactions'),
                'critical_processes_count': result.get('critical_processes_count'),
                'diagram_data': result.get('diagram_data'),
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
        logger.error(f"Error en mapeo de procesos: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_map(request):
    """
    Obtener el último mapa de procesos
    """
    try:
        organization_id = _resolve_scoped_org_id(request)
        latest = ProcessMap.objects.filter(organization_id=organization_id).order_by('-created_at').first()
        
        if not latest:
            return Response({
                'status': 'no_data',
                'message': 'No hay mapas de procesos disponibles'
            })
        
        serializer = ProcessMapSerializer(latest)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
        
    except (ValidationError, PermissionDenied):
        raise
    except Exception as e:
        logger.error(f"Error obteniendo último mapa: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)