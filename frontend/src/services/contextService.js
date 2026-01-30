import api from './api';

const contextService = {
  // Obtener último análisis de contexto
  getLatest: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get(`/context/latest/`, { params });
    return response.data;
  },

  // Ejecutar nuevo análisis
  triggerAnalysis: async (organizationId = null) => {
    const data = organizationId ? { organization: organizationId } : {};
    const response = await api.post(`/context/analyze/`, data);
    return response.data;
  },

  // Obtener resumen del dashboard
  getDashboardSummary: async () => {
    const response = await api.get(`/dashboard/`);
    return response.data;
  },

  // Obtener matriz de riesgos
  getRiskMatrix: async () => {
    const response = await api.get(`/risks/`);
    return response.data;
  }
};

export default contextService;