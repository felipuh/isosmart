# ai_modules/sca/tasks.py
from celery import shared_task
from .services.context_analyzer import ContextAnalyzer
from backend.models import ContextAnalysis, RiskMatrix

@shared_task(bind=True, max_retries=3)
def analyze_context_periodic(self):
    """Ejecuta análisis de contexto cada 24 horas"""
    analyzer = ContextAnalyzer()
    
    # Obtener documentos recientes
    from backend.models import Document
    recent_docs = Document.objects.filter(
        created_at__gte=datetime.now() - timedelta(days=7)
    ).values('id', 'content', 'source', 'created_at')
    
    # Análisis interno
    internal = analyzer.analyze_internal_context(list(recent_docs))
    
    # Análisis externo
    external_sources = [
        {'url': 'https://www.iso.org/news'},
        {'url': 'https://www.bccr.fi.cr/'},  # Banco Central Costa Rica
    ]
    external = analyzer.analyze_external_context(external_sources)
    
    # Guardar resultados
    analysis = ContextAnalysis.objects.create(
        internal_insights=internal,
        external_insights=external,
        status='completed'
    )
    
    # Alimentar matriz de riesgos automáticamente
    for riesgo in internal['riesgos_identificados']:
        RiskMatrix.objects.create(
            source_module='SCA',
            risk_description=riesgo['texto'],
            probability='media',  # Calcular con modelo predictivo
            impact='alto',
            mitigation_actions='Generado automáticamente',
            iso_clause='4.1'
        )
    
    return analysis.id