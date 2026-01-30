import api from './api';

const stakeholderService = {
  getAll: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/stakeholders/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/stakeholders/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/stakeholders/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/stakeholders/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/stakeholders/${id}/`);
    return response.data;
  },

  runAnalysis: async () => {
    const response = await api.post('/stakeholders/run_analysis/');
    return response.data;
  },

  getCritical: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/stakeholders/critical/', { params });
    return response.data;
  },

  getMatrix: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/stakeholders/matrix/', { params });
    return response.data;
  },

  getChangeHistory: async (id) => {
    const response = await api.get(`/stakeholders/${id}/change_history/`);
    return response.data;
  },

  updateSatisfaction: async (id, score) => {
    const response = await api.post(
      `/stakeholders/${id}/update_satisfaction/`,
      { satisfaction_score: score }
    );
    return response.data;
  },

  getChangeLogs: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/change-logs/', { params });
    return response.data;
  },

  getRecentChanges: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/change-logs/recent/', { params });
    return response.data;
  }
};

export default stakeholderService;