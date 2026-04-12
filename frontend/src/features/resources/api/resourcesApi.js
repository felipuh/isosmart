// features/resources/api/resourcesApi.js
import api from '../../../services/api';

const API_URL = '/resources';

// ==================== RECURSOS ====================
export const getResources = async (params = {}) => {
  const response = await api.get(`${API_URL}/resources/`, { params });
  return response.data;
};

export const getResource = async (id) => {
  const response = await api.get(`${API_URL}/resources/${id}/`);
  return response.data;
};

export const createResource = async (data) => {
  const response = await api.post(`${API_URL}/resources/`, data);
  return response.data;
};

export const updateResource = async (id, data) => {
  const response = await api.put(`${API_URL}/resources/${id}/`, data);
  return response.data;
};

export const deleteResource = async (id) => {
  const response = await api.delete(`${API_URL}/resources/${id}/`);
  return response.data;
};

export const getResourcesByType = async (organizationId) => {
  const response = await api.get(`${API_URL}/resources/by_type/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== INFRAESTRUCTURA ====================
export const getInfrastructure = async (params = {}) => {
  const response = await api.get(`${API_URL}/infrastructure/`, { params });
  return response.data;
};

export const createInfrastructure = async (data) => {
  const response = await api.post(`${API_URL}/infrastructure/`, data);
  return response.data;
};

export const updateInfrastructure = async (id, data) => {
  const response = await api.put(`${API_URL}/infrastructure/${id}/`, data);
  return response.data;
};

export const deleteInfrastructure = async (id) => {
  const response = await api.delete(`${API_URL}/infrastructure/${id}/`);
  return response.data;
};

export const getMaintenanceDue = async (organizationId, days = 30) => {
  const response = await api.get(`${API_URL}/infrastructure/maintenance_due/`, {
    params: { organization_id: organizationId, days }
  });
  return response.data;
};

// ==================== AMBIENTE DE TRABAJO ====================
export const getWorkEnvironments = async (params = {}) => {
  const response = await api.get(`${API_URL}/work-environment/`, { params });
  return response.data;
};

export const createWorkEnvironment = async (data) => {
  const response = await api.post(`${API_URL}/work-environment/`, data);
  return response.data;
};

export const updateWorkEnvironment = async (id, data) => {
  const response = await api.put(`${API_URL}/work-environment/${id}/`, data);
  return response.data;
};

export const deleteWorkEnvironment = async (id) => {
  const response = await api.delete(`${API_URL}/work-environment/${id}/`);
  return response.data;
};

// ==================== COMPETENCIAS ====================
export const getCompetences = async (params = {}) => {
  const response = await api.get(`${API_URL}/competences/`, { params });
  return response.data;
};

export const createCompetence = async (data) => {
  const response = await api.post(`${API_URL}/competences/`, data);
  return response.data;
};

export const updateCompetence = async (id, data) => {
  const response = await api.put(`${API_URL}/competences/${id}/`, data);
  return response.data;
};

export const deleteCompetence = async (id) => {
  const response = await api.delete(`${API_URL}/competences/${id}/`);
  return response.data;
};

export const getCompetenceGaps = async (organizationId) => {
  const response = await api.get(`${API_URL}/competences/gaps/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const getCompetencesByUser = async (organizationId, userId) => {
  const response = await api.get(`${API_URL}/competences/by_user/`, {
    params: { organization_id: organizationId, user_id: userId }
  });
  return response.data;
};

// ==================== CAPACITACIONES ====================
export const getTrainings = async (params = {}) => {
  const response = await api.get(`${API_URL}/trainings/`, { params });
  return response.data;
};

export const createTraining = async (data) => {
  const response = await api.post(`${API_URL}/trainings/`, data);
  return response.data;
};

export const updateTraining = async (id, data) => {
  const response = await api.put(`${API_URL}/trainings/${id}/`, data);
  return response.data;
};

export const deleteTraining = async (id) => {
  const response = await api.delete(`${API_URL}/trainings/${id}/`);
  return response.data;
};

export const getUpcomingTrainings = async (organizationId) => {
  const response = await api.get(`${API_URL}/trainings/upcoming/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const addTrainingParticipant = async (trainingId, userId) => {
  const response = await api.post(`${API_URL}/trainings/${trainingId}/add_participant/`, {
    user_id: userId
  });
  return response.data;
};

// ==================== CONCIENCIA ====================
export const getAwareness = async (params = {}) => {
  const response = await api.get(`${API_URL}/awareness/`, { params });
  return response.data;
};

export const createAwareness = async (data) => {
  const response = await api.post(`${API_URL}/awareness/`, data);
  return response.data;
};

export const updateAwareness = async (id, data) => {
  const response = await api.put(`${API_URL}/awareness/${id}/`, data);
  return response.data;
};

export const deleteAwareness = async (id) => {
  const response = await api.delete(`${API_URL}/awareness/${id}/`);
  return response.data;
};

export const addAwarenessParticipant = async (awarenessId, userId) => {
  const response = await api.post(`${API_URL}/awareness/${awarenessId}/add_participant/`, {
    user_id: userId
  });
  return response.data;
};

// ==================== COMUNICACIONES ====================
export const getCommunications = async (params = {}) => {
  const response = await api.get(`${API_URL}/communications/`, { params });
  return response.data;
};

export const createCommunication = async (data) => {
  const response = await api.post(`${API_URL}/communications/`, data);
  return response.data;
};

export const updateCommunication = async (id, data) => {
  const response = await api.put(`${API_URL}/communications/${id}/`, data);
  return response.data;
};

export const deleteCommunication = async (id) => {
  const response = await api.delete(`${API_URL}/communications/${id}/`);
  return response.data;
};

export const getPendingCommunications = async (organizationId) => {
  const response = await api.get(`${API_URL}/communications/pending/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

// ==================== SUPPORT COCKPIT + IA ====================
export const getSupportCockpitKpis = async (organizationId) => {
  const response = await api.get(`${API_URL}/cockpit/kpis/`, {
    params: { organization_id: organizationId }
  });
  return response.data;
};

export const generateCompetencePlanWithAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/competence-plan/?organization_id=${organizationId}`, {});
  return response.data;
};

export const generateAwarenessPulseWithAI = async (organizationId) => {
  const response = await api.post(`${API_URL}/ai/awareness-pulse/?organization_id=${organizationId}`, {});
  return response.data;
};

export const generateCommunicationDraftWithAI = async (organizationId, payload) => {
  const response = await api.post(`${API_URL}/ai/communication-draft/?organization_id=${organizationId}`, payload);
  return response.data;
};

export const evaluateDocumentHealthWithAI = async (organizationId, documents = []) => {
  const response = await api.post(`${API_URL}/ai/document-health/?organization_id=${organizationId}`, { documents });
  return response.data;
};

export const getUsers = async (params = {}) => {
  const response = await api.get('/auth/users/', { params });
  return response.data;
};

export default {
  // Resources
  getResources,
  getResource,
  createResource,
  updateResource,
  deleteResource,
  getResourcesByType,
  
  // Infrastructure
  getInfrastructure,
  createInfrastructure,
  updateInfrastructure,
  deleteInfrastructure,
  getMaintenanceDue,
  
  // Work Environment
  getWorkEnvironments,
  createWorkEnvironment,
  updateWorkEnvironment,
  deleteWorkEnvironment,
  
  // Competences
  getCompetences,
  createCompetence,
  updateCompetence,
  deleteCompetence,
  getCompetenceGaps,
  getCompetencesByUser,
  
  // Trainings
  getTrainings,
  createTraining,
  updateTraining,
  deleteTraining,
  getUpcomingTrainings,
  addTrainingParticipant,
  
  // Awareness
  getAwareness,
  createAwareness,
  updateAwareness,
  deleteAwareness,
  addAwarenessParticipant,
  
  // Communications
  getCommunications,
  createCommunication,
  updateCommunication,
  deleteCommunication,
  getPendingCommunications,
  getSupportCockpitKpis,
  generateCompetencePlanWithAI,
  generateAwarenessPulseWithAI,
  generateCommunicationDraftWithAI,
  evaluateDocumentHealthWithAI,
  getUsers
};
