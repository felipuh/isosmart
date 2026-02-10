// features/planning/api/planningApi.js
import api from '../../../services/api';

const API_URL = '/planning';

// ==================== RIESGOS Y OPORTUNIDADES ====================
export const getRisksOpportunities = async (params = {}) => {
  const response = await api.get(`${API_URL}/risks-opportunities/`, { params });
  return response.data;
};

export const getRiskOpportunity = async (id) => {
  const response = await api.get(`${API_URL}/risks-opportunities/${id}/`);
  return response.data;
};

export const createRiskOpportunity = async (data) => {
  const response = await api.post(`${API_URL}/risks-opportunities/`, data);
  return response.data;
};

export const updateRiskOpportunity = async (id, data) => {
  const response = await api.put(`${API_URL}/risks-opportunities/${id}/`, data);
  return response.data;
};

export const deleteRiskOpportunity = async (id) => {
  const response = await api.delete(`${API_URL}/risks-opportunities/${id}/`);
  return response.data;
};

export const getRisks = async (organizationId) => {
  const response = await api.get(`${API_URL}/risks-opportunities/risks/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getOpportunities = async (organizationId) => {
  const response = await api.get(`${API_URL}/risks-opportunities/opportunities/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getHighPriorityRisks = async (organizationId) => {
  const response = await api.get(`${API_URL}/risks-opportunities/high_priority/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== OBJETIVOS DE CALIDAD ====================
export const getObjectives = async (params = {}) => {
  const response = await api.get(`${API_URL}/objectives/`, { params });
  return response.data;
};

export const getObjective = async (id) => {
  const response = await api.get(`${API_URL}/objectives/${id}/`);
  return response.data;
};

export const createObjective = async (data) => {
  const response = await api.post(`${API_URL}/objectives/`, data);
  return response.data;
};

export const updateObjective = async (id, data) => {
  const response = await api.put(`${API_URL}/objectives/${id}/`, data);
  return response.data;
};

export const deleteObjective = async (id) => {
  const response = await api.delete(`${API_URL}/objectives/${id}/`);
  return response.data;
};

export const getActiveObjectives = async (organizationId) => {
  const response = await api.get(`${API_URL}/objectives/active/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getSmartObjectives = async (organizationId) => {
  const response = await api.get(`${API_URL}/objectives/smart_compliant/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getAtRiskObjectives = async (organizationId) => {
  const response = await api.get(`${API_URL}/objectives/at_risk/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== ACCIONES DE OBJETIVOS ====================
export const getActions = async (params = {}) => {
  const response = await api.get(`${API_URL}/actions/`, { params });
  return response.data;
};

export const createAction = async (data) => {
  const response = await api.post(`${API_URL}/actions/`, data);
  return response.data;
};

export const updateAction = async (id, data) => {
  const response = await api.put(`${API_URL}/actions/${id}/`, data);
  return response.data;
};

export const deleteAction = async (id) => {
  const response = await api.delete(`${API_URL}/actions/${id}/`);
  return response.data;
};

export const getOverdueActions = async (organizationId) => {
  const response = await api.get(`${API_URL}/actions/overdue/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== CONTROL DE CAMBIOS ====================
export const getChanges = async (params = {}) => {
  const response = await api.get(`${API_URL}/changes/`, { params });
  return response.data;
};

export const createChange = async (data) => {
  const response = await api.post(`${API_URL}/changes/`, data);
  return response.data;
};

export const updateChange = async (id, data) => {
  const response = await api.put(`${API_URL}/changes/${id}/`, data);
  return response.data;
};

export const deleteChange = async (id) => {
  const response = await api.delete(`${API_URL}/changes/${id}/`);
  return response.data;
};

export const approveChange = async (id) => {
  const response = await api.post(`${API_URL}/changes/${id}/approve/`, {});
  return response.data;
};

export const rejectChange = async (id, comments) => {
  const response = await api.post(`${API_URL}/changes/${id}/reject/`, { comments });
  return response.data;
};

export const getPendingChanges = async (organizationId) => {
  const response = await api.get(`${API_URL}/changes/pending_approval/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getUsers = async (params = {}) => {
  const response = await api.get('/auth/users/', { params });
  return response.data;
};

export default {
  getRisksOpportunities,
  getRiskOpportunity,
  createRiskOpportunity,
  updateRiskOpportunity,
  deleteRiskOpportunity,
  getRisks,
  getOpportunities,
  getHighPriorityRisks,
  
  getObjectives,
  getObjective,
  createObjective,
  updateObjective,
  deleteObjective,
  getActiveObjectives,
  getSmartObjectives,
  getAtRiskObjectives,
  
  getActions,
  createAction,
  updateAction,
  deleteAction,
  getOverdueActions,
  
  getChanges,
  createChange,
  updateChange,
  deleteChange,
  approveChange,
  rejectChange,
  getPendingChanges,
  getUsers
};
