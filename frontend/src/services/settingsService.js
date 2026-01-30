import api from './api';

const settingsService = {
  // =====================================================
  // Organización
  // =====================================================
  
  getOrganization: async (orgId = 1) => {
    const response = await api.get(`/organizations/${orgId}/`);
    return response.data;
  },
  
  updateOrganization: async (orgId, data) => {
    const response = await api.patch(`/organizations/${orgId}/`, data);
    return response.data;
  },
  
  uploadLogo: async (orgId, file) => {
    const formData = new FormData();
    formData.append('logo', file);
    const response = await api.patch(`/organizations/${orgId}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  getOrganizationDashboard: async (orgId = 1) => {
    const response = await api.get(`/organizations/${orgId}/dashboard/`);
    return response.data;
  },

  // =====================================================
  // Configuración General
  // =====================================================
  
  getSettings: async (orgId) => {
    const response = await api.get('/settings/current/', {
      params: { organization: orgId }
    });
    return response.data;
  },
  
  updateAIModules: async (data) => {
    const response = await api.post('/settings/update_ai_modules/', data);
    return response.data;
  },
  
  updateNotifications: async (data) => {
    const response = await api.post('/settings/update_notifications/', data);
    return response.data;
  },
  
  triggerBackup: async (orgId) => {
    const response = await api.post('/settings/trigger_backup/', {
      organization_id: orgId
    });
    return response.data;
  },

  // =====================================================
  // Usuarios
  // =====================================================
  
  getUsers: async (orgId) => {
    const response = await api.get('/users/', {
      params: { organization: orgId }
    });
    return response.data;
  },
  
  getUserStats: async (orgId) => {
    const response = await api.get('/users/stats/', {
      params: { organization: orgId }
    });
    return response.data;
  },
  
  createUser: async (userData) => {
    const response = await api.post('/users/create_user/', userData);
    return response.data;
  },
  
  updateUser: async (userId, data) => {
    const response = await api.patch(`/users/${userId}/`, data);
    return response.data;
  },
  
  deleteUser: async (userId) => {
    const response = await api.delete(`/users/${userId}/`);
    return response.data;
  },
  
  changeUserRole: async (userId, role) => {
    const response = await api.post(`/users/${userId}/change_role/`, { role });
    return response.data;
  },
  
  toggleUserActive: async (userId) => {
    const response = await api.post(`/users/${userId}/toggle_active/`);
    return response.data;
  },
  
  resetPassword: async (userId, password) => {
    const response = await api.post(`/users/${userId}/reset_password/`, { password });
    return response.data;
  },

  // =====================================================
  // Cláusulas ISO
  // =====================================================
  
  getISOClauses: async (orgId) => {
    const response = await api.get('/iso-clauses/', {
      params: { organization: orgId }
    });
    return response.data;
  },
  
  updateISOClause: async (clauseId, data) => {
    const response = await api.patch(`/iso-clauses/${clauseId}/`, data);
    return response.data;
  },
  
  initializeISOClauses: async (orgId) => {
    const response = await api.post('/iso-clauses/initialize_iso9001/', {
      organization_id: orgId
    });
    return response.data;
  },

  // =====================================================
  // Logs de Auditoría
  // =====================================================
  
  getAuditLogs: async (orgId, filters = {}) => {
    const response = await api.get('/audit-logs/', {
      params: { organization: orgId, ...filters }
    });
    return response.data;
  },

  // =====================================================
  // Exportación y Backup
  // =====================================================
  
  exportData: async (type = 'all') => {
    const response = await api.get('/export/', {
      params: { type }
    });
    return response.data;
  },
  
  downloadExport: async (type = 'all') => {
    const response = await api.get('/export/', {
      params: { type },
      responseType: 'blob'
    });
    
    // Crear descarga
    const blob = new Blob([response.data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `isosmart_export_${type}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    return response.data;
  }
};

export default settingsService;
