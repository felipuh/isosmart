/**
 * Servicio de Alcance (ASB) - ISO 4.3
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

const scopeService = {
  // Obtener todos los elementos del alcance
  getAll: async (params = {}) => {
    const response = await api.get('/scope/scopes/', { params });
    return response.data.results || response.data;
  },

  // Obtener el último alcance definido
  getLatest: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/scope/latest/', { params });
    return response.data;
  },

  // Obtener elemento por ID
  getById: async (id, organizationId = null) => {
    const response = await api.get(`/scope/scopes/${id}/`, {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },

  // Crear nuevo elemento
  create: async (data, organizationId = null) => {
    const response = await api.post('/scope/scopes/', withOrgPayload(organizationId, data));
    return response.data;
  },

  // Actualizar elemento
  update: async (id, data, organizationId = null) => {
    const response = await api.put(`/scope/scopes/${id}/`, withOrgPayload(organizationId, data));
    return response.data;
  },

  // Actualizar parcialmente
  patch: async (id, data, organizationId = null) => {
    const response = await api.patch(`/scope/scopes/${id}/`, withOrgPayload(organizationId, data));
    return response.data;
  },

  // Eliminar elemento
  delete: async (id, organizationId = null) => {
    const response = await api.delete(`/scope/scopes/${id}/`, {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },

  // Obtener estadísticas
  getStats: async (organizationId = null) => {
    const response = await api.get('/scope/scopes/stats/', {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },

  // Generar alcance automáticamente
  generate: async (organizationId = null, payload = {}) => {
    const response = await api.post('/scope/generate/', withOrgPayload(organizationId, payload));
    return response.data;
  },

  // Ejecutar análisis (alias principal usado por dashboard)
  runAnalysis: async (payload = {}, organizationId = null) => {
    const response = await api.post('/scope/analyze/', withOrgPayload(organizationId, payload));
    return response.data;
  },

  // Obtener declaración de alcance
  getStatement: async (organizationId = null) => {
    const response = await api.get('/scope/statement/', {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },

  // Auditar alcance
  audit: async (organizationId = null) => {
    const response = await api.post('/scope/audit/', withOrgPayload(organizationId));
    return response.data;
  },

  // Procesos de alcance
  getProcesses: async (scopeId, organizationId = null) => {
    const response = await api.get('/scope/processes/', {
      params: withOrgParams(organizationId, { scope_id: scopeId })
    });
    return response.data.results || response.data;
  },

  createProcess: async (data, organizationId = null) => {
    const response = await api.post('/scope/processes/', withOrgPayload(organizationId, data));
    return response.data;
  },

  updateProcess: async (id, data, organizationId = null) => {
    const response = await api.put(`/scope/processes/${id}/`, withOrgPayload(organizationId, data));
    return response.data;
  },

  deleteProcess: async (id, organizationId = null) => {
    const response = await api.delete(`/scope/processes/${id}/`, {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },

  // Ubicaciones de alcance
  getLocations: async (scopeId, organizationId = null) => {
    const response = await api.get('/scope/locations/', {
      params: withOrgParams(organizationId, { scope_id: scopeId })
    });
    return response.data.results || response.data;
  },

  createLocation: async (data, organizationId = null) => {
    const response = await api.post('/scope/locations/', withOrgPayload(organizationId, data));
    return response.data;
  },

  updateLocation: async (id, data, organizationId = null) => {
    const response = await api.put(`/scope/locations/${id}/`, withOrgPayload(organizationId, data));
    return response.data;
  },

  deleteLocation: async (id, organizationId = null) => {
    const response = await api.delete(`/scope/locations/${id}/`, {
      params: withOrgParams(organizationId)
    });
    return response.data;
  },
};

export default scopeService;
