import api from './api';

const documentService = {
  // Obtener todos los documentos
  getAll: async (organizationId = null, params = {}) => {
    const finalParams = organizationId ? { ...params, organization: organizationId } : params;
    const response = await api.get(`/documents/`, { params: finalParams });
    return response.data;
  },

  // Obtener documento por ID
  getById: async (id) => {
    const response = await api.get(`/documents/${id}/`);
    return response.data;
  },

  // Subir nuevo documento
  upload: async (formData) => {
    const response = await api.post(`/documents/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Eliminar documento
  delete: async (id) => {
    const response = await api.delete(`/documents/${id}/`);
    return response.data;
  },

  // Descargar documento
  download: async (id) => {
    const response = await api.get(`/documents/${id}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Obtener estadísticas
  getStats: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get(`/documents/stats/`, { params });
    return response.data;
  },
};

export default documentService;