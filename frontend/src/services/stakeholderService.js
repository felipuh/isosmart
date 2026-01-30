/**
 * Servicio de Stakeholders (SIE) - ISO 4.2
 */
import api from './api';

const stakeholderService = {
  // Obtener todos los stakeholders
  getAll: async (params = {}) => {
    const response = await api.get('/sie/stakeholders/', { params });
    return response.data.results || response.data;
  },

  // Obtener stakeholder por ID
  getById: async (id) => {
    const response = await api.get(`/sie/stakeholders/${id}/`);
    return response.data;
  },

  // Crear nuevo stakeholder
  create: async (data) => {
    const response = await api.post('/sie/stakeholders/', data);
    return response.data;
  },

  // Actualizar stakeholder
  update: async (id, data) => {
    const response = await api.put(`/sie/stakeholders/${id}/`, data);
    return response.data;
  },

  // Actualizar parcialmente
  patch: async (id, data) => {
    const response = await api.patch(`/sie/stakeholders/${id}/`, data);
    return response.data;
  },

  // Eliminar stakeholder
  delete: async (id) => {
    const response = await api.delete(`/sie/stakeholders/${id}/`);
    return response.data;
  },

  // Obtener estadísticas
  getStats: async () => {
    const response = await api.get('/sie/stakeholders/stats/');
    return response.data;
  },

  // Ejecutar análisis de stakeholders
  analyze: async () => {
    const response = await api.post('/sie/analyze/');
    return response.data;
  },

  // Obtener matriz de poder/interés
  getMatrix: async () => {
    const response = await api.get('/sie/stakeholders/matrix/');
    return response.data;
  }
};

export default stakeholderService;
