import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const ContextDashboard = () => {
  const [contextData, setContextData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchContextAnalysis();
    const interval = setInterval(fetchContextAnalysis, 300000); // Cada 5 min
    return () => clearInterval(interval);
  }, []);

  const fetchContextAnalysis = async () => {
    try {
      const response = await axios.get('/api/ai/context-analysis/latest');
      setContextData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching context:', error);
    }
  };

  const triggerManualAnalysis = async () => {
    setLoading(true);
    await axios.post('/api/ai/trigger-context-analysis');
    setTimeout(fetchContextAnalysis, 5000); // Esperar 5 seg
  };

  if (loading) return <div>Analizando contexto organizacional...</div>;

  return (
    <div className="context-dashboard">
      <h2>Análisis de Contexto Inteligente (ISO 4.1)</h2>
      
      <div className="insights-grid">
        <div className="card">
          <h3>Fortalezas Identificadas</h3>
          <ul>
            {contextData.internal_insights.fortalezas.map((f, i) => (
              <li key={i}>
                {f.texto} <span className="confidence">({(f.confianza * 100).toFixed(0)}%)</span>
              </li>
            ))}
          </ul>
        </div>
        
        <div className="card">
          <h3>Tendencias Externas Relevantes</h3>
          <ul>
            {contextData.external_insights.tendencias_industria.map((t, i) => (
              <li key={i}>
                <strong>{t.titulo}</strong>
                <p>Relevancia: {(t.relevancia * 100).toFixed(0)}%</p>
              </li>
            ))}
          </ul>
        </div>
        
        <div className="card">
          <h3>Riesgos Emergentes</h3>
          <ul>
            {contextData.internal_insights.riesgos_identificados.map((r, i) => (
              <li key={i} className="risk-item">{r.texto}</li>
            ))}
          </ul>
        </div>
      </div>
      
      <button onClick={triggerManualAnalysis} className="btn-primary">
        Actualizar Análisis
      </button>
    </div>
  );
};

export default ContextDashboard;