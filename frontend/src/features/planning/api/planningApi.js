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

export const getRiskHeatmap = async (organizationId) => {
  const response = await api.get(`${API_URL}/risks-opportunities/heatmap/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const detectRiskWithAI = async (organizationId, payload) => {
  const response = await api.post(`${API_URL}/risks-opportunities/ai-detect/?organization_id=${organizationId}`, payload);
  return response.data;
};

export const approveRiskOpportunity = async (id, notes = '') => {
  const response = await api.post(`${API_URL}/risks-opportunities/${id}/approve/`, { notes });
  return response.data;
};

export const getRiskVersionHistory = async (id, organizationId) => {
  const response = await api.get(`${API_URL}/risks-opportunities/${id}/version_history/`, {
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

export const validateSmartObjective = async (payload) => {
  const response = await api.post(`${API_URL}/objectives/validate_smart/`, payload);
  return response.data;
};

export const generateSmartObjectiveWithAI = async (organizationId, payload) => {
  const response = await api.post(`${API_URL}/objectives/ai_generate/?organization_id=${organizationId}`, payload);
  return response.data;
};

export const forecastObjective = async (id, organizationId) => {
  const response = await api.get(`${API_URL}/objectives/${id}/forecast/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const approveObjective = async (id, notes = '') => {
  const response = await api.post(`${API_URL}/objectives/${id}/approve/`, { notes });
  return response.data;
};

export const getObjectiveVersionHistory = async (id, organizationId) => {
  const response = await api.get(`${API_URL}/objectives/${id}/version_history/`, {
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

export const simulateChangeImpact = async (id, organizationId, payload = {}) => {
  const response = await api.post(`${API_URL}/changes/${id}/simulate_impact/?organization_id=${organizationId}`, payload);
  return response.data;
};

export const generateChangePlan = async (id, organizationId) => {
  const response = await api.post(`${API_URL}/changes/${id}/generate_plan/?organization_id=${organizationId}`, {});
  return response.data;
};

export const getChangeTimeline = async (id, organizationId) => {
  const response = await api.get(`${API_URL}/changes/${id}/timeline/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getChangeVersionHistory = async (id, organizationId) => {
  const response = await api.get(`${API_URL}/changes/${id}/version_history/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getPlanningCockpitKPIs = async (organizationId) => {
  const response = await api.get(`${API_URL}/cockpit/kpis/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getPlanningApprovalRecords = async (params = {}) => {
  const response = await api.get(`${API_URL}/approval-records/`, { params });
  return response.data;
};

export const verifyPlanningApprovalSignature = async (id, organizationId) => {
  const response = await api.get(`${API_URL}/approval-records/${id}/verify_signature/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getPlanningAIGovernanceLogs = async (params = {}) => {
  const response = await api.get(`${API_URL}/ai-governance-logs/`, { params });
  return response.data;
};

export const getPendingPlanningAIDecisions = async (organizationId) => {
  const response = await api.get(`${API_URL}/ai-governance-logs/pending/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const decidePlanningAIRecommendation = async (id, decision, notes = '') => {
  const response = await api.post(`${API_URL}/ai-governance-logs/${id}/decide/`, { decision, notes });
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
  getRiskHeatmap,
  detectRiskWithAI,
  approveRiskOpportunity,
  getRiskVersionHistory,
  
  getObjectives,
  getObjective,
  createObjective,
  updateObjective,
  deleteObjective,
  getActiveObjectives,
  getSmartObjectives,
  getAtRiskObjectives,
  validateSmartObjective,
  generateSmartObjectiveWithAI,
  forecastObjective,
  approveObjective,
  getObjectiveVersionHistory,
  
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
  simulateChangeImpact,
  generateChangePlan,
  getChangeTimeline,
  getChangeVersionHistory,
  getPlanningCockpitKPIs,
  getPlanningApprovalRecords,
  verifyPlanningApprovalSignature,
  getPlanningAIGovernanceLogs,
  getPendingPlanningAIDecisions,
  decidePlanningAIRecommendation,
  getUsers
};
