import axios from 'axios';

const API_BASE = 'http://192.168.100.100/api';

const riskService = {
  async getRisks(filters = {}) {
    const params = new URLSearchParams();
    if (filters.source) params.append('source', filters.source);
    if (filters.level) params.append('level', filters.level);
    if (filters.status) params.append('status', filters.status);
    if (filters.category) params.append('category', filters.category);
    
    const response = await axios.get(`${API_BASE}/risks/?${params}`);
    return response.data;
  },

  async getRisk(id) {
    const response = await axios.get(`${API_BASE}/risks/${id}/`);
    return response.data;
  },

  async createRisk(riskData) {
    const response = await axios.post(`${API_BASE}/risks/`, riskData);
    return response.data;
  },

  async updateRisk(id, riskData) {
    const response = await axios.put(`${API_BASE}/risks/${id}/`, riskData);
    return response.data;
  },

  async deleteRisk(id) {
    const response = await axios.delete(`${API_BASE}/risks/${id}/`);
    return response.data;
  },

  async changeStatus(id, newStatus) {
    const response = await axios.post(`${API_BASE}/risks/${id}/change_status/`, { status: newStatus });
    return response.data;
  },

  async getStats() {
    const response = await axios.get(`${API_BASE}/risks/stats/`);
    return response.data;
  },

  async getByLevel() {
    const response = await axios.get(`${API_BASE}/risks/by_level/`);
    return response.data;
  },

  async getMatrixData() {
    const response = await axios.get(`${API_BASE}/risks/matrix_data/`);
    return response.data;
  },

  async getCategories() {
    const response = await axios.get(`${API_BASE}/risks/categories/`);
    return response.data;
  },
};

export default riskService;
