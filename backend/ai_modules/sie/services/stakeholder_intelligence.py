"""
Stakeholder Intelligence Engine (SIE)
ISO 4.2: Comprensión de las necesidades y expectativas de las partes interesadas

Este módulo implementa análisis inteligente de stakeholders usando:
- Network Analysis (NetworkX)
- NLP para detectar cambios en expectativas
- Scoring de influencia multi-criterio
"""

import logging
import networkx as nx
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class StakeholderIntelligenceEngine:
    """Motor de inteligencia para análisis de stakeholders"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.logger = logging.getLogger('ai_modules.sie')
        
    def build_stakeholder_network(self, stakeholders: List[Dict]) -> nx.DiGraph:
        """
        Construye el grafo de relaciones entre stakeholders
        
        Args:
            stakeholders: Lista de diccionarios con datos de stakeholders
            
        Returns:
            NetworkX DiGraph con la red completa
        """
        self.graph.clear()
        
        for sh in stakeholders:
            # Agregar nodo con todos sus atributos
            self.graph.add_node(
                sh['id'],
                name=sh.get('name', f"Stakeholder {sh['id']}"),
                stakeholder_type=sh.get('stakeholder_type', 'otro'),
                influence_score=sh.get('influence_score', 0.0),
                power=sh.get('power', 'medio'),
                interest=sh.get('interest', 'medio'),
                satisfaction_score=sh.get('satisfaction_score', 0.0),
                expectations=sh.get('expectations', [])
            )
            
            # Agregar relaciones basadas en tipo y sector
            for other_sh in stakeholders:
                if sh['id'] != other_sh['id']:
                    # Calcular peso de la relación
                    weight = self._calculate_relationship_weight(sh, other_sh)
                    
                    if weight > 0.3:  # Solo agregar relaciones significativas
                        self.graph.add_edge(
                            sh['id'],
                            other_sh['id'],
                            weight=weight,
                            relationship_type=self._infer_relationship_type(sh, other_sh)
                        )
        
        self.logger.info(f"Red construida: {len(self.graph.nodes)} nodos, {len(self.graph.edges)} aristas")
        return self.graph
    
    def _calculate_relationship_weight(self, sh1: Dict, sh2: Dict) -> float:
        """Calcula el peso de la relación entre dos stakeholders"""
        weight = 0.0
        
        # Misma industria/sector
        if sh1.get('stakeholder_type') == sh2.get('stakeholder_type'):
            weight += 0.3
            
        # Relación cliente-proveedor
        if (sh1.get('stakeholder_type') == 'cliente' and sh2.get('stakeholder_type') == 'proveedor') or \
           (sh1.get('stakeholder_type') == 'proveedor' and sh2.get('stakeholder_type') == 'cliente'):
            weight += 0.5
            
        # Ambos con alta influencia
        if sh1.get('influence_score', 0) > 0.7 and sh2.get('influence_score', 0) > 0.7:
            weight += 0.2
            
        return min(weight, 1.0)
    
    def _infer_relationship_type(self, sh1: Dict, sh2: Dict) -> str:
        """Infiere el tipo de relación entre stakeholders"""
        type1 = sh1.get('stakeholder_type', 'otro')
        type2 = sh2.get('stakeholder_type', 'otro')
        
        if type1 == 'cliente' and type2 == 'proveedor':
            return 'cliente-proveedor'
        elif type1 == 'empleado' and type2 == 'empleado':
            return 'colaboracion'
        elif 'regulador' in [type1, type2]:
            return 'regulatoria'
        else:
            return 'general'
    
    def calculate_influence_metrics(self) -> Dict[int, Dict[str, float]]:
        """
        Calcula métricas avanzadas de influencia para cada stakeholder
        
        Returns:
            Dict con métricas por stakeholder_id
        """
        if len(self.graph.nodes) == 0:
            return {}
        
        metrics = {}
        
        # Centralidad de grado (cuántas conexiones tiene)
        degree_centrality = nx.degree_centrality(self.graph)
        
        # Centralidad de intermediación (cuán crítico es para conectar a otros)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        
        # PageRank (importancia ponderada)
        try:
            pagerank = nx.pagerank(self.graph, weight='weight')
        except:
            pagerank = {node: 0.0 for node in self.graph.nodes}
        
        # Centralidad de cercanía (qué tan cerca está de todos los demás)
        try:
            closeness_centrality = nx.closeness_centrality(self.graph)
        except:
            closeness_centrality = {node: 0.0 for node in self.graph.nodes}
        
        # Calcular métricas combinadas
        for node in self.graph.nodes:
            node_data = self.graph.nodes[node]
            
            # Score compuesto
            composite_score = (
                degree_centrality.get(node, 0) * 0.25 +
                betweenness_centrality.get(node, 0) * 0.30 +
                pagerank.get(node, 0) * 0.25 +
                closeness_centrality.get(node, 0) * 0.20
            )
            
            metrics[node] = {
                'degree_centrality': round(degree_centrality.get(node, 0), 3),
                'betweenness_centrality': round(betweenness_centrality.get(node, 0), 3),
                'pagerank': round(pagerank.get(node, 0), 3),
                'closeness_centrality': round(closeness_centrality.get(node, 0), 3),
                'composite_influence_score': round(composite_score, 3),
                'connections': self.graph.degree(node),
                'influence_category': self._categorize_influence(composite_score),
                'is_hub': degree_centrality.get(node, 0) > 0.5,
                'is_broker': betweenness_centrality.get(node, 0) > 0.3
            }
        
        return metrics
    
    def _categorize_influence(self, score: float) -> str:
        """Categoriza el nivel de influencia"""
        if score >= 0.7:
            return 'Crítico'
        elif score >= 0.5:
            return 'Alto'
        elif score >= 0.3:
            return 'Medio'
        else:
            return 'Bajo'
    
    def detect_expectation_changes(self, historical_data: Dict[int, List[Dict]]) -> List[Dict]:
        """
        Detecta cambios significativos en las expectativas de stakeholders
        
        Args:
            historical_data: Dict con {stakeholder_id: [lista de registros históricos]}
            
        Returns:
            Lista de cambios detectados
        """
        changes = []
        
        for stakeholder_id, history in historical_data.items():
            if len(history) < 2:
                continue
            
            # Obtener expectativas actuales vs anteriores
            current = history[-1]
            previous = history[-2]
            
            current_expectations = set(current.get('expectations', []))
            previous_expectations = set(previous.get('expectations', []))
            
            # Detectar cambios
            new_expectations = current_expectations - previous_expectations
            removed_expectations = previous_expectations - current_expectations
            
            if new_expectations or removed_expectations:
                # Calcular severidad del cambio
                change_magnitude = len(new_expectations) + len(removed_expectations)
                severity = 'alto' if change_magnitude >= 3 else 'medio' if change_magnitude >= 2 else 'bajo'
                
                # Obtener información del stakeholder
                stakeholder_name = current.get('name', f'Stakeholder {stakeholder_id}')
                stakeholder_type = current.get('stakeholder_type', 'desconocido')
                
                change_record = {
                    'stakeholder_id': stakeholder_id,
                    'stakeholder_name': stakeholder_name,
                    'stakeholder_type': stakeholder_type,
                    'change_detected': True,
                    'change_date': datetime.now().isoformat(),
                    'severity': severity,
                    'new_expectations': list(new_expectations),
                    'removed_expectations': list(removed_expectations),
                    'change_magnitude': change_magnitude,
                    'recommendation': self._generate_recommendation(
                        severity, 
                        stakeholder_type,
                        new_expectations,
                        removed_expectations
                    ),
                    'action_required': severity in ['alto', 'medio']
                }
                
                changes.append(change_record)
                
                self.logger.info(
                    f"Cambio detectado en {stakeholder_name}: "
                    f"+{len(new_expectations)} expectativas, "
                    f"-{len(removed_expectations)} expectativas"
                )
        
        return changes
    
    def _generate_recommendation(self, severity: str, stakeholder_type: str, 
                                 new_exp: set, removed_exp: set) -> str:
        """Genera recomendaciones basadas en los cambios detectados"""
        
        if severity == 'alto':
            return (
                f"⚠️ ACCIÓN URGENTE: Programar reunión inmediata con este {stakeholder_type}. "
                f"Cambios significativos en expectativas detectados. "
                f"Revisar contratos/acuerdos existentes."
            )
        elif severity == 'medio':
            return (
                f"📋 ACCIÓN REQUERIDA: Agendar seguimiento con {stakeholder_type} "
                f"en las próximas 2 semanas. Actualizar matriz de requisitos."
            )
        else:
            return (
                f"ℹ️ MONITOREO: Cambios menores detectados. "
                f"Incluir en próxima revisión de stakeholders."
            )
    
    def identify_critical_stakeholders(self, threshold: float = 0.7) -> List[Dict]:
        """
        Identifica stakeholders críticos basándose en múltiples criterios
        
        Args:
            threshold: Umbral mínimo para considerar crítico (0-1)
            
        Returns:
            Lista de stakeholders críticos con detalles
        """
        metrics = self.calculate_influence_metrics()
        critical = []
        
        for node_id, node_metrics in metrics.items():
            if node_metrics['composite_influence_score'] >= threshold:
                node_data = self.graph.nodes[node_id]
                
                critical_info = {
                    'stakeholder_id': node_id,
                    'name': node_data.get('name', f'Stakeholder {node_id}'),
                    'type': node_data.get('stakeholder_type', 'desconocido'),
                    'composite_score': node_metrics['composite_influence_score'],
                    'influence_category': node_metrics['influence_category'],
                    'connections': node_metrics['connections'],
                    'is_hub': node_metrics['is_hub'],
                    'is_broker': node_metrics['is_broker'],
                    'power': node_data.get('power', 'desconocido'),
                    'interest': node_data.get('interest', 'desconocido'),
                    'satisfaction': node_data.get('satisfaction_score', 0.0),
                    'risk_level': self._assess_stakeholder_risk(node_data, node_metrics),
                    'engagement_strategy': self._suggest_engagement_strategy(
                        node_data.get('power', 'medio'),
                        node_data.get('interest', 'medio'),
                        node_metrics['composite_influence_score']
                    )
                }
                
                critical.append(critical_info)
        
        # Ordenar por score descendente
        critical.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return critical
    
    def _assess_stakeholder_risk(self, node_data: Dict, metrics: Dict) -> str:
        """Evalúa el nivel de riesgo de un stakeholder"""
        power = node_data.get('power', 'medio')
        satisfaction = node_data.get('satisfaction_score', 5.0)
        influence = metrics['composite_influence_score']
        
        # Alto riesgo: Alto poder/influencia + Baja satisfacción
        if power == 'alto' and satisfaction < 3.0:
            return 'CRÍTICO'
        elif influence > 0.7 and satisfaction < 3.5:
            return 'ALTO'
        elif influence > 0.5 or power == 'alto':
            return 'MEDIO'
        else:
            return 'BAJO'
    
    def _suggest_engagement_strategy(self, power: str, interest: str, 
                                     influence: float) -> str:
        """Sugiere estrategia de engagement basada en la matriz poder/interés"""
        
        # Matriz de poder/interés estándar
        if power == 'alto' and interest == 'alto':
            return "🎯 GESTIONAR DE CERCA - Comunicación frecuente y participación activa"
        elif power == 'alto' and interest in ['medio', 'bajo']:
            return "😊 MANTENER SATISFECHO - Comunicación regular, evitar sorpresas"
        elif power in ['medio', 'bajo'] and interest == 'alto':
            return "📢 MANTENER INFORMADO - Actualizaciones regulares, bajo esfuerzo"
        else:
            return "📊 MONITOREAR - Comunicación básica, revisión periódica"
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """Calcula estadísticas generales de la red"""
        
        if len(self.graph.nodes) == 0:
            return {'error': 'Red vacía'}
        
        stats = {
            'total_stakeholders': len(self.graph.nodes),
            'total_relationships': len(self.graph.edges),
            'network_density': round(nx.density(self.graph), 3),
            'avg_degree': round(sum(dict(self.graph.degree()).values()) / len(self.graph.nodes), 2),
        }
        
        # Intentar calcular componentes conectados
        try:
            if nx.is_weakly_connected(self.graph):
                stats['is_connected'] = True
                stats['connected_components'] = 1
            else:
                stats['is_connected'] = False
                stats['connected_components'] = nx.number_weakly_connected_components(self.graph)
        except:
            stats['is_connected'] = False
            stats['connected_components'] = 0
        
        # Distribución por tipo
        type_distribution = defaultdict(int)
        for node in self.graph.nodes:
            sh_type = self.graph.nodes[node].get('stakeholder_type', 'desconocido')
            type_distribution[sh_type] += 1
        
        stats['stakeholder_types'] = dict(type_distribution)
        
        return stats
    
    def export_network_for_visualization(self) -> Dict[str, List[Dict]]:
        """
        Exporta la red en formato compatible con visualizaciones frontend
        
        Returns:
            Dict con 'nodes' y 'edges' para D3.js o similar
        """
        nodes = []
        edges = []
        
        # Exportar nodos
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id]
            nodes.append({
                'id': node_id,
                'name': node_data.get('name', f'SH-{node_id}'),
                'type': node_data.get('stakeholder_type', 'otro'),
                'influence': node_data.get('influence_score', 0.0),
                'power': node_data.get('power', 'medio'),
                'interest': node_data.get('interest', 'medio'),
                'satisfaction': node_data.get('satisfaction_score', 0.0),
                'degree': self.graph.degree(node_id)
            })
        
        # Exportar aristas
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                'source': source,
                'target': target,
                'weight': data.get('weight', 0.5),
                'type': data.get('relationship_type', 'general')
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'statistics': self.get_network_statistics()
        }
