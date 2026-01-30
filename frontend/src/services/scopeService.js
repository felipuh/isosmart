/**
 * Servicio de Alcance (ASB) - ISO 4.3
 */
import api from './api';

const scopeService = {
  // Obtener todos los elementos del alcance
  getAll: async (params = {}) => {
    const response = await api.get('/scope/scopes/', { params });
    return response.data.results || response.data;
  },

  // Obtener el último alcance definido
  getLatest: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/scope/latest/', { params });
    return response.data;
  },

  // Obtener elemento por ID
  getById: async (id) => {
    const response = await api.get(`/scope/scopes/${id}/`);
    return response.data;
  },

  // Crear nuevo elemento
  create: async (data) => {
    const response = await api.post('/scope/scopes/', data);
    return response.data;
  },

  // Actualizar elemento
  update: async (id, data) => {
    const response = await api.put(`/scope/scopes/${id}/`, data);
    return response.data;
  },

  // Actualizar parcialmente
  patch: async (id, data) => {
    const response = await api.patch(`/scope/scopes/${id}/`, data);
    return response.data;
  },

  // Eliminar elemento
  delete: async (id) => {
    const response = await api.delete(`/scope/scopes/${id}/`);
    return response.data;
  },

  // Obtener estadísticas
  getStats: async () => {
    const response = await api.get('/scope/scopes/stats/');
    return response.data;
  },

  // Generar alcance automáticamente
  generate: async () => {
    const response = await api.post('/scope/generate/');
    return response.data;
  },

  // Obtener declaración de alcance
  getStatement: async () => {
    const response = await api.get('/scope/statement/');
    return response.data;
  },

  // Auditar alcance
  audit: async () => {
    const response = await api.post('/scope/audit/');
    return response.data;
  }
};

export default scopeService;
