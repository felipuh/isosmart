from celery import shared_task
from django.utils import timezone
from .services.context_analyzer import ContextAnalyzer
from .services.external_context_pipeline import ExternalContextPipeline
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def analyze_context_periodic(self):
    """
    Tarea periódica para análisis de contexto
    Se ejecuta diariamente a las 2 AM
    """
    try:
        logger.info("Iniciando análisis periódico de contexto...")
        
        analyzer = ContextAnalyzer()
        result = analyzer.process()
        
        logger.info(f"Análisis de contexto completado: Analysis ID {result.get('analysis_id')}")
        
        return {
            'status': 'success',
            'analysis_id': result.get('analysis_id'),
            'documents_processed': result.get('internal_insights', {}).get('total_documents', 0),
            'risks_identified': len(result.get('internal_insights', {}).get('riesgos_identificados', [])),
            'execution_time': result.get('execution_time')
        }
        
    except Exception as e:
        logger.error(f"Error en análisis periódico de contexto: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300)  # Reintentar en 5 minutos

@shared_task
def analyze_document(document_id: int):
    """Analiza un documento específico"""
    from core.models import Document
    
    try:
        document = Document.objects.get(id=document_id)
        logger.info(f"Analizando documento {document_id}: {document.title}")
        
        analyzer = ContextAnalyzer()
        
        # Procesar solo este documento
        result = analyzer.analyze_internal_context([{
            'id': document.id,
            'content': document.content,
            'source': document.source,
            'date': document.created_at.isoformat(),
            'type': document.document_type
        }])
        
        document.is_processed = True
        document.processed_at = timezone.now()
        document.save()
        
        return {
            'status': 'success',
            'document_id': document_id,
            'insights': result
        }
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return {'status': 'error', 'message': 'Document not found'}
    except Exception as e:
        logger.error(f"Error analyzing document {document_id}: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True, max_retries=2, name='ai_modules.sca.tasks.sync_external_context_signals')
def sync_external_context_signals(self):
    """Sincroniza señales externas por organización y deja trazabilidad auditable."""
    from core.models import Organization

    try:
        total_signals = 0
        organizations = list(Organization.objects.values_list('id', flat=True))
        for organization_id in organizations:
            pipeline = ExternalContextPipeline(organization_id=organization_id)
            signals = pipeline.collect_signals(max_items_per_source=3)
            total_signals += len(signals)

        return {
            'status': 'success',
            'organizations_processed': len(organizations),
            'signals_collected': total_signals,
        }
    except Exception as exc:
        logger.error('Error syncing external context signals: %s', exc, exc_info=True)
        raise self.retry(exc=exc, countdown=600)