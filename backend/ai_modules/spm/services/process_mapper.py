"""
Process Mapper Engine
Motor de IA para mapeo automático de procesos
ISO 4.4
"""

import logging
from typing import Dict, List, Any, Optional
import networkx as nx

logger = logging.getLogger(__name__)


class ProcessMapperEngine:
    """
    Motor de IA para mapeo inteligente de procesos organizacionales
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ProcessMapperEngine")
        self.process_graph = nx.DiGraph()
    
    def identify_processes(self, context_data: Dict, scope_data: Dict) -> List[Dict]:
        """
        Identifica procesos basándose en contexto y alcance
        
        Args:
            context_data: Datos del análisis de contexto (SCA)
            scope_data: Datos del alcance (ASB)
        
        Returns:
            Lista de procesos identificados
        """
        self.logger.info("Identificando procesos organizacionales...")
        
        processes = []
        
        # Procesos estratégicos
        strategic = self._identify_strategic_processes(context_data, scope_data)
        processes.extend(strategic)
        
        # Procesos operativos
        operational = self._identify_operational_processes(scope_data)
        processes.extend(operational)
        
        # Procesos de apoyo
        support = self._identify_support_processes()
        processes.extend(support)
        
        self.logger.info(f"Total procesos identificados: {len(processes)}")
        
        return processes

    def enrich_processes_with_climate(self, processes: List[Dict], context_data: Dict) -> List[Dict]:
        """Asigna atributos climáticos y de resiliencia a cada proceso."""
        climate = context_data.get('climate', {}) if context_data else {}
        supply_signals = set(climate.get('supply_chain_signals', []))

        for process in processes:
            code = process.get('code', '')
            p_type = process.get('process_type', '')

            if p_type == 'operational':
                process['carbon_intensity_category'] = 'high'
                process['climate_exposure_level'] = 'high'
                process['resilience_score'] = 55.0
            elif p_type == 'strategic':
                process['carbon_intensity_category'] = 'medium'
                process['climate_exposure_level'] = 'medium'
                process['resilience_score'] = 70.0
            else:
                process['carbon_intensity_category'] = 'low'
                process['climate_exposure_level'] = 'medium'
                process['resilience_score'] = 65.0

            process['supply_chain_risk'] = 'high' if supply_signals else 'medium'

            if code in {'OPE-01', 'OPE-02'} and supply_signals:
                process['supply_chain_risk'] = 'high'
                process['resilience_score'] = max(35.0, process['resilience_score'] - 15.0)

        return processes

    def detect_emerging_climate_risks(self, processes: List[Dict]) -> List[Dict]:
        """Detecta riesgos emergentes por exposición climática y resiliencia."""
        emerging = []
        for process in processes:
            if process.get('climate_exposure_level') == 'high' and process.get('resilience_score', 100) <= 60:
                emerging.append({
                    'process_code': process.get('code'),
                    'process_name': process.get('name'),
                    'risk_type': 'process_exposure',
                    'severity': 'high' if process.get('resilience_score', 100) > 45 else 'critical',
                    'description': (
                        f"Proceso {process.get('code')} con alta exposición climática y resiliencia "
                        f"{process.get('resilience_score')}"
                    ),
                })
        return emerging
    
    def map_interactions(self, processes: List[Dict]) -> List[Dict]:
        """
        Mapea interacciones entre procesos
        
        Args:
            processes: Lista de procesos identificados
        
        Returns:
            Lista de interacciones entre procesos
        """
        self.logger.info("Mapeando interacciones entre procesos...")
        
        interactions = []
        
        # Construir grafo de procesos
        for process in processes:
            self.process_graph.add_node(
                process['code'],
                name=process['name'],
                type=process['process_type']
            )
        
        # Identificar interacciones lógicas
        for i, source in enumerate(processes):
            for target in processes[i+1:]:
                interaction = self._analyze_potential_interaction(source, target)
                if interaction:
                    interactions.append(interaction)
                    self.process_graph.add_edge(
                        source['code'],
                        target['code'],
                        type=interaction['interaction_type']
                    )
        
        self.logger.info(f"Interacciones mapeadas: {len(interactions)}")
        
        return interactions
    
    def calculate_criticality(self, processes: List[Dict], 
                             interactions: List[Dict]) -> Dict[str, float]:
        """
        Calcula criticidad de cada proceso
        
        Args:
            processes: Lista de procesos
            interactions: Lista de interacciones
        
        Returns:
            Dict con scores de criticidad por código de proceso
        """
        self.logger.info("Calculando criticidad de procesos...")
        
        criticality_scores = {}
        
        for process in processes:
            code = process['code']
            
            # Factores de criticidad
            factors = {
                'centrality': self._calculate_centrality(code),
                'type_weight': self._get_type_weight(process['process_type']),
                'output_impact': self._calculate_output_impact(process),
                'risk_factor': self._calculate_risk_factor(process)
            }
            
            # Score compuesto (0-1)
            score = (
                factors['centrality'] * 0.3 +
                factors['type_weight'] * 0.2 +
                factors['output_impact'] * 0.3 +
                factors['risk_factor'] * 0.2
            )
            
            criticality_scores[code] = min(max(score, 0), 1)
        
        return criticality_scores
    
    def generate_process_diagram_data(self, processes: List[Dict], 
                                     interactions: List[Dict]) -> Dict:
        """
        Genera datos para visualización de diagrama de procesos
        
        Returns:
            Dict con estructura para diagrama
        """
        self.logger.info("Generando datos para diagrama...")
        
        # Agrupar por tipo
        by_type = {
            'strategic': [],
            'operational': [],
            'support': []
        }
        
        for process in processes:
            by_type[process['process_type']].append({
                'id': process['code'],
                'name': process['name'],
                'owner': process.get('owner', ''),
                'is_critical': process.get('is_critical', False)
            })
        
        # Preparar conexiones
        connections = [
            {
                'from': interaction['source_code'],
                'to': interaction['target_code'],
                'type': interaction['interaction_type'],
                'critical': interaction.get('is_critical', False)
            }
            for interaction in interactions
        ]
        
        return {
            'layers': by_type,
            'connections': connections,
            'statistics': {
                'total_processes': len(processes),
                'total_interactions': len(interactions),
                'critical_processes': sum(1 for p in processes if p.get('is_critical')),
                'network_density': self._calculate_network_density()
            }
        }
    
    def suggest_improvements(self, processes: List[Dict], 
                           interactions: List[Dict]) -> List[str]:
        """
        Genera sugerencias de mejora
        
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Analizar densidad de red
        density = self._calculate_network_density()
        if density > 0.7:
            recommendations.append(
                "🔗 Alta densidad de interacciones detectada. "
                "Considerar simplificar flujos entre procesos para reducir complejidad."
            )
        
        # Procesos sin KPIs
        without_kpis = [p for p in processes if not p.get('kpis')]
        if len(without_kpis) > 0:
            recommendations.append(
                f"📊 {len(without_kpis)} proceso(s) sin KPIs definidos. "
                "Establecer indicadores para medir desempeño."
            )
        
        # Procesos críticos sin documentación
        critical_undocumented = [
            p for p in processes 
            if p.get('is_critical') and not p.get('documented_in')
        ]
        if len(critical_undocumented) > 0:
            recommendations.append(
                f"⚠️ {len(critical_undocumented)} proceso(s) crítico(s) sin documentación formal. "
                "Prioritizar documentación de procedimientos."
            )
        
        # Balance de tipos
        strategic_count = sum(1 for p in processes if p['process_type'] == 'strategic')
        if strategic_count < 3:
            recommendations.append(
                "🎯 Pocos procesos estratégicos identificados. "
                "Revisar si se han mapeado todos los procesos de dirección."
            )
        
        if len(recommendations) == 0:
            recommendations.append(
                "✅ Mapa de procesos bien estructurado. Mantener actualización periódica."
            )
        
        return recommendations
    
    # Métodos privados auxiliares
    
    def _identify_strategic_processes(self, context_data: Dict, 
                                     scope_data: Dict) -> List[Dict]:
        """Identifica procesos estratégicos"""
        processes = [
            {
                'code': 'EST-01',
                'name': 'Planificación Estratégica',
                'process_type': 'strategic',
                'objective': 'Definir dirección estratégica y objetivos de calidad',
                'owner': 'Dirección General',
                'inputs': ['Análisis de contexto', 'Expectativas de stakeholders'],
                'outputs': ['Plan estratégico', 'Objetivos de calidad', 'Políticas'],
                'kpis': [
                    {'name': 'Cumplimiento de objetivos', 'target': '90%'},
                    {'name': 'Revisión de contexto', 'target': 'Semestral'}
                ]
            },
            {
                'code': 'EST-02',
                'name': 'Revisión por la Dirección',
                'process_type': 'strategic',
                'objective': 'Evaluar desempeño del SGC y tomar decisiones',
                'owner': 'Dirección General',
                'inputs': ['Indicadores SGC', 'Auditorías', 'No conformidades'],
                'outputs': ['Decisiones de mejora', 'Recursos asignados'],
                'kpis': [
                    {'name': 'Frecuencia de revisión', 'target': 'Trimestral'},
                    {'name': 'Acciones de mejora', 'target': '>5 por revisión'}
                ]
            },
            {
                'code': 'EST-03',
                'name': 'Gestión de Riesgos y Oportunidades',
                'process_type': 'strategic',
                'objective': 'Identificar y gestionar riesgos que afecten el SGC',
                'owner': 'Responsable de Calidad',
                'inputs': ['Matriz de riesgos', 'Contexto organizacional'],
                'outputs': ['Plan de tratamiento de riesgos', 'Controles'],
                'kpis': [
                    {'name': 'Riesgos mitigados', 'target': '80%'},
                    {'name': 'Oportunidades aprovechadas', 'target': '>3/año'}
                ]
            }
        ]
        
        return processes
    
    def _identify_operational_processes(self, scope_data: Dict) -> List[Dict]:
        """Identifica procesos operativos basados en productos/servicios"""
        processes = []
        
        products = scope_data.get('products_services', [])
        
        # Proceso general de operaciones
        processes.append({
            'code': 'OPE-01',
            'name': 'Prestación del Servicio',
            'process_type': 'operational',
            'objective': 'Entregar servicios que cumplan requisitos del cliente',
            'owner': 'Gerente de Operaciones',
            'inputs': ['Pedidos de clientes', 'Requisitos', 'Recursos'],
            'outputs': products if products else ['Servicios entregados'],
            'kpis': [
                {'name': 'Satisfacción del cliente', 'target': '>85%'},
                {'name': 'Entregas a tiempo', 'target': '>95%'},
                {'name': 'Conformidad', 'target': '100%'}
            ]
        })
        
        # Ventas y marketing
        processes.append({
            'code': 'OPE-02',
            'name': 'Ventas y Gestión Comercial',
            'process_type': 'operational',
            'objective': 'Captar y gestionar clientes',
            'owner': 'Gerente Comercial',
            'inputs': ['Necesidades del mercado', 'Leads'],
            'outputs': ['Contratos', 'Pedidos', 'Relaciones con clientes'],
            'kpis': [
                {'name': 'Conversión de leads', 'target': '>30%'},
                {'name': 'Crecimiento de ventas', 'target': '+10% anual'}
            ]
        })
        
        # Gestión de quejas
        processes.append({
            'code': 'OPE-03',
            'name': 'Gestión de Quejas y Reclamos',
            'process_type': 'operational',
            'objective': 'Atender y resolver quejas de clientes',
            'owner': 'Responsable de Calidad',
            'inputs': ['Quejas de clientes', 'No conformidades'],
            'outputs': ['Quejas resueltas', 'Acciones correctivas'],
            'kpis': [
                {'name': 'Tiempo de respuesta', 'target': '<48 horas'},
                {'name': 'Resolución efectiva', 'target': '>90%'}
            ]
        })
        
        return processes
    
    def _identify_support_processes(self) -> List[Dict]:
        """Identifica procesos de apoyo"""
        processes = [
            {
                'code': 'APO-01',
                'name': 'Gestión de Recursos Humanos',
                'process_type': 'support',
                'objective': 'Asegurar personal competente y capacitado',
                'owner': 'Gerente de RRHH',
                'inputs': ['Perfiles de puesto', 'Necesidades de capacitación'],
                'outputs': ['Personal competente', 'Registros de capacitación'],
                'kpis': [
                    {'name': 'Cumplimiento plan capacitación', 'target': '100%'},
                    {'name': 'Evaluación de desempeño', 'target': '>80% satisfactorio'}
                ]
            },
            {
                'code': 'APO-02',
                'name': 'Gestión de Infraestructura y Equipos',
                'process_type': 'support',
                'objective': 'Mantener infraestructura adecuada',
                'owner': 'Gerente de Operaciones',
                'inputs': ['Necesidades de infraestructura', 'Mantenimiento'],
                'outputs': ['Instalaciones operativas', 'Equipos calibrados'],
                'kpis': [
                    {'name': 'Disponibilidad de equipos', 'target': '>95%'},
                    {'name': 'Mantenimiento preventivo', 'target': '100%'}
                ]
            },
            {
                'code': 'APO-03',
                'name': 'Gestión Documental',
                'process_type': 'support',
                'objective': 'Controlar documentos y registros del SGC',
                'owner': 'Responsable de Calidad',
                'inputs': ['Documentos del SGC', 'Cambios requeridos'],
                'outputs': ['Documentos controlados', 'Registros archivados'],
                'kpis': [
                    {'name': 'Documentos actualizados', 'target': '100%'},
                    {'name': 'Accesibilidad', 'target': '100%'}
                ]
            },
            {
                'code': 'APO-04',
                'name': 'Auditorías Internas',
                'process_type': 'support',
                'objective': 'Verificar conformidad del SGC',
                'owner': 'Auditor Líder',
                'inputs': ['Programa de auditorías', 'Requisitos ISO'],
                'outputs': ['Informes de auditoría', 'No conformidades'],
                'kpis': [
                    {'name': 'Cumplimiento programa', 'target': '100%'},
                    {'name': 'Hallazgos cerrados', 'target': '>90% en plazo'}
                ]
            },
            {
                'code': 'APO-05',
                'name': 'Mejora Continua',
                'process_type': 'support',
                'objective': 'Implementar mejoras en el SGC',
                'owner': 'Responsable de Calidad',
                'inputs': ['No conformidades', 'Oportunidades de mejora'],
                'outputs': ['Acciones correctivas', 'Mejoras implementadas'],
                'kpis': [
                    {'name': 'Acciones implementadas', 'target': '>80%'},
                    {'name': 'Eficacia de acciones', 'target': '>90%'}
                ]
            }
        ]
        
        return processes
    
    def _analyze_potential_interaction(self, source: Dict, target: Dict) -> Optional[Dict]:
        """Analiza si dos procesos interactúan"""
        # Lógica de interacciones típicas
        interactions_rules = [
            # Estratégicos → Operativos
            ('EST-01', 'OPE-01', 'input_output', ['Objetivos de calidad', 'Políticas']),
            ('EST-03', 'OPE-01', 'information', ['Controles de riesgos']),
            
            # Operativos entre sí
            ('OPE-02', 'OPE-01', 'input_output', ['Pedidos de clientes', 'Requisitos']),
            ('OPE-01', 'OPE-03', 'information', ['Quejas detectadas']),
            
            # Apoyo → Operativos
            ('APO-01', 'OPE-01', 'resource_sharing', ['Personal capacitado']),
            ('APO-02', 'OPE-01', 'resource_sharing', ['Equipos e infraestructura']),
            ('APO-03', 'OPE-01', 'information', ['Procedimientos', 'Registros']),
            
            # Apoyo → Estratégicos
            ('APO-04', 'EST-02', 'input_output', ['Informes de auditoría']),
            ('APO-05', 'EST-02', 'input_output', ['Acciones de mejora']),
        ]
        
        source_code = source['code']
        target_code = target['code']
        
        for rule in interactions_rules:
            if rule[0] == source_code and rule[1] == target_code:
                # Calcular is_critical correctamente
                source_critical = source.get('is_critical', False)
                target_critical = target.get('is_critical', False)
                
                # Si source o target son None, usar False
                if source_critical is None:
                    source_critical = False
                if target_critical is None:
                    target_critical = False
                
                return {
                    'source_code': source_code,
                    'target_code': target_code,
                    'interaction_type': rule[2],
                    'exchanged_items': rule[3],
                    'frequency': 'continuous' if rule[2] == 'resource_sharing' else 'on_demand',
                    'is_critical': source_critical or target_critical
                }
        
        return None
    
    def _calculate_centrality(self, process_code: str) -> float:
        """Calcula centralidad del proceso en la red"""
        if len(self.process_graph.nodes()) == 0:
            return 0.5
        
        try:
            centrality = nx.degree_centrality(self.process_graph)
            return centrality.get(process_code, 0.5)
        except:
            return 0.5
    
    def _get_type_weight(self, process_type: str) -> float:
        """Peso por tipo de proceso"""
        weights = {
            'strategic': 0.9,
            'operational': 0.8,
            'support': 0.6
        }
        return weights.get(process_type, 0.5)
    
    def _calculate_output_impact(self, process: Dict) -> float:
        """Impacto de las salidas del proceso"""
        outputs = process.get('outputs', [])
        
        # Más salidas = mayor impacto
        if len(outputs) >= 3:
            return 0.9
        elif len(outputs) >= 2:
            return 0.7
        elif len(outputs) >= 1:
            return 0.5
        return 0.3
    
    def _calculate_risk_factor(self, process: Dict) -> float:
        """Factor de riesgo del proceso"""
        risks = process.get('risks', [])
        
        if len(risks) >= 3:
            return 0.8
        elif len(risks) >= 1:
            return 0.6
        return 0.4
    
    def _calculate_network_density(self) -> float:
        """Densidad de la red de procesos"""
        if len(self.process_graph.nodes()) == 0:
            return 0
        
        try:
            return nx.density(self.process_graph)
        except:
            return 0