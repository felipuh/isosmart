from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
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
        ).order_by('-created_at').first()
        
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
            'timestamp': latest.created_at,
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