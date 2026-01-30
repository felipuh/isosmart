/**
 * Servicio de Objetivos de Calidad - ISO 6.2
 */
import api from './api';

const objectiveService = {
  // Obtener todos los objetivos
  getAll: async (params = {}) => {
    const response = await api.get('/objectives/', { params });
    return response.data.results || response.data;
  },

  // Obtener objetivos (alias para compatibilidad)
  getObjectives: async (params = {}) => {
    const response = await api.get('/objectives/', { params });
    return response.data.results || response.data;
  },

  // Obtener objetivo por ID
  getById: async (id) => {
    const response = await api.get(`/objectives/${id}/`);
    return response.data;
  },

  // Crear nuevo objetivo
  create: async (data) => {
    const response = await api.post('/objectives/', data);
    return response.data;
  },

  // Actualizar objetivo
  update: async (id, data) => {
    const response = await api.put(`/objectives/${id}/`, data);
    return response.data;
  },

  // Actualizar parcialmente
  patch: async (id, data) => {
    const response = await api.patch(`/objectives/${id}/`, data);
    return response.data;
  },

  // Eliminar objetivo
  delete: async (id) => {
    const response = await api.delete(`/objectives/${id}/`);
    return response.data;
  },

  // Obtener estadísticas
  getStats: async () => {
    const response = await api.get('/objectives/stats/');
    return response.data;
  },

  // Actualizar progreso
  updateProgress: async (id, currentValue) => {
    const response = await api.patch(`/objectives/${id}/`, {
      current_value: currentValue
    });
    return response.data;
  },

  // Obtener objetivos por proceso
  getByProcess: async (processId) => {
    const response = await api.get('/objectives/', {
      params: { process_id: processId }
    });
    return response.data.results || response.data;
  }
};

export default objectiveService;
