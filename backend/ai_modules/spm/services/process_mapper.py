import tensorflow as tf
from tensorflow import keras
import pandas as pd

class ProcessMapper:
    def __init__(self):
        self.risk_model = self.load_risk_prediction_model()
    
    def load_risk_prediction_model(self):
        """Carga modelo de predicción de riesgos en procesos"""
        # Modelo simple de ejemplo - mejorar con datos históricos
        model = keras.Sequential([
            keras.layers.Dense(64, activation='relu', input_shape=(10,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(3, activation='softmax')  # bajo, medio, alto
        ])
        model.compile(optimizer='adam', loss='categorical_crossentropy')
        return model
    
    def map_process(self, process_data: dict) -> dict:
        """Genera mapa completo de proceso con KPIs y responsables"""
        process_map = {
            'id': process_data['id'],
            'nombre': process_data['nombre'],
            'entradas': process_data['inputs'],
            'salidas': process_data['outputs'],
            'actividades': [],
            'responsables': [],
            'kpis': [],
            'riesgos': []
        }
        
        # Asignación inteligente de responsables basada en roles
        for activity in process_data['activities']:
            best_match = self.assign_responsible(activity, process_data['available_roles'])
            process_map['responsables'].append({
                'actividad': activity['nombre'],
                'responsable': best_match['persona'],
                'confianza': best_match['score']
            })
        
        # Generación automática de KPIs
        suggested_kpis = self.generate_kpis(process_data)
        process_map['kpis'] = suggested_kpis
        
        # Predicción de riesgos
        risk_features = self.extract_risk_features(process_data)
        risk_prediction = self.risk_model.predict(np.array([risk_features]))
        process_map['riesgos'] = self.interpret_risk_prediction(risk_prediction, process_data)
        
        return process_map
    
    def generate_kpis(self, process_data: dict) -> list:
        """Genera KPIs relevantes según tipo de proceso"""
        kpi_templates = {
            'core': [
                {'nombre': 'Tiempo de ciclo', 'formula': 'sum(duracion_actividades)', 'unidad': 'horas'},
                {'nombre': 'Tasa de defectos', 'formula': 'defectos/total', 'unidad': '%'},
                {'nombre': 'Satisfacción del cliente', 'formula': 'avg(encuestas)', 'unidad': 'escala 1-5'}
            ],
            'soporte': [
                {'nombre': 'Costo por transacción', 'formula': 'costo_total/num_transacciones', 'unidad': 'USD'},
                {'nombre': 'Disponibilidad', 'formula': 'uptime/total_time', 'unidad': '%'}
            ]
        }
        
        return kpi_templates.get(process_data['tipo'], [])
    
    def assign_responsible(self, activity: dict, available_roles: list) -> dict:
        """Asigna responsable óptimo usando similitud semántica"""
        from sentence_transformers import util
        
        activity_embedding = self.embedder.encode(activity['descripcion'])
        best_match = None
        best_score = 0
        
        for role in available_roles:
            role_embedding = self.embedder.encode(role['competencias'])
            similarity = util.cos_sim(activity_embedding, role_embedding).item()
            
            if similarity > best_score:
                best_score = similarity
                best_match = role
        
        return {'persona': best_match['nombre'], 'score': best_score}