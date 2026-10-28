import api from './api';

const foundationService = {
  getOnboardingStatus: async () => {
    const response = await api.get('/v1/onboarding/status');
    return response.data;
  },

  submitFoundationAttempt: async ({ learningPathId, answers }) => {
    const response = await api.post('/v1/learning/iso9000/attempts', {
      learning_path_id: learningPathId,
      answers,
    });
    return response.data;
  },

  getOnboardingOrganizations: async () => {
    const response = await api.get('/v1/onboarding/organizations');
    return response.data;
  },

  saveOrganizationalProfile: async ({ organizationId, eventId, profile }) => {
    const response = await api.post('/v1/onboarding/organizational-profile', {
      organization_id: organizationId,
      event_id: eventId,
      ...profile,
    });
    return response.data;
  },

  executeValueDiscovery: async ({ organizationId, eventId, declaredPurpose }) => {
    const response = await api.post('/v1/onboarding/value-discovery', {
      organization_id: organizationId,
      event_id: eventId,
      organization_declared_purpose: declaredPurpose,
    });
    return response.data;
  },

  getValueDiscoveryResult: async () => {
    const response = await api.get('/v1/onboarding/value-discovery');
    return response.data;
  },

  ingestDocumentReferences: async ({ organizationId, eventId, items }) => {
    const response = await api.post('/v1/onboarding/document-references', {
      organization_id: organizationId,
      event_id: eventId,
      items,
    });
    return response.data;
  },
};

export default foundationService;
