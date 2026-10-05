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
};

export default foundationService;
