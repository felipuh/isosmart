import axios from 'axios';

const API_BASE_URL = 'http://192.168.100.100/api/processes';

const processService = {
  // Ejecutar mapeo de procesos
  runMapping: async (data = {}) => {
    const response = await axios.post(`${API_BASE_URL}/analyze/`, data);
    return response.data;
  },

  // Obtener último mapa
  getLatest: async () => {
    const response = await axios.get(`${API_BASE_URL}/latest/`);
    return response.data;
  },

  // Obtener todos los mapas
  getAllMaps: async (status = null) => {
    const params = status ? { status } : {};
    const response = await axios.get(`${API_BASE_URL}/maps/`, { params });
    return response.data;
  },

  // Obtener mapa por ID
  getMapById: async (id) => {
    const response = await axios.get(`${API_BASE_URL}/maps/${id}/`);
    return response.data;
  },

  // Obtener mapa activo
  getActiveMap: async () => {
    const response = await axios.get(`${API_BASE_URL}/maps/active/`);
    return response.data;
  },

  // Obtener estadísticas
  getStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/maps/stats/`);
    return response.data;
  },

  // Obtener diagrama
  getDiagram: async (mapId) => {
    const response = await axios.get(`${API_BASE_URL}/maps/${mapId}/diagram/`);
    return response.data;
  },

  // Obtener procesos
  getProcesses: async (params = {}) => {
    const response = await axios.get(`${API_BASE_URL}/processes/`, { params });
    return response.data;
  },

  // Obtener procesos por tipo
  getProcessesByType: async (mapId = null) => {
    const params = mapId ? { map_id: mapId } : {};
    const response = await axios.get(`${API_BASE_URL}/processes/by_type/`, { params });
    return response.data;
  },

  // Obtener interacciones
  getInteractions: async (mapId = null) => {
    const params = mapId ? { map_id: mapId } : {};
    const response = await axios.get(`${API_BASE_URL}/interactions/`, { params });
    return response.data;
  },

  // Obtener actividades de un proceso
  getActivities: async (processId) => {
    const response = await axios.get(`${API_BASE_URL}/activities/`, {
      params: { process_id: processId }
    });
    return response.data;
  },

  // Aprobar mapa
  approveMap: async (id) => {
    const response = await axios.post(`${API_BASE_URL}/maps/${id}/approve/`);
    return response.data;
  },

  // Activar mapa
  activateMap: async (id) => {
    const response = await axios.post(`${API_BASE_URL}/maps/${id}/activate/`);
    return response.data;
  }
};

export default processService;