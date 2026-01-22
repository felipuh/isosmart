import axios from 'axios';

const API_BASE = 'http://192.168.100.100/api';

const objectiveService = {
  async getObjectives(filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.source) params.append('source', filters.source);
    
    const response = await axios.get(`${API_BASE}/objectives/?${params}`);
    return response.data;
  },

  async getObjective(id) {
    const response = await axios.get(`${API_BASE}/objectives/${id}/`);
    return response.data;
  },

  async createObjective(data) {
    const response = await axios.post(`${API_BASE}/objectives/`, data);
    return response.data;
  },

  async updateObjective(id, data) {
    const response = await axios.put(`${API_BASE}/objectives/${id}/`, data);
    return response.data;
  },

  async deleteObjective(id) {
    const response = await axios.delete(`${API_BASE}/objectives/${id}/`);
    return response.data;
  },

  async updateProgress(id, currentValue) {
    const response = await axios.post(`${API_BASE}/objectives/${id}/update_progress/`, {
      current_value: currentValue
    });
    return response.data;
  },

  async getStats() {
    const response = await axios.get(`${API_BASE}/objectives/stats/`);
    return response.data;
  },

  async getDashboardData() {
    const response = await axios.get(`${API_BASE}/objectives/dashboard_data/`);
    return response.data;
  }
};

export default objectiveService;
