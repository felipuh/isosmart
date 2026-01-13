import axios from 'axios';

const API_BASE_URL = 'http://192.168.100.100/api/sie';

const stakeholderService = {
  getAll: async () => {
    const response = await axios.get(API_BASE_URL + '/stakeholders/');
    return response.data;
  },

  getById: async (id) => {
    const response = await axios.get(API_BASE_URL + '/stakeholders/' + id + '/');
    return response.data;
  },

  create: async (data) => {
    const response = await axios.post(API_BASE_URL + '/stakeholders/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await axios.put(API_BASE_URL + '/stakeholders/' + id + '/', data);
    return response.data;
  },

  delete: async (id) => {
    const response = await axios.delete(API_BASE_URL + '/stakeholders/' + id + '/');
    return response.data;
  },

  runAnalysis: async () => {
    const response = await axios.post(API_BASE_URL + '/stakeholders/run_analysis/');
    return response.data;
  },

  getCritical: async () => {
    const response = await axios.get(API_BASE_URL + '/stakeholders/critical/');
    return response.data;
  },

  getMatrix: async () => {
    const response = await axios.get(API_BASE_URL + '/stakeholders/matrix/');
    return response.data;
  },

  getChangeHistory: async (id) => {
    const response = await axios.get(API_BASE_URL + '/stakeholders/' + id + '/change_history/');
    return response.data;
  },

  updateSatisfaction: async (id, score) => {
    const response = await axios.post(
      API_BASE_URL + '/stakeholders/' + id + '/update_satisfaction/',
      { satisfaction_score: score }
    );
    return response.data;
  },

  getChangeLogs: async () => {
    const response = await axios.get(API_BASE_URL + '/change-logs/');
    return response.data;
  },

  getRecentChanges: async () => {
    const response = await axios.get(API_BASE_URL + '/change-logs/recent/');
    return response.data;
  }
};

export default stakeholderService;