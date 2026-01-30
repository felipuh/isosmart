import api from './api';

const processService = {
  // Ejecutar mapeo de procesos
  runMapping: async (data = {}) => {
    const response = await api.post('/analyze/', data);
    return response.data;
  },

  // Obtener último mapa
  getLatest: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/latest/', { params });
    return response.data;
  },

  // Obtener todos los mapas
  getAllMaps: async (status = null) => {
    const params = status ? { status } : {};
    const response = await api.get('/maps/', { params });
    return response.data;
  },

  // Obtener mapa por ID
  getMapById: async (id) => {
    const response = await api.get(`/maps/${id}/`);
    return response.data;
  },

  // Obtener mapa activo
  getActiveMap: async () => {
    const response = await api.get('/maps/active/');
    return response.data;
  },

  // Obtener estadísticas
  getStats: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/maps/stats/', { params });
    return response.data;
  },

  // Obtener diagrama
  getDiagram: async (mapId) => {
    const response = await api.get(`/maps/${mapId}/diagram/`);
    return response.data;
  },

  // CRUD Procesos
  getProcesses: async (mapId = null) => {
    const params = mapId ? { process_map: mapId } : {};
    const response = await api.get('/processes/', { params });
    return response.data;
  },

  getProcessById: async (id) => {
    const response = await api.get(`/processes/${id}/`);
    return response.data;
  },

  createProcess: async (data) => {
    const response = await api.post('/processes/', data);
    return response.data;
  },

  updateProcess: async (id, data) => {
    const response = await api.put(`/processes/${id}/`, data);
    return response.data;
  },

  deleteProcess: async (id) => {
    const response = await api.delete(`/processes/${id}/`);
    return response.data;
  },

  // Obtener procesos por tipo
  getProcessesByType: async (mapId = null) => {
    const params = mapId ? { map_id: mapId } : {};
    const response = await api.get('/processes/by_type/', { params });
    return response.data;
  },

  // CRUD Interacciones
  getInteractions: async (mapId = null) => {
    const params = mapId ? { process_map: mapId } : {};
    const response = await api.get('/interactions/', { params });
    return response.data;
  },

  createInteraction: async (data) => {
    const response = await api.post('/interactions/', data);
    return response.data;
  },

  updateInteraction: async (id, data) => {
    const response = await api.put(`/interactions/${id}/`, data);
    return response.data;
  },

  deleteInteraction: async (id) => {
    const response = await api.delete(`/interactions/${id}/`);
    return response.data;
  },

  // CRUD Actividades
  getActivities: async (processId) => {
    const params = processId ? { process: processId } : {};
    const response = await api.get('/activities/', { params });
    return response.data;
  },

  createActivity: async (data) => {
    const response = await api.post('/activities/', data);
    return response.data;
  },

  updateActivity: async (id, data) => {
    const response = await api.put(`/activities/${id}/`, data);
    return response.data;
  },

  deleteActivity: async (id) => {
    const response = await api.delete(`/activities/${id}/`);
    return response.data;
  },

  // Aprobar mapa
  approveMap: async (id) => {
    const response = await api.post(`/maps/${id}/approve/`);
    return response.data;
  },

  // Activar mapa
  activateMap: async (id) => {
    const response = await api.post(`/maps/${id}/activate/`);
    return response.data;
  }
};

export default processService;