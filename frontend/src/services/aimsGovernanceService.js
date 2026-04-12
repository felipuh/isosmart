import api from './api';

const BASE_URL = '/integration/aims';

export const getAimsOverview = async (payload) => {
  const response = await api.post(`${BASE_URL}/overview/`, payload || {});
  return response.data;
};

export const runAimsLifecycleCheck = async (models = []) => {
  const response = await api.post(`${BASE_URL}/model-lifecycle-check/`, { models });
  return response.data;
};

export const getAimsRiskRegister = async (risks = []) => {
  const response = await api.post(`${BASE_URL}/risk-register/`, { risks });
  return response.data;
};

export const getAimsAuditDigest = async (events = []) => {
  const response = await api.post(`${BASE_URL}/audit-digest/`, { events });
  return response.data;
};

export default {
  getAimsOverview,
  runAimsLifecycleCheck,
  getAimsRiskRegister,
  getAimsAuditDigest,
};
