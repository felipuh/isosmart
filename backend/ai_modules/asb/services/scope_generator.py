import graphviz
from pydantic import BaseModel, validator
from typing import List, Optional

class ScopeElement(BaseModel):
    proceso: str
    incluido: bool
    justificacion: Optional[str]
    clausula_iso: str
    
    @validator('justificacion')
    def validate_exclusion(cls, v, values):
        if not values.get('incluido') and not v:
            raise ValueError("Exclusiones requieren justificación")
        return v

class ScopeBuilder:
    def __init__(self):
        self.scope_elements = []
        
    def generate_scope_diagram(self, processes: List[dict]) -> str:
        """Genera diagrama de alcance usando Graphviz"""
        dot = graphviz.Digraph(comment='Alcance del SGC')
        dot.attr(rankdir='LR')
        
        # Agrupar por tipo
        with dot.subgraph(name='cluster_core') as c:
            c.attr(label='Procesos Core')
            c.attr(color='blue')
            for p in [p for p in processes if p['tipo'] == 'core']:
                c.node(p['id'], p['nombre'], shape='box', style='filled', fillcolor='lightblue')
        
        with dot.subgraph(name='cluster_support') as c:
            c.attr(label='Procesos de Soporte')
            c.attr(color='green')
            for p in [p for p in processes if p['tipo'] == 'soporte']:
                c.node(p['id'], p['nombre'], shape='ellipse', style='filled', fillcolor='lightgreen')
        
        # Agregar relaciones
        for p in processes:
            for dep in p.get('dependencias', []):
                dot.edge(p['id'], dep)
        
        # Guardar diagrama
        output_path = '/home/aplicacion/projects/isosmart/data/scope_diagram'
        dot.render(output_path, format='png', cleanup=True)
        
        return f"{output_path}.png"
    
    def audit_scope_completeness(self, current_scope: dict) -> dict:
        """Audita completitud del alcance vs requisitos ISO"""
        required_clauses = ['4.1', '4.2', '4.3', '4.4', '5.1', '5.2', '5.3', 
                           '6.1', '6.2', '6.3', '7.1', '7.2', '7.3', '7.4', '7.5',
                           '8.1', '8.2', '8.3', '8.4', '8.5', '8.6', '8.7',
                           '9.1', '9.2', '9.3', '10.1', '10.2', '10.3']
        
        coverage = {}
        gaps = []
        
        for clause in required_clauses:
            processes_covering = [p for p in current_scope['processes'] 
                                 if clause in p.get('clausulas_cubiertas', [])]
            coverage[clause] = len(processes_covering)
            
            if len(processes_covering) == 0:
                gaps.append({
                    'clausula': clause,
                    'severity': 'critical',
                    'action': f'Definir proceso que cubra cláusula {clause}'
                })
        
        return {
            'coverage_percentage': (len([c for c in coverage.values() if c > 0]) / len(required_clauses)) * 100,
            'gaps': gaps,
            'status': 'compliant' if len(gaps) == 0 else 'non_compliant'
        }