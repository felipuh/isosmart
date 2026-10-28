import networkx as nx
from sklearn.cluster import DBSCAN
import numpy as np

class StakeholderMapper:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    def build_stakeholder_network(self, stakeholders: list) -> nx.DiGraph:
        """Construye grafo de relaciones entre partes interesadas"""
        for sh in stakeholders:
            self.graph.add_node(sh['id'], **sh['attributes'])
            
            # Agregar relaciones
            for relation in sh.get('relations', []):
                self.graph.add_edge(
                    sh['id'], 
                    relation['target'],
                    weight=relation['strength'],
                    type=relation['type']
                )
        
        return self.graph
    
    def calculate_influence(self) -> dict:
        """Calcula métricas de influencia usando centralidad"""
        betweenness = nx.betweenness_centrality(self.graph)
        pagerank = nx.pagerank(self.graph)
        degree = dict(self.graph.degree())
        
        influence_scores = {}
        for node in self.graph.nodes():
            influence_scores[node] = {
                'betweenness': betweenness[node],
                'pagerank': pagerank[node],
                'connections': degree[node],
                'total_score': (betweenness[node] + pagerank[node] + degree[node]/10) / 3
            }
        
        return influence_scores
    
    def detect_expectation_changes(self, historical_data: list) -> list:
        """Detecta cambios significativos en expectativas usando embeddings"""
        changes = []
        
        for stakeholder_id, history in historical_data.items():
            embeddings = [self.embedder.encode(text) for text in history['expectations']]
            
            # Clustering para detectar cambios de patrón
            clustering = DBSCAN(eps=0.3, min_samples=2).fit(embeddings)
            
            if len(set(clustering.labels_)) > 1:  # Múltiples clusters = cambio
                changes.append({
                    'stakeholder_id': stakeholder_id,
                    'change_detected': True,
                    'severity': 'high',
                    'recommendation': 'Reunión de alineación requerida'
                })
        
        return changes