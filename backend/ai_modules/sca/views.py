from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage
from ai_modules.sca.services.context_analyzer import ContextAnalyzer
from core.models import ContextAnalysis
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def trigger_analysis(request):
    """
    Endpoint para ejecutar análisis de contexto manualmente
    """
    try:
        logger.info("Iniciando análisis de contexto manual...")
        
        # Crear instancia del analizador
        analyzer = ContextAnalyzer()
        
        # Ejecutar análisis
        result = analyzer.process()
        
        logger.info(f"Análisis completado: {result.get('status')}")
        
        # Si el análisis fue exitoso, devolver el resultado
        if result.get('status') == 'completed':
            return Response({
                'status': 'success',
                'message': 'Análisis completado exitosamente',
                'total_documents': result.get('total_documents', 0),
                'internal_insights': result.get('internal_insights', {}),
                'external_insights': result.get('external_insights', {}),
                'analysis_id': result.get('analysis_id')
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': result.get('error', 'Error desconocido en el análisis')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error en trigger_analysis: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_latest_analysis(request):
    """
    Obtener el último análisis de contexto
    """
    try:
        latest = ContextAnalysis.objects.filter(
            status='completed'
        ).order_by('-timestamp').first()
        
        if not latest:
            return Response({
                'status': 'no_data',
                'message': 'No hay análisis disponibles',
                'total_documents_processed': 0,
                'internal_insights': {
                    'fortalezas': [],
                    'debilidades': [],
                    'riesgos_identificados': []
                },
                'external_insights': {
                    'oportunidades': [],
                    'amenazas': [],
                    'factores_externos': []
                }
            })
        
        return Response({
            'status': 'success',
            'analysis_id': latest.id,
            'timestamp': latest.timestamp,
            'total_documents_processed': latest.total_documents_processed,
            'internal_insights': latest.internal_insights,
            'external_insights': latest.external_insights
        })
        
    except Exception as e:
        logger.error(f"Error en get_latest_analysis: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_analysis_history(request):
    """
    Obtener historial de análisis de contexto (paginado)
    """
    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        queryset = ContextAnalysis.objects.order_by('-timestamp')
        paginator = Paginator(queryset, page_size)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            return Response({
                'count': paginator.count,
                'next': None,
                'previous': None,
                'results': []
            })

        results = []
        for item in page_obj.object_list:
            results.append({
                'id': item.id,
                'timestamp': item.timestamp,
                'status': item.status,
                'total_documents_processed': item.total_documents_processed,
                'execution_time_seconds': item.execution_time_seconds
            })

        return Response({
            'count': paginator.count,
            'next': page + 1 if page_obj.has_next() else None,
            'previous': page - 1 if page_obj.has_previous() else None,
            'results': results
        })

    except Exception as e:
        logger.error(f"Error en get_analysis_history: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)