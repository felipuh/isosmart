import api from './api';

const withOrg = (organizationId, params = {}) => {
  if (!organizationId) return params;
  return { ...params, organization: organizationId, organization_id: organizationId };
};

const parseFilename = (contentDisposition, fallback = 'reporte-isosmart') => {
  if (!contentDisposition) return fallback;
  const match = contentDisposition.match(/filename="?([^";]+)"?/i);
  return match?.[1] || fallback;
};

const triggerBlobDownload = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

const reportService = {
  downloadBusinessReport: async ({
    organizationId,
    type = 'sgq_executive',
    fileFormat = 'pdf',
    dateFrom,
    dateTo,
    status,
  }) => {
    const params = withOrg(organizationId, {
      type,
      file_format: fileFormat,
      ...(dateFrom ? { date_from: dateFrom } : {}),
      ...(dateTo ? { date_to: dateTo } : {}),
      ...(status ? { status } : {}),
    });

    const response = await api.get('/settings/business_report/', {
      params,
      responseType: 'blob',
    });

    const fallbackName = `isosmart-${type}-${new Date().toISOString().slice(0, 10)}.${fileFormat}`;
    const filename = parseFilename(response.headers['content-disposition'], fallbackName);
    const blob = new Blob([response.data], {
      type: response.headers['content-type'] || 'application/octet-stream',
    });

    triggerBlobDownload(blob, filename);
    return { filename };
  },
};

export default reportService;
