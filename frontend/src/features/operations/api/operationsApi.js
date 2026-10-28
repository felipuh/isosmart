// features/operations/api/operationsApi.js
import api from '../../../services/api';

const API_URL = '/operations';

// ==================== CONTROLES OPERACIONALES ====================
export const getOperationalControls = async (params = {}) => {
  const response = await api.get(`${API_URL}/controls/`, { params });
  return response.data;
};

export const createOperationalControl = async (data) => {
  const response = await api.post(`${API_URL}/controls/`, data);
  return response.data;
};

export const updateOperationalControl = async (id, data) => {
  const response = await api.put(`${API_URL}/controls/${id}/`, data);
  return response.data;
};

export const deleteOperationalControl = async (id) => {
  const response = await api.delete(`${API_URL}/controls/${id}/`);
  return response.data;
};

// ==================== REQUISITOS DEL CLIENTE ====================
export const getCustomerRequirements = async (params = {}) => {
  const response = await api.get(`${API_URL}/requirements/`, { params });
  return response.data;
};

export const createCustomerRequirement = async (data) => {
  const response = await api.post(`${API_URL}/requirements/`, data);
  return response.data;
};

export const updateCustomerRequirement = async (id, data) => {
  const response = await api.put(`${API_URL}/requirements/${id}/`, data);
  return response.data;
};

export const deleteCustomerRequirement = async (id) => {
  const response = await api.delete(`${API_URL}/requirements/${id}/`);
  return response.data;
};

export const getPendingReviewRequirements = async (organizationId) => {
  const response = await api.get(`${API_URL}/requirements/pending_review/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getPendingConfirmationRequirements = async (organizationId) => {
  const response = await api.get(`${API_URL}/requirements/pending_confirmation/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getNotFeasibleRequirements = async (organizationId) => {
  const response = await api.get(`${API_URL}/requirements/not_feasible/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== PROYECTOS DE DISEÑO ====================
export const getDesignProjects = async (params = {}) => {
  const response = await api.get(`${API_URL}/design-projects/`, { params });
  return response.data;
};

export const createDesignProject = async (data) => {
  const response = await api.post(`${API_URL}/design-projects/`, data);
  return response.data;
};

export const updateDesignProject = async (id, data) => {
  const response = await api.put(`${API_URL}/design-projects/${id}/`, data);
  return response.data;
};

export const deleteDesignProject = async (id) => {
  const response = await api.delete(`${API_URL}/design-projects/${id}/`);
  return response.data;
};

export const getActiveDesignProjects = async (organizationId) => {
  const response = await api.get(`${API_URL}/design-projects/active/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getPendingVerificationProjects = async (organizationId) => {
  const response = await api.get(`${API_URL}/design-projects/pending_verification/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getPendingValidationProjects = async (organizationId) => {
  const response = await api.get(`${API_URL}/design-projects/pending_validation/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== PROVEEDORES EXTERNOS ====================
export const getExternalProviders = async (params = {}) => {
  const response = await api.get(`${API_URL}/providers/`, { params });
  return response.data;
};

export const createExternalProvider = async (data) => {
  const response = await api.post(`${API_URL}/providers/`, data);
  return response.data;
};

export const updateExternalProvider = async (id, data) => {
  const response = await api.put(`${API_URL}/providers/${id}/`, data);
  return response.data;
};

export const deleteExternalProvider = async (id) => {
  const response = await api.delete(`${API_URL}/providers/${id}/`);
  return response.data;
};

export const getApprovedProviders = async (organizationId) => {
  const response = await api.get(`${API_URL}/providers/approved/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getEvaluationDueProviders = async (organizationId) => {
  const response = await api.get(`${API_URL}/providers/evaluation_due/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== CONTROL DE PRODUCCION ====================
export const getProductionControls = async (params = {}) => {
  const response = await api.get(`${API_URL}/production/`, { params });
  return response.data;
};

export const createProductionControl = async (data) => {
  const response = await api.post(`${API_URL}/production/`, data);
  return response.data;
};

export const updateProductionControl = async (id, data) => {
  const response = await api.put(`${API_URL}/production/${id}/`, data);
  return response.data;
};

export const deleteProductionControl = async (id) => {
  const response = await api.delete(`${API_URL}/production/${id}/`);
  return response.data;
};

// ==================== LIBERACIONES ====================
export const getProductReleases = async (params = {}) => {
  const response = await api.get(`${API_URL}/releases/`, { params });
  return response.data;
};

export const createProductRelease = async (data) => {
  const response = await api.post(`${API_URL}/releases/`, data);
  return response.data;
};

export const updateProductRelease = async (id, data) => {
  const response = await api.put(`${API_URL}/releases/${id}/`, data);
  return response.data;
};

export const deleteProductRelease = async (id) => {
  const response = await api.delete(`${API_URL}/releases/${id}/`);
  return response.data;
};

export const getPendingReleases = async (organizationId) => {
  const response = await api.get(`${API_URL}/releases/pending_approval/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getRecentReleases = async (organizationId) => {
  const response = await api.get(`${API_URL}/releases/recent/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

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

export const getOpenNonconformities = async (organizationId) => {
  const response = await api.get(`${API_URL}/nonconformities/open/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getCriticalNonconformities = async (organizationId) => {
  const response = await api.get(`${API_URL}/nonconformities/critical/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getCustomerImpactNonconformities = async (organizationId) => {
  const response = await api.get(`${API_URL}/nonconformities/customer_impact/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getPendingDispositionNonconformities = async (organizationId) => {
  const response = await api.get(`${API_URL}/nonconformities/pending_disposition/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== DISPOSICIONES ====================
export const getDispositions = async (params = {}) => {
  const response = await api.get(`${API_URL}/dispositions/`, { params });
  return response.data;
};

export const createDisposition = async (data) => {
  const response = await api.post(`${API_URL}/dispositions/`, data);
  return response.data;
};

export const updateDisposition = async (id, data) => {
  const response = await api.put(`${API_URL}/dispositions/${id}/`, data);
  return response.data;
};

export const deleteDisposition = async (id) => {
  const response = await api.delete(`${API_URL}/dispositions/${id}/`);
  return response.data;
};

export const getUsers = async (params = {}) => {
  const response = await api.get('/auth/users/', { params });
  return response.data;
};

// ==================== COCKPIT + IA (CLAUSULA 8) ====================
export const getOperationsCockpitKpis = async (organizationId) => {
  const response = await api.get(`${API_URL}/cockpit/kpis/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeOperationsRequirementsAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/requirements/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeOperationsProvidersAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/providers/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeOperationsReleasesAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/releases/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const analyzeOperationsNonconformitiesAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/nonconformities/`, {}, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export default {
  getOperationalControls,
  createOperationalControl,
  updateOperationalControl,
  deleteOperationalControl,
  
  getCustomerRequirements,
  createCustomerRequirement,
  updateCustomerRequirement,
  deleteCustomerRequirement,
  getPendingReviewRequirements,
  getPendingConfirmationRequirements,
  
  getDesignProjects,
  createDesignProject,
  updateDesignProject,
  deleteDesignProject,
  getActiveDesignProjects,
  getPendingVerificationProjects,
  getPendingValidationProjects,
  
  getExternalProviders,
  createExternalProvider,
  updateExternalProvider,
  deleteExternalProvider,
  getApprovedProviders,
  getEvaluationDueProviders,

  getProductionControls,
  createProductionControl,
  updateProductionControl,
  deleteProductionControl,
  
  getProductReleases,
  createProductRelease,
  updateProductRelease,
  deleteProductRelease,
  getPendingReleases,
  getRecentReleases,
  
  getNonconformities,
  createNonconformity,
  updateNonconformity,
  deleteNonconformity,
  getOpenNonconformities,
  getCriticalNonconformities,
  getCustomerImpactNonconformities,
  getPendingDispositionNonconformities,
  
  getDispositions,
  createDisposition,
  updateDisposition,
  deleteDisposition,

  getOperationsCockpitKpis,
  analyzeOperationsRequirementsAI,
  analyzeOperationsProvidersAI,
  analyzeOperationsReleasesAI,
  analyzeOperationsNonconformitiesAI,
  getUsers
};
