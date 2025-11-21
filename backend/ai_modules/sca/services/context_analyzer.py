import spacy
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import chromadb
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ContextAnalyzer:
    def __init__(self):
        self.nlp = spacy.load("es_core_news_lg")
        self.sentiment_model = pipeline("sentiment-analysis", 
                                       model="nlptown/bert-base-multilingual-uncased-sentiment")
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.chroma_client = chromadb.HttpClient(host='localhost', port=8002)
        self.collection = self.chroma_client.get_or_create_collection(name="context_docs")
    
    def analyze_internal_context(self, documents: list) -> dict:
        """Analiza documentos internos para extraer contexto organizacional"""
        insights = {
            'fortalezas': [],
            'debilidades': [],
            'temas_clave': [],
            'riesgos_identificados': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for doc in documents:
            # Procesamiento NLP
            doc_nlp = self.nlp(doc['content'])
            
            # Extracción de entidades
            entities = [(ent.text, ent.label_) for ent in doc_nlp.ents]
            
            # Análisis de sentimiento
            sentiment = self.sentiment_model(doc['content'][:512])[0]
            
            # Almacenar embeddings en ChromaDB
            embedding = self.embedder.encode(doc['content']).tolist()
            self.collection.add(
                embeddings=[embedding],
                documents=[doc['content']],
                metadatas=[{'source': doc['source'], 'date': doc['date']}],
                ids=[f"doc_{doc['id']}"]
            )
            
            # Clasificación de insights
            if sentiment['label'] in ['4 stars', '5 stars']:
                insights['fortalezas'].append({
                    'texto': doc['content'][:200],
                    'fuente': doc['source'],
                    'confianza': sentiment['score']
                })
            
        return insights
    
    def analyze_external_context(self, sources: list) -> dict:
        """Analiza fuentes externas para identificar tendencias y amenazas"""
        from scrapy import Selector
        import requests
        
        external_insights = {
            'tendencias_industria': [],
            'cambios_regulatorios': [],
            'riesgos_emergentes': [],
            'oportunidades': []
        }
        
        for source in sources:
            try:
                response = requests.get(source['url'], timeout=10)
                selector = Selector(text=response.text)
                
                # Extracción de contenido relevante
                headlines = selector.css('h1::text, h2::text').getall()
                
                for headline in headlines:
                    embedding = self.embedder.encode(headline).tolist()
                    # Búsqueda de similitud con contexto interno
                    results = self.collection.query(
                        query_embeddings=[embedding],
                        n_results=3
                    )
                    
                    if results['distances'][0][0] < 0.5:  # Alta similitud
                        external_insights['tendencias_industria'].append({
                            'titulo': headline,
                            'relevancia': 1 - results['distances'][0][0],
                            'fuente': source['url']
                        })
                        
            except Exception as e:
                logger.error(f"Error procesando {source['url']}: {e}")
                
        return external_insights
        