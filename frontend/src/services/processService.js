/**
 * Servicio de Procesos (SPM) - ISO 4.4
 */
import api from './api';

const processService = {
  // Obtener todos los procesos
  getAll: async (params = {}) => {
    const response = await api.get('/processes/maps/', { params });
    return response.data.results || response.data;
  },

  // Obtener proceso por ID
  getById: async (id) => {
    const response = await api.get(`/processes/maps/${id}/`);
    return response.data;
  },

  // Crear nuevo proceso
  create: async (data) => {
    const response = await api.post('/processes/maps/', data);
    return response.data;
  },

  // Actualizar proceso
  update: async (id, data) => {
    const response = await api.put(`/processes/maps/${id}/`, data);
    return response.data;
  },

  // Actualizar parcialmente
  patch: async (id, data) => {
    const response = await api.patch(`/processes/maps/${id}/`, data);
    return response.data;
  },

  // Eliminar proceso
  delete: async (id) => {
    const response = await api.delete(`/processes/maps/${id}/`);
    return response.data;
  },

  // Obtener estadísticas
  getStats: async () => {
    const response = await api.get('/processes/maps/stats/');
    return response.data;
  },

  // Mapear proceso automáticamente
  mapProcess: async (data) => {
    const response = await api.post('/processes/map/', data);
    return response.data;
  },

  // Obtener interacciones entre procesos
  getInteractions: async () => {
    const response = await api.get('/processes/interactions/');
    return response.data;
  },

  // Analizar riesgos del proceso
  analyzeRisks: async (processId) => {
    const response = await api.post(`/processes/maps/${processId}/analyze-risks/`);
    return response.data;
  }
};

export default processService;
