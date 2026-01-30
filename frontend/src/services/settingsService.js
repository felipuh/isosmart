/**
 * Servicio de Configuración
 */
import api from './api';

const settingsService = {
  // Obtener configuración actual
  getCurrent: async () => {
    const response = await api.get('/settings/current/');
    return response.data;
  },

  // Actualizar configuración
  update: async (data) => {
    const response = await api.put('/settings/current/', data);
    return response.data;
  },

  // Actualizar parcialmente
  patch: async (data) => {
    const response = await api.patch('/settings/current/', data);
    return response.data;
  },

  // Obtener organización actual (desde settings)
  getOrganization: async () => {
    try {
      const response = await api.get('/settings/');
      // Si es una lista, retorna el primer elemento o un objeto vacío
      return response.data.results?.[0] || response.data || {};
    } catch (e) {
      return {};
    }
  },

  // Obtener configuración (alias)
  getSettings: async () => {
    const response = await api.get('/settings/');
    return response.data.results || response.data;
  },

  // Obtener dashboard de organización
  getOrganizationDashboard: async () => {
    const response = await api.get('/dashboard/');
    return response.data;
  },

  // Actualizar organización
  updateOrganization: async (id, data) => {
    const response = await api.put(`/organizations/${id}/`, data);
    return response.data;
  },

  // Subir logo de organización
  uploadLogo: async (id, formData) => {
    const response = await api.post(`/organizations/${id}/upload-logo/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Obtener cláusulas ISO
  getISOClauses: async () => {
    const response = await api.get('/settings/iso-clauses/');
    return response.data;
  },

  // Actualizar cláusula ISO
  updateISOClause: async (id, data) => {
    const response = await api.put(`/settings/iso-clauses/${id}/`, data);
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
