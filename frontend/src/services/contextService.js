/**
 * Servicio de Contexto (SCA) - ISO 4.1
 */
import api from './api';

const contextService = {
  // Obtener último análisis de contexto
  getLatest: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/sca/latest/', { params });
    return response.data;
  },

  // Ejecutar nuevo análisis
  triggerAnalysis: async (organizationId = null) => {
    const data = organizationId ? { organization: organizationId } : {};
    const response = await api.post('/sca/analyze/', data);
    return response.data;
  },

  // Obtener historial de análisis
  getHistory: async (page = 1) => {
    const response = await api.get('/sca/history/', { params: { page } });
    return response.data;
  },

  // Obtener señales externas auditables
  getExternalSignals: async ({ organizationId = null, page = 1, pageSize = 10, sourceType = null, impactLevel = null } = {}) => {
    const params = {
      page,
      page_size: pageSize,
      ...(organizationId ? { organization: organizationId } : {}),
      ...(sourceType ? { source_type: sourceType } : {}),
      ...(impactLevel ? { impact_level: impactLevel } : {}),
    };
    const response = await api.get('/sca/external-signals/', { params });
    return response.data;
  },

  // Obtener alertas ambientales
  getEnvironmentalAlerts: async ({ organizationId = null, page = 1, pageSize = 10, severity = null, status = null } = {}) => {
    const params = {
      page,
      page_size: pageSize,
      ...(organizationId ? { organization: organizationId } : {}),
      ...(severity ? { severity } : {}),
      ...(status ? { status } : {}),
    };
    const response = await api.get('/sca/environmental-alerts/', { params });
    return response.data;
  },

  // Reconocer alerta ambiental
  acknowledgeEnvironmentalAlert: async (alertId, organizationId = null) => {
    const data = organizationId ? { organization: organizationId } : {};
    const response = await api.post(`/sca/environmental-alerts/${alertId}/acknowledge/`, data);
    return response.data;
  },

  // Obtener resumen ejecutivo ambiental
  getEnvironmentalDashboard: async (organizationId = null) => {
    const params = organizationId ? { organization: organizationId } : {};
    const response = await api.get('/sca/environmental-dashboard/', { params });
    return response.data;
  },

  // Obtener resumen del dashboard
  getDashboardSummary: async (organizationId = null) => {
    const params = organizationId ? { organization_id: organizationId } : {};
    const response = await api.get('/dashboard/', { params });
    return response.data;
  },

  // Obtener matriz de riesgos
  getRiskMatrix: async (organizationId = null) => {
    const params = organizationId ? { organization_id: organizationId } : {};
    const response = await api.get('/risks/', { params });
    return response.data.results || response.data;
  }
};

export default contextService;
