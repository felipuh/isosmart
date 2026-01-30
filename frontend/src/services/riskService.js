/**
 * Servicio de Riesgos - ISO 6.1
 */
import api from './api';

const riskService = {
  // Obtener todos los riesgos
  getAll: async (params = {}) => {
    const response = await api.get('/risks/', { params });
    return response.data.results || response.data;
  },

  // Obtener riesgos (alias para compatibilidad)
  getRisks: async (params = {}) => {
    const response = await api.get('/risks/', { params });
    return response.data.results || response.data;
  },

  // Obtener riesgo por ID
  getById: async (id) => {
    const response = await api.get(`/risks/${id}/`);
    return response.data;
  },

  // Crear nuevo riesgo
  create: async (data) => {
    const response = await api.post('/risks/', data);
    return response.data;
  },

  // Actualizar riesgo
  update: async (id, data) => {
    const response = await api.put(`/risks/${id}/`, data);
    return response.data;
  },

  // Actualizar parcialmente
  patch: async (id, data) => {
    const response = await api.patch(`/risks/${id}/`, data);
    return response.data;
  },

  // Eliminar riesgo
  delete: async (id) => {
    const response = await api.delete(`/risks/${id}/`);
    return response.data;
  },

  // Obtener estadísticas
  getStats: async () => {
    const response = await api.get('/risks/stats/');
    return response.data;
  },

  // Obtener matriz de riesgos
  getMatrix: async () => {
    const response = await api.get('/risks/matrix/');
    return response.data;
  },

  // Evaluar riesgo
  evaluate: async (id) => {
    const response = await api.post(`/risks/${id}/evaluate/`);
    return response.data;
  }
};

export default riskService;
