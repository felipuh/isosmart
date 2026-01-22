import axios from 'axios';

const API_BASE_URL = 'http://192.168.100.100/api';

const settingsService = {
  // =====================================================
  // Organización
  // =====================================================
  
  getOrganization: async (orgId = 1) => {
    const response = await axios.get(`${API_BASE_URL}/organizations/${orgId}/`);
    return response.data;
  },
  
  updateOrganization: async (orgId, data) => {
    const response = await axios.patch(`${API_BASE_URL}/organizations/${orgId}/`, data);
    return response.data;
  },
  
  uploadLogo: async (orgId, file) => {
    const formData = new FormData();
    formData.append('logo', file);
    const response = await axios.patch(`${API_BASE_URL}/organizations/${orgId}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  getOrganizationDashboard: async (orgId = 1) => {
    const response = await axios.get(`${API_BASE_URL}/organizations/${orgId}/dashboard/`);
    return response.data;
  },

  // =====================================================
  // Configuración General
  // =====================================================
  
  getSettings: async (orgId) => {
    const response = await axios.get(`${API_BASE_URL}/settings/current/`, {
      params: { organization: orgId }
    });
    return response.data;
  },
  
  updateAIModules: async (data) => {
    const response = await axios.post(`${API_BASE_URL}/settings/update_ai_modules/`, data);
    return response.data;
  },
  
  updateNotifications: async (data) => {
    const response = await axios.post(`${API_BASE_URL}/settings/update_notifications/`, data);
    return response.data;
  },
  
  triggerBackup: async (orgId) => {
    const response = await axios.post(`${API_BASE_URL}/settings/trigger_backup/`, {
      organization_id: orgId
    });
    return response.data;
  },

  // =====================================================
  // Usuarios
  // =====================================================
  
  getUsers: async (orgId) => {
    const response = await axios.get(`${API_BASE_URL}/users/`, {
      params: { organization: orgId }
    });
    return response.data;
  },
  
  getUserStats: async (orgId) => {
    const response = await axios.get(`${API_BASE_URL}/users/stats/`, {
      params: { organization: orgId }
    });
    return response.data;
  },
  
  createUser: async (userData) => {
    const response = await axios.post(`${API_BASE_URL}/users/create_user/`, userData);
    return response.data;
  },
  
  updateUser: async (userId, data) => {
    const response = await axios.patch(`${API_BASE_URL}/users/${userId}/`, data);
    return response.data;
  },
  
  deleteUser: async (userId) => {
    const response = await axios.delete(`${API_BASE_URL}/users/${userId}/`);
    return response.data;
  },
  
  changeUserRole: async (userId, role) => {
    const response = await axios.post(`${API_BASE_URL}/users/${userId}/change_role/`, { role });
    return response.data;
  },
  
  toggleUserActive: async (userId) => {
    const response = await axios.post(`${API_BASE_URL}/users/${userId}/toggle_active/`);
    return response.data;
  },
  
  resetPassword: async (userId, password) => {
    const response = await axios.post(`${API_BASE_URL}/users/${userId}/reset_password/`, { password });
    return response.data;
  },

  // =====================================================
  // Cláusulas ISO
  // =====================================================
  
  getISOClauses: async (orgId) => {
    const response = await axios.get(`${API_BASE_URL}/iso-clauses/`, {
      params: { organization: orgId }
    });
    return response.data;
  },
  
  updateISOClause: async (clauseId, data) => {
    const response = await axios.patch(`${API_BASE_URL}/iso-clauses/${clauseId}/`, data);
    return response.data;
  },
  
  initializeISOClauses: async (orgId) => {
    const response = await axios.post(`${API_BASE_URL}/iso-clauses/initialize_iso9001/`, {
      organization_id: orgId
    });
    return response.data;
  },

  // =====================================================
  // Logs de Auditoría
  // =====================================================
  
  getAuditLogs: async (orgId, filters = {}) => {
    const response = await axios.get(`${API_BASE_URL}/audit-logs/`, {
      params: { organization: orgId, ...filters }
    });
    return response.data;
  },

  // =====================================================
  // Exportación y Backup
  // =====================================================
  
  exportData: async (type = 'all') => {
    const response = await axios.get(`${API_BASE_URL}/export/`, {
      params: { type }
    });
    return response.data;
  },
  
  downloadExport: async (type = 'all') => {
    const response = await axios.get(`${API_BASE_URL}/export/`, {
      params: { type },
      responseType: 'blob'
    });
    
    // Crear descarga
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
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
