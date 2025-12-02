import axios from 'axios';

const API_BASE_URL = 'http://192.168.100.100/api';

const contextService = {
  // Obtener último análisis de contexto
  getLatest: async () => {
    const response = await axios.get(`${API_BASE_URL}/context/latest/`);
    return response.data;
  },

  // Ejecutar nuevo análisis
  triggerAnalysis: async () => {
    const response = await axios.post(`${API_BASE_URL}/context/analyze/`);
    return response.data;
  },

  // Obtener resumen del dashboard
  getDashboardSummary: async () => {
    const response = await axios.get(`${API_BASE_URL}/dashboard/`);
    return response.data;
  },

  // Obtener matriz de riesgos
  getRiskMatrix: async () => {
    const response = await axios.get(`${API_BASE_URL}/risks/`);
    return response.data;
  }
};

export default contextService;