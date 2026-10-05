import api from './api';

const get = async (path, params) => (await api.get(path, { params })).data.results;
const post = async (path, body) => (await api.post(path, body)).data;

export const qmsErrorMessage = (error) => {
  const data = error?.response?.data;
  if (data?.detail) return `${data.code ? `${data.code}: ` : ''}${data.detail}`;
  return error?.message || 'Request failed';
};

const qmsService = {
  organizations: () => get('/v1/qms/organizations'),
  requirements: () => get('/v1/qms/requirements'),
  evidence: (organizationId) => get('/v1/qms/evidence', organizationId ? { organization_id: organizationId } : undefined),
  createEvidence: (body) => post('/v1/evidence', body),
  audits: () => get('/v1/qms/audits'),
  createAudit: (body) => post('/v1/qms/audits', body),
  findings: (auditId) => get('/v1/qms/findings', auditId ? { audit_id: auditId } : undefined),
  createFinding: (body) => post('/v1/qms/findings', body),
  nonconformities: () => get('/v1/qms/nonconformities'),
  createNonconformity: (findingId, body) => post(`/v1/qms/findings/${findingId}/nonconformity`, body),
  correctiveActions: (ncId) => get('/v1/qms/corrective-actions', ncId ? { nc_id: ncId } : undefined),
  createCorrectiveAction: (ncId, body) => post(`/v1/qms/nonconformities/${ncId}/corrective-actions`, body),
};

export default qmsService;
