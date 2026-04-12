// features/performance/api/performanceApi.js
import api from '../../../services/api';

const API_URL = '/performance';

// ==================== INDICATORS ====================
export const getIndicators = async (params = {}) => {
  const response = await api.get(`${API_URL}/indicators/`, { params });
  return response.data;
};

export const createIndicator = async (data) => {
  const response = await api.post(`${API_URL}/indicators/`, data);
  return response.data;
};

export const updateIndicator = async (id, data) => {
  const response = await api.put(`${API_URL}/indicators/${id}/`, data);
  return response.data;
};

export const deleteIndicator = async (id) => {
  const response = await api.delete(`${API_URL}/indicators/${id}/`);
  return response.data;
};

// ==================== MEASUREMENTS ====================
export const getMeasurements = async (params = {}) => {
  const response = await api.get(`${API_URL}/measurements/`, { params });
  return response.data;
};

export const createMeasurement = async (data) => {
  const response = await api.post(`${API_URL}/measurements/`, data);
  return response.data;
};

export const updateMeasurement = async (id, data) => {
  const response = await api.put(`${API_URL}/measurements/${id}/`, data);
  return response.data;
};

export const deleteMeasurement = async (id) => {
  const response = await api.delete(`${API_URL}/measurements/${id}/`);
  return response.data;
};

export const getMeasurementStats = async (organizationId) => {
  const response = await api.get(`${API_URL}/measurements/dashboard_stats/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== ANALYSES ====================
export const getAnalyses = async (params = {}) => {
  const response = await api.get(`${API_URL}/analyses/`, { params });
  return response.data;
};

export const createAnalysis = async (data) => {
  const response = await api.post(`${API_URL}/analyses/`, data);
  return response.data;
};

export const updateAnalysis = async (id, data) => {
  const response = await api.put(`${API_URL}/analyses/${id}/`, data);
  return response.data;
};

export const deleteAnalysis = async (id) => {
  const response = await api.delete(`${API_URL}/analyses/${id}/`);
  return response.data;
};

// ==================== AUDITS ====================
export const getAudits = async (params = {}) => {
  const response = await api.get(`${API_URL}/audits/`, { params });
  return response.data;
};

export const createAudit = async (data) => {
  const response = await api.post(`${API_URL}/audits/`, data);
  return response.data;
};

export const updateAudit = async (id, data) => {
  const response = await api.put(`${API_URL}/audits/${id}/`, data);
  return response.data;
};

export const deleteAudit = async (id) => {
  const response = await api.delete(`${API_URL}/audits/${id}/`);
  return response.data;
};

// ==================== FINDINGS ====================
export const getFindings = async (params = {}) => {
  const response = await api.get(`${API_URL}/findings/`, { params });
  return response.data;
};

export const createFinding = async (data) => {
  const response = await api.post(`${API_URL}/findings/`, data);
  return response.data;
};

export const updateFinding = async (id, data) => {
  const response = await api.put(`${API_URL}/findings/${id}/`, data);
  return response.data;
};

export const deleteFinding = async (id) => {
  const response = await api.delete(`${API_URL}/findings/${id}/`);
  return response.data;
};

// ==================== REVIEWS ====================
export const getReviews = async (params = {}) => {
  const response = await api.get(`${API_URL}/reviews/`, { params });
  return response.data;
};

export const createReview = async (data) => {
  const response = await api.post(`${API_URL}/reviews/`, data);
  return response.data;
};

export const updateReview = async (id, data) => {
  const response = await api.put(`${API_URL}/reviews/${id}/`, data);
  return response.data;
};

export const deleteReview = async (id) => {
  const response = await api.delete(`${API_URL}/reviews/${id}/`);
  return response.data;
};

// ==================== COCKPIT + IA (CLAUSULA 9) ====================
export const getPerformanceCockpitKpis = async (organizationId) => {
  const response = await api.get(`${API_URL}/cockpit/kpis/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeIndicatorDriftAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/indicator-drift/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeAuditAssistantAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/audit-assistant/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const generateExecutiveBriefAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/executive-brief/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export default {
  getIndicators,
  createIndicator,
  updateIndicator,
  deleteIndicator,
  getMeasurements,
  createMeasurement,
  updateMeasurement,
  deleteMeasurement,
  getMeasurementStats,
  getAnalyses,
  createAnalysis,
  updateAnalysis,
  deleteAnalysis,
  getAudits,
  createAudit,
  updateAudit,
  deleteAudit,
  getFindings,
  createFinding,
  updateFinding,
  deleteFinding,
  getReviews,
  createReview,
  updateReview,
  deleteReview,
  getPerformanceCockpitKpis,
  analyzeIndicatorDriftAI,
  analyzeAuditAssistantAI,
  generateExecutiveBriefAI
};
