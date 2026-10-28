import React, { useMemo, useState } from 'react';
import { Download, FileSpreadsheet, FileText, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import reportService from '../services/reportService';

const ReportsPage = () => {
  const { currentOrganization } = useAuth();
  const { t } = useI18n();
  const organizationId = currentOrganization?.id || null;

  const [reportType, setReportType] = useState('sgq_executive');
  const [fileFormat, setFileFormat] = useState('pdf');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [status, setStatus] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const reportTypes = useMemo(() => ([
    { value: 'sgq_executive', label: t('reportsPage.reportTypes.sgqExecutive') },
    { value: 'risks', label: t('reportsPage.reportTypes.risks') },
    { value: 'objectives', label: t('reportsPage.reportTypes.objectives') },
  ]), [t]);

  const fileFormats = useMemo(() => ([
    { value: 'pdf', label: 'PDF' },
    { value: 'xlsx', label: 'XLSX' },
    { value: 'csv', label: 'CSV' },
  ]), []);

  const statusOptions = useMemo(() => ([
    { value: '', label: t('reportsPage.statusOptions.all') },
    { value: 'identified', label: t('reportsPage.statusOptions.identified') },
    { value: 'under_analysis', label: t('reportsPage.statusOptions.underAnalysis') },
    { value: 'mitigated', label: t('reportsPage.statusOptions.mitigated') },
    { value: 'accepted', label: t('reportsPage.statusOptions.accepted') },
    { value: 'closed', label: t('reportsPage.statusOptions.closed') },
    { value: 'active', label: t('reportsPage.statusOptions.active') },
    { value: 'in_progress', label: t('reportsPage.statusOptions.inProgress') },
    { value: 'achieved', label: t('reportsPage.statusOptions.achieved') },
    { value: 'delayed', label: t('reportsPage.statusOptions.delayed') },
    { value: 'cancelled', label: t('reportsPage.statusOptions.cancelled') },
  ]), [t]);

  const canUseStatus = useMemo(() => reportType === 'risks' || reportType === 'objectives', [reportType]);

  const handleDownload = async () => {
    if (!organizationId) {
      setError(t('reportsPage.messages.noOrganization'));
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

      setSuccess(t('reportsPage.messages.success', { filename: result.filename }));
    } catch (err) {
      const detail = err?.response?.data?.error || t('reportsPage.messages.error');
      setError(typeof detail === 'string' ? detail : t('reportsPage.messages.error'));
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
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-slate-100">{t('reportsPage.title')}</h1>
          </div>
          <p className="text-slate-600 dark:text-slate-300 mb-8">
            {t('reportsPage.subtitle')}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <label className="flex flex-col gap-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t('reportsPage.fields.reportType')}</span>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100"
              >
                {reportTypes.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t('reportsPage.fields.format')}</span>
              <select
                value={fileFormat}
                onChange={(e) => setFileFormat(e.target.value)}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100"
              >
                {fileFormats.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t('reportsPage.fields.dateFrom')}</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100"
              />
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t('reportsPage.fields.dateTo')}</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100"
              />
            </label>

            <label className="flex flex-col gap-2 md:col-span-2">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t('reportsPage.fields.statusOptional')}</span>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                disabled={!canUseStatus}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-800 dark:text-slate-100 disabled:opacity-50"
              >
                {statusOptions.map((item) => (
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
              {downloading ? t('reportsPage.actions.generating') : t('reportsPage.actions.download')}
            </button>

            <div className="inline-flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
              <FileSpreadsheet className="w-4 h-4" />
              {t('reportsPage.activeOrganization')} <strong>{currentOrganization?.name || t('reportsPage.noOrganization')}</strong>
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
