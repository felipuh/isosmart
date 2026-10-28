/**
 * Servicio de Stakeholders (SIE) - ISO 4.2
 */
import api from './api';

const stakeholderService = {
  // Obtener todos los stakeholders
  getAll: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
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

  // Ejecutar análisis de stakeholders con IA
  runAnalysis: async () => {
    const response = await api.post('/sie/stakeholders/run_analysis/');
    return response.data;
  },

  // Obtener stakeholders críticos
  getCritical: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/stakeholders/critical/', { params });
    return response.data;
  },

  // Obtener matriz poder/interés
  getMatrix: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/stakeholders/matrix/', { params });
    return response.data;
  },

  // Obtener historial de cambios de un stakeholder
  getChangeHistory: async (id) => {
    const response = await api.get(`/sie/stakeholders/${id}/change_history/`);
    return response.data;
  },

  // Actualizar satisfacción
  updateSatisfaction: async (id, score) => {
    const response = await api.post(
      `/sie/stakeholders/${id}/update_satisfaction/`,
      { satisfaction_score: score }
    );
    return response.data;
  },

  // Obtener logs de cambios
  getChangeLogs: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/sie/change-logs/', { params });
    return response.data.results || response.data;
  },

  // Obtener cambios recientes
  getRecentChanges: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/change-logs/recent/', { params });
    return response.data;
  },

  // Obtener estadísticas
  getStats: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/sie/stakeholders/stats/', { params });
    return response.data;
  }
};

export default stakeholderService;
