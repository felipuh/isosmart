import axios from 'axios';

const API_BASE_URL = 'http://192.168.100.100/api/scope';

const scopeService = {
  // Ejecutar análisis de alcance
  runAnalysis: async (data = {}) => {
    const response = await axios.post(`${API_BASE_URL}/analyze/`, data);
    return response.data;
  },

  // Obtener último alcance
  getLatest: async () => {
    const response = await axios.get(`${API_BASE_URL}/latest/`);
    return response.data;
  },

  // Obtener todas las definiciones de alcance
  getAll: async (status = null) => {
    const params = status ? { status } : {};
    const response = await axios.get(`${API_BASE_URL}/scopes/`, { params });
    return response.data;
  },

  // Obtener alcance por ID
  getById: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/scopes/${id}/`);
    return response.data;
  },

  // Obtener alcance activo
  getActive: async () => {
    const response = await axios.get(`${API_BASE_URL}/scopes/active/`);
    return response.data;
  },

  // Aprobar alcance
  approve: async (id) => {
    const response = await axios.post(`${API_BASE_URL}/scopes/${id}/approve/`);
    return response.data;
  },

  // Activar alcance
  activate: async (id) => {
    const response = await axios.post(`${API_BASE_URL}/scopes/${id}/activate/`);
    return response.data;
  },

  // Obtener estadísticas
  getStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/scopes/stats/`);
    return response.data;
  },

  // Obtener procesos de un alcance
  getProcesses: async (scopeId) => {
    const response = await axios.get(`${API_BASE_URL}/processes/`, {
      params: { scope_id: scopeId }
    });
    return response.data;
  },

  // Obtener ubicaciones de un alcance
  getLocations: async (scopeId) => {
    const response = await axios.get(`${API_BASE_URL}/locations/`, {
      params: { scope_id: scopeId }
    });
    return response.data;
  }
};

export default scopeService;