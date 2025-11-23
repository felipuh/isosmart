from celery import shared_task
from .services.context_analyzer import ContextAnalyzer
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def analyze_context_periodic(self):
    """
    Tarea periódica para análisis de contexto
    Se ejecuta diariamente a las 2 AM
    """
    try:
        analyzer = ContextAnalyzer()
        
        # Por ahora, datos de prueba
        # TODO: Obtener documentos reales de la base de datos
        test_data = {
            'documents': [
                {
                    'content': 'Logramos mejorar la eficiencia del proceso en un 20%',
                    'source': 'Acta Gerencial Q4',
                    'date': '2025-11-01'
                },
                {
                    'content': 'Identificamos un riesgo en el proceso de compras',
                    'source': 'Reporte de Auditoría',
                    'date': '2025-11-15'
                }
            ],
            'sources': []
        }
        
        result = analyzer.process(test_data)
        
        logger.info(f"Context analysis completed: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in periodic context analysis: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)

@shared_task
def analyze_document(document_id: int):
    """Analiza un documento específico"""
    analyzer = ContextAnalyzer()
    
    # TODO: Obtener documento de la base de datos
    logger.info(f"Analyzing document {document_id}")
    
    return {'status': 'completed', 'document_id': document_id}