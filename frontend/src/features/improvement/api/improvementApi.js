// features/improvement/api/improvementApi.js
import api from '../../../services/api';

const API_URL = '/improvement';

// ==================== NO CONFORMIDADES ====================
export const getNonconformities = async (params = {}) => {
  const response = await api.get(`${API_URL}/nonconformities/`, { params });
  return response.data;
};

export const createNonconformity = async (data) => {
  const response = await api.post(`${API_URL}/nonconformities/`, data);
  return response.data;
};

export const updateNonconformity = async (id, data) => {
  const response = await api.put(`${API_URL}/nonconformities/${id}/`, data);
  return response.data;
};

export const deleteNonconformity = async (id) => {
  const response = await api.delete(`${API_URL}/nonconformities/${id}/`);
  return response.data;
};

export const getNonconformityStats = async (organizationId) => {
  const response = await api.get(`${API_URL}/nonconformities/dashboard_stats/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== ACCIONES CORRECTIVAS ====================
export const getCorrectiveActions = async (params = {}) => {
  const response = await api.get(`${API_URL}/corrective-actions/`, { params });
  return response.data;
};

export const createCorrectiveAction = async (data) => {
  const response = await api.post(`${API_URL}/corrective-actions/`, data);
  return response.data;
};

export const updateCorrectiveAction = async (id, data) => {
  const response = await api.put(`${API_URL}/corrective-actions/${id}/`, data);
  return response.data;
};

export const deleteCorrectiveAction = async (id) => {
  const response = await api.delete(`${API_URL}/corrective-actions/${id}/`);
  return response.data;
};

export const getOverdueActions = async (organizationId) => {
  const response = await api.get(`${API_URL}/corrective-actions/overdue/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== MEJORA CONTINUA ====================
export const getContinualImprovements = async (params = {}) => {
  const response = await api.get(`${API_URL}/continual-improvements/`, { params });
  return response.data;
};

export const createContinualImprovement = async (data) => {
  const response = await api.post(`${API_URL}/continual-improvements/`, data);
  return response.data;
};

export const updateContinualImprovement = async (id, data) => {
  const response = await api.put(`${API_URL}/continual-improvements/${id}/`, data);
  return response.data;
};

export const deleteContinualImprovement = async (id) => {
  const response = await api.delete(`${API_URL}/continual-improvements/${id}/`);
  return response.data;
};

export const getActiveInitiatives = async (organizationId) => {
  const response = await api.get(`${API_URL}/continual-improvements/active_initiatives/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== COCKPIT + IA (CLAUSULA 10) ====================
export const getImprovementCockpitKpis = async (organizationId) => {
  const response = await api.get(`${API_URL}/cockpit/kpis/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeImprovementRootCauseAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/root-cause/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeCorrectiveTrackerAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/corrective-tracker/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeContinualOptimizerAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/continual-optimizer/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export default {
  getNonconformities, createNonconformity, updateNonconformity, deleteNonconformity, getNonconformityStats,
  getCorrectiveActions, createCorrectiveAction, updateCorrectiveAction, deleteCorrectiveAction, getOverdueActions,
  getContinualImprovements, createContinualImprovement, updateContinualImprovement, deleteContinualImprovement, getActiveInitiatives,
  getImprovementCockpitKpis, analyzeImprovementRootCauseAI, analyzeCorrectiveTrackerAI, analyzeContinualOptimizerAI
};