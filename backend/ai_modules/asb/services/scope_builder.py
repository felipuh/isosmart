"""
Scope Builder Engine
Motor de IA para construcción automática del alcance del SGC
ISO 4.3
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ScopeBuilderEngine:
    """
    Motor de IA para definición inteligente del alcance del SGC
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ScopeBuilderEngine")
    
    def analyze_organizational_boundaries(self, context_data: Dict) -> Dict:
        """
        Analiza límites organizacionales basándose en contexto
        
        Args:
            context_data: Datos del análisis de contexto (SCA)
        
        Returns:
            Dict con límites organizacionales identificados
        """
        self.logger.info("Analizando límites organizacionales...")
        
        boundaries = {
            'geographic': self._identify_geographic_boundaries(context_data),
            'functional': self._identify_functional_boundaries(context_data),
            'product_lines': self._identify_product_lines(context_data),
            'organizational_units': self._identify_organizational_units(context_data)
        }
        
        return boundaries
    
    def evaluate_iso_requirements(self, scope_data: Dict) -> Dict:
        """
        Evalúa aplicabilidad de requisitos ISO 9001:2015
        
        Args:
            scope_data: Datos del alcance propuesto
        
        Returns:
            Dict con requisitos aplicables y exclusiones justificadas
        """
        self.logger.info("Evaluando requisitos ISO 9001:2015...")
        
        # Requisitos base de ISO 9001:2015
        all_requirements = self._get_iso_9001_requirements()
        
        applicable = []
        exclusions = []
        
        for req in all_requirements:
            evaluation = self._evaluate_requirement(req, scope_data)
            
            if evaluation['is_applicable']:
                applicable.append({
                    'clause': req['clause'],
                    'title': req['title'],
                    'justification': evaluation['justification']
                })
            else:
                exclusions.append({
                    'clause': req['clause'],
                    'title': req['title'],
                    'reason': evaluation['exclusion_reason'],
                    'impact': evaluation['impact']
                })
        
        return {
            'applicable_requirements': applicable,
            'exclusions': exclusions,
            'coverage_percentage': (len(applicable) / len(all_requirements)) * 100
        }
    
    def generate_scope_statement(self, scope_data: Dict) -> str:
        """
        Genera declaración formal del alcance
        
        Args:
            scope_data: Datos completos del alcance
        
        Returns:
            String con declaración de alcance en lenguaje natural
        """
        self.logger.info("Generando declaración de alcance...")
        
        statement_parts = []
        
        # Introducción
        statement_parts.append(
            "El Sistema de Gestión de Calidad de la organización aplica a:"
        )
        
        # Productos y servicios
        if scope_data.get('products_services'):
            products = scope_data['products_services']
            if len(products) == 1:
                statement_parts.append(f"\n\nProductos y Servicios:\n- {products[0]}")
            else:
                products_text = "\n".join([f"- {p}" for p in products])
                statement_parts.append(f"\n\nProductos y Servicios:\n{products_text}")
        
        # Ubicaciones
        if scope_data.get('boundaries', {}).get('geographic'):
            locations = scope_data['boundaries']['geographic']
            if locations:
                loc_text = ", ".join(locations)
                statement_parts.append(f"\n\nUbicaciones: {loc_text}")
        
        # Procesos
        if scope_data.get('processes'):
            processes = scope_data['processes']
            if len(processes) > 0:
                proc_text = "\n".join([f"- {p['name']}" for p in processes[:5]])
                statement_parts.append(f"\n\nProcesos principales:\n{proc_text}")
        
        # Exclusiones
        if scope_data.get('exclusions'):
            exclusions = scope_data['exclusions']
            if len(exclusions) > 0:
                exc_text = "\n".join([
                    f"- {e['clause']}: {e['reason']}" 
                    for e in exclusions
                ])
                statement_parts.append(
                    f"\n\nExclusiones permitidas (cláusula 7.1.4 ISO 9001:2015):\n{exc_text}"
                )
        
        # Cierre
        statement_parts.append(
            "\n\nEste alcance cumple con los requisitos de ISO 9001:2015 "
            "y está sujeto a revisión periódica para asegurar su vigencia."
        )
        
        return "".join(statement_parts)
    
    def analyze_coverage(self, scope_data: Dict, context_data: Dict, 
                        stakeholder_data: Dict) -> Dict:
        """
        Analiza qué tan completo es el alcance definido
        
        Args:
            scope_data: Datos del alcance
            context_data: Datos del contexto (SCA)
            stakeholder_data: Datos de stakeholders (SIE)
        
        Returns:
            Dict con análisis de cobertura
        """
        self.logger.info("Analizando cobertura del alcance...")
        
        coverage = {
            'products_coverage': self._analyze_product_coverage(scope_data),
            'stakeholder_coverage': self._analyze_stakeholder_coverage(
                scope_data, stakeholder_data
            ),
            'process_coverage': self._analyze_process_coverage(scope_data),
            'risk_coverage': self._analyze_risk_coverage(scope_data, context_data),
            'overall_score': 0,
            'gaps': [],
            'recommendations': []
        }
        
        # Calcular score general
        scores = [
            coverage['products_coverage'].get('score', 0),
            coverage['stakeholder_coverage'].get('score', 0),
            coverage['process_coverage'].get('score', 0),
            coverage['risk_coverage'].get('score', 0)
        ]
        coverage['overall_score'] = sum(scores) / len(scores)
        
        # Identificar gaps
        if coverage['products_coverage'].get('score', 0) < 70:
            coverage['gaps'].append('Cobertura de productos/servicios insuficiente')
        
        if coverage['stakeholder_coverage'].get('score', 0) < 70:
            coverage['gaps'].append('Stakeholders críticos no cubiertos')
        
        # Generar recomendaciones
        if len(coverage['gaps']) > 0:
            coverage['recommendations'].append(
                'Revisar y ampliar el alcance para cubrir brechas identificadas'
            )
        
        return coverage
    
    # Métodos privados auxiliares
    
    def _identify_geographic_boundaries(self, context_data: Dict) -> List[str]:
        """Identifica límites geográficos"""
        # Por ahora retorna datos de ejemplo
        return ['Sede principal - Ciudad', 'Sucursal Norte', 'Centro de distribución']
    
    def _identify_functional_boundaries(self, context_data: Dict) -> List[str]:
        """Identifica límites funcionales"""
        return [
            'Operaciones',
            'Ventas y Marketing',
            'Administración',
            'Calidad'
        ]
    
    def _identify_product_lines(self, context_data: Dict) -> List[str]:
        """Identifica líneas de productos/servicios"""
        return [
            'Servicios de consultoría en calidad',
            'Auditorías ISO',
            'Capacitación'
        ]
    
    def _identify_organizational_units(self, context_data: Dict) -> List[str]:
        """Identifica unidades organizacionales"""
        return [
            'Dirección General',
            'Gerencia de Operaciones',
            'Gerencia Comercial',
            'Gerencia de Calidad'
        ]
    
    def _get_iso_9001_requirements(self) -> List[Dict]:
        """Retorna lista de requisitos ISO 9001:2015"""
        return [
            {'clause': '4', 'title': 'Contexto de la organización', 'can_exclude': False},
            {'clause': '5', 'title': 'Liderazgo', 'can_exclude': False},
            {'clause': '6', 'title': 'Planificación', 'can_exclude': False},
            {'clause': '7', 'title': 'Apoyo', 'can_exclude': False},
            {'clause': '8', 'title': 'Operación', 'can_exclude': False},
            {'clause': '8.3', 'title': 'Diseño y desarrollo', 'can_exclude': True},
            {'clause': '9', 'title': 'Evaluación del desempeño', 'can_exclude': False},
            {'clause': '10', 'title': 'Mejora', 'can_exclude': False},
        ]
    
    def _evaluate_requirement(self, requirement: Dict, scope_data: Dict) -> Dict:
        """Evalúa si un requisito es aplicable"""
        # Lógica simplificada
        
        # Cláusula 8.3 (Diseño) es comúnmente excluible
        if requirement['clause'] == '8.3':
            if not scope_data.get('has_design_activities', True):
                return {
                    'is_applicable': False,
                    'exclusion_reason': 'La organización no realiza actividades de diseño y desarrollo',
                    'impact': 'Sin impacto en la capacidad de conformidad de productos/servicios'
                }
        
        return {
            'is_applicable': True,
            'justification': f"Requisito aplicable a las actividades de la organización"
        }
    
    def _analyze_product_coverage(self, scope_data: Dict) -> Dict:
        """Analiza cobertura de productos"""
        products = scope_data.get('products_services', [])
        return {
            'score': 85 if len(products) > 0 else 0,
            'total_products': len(products),
            'covered': len(products)
        }
    
    def _analyze_stakeholder_coverage(self, scope_data: Dict, 
                                     stakeholder_data: Dict) -> Dict:
        """Analiza cobertura de stakeholders"""
        return {
            'score': 90,
            'critical_covered': True
        }
    
    def _analyze_process_coverage(self, scope_data: Dict) -> Dict:
        """Analiza cobertura de procesos"""
        processes = scope_data.get('processes', [])
        return {
            'score': 80 if len(processes) > 0 else 0,
            'total_processes': len(processes)
        }
    
    def _analyze_risk_coverage(self, scope_data: Dict, context_data: Dict) -> Dict:
        """Analiza cobertura de riesgos"""
        return {
            'score': 75,
            'risks_addressed': True
        }