import api from './api';

const objectiveService = {
  async getObjectives(filters = {}) {
    const params = new URLSearchParams();
    if (filters.organization) params.append('organization', filters.organization);
    if (filters.status) params.append('status', filters.status);
    if (filters.source) params.append('source', filters.source);
    
    const response = await api.get(`/objectives/?${params}`);
    return response.data;
  },

  async getObjective(id) {
    const response = await api.get(`/objectives/${id}/`);
    return response.data;
  },

  async createObjective(data) {
    const response = await api.post(`/objectives/`, data);
    return response.data;
  },

  async updateObjective(id, data) {
    const response = await api.put(`/objectives/${id}/`, data);
    return response.data;
  },

  async deleteObjective(id) {
    const response = await api.delete(`/objectives/${id}/`);
    return response.data;
  },

  async updateProgress(id, currentValue) {
    const response = await api.post(`/objectives/${id}/update_progress/`, {
      current_value: currentValue
    });
    return response.data;
  },

  async getStats(organizationId = null) {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get(`/objectives/stats/`, { params });
    return response.data;
  },

  async getDashboardData() {
    const response = await api.get(`/objectives/dashboard_data/`);
    return response.data;
  }
};

export default objectiveService;
