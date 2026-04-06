"""
Django Service para AI Scope Builder
Integra el motor de IA con los modelos Django
"""

from django.utils import timezone
from datetime import datetime
from typing import Dict, List, Any
import logging

from ai_modules.common.base import AIModuleBase
from ai_modules.asb.services.scope_builder import ScopeBuilderEngine
from ai_modules.asb.models import ScopeDefinition, ProcessScope, LocationScope
from core.models import ContextAnalysis

logger = logging.getLogger(__name__)


class ScopeAnalyzer(AIModuleBase):
    """
    Analizador de Alcance con IA
    Implementa ISO 4.3
    """
    
    def __init__(self):
        super().__init__('ASB')
        self.engine = ScopeBuilderEngine()
        self.organization_id = None
    
    def process(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Proceso principal de definición de alcance
        
        Returns:
            Dict con resultados del análisis completo
        """
        start_time = datetime.now()
        payload = data or {}
        self.organization_id = payload.get('organization_id') or payload.get('organization')
        
        try:
            # 1. Obtener último análisis de contexto
            context_qs = ContextAnalysis.objects.filter(status='completed')
            if self.organization_id:
                context_qs = context_qs.filter(organization_id=self.organization_id)
            context_analysis = context_qs.order_by('-timestamp').first()
            
            if not context_analysis:
                return {
                    'status': 'warning',
                    'message': 'Se requiere un análisis de contexto previo (Módulo SCA)',
                    'recommendation': 'Ejecutar análisis de contexto antes de definir alcance'
                }
            
            context_data = {
                'internal': context_analysis.internal_insights,
                'external': context_analysis.external_insights,
                'climate': context_analysis.climate_context,
                'environmental_scope': context_analysis.environmental_scope,
            }
            
            # 2. Analizar límites organizacionales
            self.logger.info("Analizando límites organizacionales...")
            boundaries = self.engine.analyze_organizational_boundaries(context_data)
            
            # 3. Definir productos y servicios (puede venir de data o ser automático)
            products_services = payload.get('products_services', [
                'Servicios de consultoría en gestión de calidad',
                'Auditorías internas y externas ISO 9001',
                'Capacitación en sistemas de gestión'
            ]) if payload else [
                'Servicios de consultoría en gestión de calidad',
                'Auditorías internas y externas ISO 9001',
                'Capacitación en sistemas de gestión'
            ]
            
            # 4. Evaluar requisitos ISO
            scope_data = {
                'products_services': products_services,
                'boundaries': boundaries,
                'has_design_activities': payload.get('has_design', False) if payload else False
            }
            
            self.logger.info("Evaluando requisitos ISO 9001:2015...")
            requirements_eval = self.engine.evaluate_iso_requirements(scope_data)
            
            # 5. Analizar cobertura
            coverage = self.engine.analyze_coverage(
                scope_data,
                context_data,
                {}  # Stakeholder data (integrar con SIE después)
            )

            environmental_criteria = self._build_environmental_criteria(context_analysis)
            climate_readiness = self._calculate_climate_readiness(coverage, context_analysis)
            digital_readiness = self._calculate_digital_readiness(context_analysis)
            
            # 6. Generar declaración de alcance
            full_scope_data = {
                **scope_data,
                'exclusions': requirements_eval['exclusions'],
                'processes': []  # Se agregará en integración con SPM
            }
            
            scope_statement = self.engine.generate_scope_statement(full_scope_data)
            
            # 7. Crear o actualizar definición de alcance en BD
            existing_scope_qs = ScopeDefinition.objects.filter(status__in=['draft', 'active'])
            if self.organization_id:
                existing_scope_qs = existing_scope_qs.filter(organization_id=self.organization_id)
            existing_scope = existing_scope_qs.order_by('-created_at').first()
            
            if existing_scope:
                # Actualizar alcance existente
                existing_scope.title = f"Alcance SGC - {datetime.now().strftime('%Y-%m')}"
                existing_scope.organizational_boundaries = boundaries
                existing_scope.products_services = products_services
                existing_scope.applicable_requirements = {
                    'requirements': requirements_eval['applicable_requirements'],
                    'coverage': requirements_eval['coverage_percentage']
                }
                existing_scope.exclusions = requirements_eval['exclusions']
                existing_scope.scope_statement = scope_statement
                existing_scope.coverage_analysis = coverage
                existing_scope.environmental_criteria = environmental_criteria
                existing_scope.climate_readiness_score = climate_readiness
                existing_scope.digital_readiness_score = digital_readiness
                existing_scope.context_analysis = context_analysis
                if self.organization_id:
                    existing_scope.organization_id = self.organization_id
                existing_scope.save()
                
                # Eliminar ubicaciones anteriores y recrear
                LocationScope.objects.filter(scope_definition=existing_scope).delete()
                
                scope_definition = existing_scope
                self.logger.info(f"Alcance actualizado: ID {scope_definition.id}")
            else:
                # Crear nuevo alcance
                scope_definition = ScopeDefinition.objects.create(
                    title=f"Alcance SGC - {datetime.now().strftime('%Y-%m')}",
                    version="1.0",
                    organizational_boundaries=boundaries,
                    products_services=products_services,
                    applicable_requirements={
                        'requirements': requirements_eval['applicable_requirements'],
                        'coverage': requirements_eval['coverage_percentage']
                    },
                    exclusions=requirements_eval['exclusions'],
                    scope_statement=scope_statement,
                    coverage_analysis=coverage,
                    environmental_criteria=environmental_criteria,
                    climate_readiness_score=climate_readiness,
                    digital_readiness_score=digital_readiness,
                    status='draft',
                    context_analysis=context_analysis,
                    organization_id=self.organization_id
                )
                self.logger.info(f"Nuevo alcance creado: ID {scope_definition.id}")
            
            # 8. Crear ubicaciones
            self._create_locations(scope_definition, boundaries)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'status': 'completed',
                'module': 'ASB',
                'iso_clause': '4.3',
                'execution_time': execution_time,
                'scope_id': scope_definition.id,
                'scope_statement': scope_statement,
                'products_count': len(products_services),
                'exclusions_count': len(requirements_eval['exclusions']),
                'coverage_score': coverage['overall_score'],
                'climate_readiness_score': climate_readiness,
                'digital_readiness_score': digital_readiness,
                'environmental_criteria': environmental_criteria,
                'boundaries': boundaries,
                'requirements': requirements_eval,
                'recommendations': self._generate_recommendations(
                    scope_definition,
                    coverage
                )
            }
            
            self.log_execution('scope_definition', 'success', {
                'scope_id': scope_definition.id,
                'coverage': coverage['overall_score']
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en definición de alcance: {e}", exc_info=True)
            
            self.log_execution('scope_definition', 'error', {'error': str(e)})
            
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _create_locations(self, scope_definition: ScopeDefinition, 
                         boundaries: Dict):
        """Crea registros de ubicaciones"""
        geographic = boundaries.get('geographic', [])
        
        for location_name in geographic:
            LocationScope.objects.create(
                scope_definition=scope_definition,
                location_name=location_name,
                location_type='office',
                country='Costa Rica',
                city='San José',
                activities=['Operaciones generales'],
                employee_count=10,
                is_included=True
            )
    
    def _generate_recommendations(self, scope_def: ScopeDefinition, 
                                 coverage: Dict) -> List[str]:
        """Genera recomendaciones sobre el alcance"""
        recommendations = []
        
        # Recomendación sobre cobertura
        if coverage['overall_score'] < 70:
            recommendations.append(
                f"⚠️ Cobertura del alcance es {coverage['overall_score']:.1f}%. "
                "Se recomienda revisar y ampliar el alcance."
            )
        elif coverage['overall_score'] >= 90:
            recommendations.append(
                f"✅ Excelente cobertura del alcance ({coverage['overall_score']:.1f}%)."
            )
        
        # Recomendación sobre exclusiones
        if len(scope_def.exclusions) > 0:
            recommendations.append(
                f"📋 Se identificaron {len(scope_def.exclusions)} exclusión(es). "
                "Verificar justificación y documentar adecuadamente."
            )
        
        # Recomendación sobre integración
        recommendations.append(
            "🔗 Integrar con módulo SPM para mapeo detallado de procesos dentro del alcance."
        )
        
        if len(recommendations) == 0:
            recommendations.append(
                "✅ Alcance bien definido. Proceder con implementación del SGC."
            )
        
        return recommendations

    def _build_environmental_criteria(self, context_analysis: ContextAnalysis) -> Dict[str, Any]:
        climate = context_analysis.climate_context or {}
        env_scope = context_analysis.environmental_scope or []
        return {
            'signals': [item.get('area') for item in env_scope],
            'supply_chain_signals': climate.get('supply_chain_signals', []),
            'regulatory_trends': climate.get('regulatory_trends', []),
            'emerging_risks': climate.get('emerging_risks', []),
        }

    def _calculate_climate_readiness(self, coverage: Dict[str, Any], context_analysis: ContextAnalysis) -> float:
        base = float(coverage.get('overall_score', 0))
        climate = context_analysis.climate_context or {}
        env_scope = context_analysis.environmental_scope or []
        signal_bonus = min(len(climate.get('regulatory_trends', [])) * 3, 15)
        scope_bonus = min(len(env_scope) * 5, 20)
        return max(0.0, min(100.0, base * 0.6 + 20 + signal_bonus + scope_bonus))

    def _calculate_digital_readiness(self, context_analysis: ContextAnalysis) -> float:
        internal = context_analysis.internal_insights or {}
        digital = internal.get('tendencias_digitales', [])
        return max(0.0, min(100.0, 40 + (len(digital) * 10)))