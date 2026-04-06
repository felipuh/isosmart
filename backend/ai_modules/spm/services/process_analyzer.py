"""
Django Service para Smart Process Mapper
Integra el motor de IA con los modelos Django
"""

from django.utils import timezone
from datetime import datetime
from typing import Dict, List, Any
import logging

from ai_modules.common.base import AIModuleBase
from ai_modules.spm.services.process_mapper import ProcessMapperEngine
from ai_modules.spm.models import ProcessMap, Process, ProcessInteraction, ProcessActivity
from ai_modules.asb.models import ScopeDefinition
from core.models import ContextAnalysis, RiskMatrix, EnvironmentalRiskAlert

logger = logging.getLogger(__name__)


class ProcessAnalyzer(AIModuleBase):
    """
    Analizador de Procesos con IA
    Implementa ISO 4.4
    """
    
    def __init__(self):
        super().__init__('SPM')
        self.engine = ProcessMapperEngine()
        self.organization_id = None
    
    def process(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Proceso principal de mapeo de procesos
        
        Returns:
            Dict con resultados del análisis completo
        """
        start_time = datetime.now()
        payload = data or {}
        self.organization_id = payload.get('organization_id') or payload.get('organization')
        
        try:
            # 1. Obtener contexto y alcance previos
            context_qs = ContextAnalysis.objects.filter(status='completed')
            if self.organization_id:
                context_qs = context_qs.filter(organization_id=self.organization_id)
            context_analysis = context_qs.order_by('-timestamp').first()

            scope_qs = ScopeDefinition.objects.filter(status__in=['active', 'approved'])
            if self.organization_id:
                scope_qs = scope_qs.filter(organization_id=self.organization_id)
            scope_definition = scope_qs.order_by('-created_at').first()

            if scope_definition and not self.organization_id:
                self.organization_id = scope_definition.organization_id
            
            if not context_analysis:
                return {
                    'status': 'warning',
                    'message': 'Se requiere un análisis de contexto previo (Módulo SCA)',
                    'recommendation': 'Ejecutar análisis de contexto antes de mapear procesos'
                }
            
            # Preparar datos
            context_data = {
                'internal': context_analysis.internal_insights,
                'external': context_analysis.external_insights,
                'climate': context_analysis.climate_context,
            }
            
            scope_data = {
                'products_services': scope_definition.products_services if scope_definition else [],
                'boundaries': scope_definition.organizational_boundaries if scope_definition else {}
            }
            
            # 2. Identificar procesos
            self.logger.info("Identificando procesos organizacionales...")
            processes_data = self.engine.identify_processes(context_data, scope_data)
            processes_data = self.engine.enrich_processes_with_climate(processes_data, context_data)
            
            # 3. Mapear interacciones
            self.logger.info("Mapeando interacciones entre procesos...")
            interactions_data = self.engine.map_interactions(processes_data)
            
            # 4. Calcular criticidad
            self.logger.info("Calculando criticidad de procesos...")
            criticality_scores = self.engine.calculate_criticality(
                processes_data,
                interactions_data
            )
            
            # Actualizar criticidad en procesos
            for process_data in processes_data:
                code = process_data['code']
                score = criticality_scores.get(code, 0.5)
                process_data['criticality_score'] = score
                process_data['is_critical'] = score >= 0.7
            
            # 5. Generar datos de diagrama
            diagram_data = self.engine.generate_process_diagram_data(
                processes_data,
                interactions_data
            )
            
            # 6. Generar recomendaciones
            recommendations = self.engine.suggest_improvements(
                processes_data,
                interactions_data
            )
            emerging_risks = self.engine.detect_emerging_climate_risks(processes_data)
            
            # 7. Crear o actualizar mapa de procesos en BD
            existing_map_qs = ProcessMap.objects.filter(status__in=['draft', 'active'])
            if self.organization_id:
                existing_map_qs = existing_map_qs.filter(organization_id=self.organization_id)
            existing_map = existing_map_qs.order_by('-created_at').first()
            
            if existing_map:
                # Actualizar mapa existente
                existing_map.title = f"Mapa de Procesos - {datetime.now().strftime('%Y-%m')}"
                existing_map.total_processes = len(processes_data)
                existing_map.strategic_count = sum(1 for p in processes_data if p['process_type'] == 'strategic')
                existing_map.operational_count = sum(1 for p in processes_data if p['process_type'] == 'operational')
                existing_map.support_count = sum(1 for p in processes_data if p['process_type'] == 'support')
                existing_map.interaction_analysis = diagram_data
                existing_map.critical_processes = [p['code'] for p in processes_data if p.get('is_critical')]
                existing_map.recommendations = recommendations
                existing_map.scope_definition = scope_definition
                if self.organization_id:
                    existing_map.organization_id = self.organization_id
                existing_map.save()
                
                # Eliminar procesos e interacciones anteriores del mapa
                Process.objects.filter(process_map=existing_map).delete()
                ProcessInteraction.objects.filter(process_map=existing_map).delete()
                
                process_map = existing_map
                self.logger.info(f"Mapa de procesos actualizado: ID {process_map.id}")
            else:
                # Crear nuevo mapa
                process_map = ProcessMap.objects.create(
                    title=f"Mapa de Procesos - {datetime.now().strftime('%Y-%m')}",
                    version="1.0",
                    total_processes=len(processes_data),
                    strategic_count=sum(1 for p in processes_data if p['process_type'] == 'strategic'),
                    operational_count=sum(1 for p in processes_data if p['process_type'] == 'operational'),
                    support_count=sum(1 for p in processes_data if p['process_type'] == 'support'),
                    interaction_analysis=diagram_data,
                    critical_processes=[p['code'] for p in processes_data if p.get('is_critical')],
                    recommendations=recommendations,
                    status='draft',
                    scope_definition=scope_definition,
                    organization_id=self.organization_id
                )
                self.logger.info(f"Nuevo mapa de procesos creado: ID {process_map.id}")
            
            # 8. Crear procesos individuales
            created_processes = self._create_processes(process_map, processes_data)
            
            # 9. Crear interacciones
            created_interactions = self._create_interactions(
                process_map,
                created_processes,
                interactions_data
            )

            created_climate_items = self._create_emerging_risks(process_map, emerging_risks)
            
            # 10. Crear actividades de ejemplo para procesos críticos
            self._create_sample_activities(created_processes)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'status': 'completed',
                'module': 'SPM',
                'iso_clause': '4.4',
                'execution_time': execution_time,
                'process_map_id': process_map.id,
                'total_processes': len(processes_data),
                'strategic_count': process_map.strategic_count,
                'operational_count': process_map.operational_count,
                'support_count': process_map.support_count,
                'total_interactions': len(interactions_data),
                'critical_processes_count': len(process_map.critical_processes),
                'diagram_data': diagram_data,
                'recommendations': recommendations,
                'emerging_risks': emerging_risks,
                'emerging_risks_created': created_climate_items,
                'processes': processes_data,
                'interactions': interactions_data
            }
            
            self.log_execution('process_mapping', 'success', {
                'process_map_id': process_map.id,
                'total_processes': len(processes_data),
                'interactions': len(interactions_data)
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en mapeo de procesos: {e}", exc_info=True)
            
            self.log_execution('process_mapping', 'error', {'error': str(e)})
            
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _create_processes(self, process_map: ProcessMap, 
                         processes_data: List[Dict]) -> Dict[str, Process]:
        """Crea procesos en la BD"""
        created = {}
        
        for process_data in processes_data:
            process = Process.objects.create(
                process_map=process_map,
                code=process_data['code'],
                name=process_data['name'],
                description=process_data.get('description', ''),
                process_type=process_data['process_type'],
                objective=process_data.get('objective', ''),
                owner=process_data.get('owner', 'Sin asignar'),
                inputs=process_data.get('inputs', []),
                outputs=process_data.get('outputs', []),
                resources=process_data.get('resources', []),
                kpis=process_data.get('kpis', []),
                risks=process_data.get('risks', []),
                controls=process_data.get('controls', []),
                criticality_score=process_data.get('criticality_score', 0.5),
                is_critical=process_data.get('is_critical', False),
                carbon_intensity_category=process_data.get('carbon_intensity_category', 'unknown'),
                climate_exposure_level=process_data.get('climate_exposure_level', 'medium'),
                supply_chain_risk=process_data.get('supply_chain_risk', 'unknown'),
                resilience_score=process_data.get('resilience_score', 50.0),
                documented_in=process_data.get('documented_in', ''),
                is_active=True
            )
            
            created[process_data['code']] = process
            
            self.logger.debug(f"Proceso creado: {process.code} - {process.name}")
        
        return created
    
    def _create_interactions(self, process_map: ProcessMap,
                           created_processes: Dict[str, Process],
                           interactions_data: List[Dict]) -> List[ProcessInteraction]:
        """Crea interacciones en la BD"""
        created = []
        
        for interaction_data in interactions_data:
            source_code = interaction_data['source_code']
            target_code = interaction_data['target_code']
            
            if source_code not in created_processes or target_code not in created_processes:
                continue
            
            # Asegurar que is_critical nunca sea None
            is_critical = interaction_data.get('is_critical', False)
            if is_critical is None:
                is_critical = False
            
            interaction = ProcessInteraction.objects.create(
                process_map=process_map,
                source_process=created_processes[source_code],
                target_process=created_processes[target_code],
                interaction_type=interaction_data.get('interaction_type', 'information'),
                description=interaction_data.get('description', ''),
                exchanged_items=interaction_data.get('exchanged_items', []),
                frequency=interaction_data.get('frequency', 'on_demand'),
                is_critical=is_critical
            )
            
            created.append(interaction)
            
            self.logger.debug(f"Interacción creada: {source_code} → {target_code}")
        
        return created
    
    def _create_sample_activities(self, created_processes: Dict[str, Process]):
        """Crea actividades de ejemplo para procesos críticos"""
        
        # Actividades para proceso estratégico EST-01
        if 'EST-01' in created_processes:
            process = created_processes['EST-01']
            activities = [
                {
                    'sequence': 1,
                    'name': 'Análisis de contexto y stakeholders',
                    'description': 'Revisar análisis de contexto y expectativas de partes interesadas',
                    'responsible': 'Equipo directivo',
                    'duration': '1 semana'
                },
                {
                    'sequence': 2,
                    'name': 'Definición de objetivos estratégicos',
                    'description': 'Establecer objetivos SMART alineados con política de calidad',
                    'responsible': 'Dirección General',
                    'duration': '2 días'
                },
                {
                    'sequence': 3,
                    'name': 'Asignación de recursos',
                    'description': 'Determinar recursos necesarios para alcanzar objetivos',
                    'responsible': 'Gerentes de área',
                    'duration': '3 días'
                },
                {
                    'sequence': 4,
                    'name': 'Comunicación del plan',
                    'description': 'Comunicar plan estratégico a toda la organización',
                    'responsible': 'RRHH',
                    'duration': '1 semana'
                }
            ]
            
            for act in activities:
                ProcessActivity.objects.create(
                    process=process,
                    sequence_number=act['sequence'],
                    name=act['name'],
                    description=act['description'],
                    responsible=act['responsible'],
                    estimated_duration=act['duration']
                )
        
        # Actividades para proceso operativo OPE-01
        if 'OPE-01' in created_processes:
            process = created_processes['OPE-01']
            activities = [
                {
                    'sequence': 1,
                    'name': 'Recepción de pedido',
                    'description': 'Recibir y validar requisitos del cliente',
                    'responsible': 'Comercial',
                    'duration': '1 día'
                },
                {
                    'sequence': 2,
                    'name': 'Planificación de entrega',
                    'description': 'Planificar recursos y cronograma',
                    'responsible': 'Operaciones',
                    'duration': '2 días'
                },
                {
                    'sequence': 3,
                    'name': 'Ejecución del servicio',
                    'description': 'Prestar el servicio según especificaciones',
                    'responsible': 'Equipo operativo',
                    'duration': 'Variable'
                },
                {
                    'sequence': 4,
                    'name': 'Verificación de conformidad',
                    'description': 'Verificar que se cumplan todos los requisitos',
                    'responsible': 'Calidad',
                    'duration': '1 día'
                },
                {
                    'sequence': 5,
                    'name': 'Entrega al cliente',
                    'description': 'Entregar servicio y obtener conformidad del cliente',
                    'responsible': 'Comercial',
                    'duration': '1 día'
                }
            ]
            
            for act in activities:
                ProcessActivity.objects.create(
                    process=process,
                    sequence_number=act['sequence'],
                    name=act['name'],
                    description=act['description'],
                    responsible=act['responsible'],
                    estimated_duration=act['duration']
                )

    def _create_emerging_risks(self, process_map: ProcessMap, emerging_risks: List[Dict]) -> Dict[str, int]:
        """Crea riesgos 6.1 y alertas trazables para riesgos emergentes de procesos."""
        created_risks = 0
        created_alerts = 0

        for item in emerging_risks:
            process_code = item.get('process_code')
            process = Process.objects.filter(process_map=process_map, code=process_code).first()

            risk, risk_created = RiskMatrix.objects.get_or_create(
                organization_id=process_map.organization_id,
                source_module='SPM',
                source_id=process.id if process else None,
                risk_description=item.get('description', ''),
                defaults={
                    'risk_category': 'climatico_proceso',
                    'probability': 'alta' if item.get('severity') == 'critical' else 'media',
                    'impact': 'muy_alto' if item.get('severity') == 'critical' else 'alto',
                    'risk_level': 'critico' if item.get('severity') == 'critical' else 'alto',
                    'mitigation_actions': 'Revisar rediseño de proceso, controles de continuidad y redundancia de proveedores.',
                    'responsible': process.owner if process else 'Responsable de Operaciones',
                    'iso_clause': '6.1',
                    'status': 'identified',
                    'process_id': process_code,
                }
            )
            if risk_created:
                created_risks += 1

            _, alert_created = EnvironmentalRiskAlert.objects.get_or_create(
                organization_id=process_map.organization_id,
                source_module='SPM',
                source_id=process.id if process else None,
                title=f"Riesgo emergente de proceso {process_code}",
                defaults={
                    'alert_type': 'process_exposure',
                    'severity': 'critical' if item.get('severity') == 'critical' else 'high',
                    'description': item.get('description', ''),
                    'recommendation': 'Actualizar matriz 6.1, plan de continuidad y objetivos 6.2.',
                    'ai_audit_score': 0.82,
                    'linked_risk': risk,
                }
            )
            if alert_created:
                created_alerts += 1

        return {
            'risks_created': created_risks,
            'alerts_created': created_alerts,
        }