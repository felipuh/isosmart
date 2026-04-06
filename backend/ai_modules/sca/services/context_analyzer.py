"""
Django Service para Stakeholder Intelligence Engine
Integra el motor de IA con los modelos Django
"""

from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from ai_modules.common.base import AIModuleBase
from ai_modules.sie.services.stakeholder_intelligence import StakeholderIntelligenceEngine
from ai_modules.sca.services.external_context_pipeline import ExternalContextPipeline
from core.models import (
    StakeholderProfile, 
    StakeholderChangeLog, 
    RiskMatrix,
    Document, 
    ContextAnalysis,
    EnvironmentalRiskAlert,
    ExternalContextSignal,
)

logger = logging.getLogger(__name__)

class StakeholderAnalyzer(AIModuleBase):
    """
    Analizador de Stakeholders con IA
    Implementa ISO 4.2
    """
    
    def __init__(self):
        super().__init__('SIE')
        self.engine = StakeholderIntelligenceEngine()
        self.organization_id = None
    
    def process(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Proceso principal de análisis de stakeholders
        
        Returns:
            Dict con resultados del análisis completo
        """
        start_time = datetime.now()
        payload = data or {}
        self.organization_id = payload.get('organization_id') or payload.get('organization')
        
        try:
            # 1. Obtener stakeholders de la BD
            stakeholders = self._load_stakeholders()
            
            if len(stakeholders) == 0:
                return {
                    'status': 'warning',
                    'message': 'No hay stakeholders para analizar',
                    'stakeholders_count': 0
                }
            
            # 2. Construir red de relaciones
            self.logger.info(f"Construyendo red con {len(stakeholders)} stakeholders...")
            network = self.engine.build_stakeholder_network(stakeholders)
            
            # 3. Calcular métricas de influencia
            self.logger.info("Calculando métricas de influencia...")
            influence_metrics = self.engine.calculate_influence_metrics()
            
            # 4. Actualizar scores en la BD
            self._update_influence_scores(influence_metrics)
            
            # 5. Identificar stakeholders críticos
            critical_stakeholders = self.engine.identify_critical_stakeholders(threshold=0.6)
            
            # 6. Detectar cambios en expectativas
            historical_data = self._load_historical_data()
            changes = self.engine.detect_expectation_changes(historical_data)
            
            # 7. Registrar cambios detectados
            self._log_changes(changes)
            
            # 8. Crear riesgos para stakeholders críticos insatisfechos
            self._create_stakeholder_risks(critical_stakeholders)
            
            # 9. Estadísticas de la red
            network_stats = self.engine.get_network_statistics()
            
            # 10. Exportar para visualización
            network_viz = self.engine.export_network_for_visualization()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'status': 'completed',
                'module': 'SIE',
                'iso_clause': '4.2',
                'execution_time': execution_time,
                'stakeholders_analyzed': len(stakeholders),
                'critical_stakeholders': critical_stakeholders,
                'changes_detected': changes,
                'network_statistics': network_stats,
                'influence_metrics': influence_metrics,
                'network_visualization': network_viz,
                'recommendations': self._generate_recommendations(
                    critical_stakeholders, 
                    changes,
                    network_stats
                )
            }
            
            self.log_execution('stakeholder_analysis', 'success', {
                'stakeholders': len(stakeholders),
                'critical': len(critical_stakeholders),
                'changes': len(changes)
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en análisis de stakeholders: {e}", exc_info=True)
            
            self.log_execution('stakeholder_analysis', 'error', {'error': str(e)})
            
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _load_stakeholders(self) -> List[Dict]:
        """Carga stakeholders activos desde la BD"""
        stakeholders_qs = StakeholderProfile.objects.filter(is_active=True)
        if self.organization_id:
            stakeholders_qs = stakeholders_qs.filter(organization_id=self.organization_id)
        
        stakeholders = []
        for sh in stakeholders_qs:
            stakeholders.append({
                'id': sh.id,
                'organization_id': sh.organization_id,
                'name': sh.name,
                'stakeholder_type': sh.stakeholder_type,
                'influence_score': sh.influence_score,
                'power': sh.power,
                'interest': sh.interest,
                'satisfaction_score': sh.satisfaction_score or 0.0,
                'expectations': sh.expectations or [],
                'communication_frequency': sh.communication_frequency,
            })
        
        return stakeholders
    
    def _update_influence_scores(self, metrics: Dict[int, Dict]):
        """Actualiza los scores de influencia en la BD"""
        for stakeholder_id, metric_data in metrics.items():
            try:
                queryset = StakeholderProfile.objects
                if self.organization_id:
                    queryset = queryset.filter(organization_id=self.organization_id)
                sh = queryset.get(id=stakeholder_id)
                
                # Actualizar score compuesto
                sh.influence_score = metric_data['composite_influence_score']
                sh.save()
                
                self.logger.debug(
                    f"Score actualizado para {sh.name}: "
                    f"{metric_data['composite_influence_score']:.3f}"
                )
            except StakeholderProfile.DoesNotExist:
                self.logger.warning(f"Stakeholder {stakeholder_id} no encontrado")
    
    def _load_historical_data(self) -> Dict[int, List[Dict]]:
        """
        Carga datos históricos de stakeholders para detectar cambios
        """
        historical = {}
        
        # Obtener registros de los últimos 6 meses
        six_months_ago = timezone.now() - timedelta(days=180)

        stakeholders_qs = StakeholderProfile.objects.filter(is_active=True)
        if self.organization_id:
            stakeholders_qs = stakeholders_qs.filter(organization_id=self.organization_id)

        for sh in stakeholders_qs:
            # Historial simple: registro actual + cambios registrados
            history = [{
                'name': sh.name,
                'stakeholder_type': sh.stakeholder_type,
                'expectations': sh.expectations or [],
                'date': sh.last_updated
            }]
            
            # Agregar logs de cambios anteriores
            changes = StakeholderChangeLog.objects.filter(
                stakeholder=sh,
                detected_at__gte=six_months_ago
            ).order_by('detected_at')
            
            for change in changes:
                history.append({
                    'name': sh.name,
                    'stakeholder_type': sh.stakeholder_type,
                    'expectations': change.new_state.get('expectations', []),
                    'date': change.detected_at
                })
            
            historical[sh.id] = history
        
        return historical
    
    def _log_changes(self, changes: List[Dict]):
        """Registra cambios detectados en la BD"""
        for change in changes:
            try:
                queryset = StakeholderProfile.objects
                if self.organization_id:
                    queryset = queryset.filter(organization_id=self.organization_id)
                sh = queryset.get(id=change['stakeholder_id'])
                
                # Crear registro de cambio
                StakeholderChangeLog.objects.create(
                    stakeholder=sh,
                    change_type=f"expectation_change_{change['severity']}",
                    previous_state={
                        'expectations': change.get('removed_expectations', [])
                    },
                    new_state={
                        'expectations': change.get('new_expectations', [])
                    },
                    similarity_score=1.0 - (change['change_magnitude'] * 0.1),
                    detected_at=timezone.now(),
                    alert_sent=change['severity'] in ['alto', 'medio']
                )
                
                self.logger.info(
                    f"Cambio registrado: {sh.name} - "
                    f"Severidad: {change['severity']}"
                )
                
            except StakeholderProfile.DoesNotExist:
                self.logger.warning(
                    f"No se pudo registrar cambio para stakeholder {change['stakeholder_id']}"
                )
    
    def _create_stakeholder_risks(self, critical_stakeholders: List[Dict]):
        """Crea riesgos automáticos para stakeholders críticos con problemas"""
        for sh_data in critical_stakeholders:
            organization_id = sh_data.get('organization_id') or self.organization_id
            # Solo crear riesgo si hay problemas
            if sh_data['risk_level'] in ['CRÍTICO', 'ALTO']:
                
                # Verificar que no exista ya un riesgo similar
                existing = RiskMatrix.objects.filter(
                    organization_id=organization_id,
                    source_module='SIE',
                    source_id=sh_data['stakeholder_id'],
                    status__in=['identified', 'under_analysis']
                ).first()
                
                if not existing:
                    risk_level_map = {
                        'CRÍTICO': 'critico',
                        'ALTO': 'alto',
                        'MEDIO': 'medio',
                        'BAJO': 'bajo'
                    }
                    
                    RiskMatrix.objects.create(
                        organization_id=organization_id,
                        source_module='SIE',
                        source_id=sh_data['stakeholder_id'],
                        risk_description=(
                            f"Stakeholder crítico '{sh_data['name']}' ({sh_data['type']}) "
                            f"presenta riesgo {sh_data['risk_level']}. "
                            f"Score de influencia: {sh_data['composite_score']:.2f}. "
                            f"Satisfacción: {sh_data['satisfaction']:.1f}/5.0"
                        ),
                        risk_category='stakeholder',
                        probability='alta' if sh_data['risk_level'] == 'CRÍTICO' else 'media',
                        impact='alto',
                        risk_level=risk_level_map.get(sh_data['risk_level'], 'medio'),
                        mitigation_actions=sh_data['engagement_strategy'],
                        responsible='Gerente de Relaciones con Stakeholders',
                        iso_clause='4.2',
                        status='identified'
                    )
                    
                    self.logger.info(
                        f"Riesgo creado para stakeholder crítico: {sh_data['name']}"
                    )
    
    def _generate_recommendations(self, critical_sh: List, changes: List, 
                                  stats: Dict) -> List[str]:
        """Genera recomendaciones ejecutivas"""
        recommendations = []
        
        # Recomendación sobre stakeholders críticos
        if len(critical_sh) > 0:
            critical_names = [sh['name'] for sh in critical_sh[:3]]
            recommendations.append(
                f"🎯 Priorizar atención en {len(critical_sh)} stakeholders críticos: "
                f"{', '.join(critical_names)}{'...' if len(critical_sh) > 3 else ''}"
            )
        
        # Recomendación sobre cambios detectados
        high_severity_changes = [c for c in changes if c['severity'] == 'alto']
        if len(high_severity_changes) > 0:
            recommendations.append(
                f"⚠️ URGENTE: {len(high_severity_changes)} stakeholder(s) con cambios "
                f"críticos en expectativas. Requiere acción inmediata."
            )
        
        # Recomendación sobre densidad de red
        density = stats.get('network_density', 0)
        if density < 0.3:
            recommendations.append(
                "🔗 Red poco conectada. Considerar crear más canales de comunicación "
                "entre stakeholders para mejorar alineación."
            )
        
        # Recomendación sobre distribución
        types = stats.get('stakeholder_types', {})
        if len(types) < 3:
            recommendations.append(
                "👥 Diversidad de stakeholders limitada. Revisar si se han identificado "
                "todas las partes interesadas relevantes (ISO 4.2)."
            )
        
        if len(recommendations) == 0:
            recommendations.append(
                "✅ Red de stakeholders saludable. Mantener estrategia de engagement actual."
            )
        
        return recommendations

class ContextAnalyzer(AIModuleBase):
    """
    Analizador de Contexto Organizacional con IA
    Implementa ISO 4.1
    """
    
    def __init__(self):
        super().__init__('SCA')
    
    def process(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Proceso principal de análisis de contexto
        
        Returns:
            Dict con resultados del análisis completo
        """
        start_time = datetime.now()
        payload = data or {}
        organization_id = payload.get('organization_id') or payload.get('organization')
        
        try:
            # 1. Obtener documentos
            documents = Document.objects.all()
            if organization_id:
                documents = documents.filter(organization_id=organization_id)
            
            if documents.count() == 0:
                logger.warning("No hay documentos para analizar")
                return {
                    'status': 'error',
                    'error': 'No hay documentos disponibles para analizar. Por favor, sube documentos primero.',
                    'organization_id': organization_id,
                    'total_documents': 0
                }
            
            # 2. Analizar documentos (simplificado por ahora)
            internal_insights = self._analyze_internal_factors(documents)
            external_insights = self._analyze_external_factors(documents)
            external_signals = self._collect_external_signals(organization_id)
            climate_context = self._build_climate_context(documents)
            environmental_scope = self._build_environmental_scope(documents)
            climate_context['external_signals_count'] = len(external_signals)
            climate_context['external_signal_titles'] = [s.get('title', '') for s in external_signals[:5]]
            
            # 3. Crear o actualizar registro de análisis
            existing_analysis_qs = ContextAnalysis.objects.filter(status='completed')
            if organization_id:
                existing_analysis_qs = existing_analysis_qs.filter(organization_id=organization_id)
            existing_analysis = existing_analysis_qs.order_by('-timestamp').first()
            
            if existing_analysis:
                # Actualizar análisis existente
                existing_analysis.total_documents_processed = documents.count()
                existing_analysis.internal_insights = internal_insights
                existing_analysis.external_insights = external_insights
                existing_analysis.climate_context = climate_context
                existing_analysis.environmental_scope = environmental_scope
                existing_analysis.execution_time_seconds = (datetime.now() - start_time).total_seconds()
                existing_analysis.save()
                analysis = existing_analysis
                logger.info(f"Análisis de contexto actualizado: ID {analysis.id}")
            else:
                # Crear nuevo análisis
                analysis = ContextAnalysis.objects.create(
                    organization_id=organization_id,
                    status='completed',
                    total_documents_processed=documents.count(),
                    internal_insights=internal_insights,
                    external_insights=external_insights,
                    climate_context=climate_context,
                    environmental_scope=environmental_scope,
                    execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                )
                logger.info(f"Nuevo análisis de contexto creado: ID {analysis.id}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'status': 'completed',
                'module': 'SCA',
                'iso_clause': '4.1',
                'organization_id': organization_id,
                'execution_time': execution_time,
                'total_documents': documents.count(),
                'analysis_id': analysis.id,
                'internal_insights': internal_insights,
                'external_insights': external_insights,
                'climate_context': climate_context,
                'environmental_scope': environmental_scope,
            }

            # 4. Integrar señales externas a riesgos/alertas trazables (ISO 6.1 + 42001)
            if organization_id and external_signals:
                integration_stats = self._create_external_risks_and_alerts(organization_id, external_signals)
                result['external_integration'] = integration_stats
            
            self.log_execution('context_analysis', 'success', {
                'documents': documents.count(),
                'analysis_id': analysis.id
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de contexto: {e}", exc_info=True)
            
            self.log_execution('context_analysis', 'error', {'error': str(e)})
            
            return {
                'status': 'error',
                'error': str(e),
                'organization_id': organization_id,
                'total_documents': 0
            }

    def _collect_external_signals(self, organization_id: Optional[int]) -> List[Dict[str, Any]]:
        if not organization_id:
            return []
        pipeline = ExternalContextPipeline(organization_id=organization_id)
        return pipeline.collect_signals(max_items_per_source=3)

    def _create_external_risks_and_alerts(self, organization_id: int, signals: List[Dict[str, Any]]) -> Dict[str, int]:
        """Crea riesgos y alertas trazables a partir de señales externas de alto impacto."""
        created_risks = 0
        created_alerts = 0

        for signal in signals:
            if signal.get('impact_level') not in {'high', 'critical'}:
                continue

            db_signal = ExternalContextSignal.objects.filter(
                organization_id=organization_id,
                source_name=signal.get('source_name'),
                signal_hash=signal.get('signal_hash'),
            ).first()

            risk, risk_created = RiskMatrix.objects.get_or_create(
                organization_id=organization_id,
                source_module='SCA',
                source_id=db_signal.id if db_signal else None,
                risk_description=f"Señal externa: {signal.get('title', '')[:180]}",
                defaults={
                    'risk_category': 'climatico_esg',
                    'probability': 'alta' if signal.get('impact_level') == 'critical' else 'media',
                    'impact': 'muy_alto' if signal.get('impact_level') == 'critical' else 'alto',
                    'risk_level': 'critico' if signal.get('impact_level') == 'critical' else 'alto',
                    'mitigation_actions': (
                        'Evaluar impacto regulatorio y de continuidad; ajustar objetivos, alcance y controles.'
                    ),
                    'responsible': 'Responsable SGC',
                    'iso_clause': '6.1',
                    'status': 'identified',
                }
            )
            if risk_created:
                created_risks += 1

            _, alert_created = EnvironmentalRiskAlert.objects.get_or_create(
                organization_id=organization_id,
                source_module='SCA',
                source_id=db_signal.id if db_signal else None,
                title=f"Alerta externa: {signal.get('source_name', 'fuente')}",
                defaults={
                    'alert_type': 'regulatory_change',
                    'severity': signal.get('impact_level', 'medium'),
                    'description': signal.get('summary', '')[:2000],
                    'recommendation': 'Revisar impacto en procesos críticos y actualizar matriz 6.1.',
                    'ai_audit_score': 0.8,
                    'external_signal': db_signal,
                    'linked_risk': risk,
                }
            )
            if alert_created:
                created_alerts += 1

        return {
            'signals_processed': len(signals),
            'risks_created': created_risks,
            'alerts_created': created_alerts,
        }

    def analyze_internal_context(self, documents_payload: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Interfaz de compatibilidad para análisis de un subconjunto de documentos."""
        return self._analyze_internal_factors(documents_payload)

    def _extract_keywords(self, text: str, keywords: List[str]) -> List[str]:
        text_lower = (text or '').lower()
        return [keyword for keyword in keywords if keyword in text_lower]

    def _iter_document_blobs(self, documents) -> List[str]:
        blobs = []
        for doc in documents:
            if isinstance(doc, dict):
                pieces = [
                    str(doc.get('title', '')),
                    str(doc.get('source', '')),
                    str(doc.get('type', '')),
                    str(doc.get('content', '')),
                ]
            else:
                pieces = [
                    str(getattr(doc, 'title', '')),
                    str(getattr(doc, 'source', '')),
                    str(getattr(doc, 'document_type', '')),
                    str(getattr(doc, 'content', '')),
                ]
            blobs.append(' '.join(pieces).lower())
        return blobs
    
    def _analyze_internal_factors(self, documents) -> Dict:
        """Análisis de factores internos incluyendo señales ESG/digitales."""
        blobs = self._iter_document_blobs(documents)
        joined = ' '.join(blobs)
        digital_keywords = [
            'transformacion digital', 'cloud', 'iot', 'industria 4.0', 'inteligencia artificial',
            'ciberseguridad', 'blockchain', 'telemetria', 'trabajo remoto', 'hibrido'
        ]
        esg_keywords = [
            'emisiones', 'co2', 'energia', 'residuos', 'diversidad', 'inclusion',
            'etica', 'transparencia', 'anticorrupcion', 'derechos humanos'
        ]

        return {
            'fortalezas': [
                'Procesos documentados según ISO 9001',
                'Equipo capacitado en gestión de calidad',
                'Infraestructura tecnológica moderna',
            ],
            'debilidades': [
                'Necesidad de mayor integración entre áreas',
                'Procesos de comunicación por mejorar',
            ],
            'riesgos_identificados': [
                {
                    'texto': 'Dependencia de sistemas heredados',
                    'severidad': 'medio',
                    'categoria': 'Tecnología',
                    'mitigacion': 'Plan de modernización gradual'
                },
                {
                    'texto': 'Cambio climático puede alterar continuidad operativa y cadena de suministro',
                    'severidad': 'alto',
                    'categoria': 'Climático',
                    'mitigacion': 'Definir escenarios y planes de contingencia por criticidad'
                }
            ],
            'tendencias_digitales': self._extract_keywords(joined, digital_keywords),
            'factores_esg_detectados': self._extract_keywords(joined, esg_keywords),
            'recomendaciones': [
                {
                    'texto': 'Implementar sistema de gestión documental integrado',
                    'prioridad': 'alta',
                    'acciones': [
                        'Evaluar plataformas disponibles',
                        'Definir requisitos específicos',
                        'Piloto en área seleccionada'
                    ]
                }
            ]
        }
    
    def _analyze_external_factors(self, documents) -> Dict:
        """Análisis de factores externos con foco 2026 (clima, ESG y digital)."""
        blobs = self._iter_document_blobs(documents)
        joined = ' '.join(blobs)

        climate_keywords = [
            'cambio climatico', 'ipcc', 'nasa', 'desastres naturales', 'huella de carbono',
            'descarbonizacion', 'net zero', 'adaptacion climatica'
        ]
        regulatory_keywords = [
            'regulatorio', 'ley', 'norma', 'cumplimiento', 'iso 42001', 'esg', 'sostenibilidad'
        ]

        return {
            'oportunidades': [
                'Crecimiento del mercado de servicios de calidad',
                'Nuevas tecnologías de automatización disponibles',
            ],
            'amenazas': [
                'Cambios regulatorios frecuentes',
                'Competencia internacional',
                'Eventos climáticos extremos con impacto en continuidad del negocio',
            ],
            'factores_externos': [
                {
                    'tipo': 'tecnológico',
                    'descripcion': 'Adopción acelerada de IA en gestión de calidad',
                    'impacto': 'alto',
                    'tendencia': 'Crecimiento continuo'
                },
                {
                    'tipo': 'económico',
                    'descripcion': 'Volatilidad en costos operativos',
                    'impacto': 'medio',
                    'tendencia': 'Inestable'
                },
                {
                    'tipo': 'climático',
                    'descripcion': 'Mayor presión regulatoria y de mercado para descarbonización',
                    'impacto': 'alto',
                    'tendencia': 'Crecimiento continuo'
                }
            ],
            'temas_climaticos_detectados': self._extract_keywords(joined, climate_keywords),
            'temas_regulatorios_detectados': self._extract_keywords(joined, regulatory_keywords),
        }

    def _build_climate_context(self, documents) -> Dict[str, Any]:
        """Construye contexto climático y ESG trazable para ISO 9001:2026."""
        blobs = self._iter_document_blobs(documents)
        joined = ' '.join(blobs)

        trend_keywords = ['ipcc', 'nasa', 'onu', 'emisiones', 'co2', 'descarbonizacion', 'esg']
        supply_keywords = ['proveedor', 'cadena de suministro', 'third party', 'outsourcing', 'logistica']
        digital_keywords = ['ia', 'iot', 'blockchain', 'cloud', 'ciberseguridad', 'industria 4.0']

        return {
            'regulatory_trends': self._extract_keywords(joined, trend_keywords),
            'supply_chain_signals': self._extract_keywords(joined, supply_keywords),
            'digital_transformation_signals': self._extract_keywords(joined, digital_keywords),
            'emerging_risks': [
                'Interrupciones por eventos climáticos extremos',
                'Aumento de exigencias ESG de clientes y reguladores',
                'Riesgos de ciberseguridad por digitalización acelerada',
            ],
        }

    def _build_environmental_scope(self, documents) -> List[Dict[str, Any]]:
        """Identifica elementos del alcance con potencial impacto ambiental."""
        blobs = self._iter_document_blobs(documents)
        joined = ' '.join(blobs)

        criteria = {
            'energia': ['energia', 'consumo energetico', 'eficiencia energetica'],
            'residuos': ['residuos', 'reciclaje', 'desechos'],
            'emisiones': ['emisiones', 'co2', 'huella de carbono'],
            'cadena_suministro': ['proveedor', 'cadena de suministro', 'logistica'],
        }

        scope = []
        for area, keywords in criteria.items():
            matched = self._extract_keywords(joined, keywords)
            if matched:
                scope.append({
                    'area': area,
                    'signals': matched,
                    'impact_level': 'alto' if area in {'emisiones', 'cadena_suministro'} else 'medio',
                })

        return scope
