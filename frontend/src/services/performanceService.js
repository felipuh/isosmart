import api from './api';

const performanceService = {
  getIndicators: (params = {}) => api.get('/performance/indicators/', { params }),
  getMeasurements: (params = {}) => api.get('/performance/measurements/', { params }),
  getMeasurementStats: () => api.get('/performance/measurements/dashboard_stats/'),
  getAudits: (params = {}) => api.get('/performance/audits/', { params }),
  getFindings: (params = {}) => api.get('/performance/findings/', { params }),
  getReviews: (params = {}) => api.get('/performance/reviews/', { params }),
};

export default performanceService;
