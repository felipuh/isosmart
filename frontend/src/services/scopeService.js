import api from './api';

const scopeService = {
  runAnalysis: async (data = {}) => {
    const response = await api.post('/analyze/', data);
    return response.data;
  },

  getLatest: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/latest/', { params });
    return response.data;
  },

  getAll: async (status = null) => {
    const params = status ? { status } : {};
    const response = await api.get('/scopes/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/scopes/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/scopes/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/scopes/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/scopes/${id}/`);
    return response.data;
  },

  getActive: async () => {
    const response = await api.get('/scopes/active/');
    return response.data;
  },

  approve: async (id) => {
    const response = await api.post(`/scopes/${id}/approve/`);
    return response.data;
  },

  activate: async (id) => {
    const response = await api.post(`/scopes/${id}/activate/`);
    return response.data;
  },

  getStats: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/scopes/stats/', { params });
    return response.data;
  },

  // Procesos
  getProcesses: async (scopeId) => {
    const params = scopeId ? { scope_definition: scopeId } : {};
    const response = await api.get('/processes/', { params });
    return response.data;
  },

  createProcess: async (data) => {
    const response = await api.post('/processes/', data);
    return response.data;
  },

  updateProcess: async (id, data) => {
    const response = await api.put(`/processes/${id}/`, data);
    return response.data;
  },

  deleteProcess: async (id) => {
    const response = await api.delete(`/processes/${id}/`);
    return response.data;
  },

  // Ubicaciones
  getLocations: async (scopeId) => {
    const params = scopeId ? { scope_definition: scopeId } : {};
    const response = await api.get('/locations/', { params });
    return response.data;
  },

  createLocation: async (data) => {
    const response = await api.post('/locations/', data);
    return response.data;
  },

  updateLocation: async (id, data) => {
    const response = await api.put(`/locations/${id}/`, data);
    return response.data;
  },

  deleteLocation: async (id) => {
    const response = await api.delete(`/locations/${id}/`);
    return response.data;
  }
};

export default scopeService;