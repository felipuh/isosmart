from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Count, Q

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


class ProcessMapViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de mapas de procesos
    """
    queryset = ProcessMap.objects.all().order_by('-created_at')
    serializer_class = ProcessMapSerializer
    
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
            ProcessMap.objects.filter(status='active').update(status='approved')
            
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
            process_map = ProcessMap.objects.filter(status='active').first()
            
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
            total = ProcessMap.objects.count()
            by_status = ProcessMap.objects.values('status').annotate(
                count=Count('id')
            )
            
            active_map = ProcessMap.objects.filter(status='active').first()
            
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


class ProcessViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de procesos individuales
    """
    queryset = Process.objects.all().select_related('process_map')
    serializer_class = ProcessSerializer
    
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


class ProcessInteractionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de interacciones entre procesos
    """
    queryset = ProcessInteraction.objects.all().select_related(
        'source_process', 
        'target_process'
    )
    serializer_class = ProcessInteractionSerializer
    
    def get_queryset(self):
        """Filtrar por mapa si se especifica"""
        queryset = super().get_queryset()
        
        map_id = self.request.query_params.get('map_id', None)
        if map_id:
            queryset = queryset.filter(process_map_id=map_id)
        
        return queryset


class ProcessActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de actividades de procesos
    """
    queryset = ProcessActivity.objects.all().select_related('process')
    serializer_class = ProcessActivitySerializer
    
    def get_queryset(self):
        """Filtrar por proceso si se especifica"""
        queryset = super().get_queryset()
        
        process_id = self.request.query_params.get('process_id', None)
        if process_id:
            queryset = queryset.filter(process_id=process_id)
        
        return queryset


@api_view(['POST'])
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
        analyzer = ProcessAnalyzer()
        result = analyzer.process(data=serializer.validated_data)
        
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
            
    except Exception as e:
        logger.error(f"Error en mapeo de procesos: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_latest_map(request):
    """
    Obtener el último mapa de procesos
    """
    try:
        latest = ProcessMap.objects.order_by('-created_at').first()
        
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
        
    except Exception as e:
        logger.error(f"Error obteniendo último mapa: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)