"""
Django Service para Stakeholder Intelligence Engine
Integra el motor de IA con los modelos Django
"""

from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from ai_modules.common.base import AIModuleBase
from ai_modules.sie.services.stakeholder_intelligence import StakeholderIntelligenceEngine
from core.models import (
    StakeholderProfile, 
    StakeholderChangeLog, 
    RiskMatrix
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
