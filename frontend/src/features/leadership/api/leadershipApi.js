// features/leadership/api/leadershipApi.js
import api from '../../../services/api';

const API_URL = '/leadership';


// ==================== POLÍTICAS DE CALIDAD ====================
export const getPolicies = async (params = {}) => {
  const response = await api.get(`${API_URL}/policies/`, { params });
  return response.data;
};

export const getPolicy = async (id) => {
  const response = await api.get(`${API_URL}/policies/${id}/`);
  return response.data;
};

export const createPolicy = async (data) => {
  const response = await api.post(`${API_URL}/policies/`, data);
  return response.data;
};

export const updatePolicy = async (id, data) => {
  const response = await api.put(`${API_URL}/policies/${id}/`, data);
  return response.data;
};

export const deletePolicy = async (id) => {
  const response = await api.delete(`${API_URL}/policies/${id}/`);
  return response.data;
};

export const approvePolicy = async (id) => {
  const response = await api.post(`${API_URL}/policies/${id}/approve/`);
  return response.data;
};

export const publishPolicy = async (id) => {
  const response = await api.post(`${API_URL}/policies/${id}/publish/`);
  return response.data;
};

export const makeObsoletePolicy = async (id) => {
  const response = await api.post(`${API_URL}/policies/${id}/make_obsolete/`);
  return response.data;
};

// ==================== ROLES ORGANIZACIONALES ====================
export const getRoles = async (params = {}) => {
  const response = await api.get(`${API_URL}/roles/`, { params });
  return response.data;
};

export const getRole = async (id) => {
  const response = await api.get(`${API_URL}/roles/${id}/`);
  return response.data;
};

export const createRole = async (data) => {
  const response = await api.post(`${API_URL}/roles/`, data);
  return response.data;
};

export const updateRole = async (id, data) => {
  const response = await api.put(`${API_URL}/roles/${id}/`, data);
  return response.data;
};

export const deleteRole = async (id) => {
  const response = await api.delete(`${API_URL}/roles/${id}/`);
  return response.data;
};

export const getRoleHierarchy = async (id) => {
  const response = await api.get(`${API_URL}/roles/${id}/hierarchy/`);
  return response.data;
};

// ==================== ASIGNACIONES DE ROLES ====================
export const getRoleAssignments = async (params = {}) => {
  const response = await api.get(`${API_URL}/role-assignments/`, { params });
  return response.data;
};

export const createRoleAssignment = async (data) => {
  const response = await api.post(`${API_URL}/role-assignments/`, data);
  return response.data;
};

export const updateRoleAssignment = async (id, data) => {
  const response = await api.put(`${API_URL}/role-assignments/${id}/`, data);
  return response.data;
};

export const deleteRoleAssignment = async (id) => {
  const response = await api.delete(`${API_URL}/role-assignments/${id}/`);
  return response.data;
};

export const getUsers = async (params = {}) => {
  const response = await api.get('/auth/users/', { params });
  return response.data;
};

// ==================== MATRICES RACI ====================
export const getRACIMatrices = async (params = {}) => {
  const response = await api.get(`${API_URL}/raci-matrices/`, { params });
  return response.data;
};

export const getRACIMatrix = async (id) => {
  const response = await api.get(`${API_URL}/raci-matrices/${id}/`);
  return response.data;
};

export const createRACIMatrix = async (data) => {
  const response = await api.post(`${API_URL}/raci-matrices/`, data);
  return response.data;
};

export const updateRACIMatrix = async (id, data) => {
  const response = await api.put(`${API_URL}/raci-matrices/${id}/`, data);
  return response.data;
};

export const deleteRACIMatrix = async (id) => {
  const response = await api.delete(`${API_URL}/raci-matrices/${id}/`);
  return response.data;
};

// ==================== ENTRADAS RACI ====================
export const getRACIEntries = async (params = {}) => {
  const response = await api.get(`${API_URL}/raci-entries/`, { params });
  return response.data;
};

export const createRACIEntry = async (data) => {
  const response = await api.post(`${API_URL}/raci-entries/`, data);
  return response.data;
};

export const updateRACIEntry = async (id, data) => {
  const response = await api.put(`${API_URL}/raci-entries/${id}/`, data);
  return response.data;
};

export const deleteRACIEntry = async (id) => {
  const response = await api.delete(`${API_URL}/raci-entries/${id}/`);
  return response.data;
};

// ==================== COMPROMISOS DE LIDERAZGO ====================
export const getCommitments = async (params = {}) => {
  const response = await api.get(`${API_URL}/commitments/`, { params });
  return response.data;
};

export const createCommitment = async (data) => {
  const response = await api.post(`${API_URL}/commitments/`, data);
  return response.data;
};

export const updateCommitment = async (id, data) => {
  const response = await api.put(`${API_URL}/commitments/${id}/`, data);
  return response.data;
};

export const deleteCommitment = async (id) => {
  const response = await api.delete(`${API_URL}/commitments/${id}/`);
  return response.data;
};

// ==================== EVIDENCIAS DE ENFOQUE AL CLIENTE ====================
export const getCustomerFocus = async (params = {}) => {
  const response = await api.get(`${API_URL}/customer-focus/`, { params });
  return response.data;
};

export const createCustomerFocus = async (data) => {
  const response = await api.post(`${API_URL}/customer-focus/`, data);
  return response.data;
};

export const updateCustomerFocus = async (id, data) => {
  const response = await api.put(`${API_URL}/customer-focus/${id}/`, data);
  return response.data;
};

export const deleteCustomerFocus = async (id) => {
  const response = await api.delete(`${API_URL}/customer-focus/${id}/`);
  return response.data;
};

// ==================== GRAFO DE EVIDENCIA ====================
export const getEvidenceGraph = async (params = {}) => {
  const response = await api.get(`${API_URL}/evidence-nodes/graph/`, { params });
  return response.data;
};
export const getEvidenceNodes = async (params = {}) => {
  const response = await api.get(`${API_URL}/evidence-nodes/`, { params });
  return response.data;
};
export const createEvidenceNode = async (data) => {
  const response = await api.post(`${API_URL}/evidence-nodes/`, data);
  return response.data;
};
export const updateEvidenceNode = async (id, data) => {
  const response = await api.put(`${API_URL}/evidence-nodes/${id}/`, data);
  return response.data;
};
export const deleteEvidenceNode = async (id) => {
  const response = await api.delete(`${API_URL}/evidence-nodes/${id}/`);
  return response.data;
};
export const approveEvidenceNode = async (id) => {
  const response = await api.post(`${API_URL}/evidence-nodes/${id}/approve/`);
  return response.data;
};
export const createEvidenceEdge = async (data) => {
  const response = await api.post(`${API_URL}/evidence-edges/`, data);
  return response.data;
};
export const deleteEvidenceEdge = async (id) => {
  const response = await api.delete(`${API_URL}/evidence-edges/${id}/`);
  return response.data;
};

// ==================== REVISIONES DE GESTIÓN ====================
export const getManagementReviews = async (params = {}) => {
  const response = await api.get(`${API_URL}/management-reviews/`, { params });
  return response.data;
};
export const createManagementReview = async (data) => {
  const response = await api.post(`${API_URL}/management-reviews/`, data);
  return response.data;
};
export const updateManagementReview = async (id, data) => {
  const response = await api.put(`${API_URL}/management-reviews/${id}/`, data);
  return response.data;
};
export const deleteManagementReview = async (id) => {
  const response = await api.delete(`${API_URL}/management-reviews/${id}/`);
  return response.data;
};
export const generateReviewBrief = async (id) => {
  const response = await api.post(`${API_URL}/management-reviews/${id}/generate_brief/`);
  return response.data;
};
export const approveReviewBrief = async (id) => {
  const response = await api.post(`${API_URL}/management-reviews/${id}/approve_brief/`);
  return response.data;
};
export const approveReviewMinutes = async (id, data = {}) => {
  const response = await api.post(`${API_URL}/management-reviews/${id}/approve_minutes/`, data);
  return response.data;
};

// ==================== DECISIONES ====================
export const getReviewDecisions = async (params = {}) => {
  const response = await api.get(`${API_URL}/review-decisions/`, { params });
  return response.data;
};
export const createReviewDecision = async (data) => {
  const response = await api.post(`${API_URL}/review-decisions/`, data);
  return response.data;
};
export const updateReviewDecision = async (id, data) => {
  const response = await api.put(`${API_URL}/review-decisions/${id}/`, data);
  return response.data;
};
export const approveReviewDecision = async (id, data = {}) => {
  const response = await api.post(`${API_URL}/review-decisions/${id}/approve/`, data);
  return response.data;
};

// ==================== CULTURA DE CALIDAD ====================
export const getCultureSurveys = async (params = {}) => {
  const response = await api.get(`${API_URL}/culture-surveys/`, { params });
  return response.data;
};
export const createCultureSurvey = async (data) => {
  const response = await api.post(`${API_URL}/culture-surveys/`, data);
  return response.data;
};
export const getSurveyAggregateResults = async (id) => {
  const response = await api.get(`${API_URL}/culture-surveys/${id}/aggregate_results/`);
  return response.data;
};
export const submitSurveyResponse = async (data) => {
  const response = await api.post(`${API_URL}/survey-responses/submit/`, data);
  return response.data;
};

// ==================== REGISTROS DE APROBACIÓN ====================
export const getApprovalRecords = async (params = {}) => {
  const response = await api.get(`${API_URL}/approval-records/`, { params });
  return response.data;
};
export const verifyApprovalSignature = async (id) => {
  const response = await api.get(`${API_URL}/approval-records/${id}/verify_signature/`);
  return response.data;
};

// ==================== GOBERNANZA IA ====================
export const getAIGovernanceLogs = async (params = {}) => {
  const response = await api.get(`${API_URL}/ai-governance-logs/`, { params });
  return response.data;
};
export const recordAIDecision = async (id, decision, notes = '') => {
  const response = await api.post(`${API_URL}/ai-governance-logs/${id}/decide/`, { decision, notes });
  return response.data;
};
export const getPendingAIDecisions = async () => {
  const response = await api.get(`${API_URL}/ai-governance-logs/pending_decisions/`);
  return response.data;
};

// ==================== ENDPOINTS IA ====================
export const generatePolicyDraft = async (context = '') => {
  const response = await api.post(`${API_URL}/ai/policy-draft/`, { context });
  return response.data;
};
export const analyzeVOC = async () => {
  const response = await api.post(`${API_URL}/ai/voc-analysis/`);
  return response.data;
};
export const detectRaciGaps = async () => {
  const response = await api.get(`${API_URL}/ai/raci-gaps/`);
  return response.data;
};
export const detectPolicyIncoherences = async () => {
  const response = await api.get(`${API_URL}/ai/policy-incoherences/`);
  return response.data;
};
export const validateISORule = async (entity_type, data) => {
  const response = await api.post(`${API_URL}/ai/validate-iso-rules/`, { entity_type, data });
  return response.data;
};
export const generateAuditorPack = async () => {
  const response = await api.get(`${API_URL}/ai/auditor-pack/`);
  return response.data;
};
export const getCockpitKPIs = async () => {
  const response = await api.get(`${API_URL}/cockpit/kpis/`);
  return response.data;
};

export default {
  // Policies
  getPolicies,
  getPolicy,
  createPolicy,
  updatePolicy,
  deletePolicy,
  approvePolicy,
  publishPolicy,
  makeObsoletePolicy,
  
  // Roles
  getRoles,
  getRole,
  createRole,
  updateRole,
  deleteRole,
  getRoleHierarchy,
  
  // Role Assignments
  getRoleAssignments,
  createRoleAssignment,
  updateRoleAssignment,
  deleteRoleAssignment,
  getUsers,
  
  // RACI
  getRACIMatrices,
  getRACIMatrix,
  createRACIMatrix,
  updateRACIMatrix,
  deleteRACIMatrix,
  getRACIEntries,
  createRACIEntry,
  updateRACIEntry,
  deleteRACIEntry,
  
  // Commitments
  getCommitments,
  createCommitment,
  updateCommitment,
  deleteCommitment,
  
  // Customer Focus
  getCustomerFocus,
  createCustomerFocus,
  updateCustomerFocus,
  deleteCustomerFocus
};
