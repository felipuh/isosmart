/**
 * Servicio de Contexto (SCA) - ISO 4.1
 */
import api from './api';

const contextService = {
  // Obtener último análisis de contexto
  getLatest: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/sca/latest/', { params });
    return response.data;
  },

  // Ejecutar nuevo análisis
  triggerAnalysis: async (organizationId = null) => {
    const data = organizationId ? { organization: organizationId } : {};
    const response = await api.post('/sca/analyze/', data);
    return response.data;
  },

  // Obtener historial de análisis
  getHistory: async (page = 1) => {
    const response = await api.get('/sca/history/', { params: { page } });
    return response.data;
  },

  // Obtener resumen del dashboard
  getDashboardSummary: async () => {
    const response = await api.get('/dashboard/');
    return response.data;
  },

  // Obtener matriz de riesgos
  getRiskMatrix: async () => {
    const response = await api.get('/risks/');
    return response.data.results || response.data;
  }
};

export default contextService;
