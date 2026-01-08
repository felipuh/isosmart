import axios from 'axios';

const API_BASE_URL = 'http://192.168.100.100/api/documents';

const documentService = {
  // Obtener todos los documentos
  getAll: async (params = {}) => {
    const response = await axios.get(`${API_BASE_URL}/`, { params });
    return response.data;
  },

  // Obtener documento por ID
  getById: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/${id}/`);
    return response.data;
  },

  // Subir nuevo documento
  upload: async (formData) => {
    const response = await axios.post(`${API_BASE_URL}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Eliminar documento
  delete: async (id) => {
    const response = await axios.delete(`${API_BASE_URL}/${id}/`);
    return response.data;
  },

  // Descargar documento
  download: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/${id}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Obtener estadísticas
  getStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/stats/`);
    return response.data;
  },
};

export default documentService;