import api from './api';

const riskService = {
  async getRisks(filters = {}) {
    const params = new URLSearchParams();
    if (filters.organization) params.append('organization', filters.organization);
    if (filters.source) params.append('source', filters.source);
    if (filters.level) params.append('level', filters.level);
    if (filters.status) params.append('status', filters.status);
    if (filters.category) params.append('category', filters.category);
    
    const response = await api.get(`/risks/?${params}`);
    return response.data;
  },

  async getRisk(id) {
    const response = await api.get(`/risks/${id}/`);
    return response.data;
  },

  async createRisk(riskData) {
    const response = await api.post('/risks/', riskData);
    return response.data;
  },

  async updateRisk(id, riskData) {
    const response = await api.put(`/risks/${id}/`, riskData);
    return response.data;
  },

  async deleteRisk(id) {
    const response = await api.delete(`/risks/${id}/`);
    return response.data;
  },

  async changeStatus(id, newStatus) {
    const response = await api.post(`/risks/${id}/change_status/`, { status: newStatus });
    return response.data;
  },

  async getStats(organizationId = null) {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/risks/stats/', { params });
    return response.data;
  },

  async getByLevel() {
    const response = await api.get('/risks/by_level/');
    return response.data;
  },

  async getMatrixData() {
    const response = await api.get('/risks/matrix_data/');
    return response.data;
  },

  async getCategories() {
    const response = await api.get('/risks/categories/');
    return response.data;
  },
};

export default riskService;
