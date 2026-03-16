/**
 * Servicio de Procesos (SPM) - ISO 4.4
 */
import api from './api';

const withOrgParams = (organizationId, params = {}) => {
  if (!organizationId) return params;
  return { ...params, organization_id: organizationId, organization: organizationId };
};

const withOrgPayload = (organizationId, payload = {}) => {
  if (!organizationId) return payload;
  return { ...payload, organization_id: organizationId, organization: organizationId };
};

const processService = {
  // Obtener todos los procesos
  getAll: async (params = {}) => {
    const response = await api.get('/processes/maps/', { params });
    return response.data.results || response.data;
  },

  // Obtener el último mapa de procesos
  getLatest: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/processes/maps/latest/', { params });
    return response.data;
  },

  // Obtener proceso por ID
  getById: async (id, organizationId = null) => {
    const response = await api.get(`/processes/maps/${id}/`, {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },

  // Crear nuevo proceso
  create: async (data, organizationId = null) => {
    const response = await api.post('/processes/maps/', withOrgPayload(organizationId, data));
    return response.data;
  },

  // Actualizar proceso
  update: async (id, data, organizationId = null) => {
    const response = await api.put(`/processes/maps/${id}/`, withOrgPayload(organizationId, data));
    return response.data;
  },

  // Actualizar parcialmente
  patch: async (id, data, organizationId = null) => {
    const response = await api.patch(`/processes/maps/${id}/`, withOrgPayload(organizationId, data));
    return response.data;
  },

  // Eliminar proceso
  delete: async (id, organizationId = null) => {
    const response = await api.delete(`/processes/maps/${id}/`, {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },

  // Obtener estadísticas
  getStats: async (organizationId = null) => {
    const response = await api.get('/processes/maps/stats/', {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },

  // Mapear proceso automáticamente
  mapProcess: async (data = {}, organizationId = null) => {
    const response = await api.post('/processes/analyze/', withOrgPayload(organizationId, data));
    return response.data;
  },

  runMapping: async (data = {}, organizationId = null) => {
    const response = await api.post('/processes/analyze/', withOrgPayload(organizationId, data));
    return response.data;
  },

  // Obtener interacciones entre procesos
  getInteractions: async (mapId = null, organizationId = null) => {
    const response = await api.get('/processes/interactions/', {
      params: withOrgParams(organizationId, mapId ? { map_id: mapId } : {})
    });
    return response.data;
  },

  // Procesos individuales
  getProcesses: async (mapId, organizationId = null) => {
    const response = await api.get('/processes/processes/', {
      params: withOrgParams(organizationId, { map_id: mapId })
    });
    return response.data.results || response.data;
  },

  getProcessesByType: async (mapId, organizationId = null) => {
    const response = await api.get('/processes/processes/by_type/', {
      params: withOrgParams(organizationId, { map_id: mapId })
    });
    return response.data;
  },

  createProcess: async (data, organizationId = null) => {
    const response = await api.post('/processes/processes/', withOrgPayload(organizationId, data));
    return response.data;
  },

  updateProcess: async (id, data, organizationId = null) => {
    const response = await api.put(`/processes/processes/${id}/`, withOrgPayload(organizationId, data));
    return response.data;
  },

  deleteProcess: async (id, organizationId = null) => {
    const response = await api.delete(`/processes/processes/${id}/`, {
      params: withOrgParams(organizationId)
    });
    return response.data;
  }
};

export default processService;
