import axios from 'axios';

const API_BASE_URL = 'http://192.168.100.100/api/sie';

const stakeholderService = {
  // Obtener todos los stakeholders
  getAll: async () => {
    const response = await axios.get(`${API_BASE_URL}/stakeholders/`);
    return response.data;
  },

  // Obtener un stakeholder específico
  getById: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/stakeholders/${id}/`);
    return response.data;
  },

  // Crear nuevo stakeholder
  create: async (data) => {
    const response = await axios.post(`${API_BASE_URL}/stakeholders/`, data);
    return response.data;
  },

  // Actualizar stakeholder
  update: async (id, data) => {
    const response = await axios.put(`${API_BASE_URL}/stakeholders/${id}/`, data);
    return response.data;
  },

  // Eliminar stakeholder
  delete: async (id) => {
    const response = await axios.delete(`${API_BASE_URL}/stakeholders/${id}/`);
    return response.data;
  },

  // Ejecutar análisis de IA
  runAnalysis: async () => {
    const response = await axios.post(`${API_BASE_URL}/stakeholders/run_analysis/`);
    return response.data;
  },

  // Obtener stakeholders críticos
  getCritical: async () => {
    const response = await axios.get(`${API_BASE_URL}/stakeholders/critical/`);
    return response.data;
  },

  // Obtener matriz poder/interés
  getMatrix: async () => {
    const response = await axios.get(`${API_BASE_URL}/stakeholders/matrix/`);
    return response.data;
  },

  // Obtener historial de cambios
  getChangeHistory: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/stakeholders/${id}/change_history/`);
    return response.data;
  },

  // Actualizar satisfacción
  updateSatisfaction: async (id, score) => {
    const response = await axios.post(
      `${API_BASE_URL}/stakeholders/${id}/update_satisfaction/`,
      { satisfaction_score: score }
    );
    return response.data;
  },

  // Obtener logs de cambios
  getChangeLogs: async () => {
    const response = await axios.get(`${API_BASE_URL}/change-logs/`);
    return response.data;
  },

  // Obtener cambios recientes
  getRecentChanges: async () => {
    const response = await axios.get(`${API_BASE_URL}/change-logs/recent/`);
    return response.data;
  }
};

export default stakeholderService;