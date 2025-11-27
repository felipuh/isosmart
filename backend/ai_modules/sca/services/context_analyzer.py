from ai_modules.common.base import AIModuleBase
from core.models import ContextAnalysis, Document, RiskMatrix
from typing import Dict, Any, List
from datetime import datetime
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ContextAnalyzer(AIModuleBase):
    """Smart Context Analyzer - Análisis de contexto organizacional (ISO 4.1)"""
    
    def __init__(self):
        super().__init__('SCA')
        self.logger.info("Smart Context Analyzer initialized")
    
    def process(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa documentos para análisis de contexto
        
        Args:
            data: Dict opcional con parámetros de procesamiento
        
        Returns:
            Dict con insights de contexto interno y externo
        """
        start_time = datetime.now()
        
        # Crear registro de análisis
        analysis = ContextAnalysis.objects.create(
            status='processing',
            created_by=None
        )
        
        try:
            # Obtener documentos no procesados
            unprocessed_docs = Document.objects.filter(is_processed=False)
            
            if unprocessed_docs.count() == 0:
                # Si no hay documentos nuevos, usar los últimos 10
                documents_qs = Document.objects.all().order_by('-created_at')[:10]
            else:
                documents_qs = unprocessed_docs
            
            # Convertir a lista para evitar problemas con slicing
            documents_list = list(documents_qs)
            
            # Convertir a formato esperado
            docs_data = [
                {
                    'id': doc.id,
                    'content': doc.content,
                    'source': doc.source,
                    'date': doc.created_at.isoformat(),
                    'type': doc.document_type
                }
                for doc in documents_list
            ]
            
            # Análisis de contexto interno
            internal_insights = self.analyze_internal_context(docs_data)
            
            # Análisis de contexto externo
            external_insights = self.analyze_external_context([])
            
            # Guardar resultados
            execution_time = (datetime.now() - start_time).total_seconds()
            
            analysis.status = 'completed'
            analysis.internal_insights = internal_insights
            analysis.external_insights = external_insights
            analysis.total_documents_processed = len(docs_data)
            analysis.execution_time_seconds = execution_time
            analysis.save()
            
            # Marcar documentos como procesados (actualizar uno por uno)
            for doc in documents_list:
                doc.is_processed = True
                doc.processed_at = timezone.now()
                doc.save()
            
            # Alimentar matriz de riesgos automáticamente
            self.feed_risk_matrix(internal_insights, analysis.id)
            
            self.log_execution('context_analysis', 'success', {
                'analysis_id': analysis.id,
                'documents_processed': len(docs_data),
                'execution_time': execution_time
            })
            
            return {
                'analysis_id': analysis.id,
                'status': 'completed',
                'internal_insights': internal_insights,
                'external_insights': external_insights,
                'iso_clause': '4.1',
                'execution_time': execution_time
            }
            
        except Exception as e:
            self.logger.error(f"Error in context analysis: {e}", exc_info=True)
            
            analysis.status = 'error'
            analysis.error_message = str(e)
            analysis.save()
            
            self.log_execution('context_analysis', 'error', {'error': str(e)})
            
            return {'error': str(e), 'analysis_id': analysis.id}
    
    def analyze_internal_context(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analiza documentos internos"""
        insights = {
            'fortalezas': [],
            'debilidades': [],
            'temas_clave': [],
            'riesgos_identificados': [],
            'total_documents': len(documents)
        }
        
        # Palabras clave para análisis (versión simple)
        keywords_fortalezas = ['éxito', 'logro', 'mejora', 'eficiente', 'aumentó', 'incremento', 'positivo', 'excelente']
        keywords_debilidades = ['problema', 'falla', 'error', 'demora', 'disminuyó', 'reducción', 'negativo', 'deficiente']
        keywords_riesgos = ['riesgo', 'amenaza', 'peligro', 'vulnerabilidad', 'preocupación', 'crítico']
        
        for doc in documents:
            content = doc.get('content', '').lower()
            
            # Detectar fortalezas
            fortalezas_found = [word for word in keywords_fortalezas if word in content]
            if fortalezas_found:
                insights['fortalezas'].append({
                    'texto': doc.get('content', '')[:200] + ('...' if len(doc.get('content', '')) > 200 else ''),
                    'fuente': doc.get('source', 'Desconocido'),
                    'confianza': min(len(fortalezas_found) * 0.2, 0.95),
                    'palabras_clave': fortalezas_found
                })
            
            # Detectar debilidades
            debilidades_found = [word for word in keywords_debilidades if word in content]
            if debilidades_found:
                insights['debilidades'].append({
                    'texto': doc.get('content', '')[:200] + ('...' if len(doc.get('content', '')) > 200 else ''),
                    'fuente': doc.get('source', 'Desconocido'),
                    'severidad': 'media'
                })
            
            # Detectar riesgos
            riesgos_found = [word for word in keywords_riesgos if word in content]
            if riesgos_found:
                insights['riesgos_identificados'].append({
                    'texto': doc.get('content', '')[:200] + ('...' if len(doc.get('content', '')) > 200 else ''),
                    'fuente': doc.get('source', 'Desconocido'),
                    'severidad': 'alta' if 'crítico' in content else 'media',
                    'document_id': doc.get('id')
                })
        
        return insights
    
    def analyze_external_context(self, sources: List[Dict]) -> Dict[str, Any]:
        """Analiza fuentes externas"""
        # TODO: Implementar web scraping real
        external_insights = {
            'tendencias_industria': [],
            'cambios_regulatorios': [],
            'riesgos_emergentes': [],
            'oportunidades': []
        }
        
        return external_insights
    
    def feed_risk_matrix(self, insights: Dict, analysis_id: int):
        """Alimenta la matriz de riesgos con los hallazgos"""
        try:
            for riesgo in insights.get('riesgos_identificados', []):
                # Verificar que no exista ya un riesgo similar
                existing = RiskMatrix.objects.filter(
                    risk_description__icontains=riesgo['texto'][:50],
                    source_module='SCA'
                ).first()
                
                if not existing:
                    RiskMatrix.objects.create(
                        source_module='SCA',
                        source_id=analysis_id,
                        risk_description=riesgo['texto'],
                        risk_category='contextual',
                        probability='media',
                        impact='medio',
                        risk_level='medio',
                        mitigation_actions='Análisis detallado requerido',
                        responsible='Gerencia de Calidad',
                        iso_clause='4.1'
                    )
                    
                    self.logger.info(f"Riesgo agregado a matriz desde SCA: {riesgo['texto'][:50]}")
        
        except Exception as e:
            self.logger.error(f"Error feeding risk matrix: {e}", exc_info=True)