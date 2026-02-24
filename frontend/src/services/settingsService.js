/**
 * Servicio de Configuración
 */
import api from './api';

const withOrg = (organizationId, params = {}) => {
  if (!organizationId) return params;
  return { ...params, organization: organizationId, organization_id: organizationId };
};

const settingsService = {
  // Obtener configuración actual
  getCurrent: async (organizationId) => {
    const response = await api.get('/settings/current/', { params: withOrg(organizationId) });
    return response.data;
  },

  // Obtener organización
  getOrganization: async (organizationId) => {
    if (!organizationId) return {};
    const response = await api.get(`/organizations/${organizationId}/`);
    return response.data;
  },

  // Obtener configuración de organización
  getSettings: async (organizationId) => {
    const response = await api.get('/settings/current/', { params: withOrg(organizationId) });
    return response.data;
  },

  // Obtener dashboard de organización
  getOrganizationDashboard: async (organizationId) => {
    if (!organizationId) return {};
    const response = await api.get(`/organizations/${organizationId}/dashboard/`);
    return response.data;
  },

  // Actualizar organización
  updateOrganization: async (id, data) => {
    const response = await api.put(`/organizations/${id}/`, data);
    return response.data;
  },

  // Subir logo de organización
  uploadLogo: async (id, file) => {
    const formData = new FormData();
    formData.append('logo', file);
    const response = await api.patch(`/organizations/${id}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Obtener cláusulas ISO
  getISOClauses: async (organizationId, standardCode = null) => {
    const params = withOrg(organizationId);
    if (standardCode) {
      params.standard_code = standardCode;
    }
    const response = await api.get('/iso-clauses/', { params });
    return response.data.results || response.data;
  },

  // Actualizar cláusula ISO
  updateISOClause: async (id, data) => {
    const response = await api.patch(`/iso-clauses/${id}/`, data);
    return response.data;
  },

  initializeISOClauses: async (organizationId) => {
    const response = await api.post('/iso-clauses/initialize_iso9001/', { organization_id: organizationId });
    return response.data;
  },

  initializeStandards: async (organizationId, standards) => {
    const response = await api.post('/iso-clauses/initialize_standards/', {
      organization_id: organizationId,
      standards,
    });
    return response.data;
  },

  updateAIModules: async (data, organizationId) => {
    const response = await api.post('/settings/update_ai_modules/', { ...data, organization_id: organizationId });
    return response.data;
  },

  updateNotifications: async (data, organizationId) => {
    const response = await api.post('/settings/update_notifications/', { ...data, organization_id: organizationId });
    return response.data;
  },

  triggerBackup: async (organizationId) => {
    const response = await api.post('/settings/trigger_backup/', { organization_id: organizationId });
    return response.data;
  },

  downloadExport: async (type = 'all') => {
    const response = await api.get('/export/', {
      params: { type },
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `isosmart-${type}-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  getUsers: async (organizationId) => {
    const response = await api.get('/users/', { params: withOrg(organizationId) });
    return response.data.results || response.data;
  },

  getUserStats: async (organizationId) => {
    const response = await api.get('/users/stats/', { params: { organization: organizationId } });
    return response.data;
  },

  createUser: async (data) => {
    const response = await api.post('/users/create_user/', data);
    return response.data;
  },

  updateUser: async (id, data) => {
    const response = await api.patch(`/users/${id}/`, data);
    return response.data;
  },

  deleteUser: async (id) => {
    const response = await api.delete(`/users/${id}/`);
    return response.data;
  },

  toggleUserActive: async (id) => {
    const response = await api.post(`/users/${id}/toggle_active/`);
    return response.data;
  },

  resetPassword: async (id, password) => {
    const response = await api.post(`/users/${id}/reset_password/`, { password });
    return response.data;
  },

  getOnboardingStatus: async (organizationId) => {
    const response = await api.get('/settings/onboarding_status/', { params: withOrg(organizationId) });
    return response.data;
  },

  completeOnboarding: async (organizationId, payload) => {
    const response = await api.post('/settings/complete_onboarding/', {
      organization_id: organizationId,
      ...payload,
    });
    return response.data;
  },

  updateStandards: async (organizationId, standards) => {
    const response = await api.post('/settings/update_standards/', {
      organization_id: organizationId,
      enabled_standards: standards,
    });
    return response.data;
  },

  updateLanguage: async (organizationId, language) => {
    const response = await api.post('/settings/update_language/', {
      organization_id: organizationId,
      preferred_language: language,
    });
    return response.data;
  },

  // Exportar datos
  exportData: async (format = 'json') => {
    const response = await api.get('/settings/export/', {
      params: { format },
      responseType: format === 'json' ? 'json' : 'blob',
    });
    return response.data;
  },

  // Crear backup
  createBackup: async () => {
    const response = await api.post('/settings/backup/');
    return response.data;
  },

  // Obtener historial de backups
  getBackupHistory: async () => {
    const response = await api.get('/settings/backups/');
    return response.data;
  }
};

export default settingsService;
