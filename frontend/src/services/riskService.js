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
  getStats: async (organizationId = null) => {
    const params = organizationId ? { organization_id: organizationId } : {};
    const response = await api.get('/risks/stats/', { params });
    return response.data;
  },

  // Obtener matriz de riesgos
  getMatrix: async (organizationId = null) => {
    const params = organizationId ? { organization_id: organizationId } : {};
    const response = await api.get('/risks/matrix/', { params });
    return response.data;
  },

  // Aliases de compatibilidad con componentes legacy
  getMatrixData: async (organizationId = null) => {
    const params = organizationId ? { organization_id: organizationId } : {};
    const response = await api.get('/risks/matrix/', { params });
    return response.data;
  },

  createRisk: async (data) => {
    const response = await api.post('/risks/', data);
    return response.data;
  },

  updateRisk: async (id, data) => {
    const response = await api.put(`/risks/${id}/`, data);
    return response.data;
  },

  deleteRisk: async (id) => {
    const response = await api.delete(`/risks/${id}/`);
    return response.data;
  },

  changeStatus: async (id, status) => {
    const response = await api.post(`/risks/${id}/change_status/`, { status });
    return response.data;
  }
};

export default riskService;
