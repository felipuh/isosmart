import React, { useMemo, useState } from 'react';
import { Download, FileSpreadsheet, FileText, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import reportService from '../services/reportService';

const REPORT_TYPES = [
  { value: 'sgq_executive', label: 'Estado SGQ Ejecutivo' },
  { value: 'risks', label: 'Riesgos y Oportunidades' },
  { value: 'objectives', label: 'Objetivos y Desempeno' },
];

const FILE_FORMATS = [
  { value: 'pdf', label: 'PDF' },
  { value: 'xlsx', label: 'XLSX' },
  { value: 'csv', label: 'CSV' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'Todos' },
  { value: 'identified', label: 'Identificado (riesgos)' },
  { value: 'under_analysis', label: 'En analisis (riesgos)' },
  { value: 'mitigated', label: 'Mitigado (riesgos)' },
  { value: 'accepted', label: 'Aceptado (riesgos)' },
  { value: 'closed', label: 'Cerrado (riesgos)' },
  { value: 'active', label: 'Activo (objetivos)' },
  { value: 'in_progress', label: 'En progreso (objetivos)' },
  { value: 'achieved', label: 'Logrado (objetivos)' },
  { value: 'delayed', label: 'Demorado (objetivos)' },
  { value: 'cancelled', label: 'Cancelado (objetivos)' },
];

const ReportsPage = () => {
  const { currentOrganization } = useAuth();
  const organizationId = currentOrganization?.id || null;

  const [reportType, setReportType] = useState('sgq_executive');
  const [fileFormat, setFileFormat] = useState('pdf');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [status, setStatus] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const canUseStatus = useMemo(() => reportType === 'risks' || reportType === 'objectives', [reportType]);

  const handleDownload = async () => {
    if (!organizationId) {
      setError('No hay una organizacion activa seleccionada.');
      return;
    }

    try {
      setDownloading(true);
      setError('');
      setSuccess('');

      const result = await reportService.downloadBusinessReport({
        organizationId,
        type: reportType,
        fileFormat,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
        status: canUseStatus ? (status || undefined) : undefined,
      });

      setSuccess(`Reporte descargado: ${result.filename}`);
    } catch (err) {
      const detail = err?.response?.data?.error || 'No fue posible generar el reporte.';
      setError(typeof detail === 'string' ? detail : 'No fue posible generar el reporte.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50 to-indigo-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 p-6">
      <div className="max-w-5xl mx-auto">
        <div className="rounded-2xl border border-slate-200/80 dark:border-slate-700 bg-white/90 dark:bg-slate-900/80 shadow-xl p-8">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="w-6 h-6 text-blue-600" />
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-slate-100">Reportes de Negocio</h1>
          </div>
          <p className="text-slate-600 dark:text-slate-300 mb-8">
            Exporta reportes ejecutivos en PDF, XLSX o CSV con filtros por fecha, organizacion y estado.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <label className="flex flex-col gap-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Tipo de reporte</span>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100"
              >
                {REPORT_TYPES.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Formato</span>
              <select
                value={fileFormat}
                onChange={(e) => setFileFormat(e.target.value)}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100"
              >
                {FILE_FORMATS.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Desde</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100"
              />
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Hasta</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100"
              />
            </label>

            <label className="flex flex-col gap-2 md:col-span-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Estado (opcional)</span>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                disabled={!canUseStatus}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100 disabled:opacity-50"
              >
                {STATUS_OPTIONS.map((item) => (
                  <option key={item.value || 'all'} value={item.value}>{item.label}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-semibold px-6 py-3 shadow-lg disabled:opacity-60"
            >
              {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              {downloading ? 'Generando reporte...' : 'Descargar reporte'}
            </button>

            <div className="inline-flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
              <FileSpreadsheet className="w-4 h-4" />
              Organizacion activa: <strong>{currentOrganization?.name || 'Sin organizacion'}</strong>
            </div>
          </div>

          {error && (
            <div className="mt-4 rounded-xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="mt-4 rounded-xl border border-emerald-300 bg-emerald-50 text-emerald-700 px-4 py-3 text-sm">
              {success}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
