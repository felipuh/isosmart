import axios from 'axios';

const API_BASE_URL = 'http://192.168.100.100/api/scope';

const scopeService = {
  runAnalysis: async (data = {}) => {
    const response = await axios.post(API_BASE_URL + '/analyze/', data);
    return response.data;
  },

  getLatest: async () => {
    const response = await axios.get(API_BASE_URL + '/latest/');
    return response.data;
  },

  getAll: async (status = null) => {
    const params = status ? { status } : {};
    const response = await axios.get(API_BASE_URL + '/scopes/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await axios.get(API_BASE_URL + '/scopes/' + id + '/');
    return response.data;
  },

  create: async (data) => {
    const response = await axios.post(API_BASE_URL + '/scopes/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await axios.put(API_BASE_URL + '/scopes/' + id + '/', data);
    return response.data;
  },

  delete: async (id) => {
    const response = await axios.delete(API_BASE_URL + '/scopes/' + id + '/');
    return response.data;
  },

  getActive: async () => {
    const response = await axios.get(API_BASE_URL + '/scopes/active/');
    return response.data;
  },

  approve: async (id) => {
    const response = await axios.post(API_BASE_URL + '/scopes/' + id + '/approve/');
    return response.data;
  },

  activate: async (id) => {
    const response = await axios.post(API_BASE_URL + '/scopes/' + id + '/activate/');
    return response.data;
  },

  getStats: async () => {
    const response = await axios.get(API_BASE_URL + '/scopes/stats/');
    return response.data;
  },

  // Procesos
  getProcesses: async (scopeId) => {
    const params = scopeId ? { scope_definition: scopeId } : {};
    const response = await axios.get(API_BASE_URL + '/processes/', { params });
    return response.data;
  },

  createProcess: async (data) => {
    const response = await axios.post(API_BASE_URL + '/processes/', data);
    return response.data;
  },

  updateProcess: async (id, data) => {
    const response = await axios.put(API_BASE_URL + '/processes/' + id + '/', data);
    return response.data;
  },

  deleteProcess: async (id) => {
    const response = await axios.delete(API_BASE_URL + '/processes/' + id + '/');
    return response.data;
  },

  // Ubicaciones
  getLocations: async (scopeId) => {
    const params = scopeId ? { scope_definition: scopeId } : {};
    const response = await axios.get(API_BASE_URL + '/locations/', { params });
    return response.data;
  },

  createLocation: async (data) => {
    const response = await axios.post(API_BASE_URL + '/locations/', data);
    return response.data;
  },

  updateLocation: async (id, data) => {
    const response = await axios.put(API_BASE_URL + '/locations/' + id + '/', data);
    return response.data;
  },

  deleteLocation: async (id) => {
    const response = await axios.delete(API_BASE_URL + '/locations/' + id + '/');
    return response.data;
  }
};

export default scopeService;