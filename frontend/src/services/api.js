import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.100.100/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const apiService = {
  getDashboardSummary: () => api.get('/dashboard/'),
  getLatestContextAnalysis: () => api.get('/context/latest/'),
  triggerContextAnalysis: () => api.post('/context/analyze/'),
  getRiskMatrix: (params = {}) => api.get('/risks/', { params }),
  healthCheck: () => api.get('/health', { baseURL: 'http://192.168.100.100' }),
};

export default api;
