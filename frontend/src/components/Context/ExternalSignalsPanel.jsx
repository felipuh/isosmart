import React from 'react';
import { ExternalLink, Filter, Download, RefreshCw } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ExternalSignalsPanel = ({
  loading,
  data,
  filters,
  onFilterChange,
  onPageChange,
  onRefresh,
  onExport,
}) => {
  const { t, language } = useI18n();
  const rows = data?.results || [];

  const formatImpactLevel = (impactLevel) => {
    const normalized = String(impactLevel || '').toLowerCase();
    const impactMap = {
      medium: t('contextDashboard.signalsPanel.filters.medium'),
      high: t('contextDashboard.signalsPanel.filters.high'),
      critical: t('contextDashboard.signalsPanel.filters.critical'),
    };
    return impactMap[normalized] || impactLevel;
  };

  const formatPublishedAt = (publishedAt) => {
    if (!publishedAt) return '-';
    const locale = language === 'es-LATAM' ? 'es-ES' : language;
    return new Intl.DateTimeFormat(locale, {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(publishedAt));
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow dark:shadow-slate-900/50 p-5 border border-slate-200/60 dark:border-slate-700/60">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{t('contextDashboard.signalsPanel.title')}</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">{t('contextDashboard.signalsPanel.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="inline-flex items-center px-3 py-2 text-sm rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-600"
          >
            <RefreshCw className="h-4 w-4 mr-1.5" />
            {t('contextDashboard.signalsPanel.actions.refresh')}
          </button>
          <button
            onClick={onExport}
            className="inline-flex items-center px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            <Download className="h-4 w-4 mr-1.5" />
            {t('contextDashboard.signalsPanel.actions.export')}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <div className="relative">
          <Filter className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
          <select
            value={filters.sourceType}
            onChange={(e) => onFilterChange({ ...filters, sourceType: e.target.value, page: 1 })}
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-sm text-slate-700 dark:text-slate-100"
          >
            <option value="">{t('contextDashboard.signalsPanel.filters.allSources')}</option>
            <option value="un">{t('contextDashboard.signalsPanel.filters.un')}</option>
            <option value="ipcc">IPCC</option>
            <option value="iso">ISO</option>
            <option value="regulator">{t('contextDashboard.signalsPanel.filters.regulator')}</option>
            <option value="industry">{t('contextDashboard.signalsPanel.filters.industry')}</option>
          </select>
        </div>

        <select
          value={filters.impactLevel}
          onChange={(e) => onFilterChange({ ...filters, impactLevel: e.target.value, page: 1 })}
          className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-sm text-slate-700 dark:text-slate-100"
        >
          <option value="">{t('contextDashboard.signalsPanel.filters.allImpact')}</option>
          <option value="medium">{t('contextDashboard.signalsPanel.filters.medium')}</option>
          <option value="high">{t('contextDashboard.signalsPanel.filters.high')}</option>
          <option value="critical">{t('contextDashboard.signalsPanel.filters.critical')}</option>
        </select>

        <select
          value={filters.pageSize}
          onChange={(e) => onFilterChange({ ...filters, pageSize: Number(e.target.value), page: 1 })}
          className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-sm text-slate-700 dark:text-slate-100"
        >
          <option value={10}>{t('contextDashboard.common.pageSize').replace('{count}', 10)}</option>
          <option value={20}>{t('contextDashboard.common.pageSize').replace('{count}', 20)}</option>
          <option value={50}>{t('contextDashboard.common.pageSize').replace('{count}', 50)}</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/60">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.signalsPanel.table.source')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.signalsPanel.table.signal')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.signalsPanel.table.impact')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.signalsPanel.table.date')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.signalsPanel.table.action')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700 bg-white dark:bg-slate-800">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500 dark:text-slate-400">{t('contextDashboard.signalsPanel.states.loading')}</td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500 dark:text-slate-400">{t('contextDashboard.signalsPanel.states.empty')}</td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{row.source_name}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200 max-w-xl">
                    <p className="font-medium">{row.title}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{row.summary}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${
                      row.impact_level === 'critical'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                        : row.impact_level === 'high'
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    }`}>
                      {formatImpactLevel(row.impact_level)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                    {formatPublishedAt(row.published_at)}
                  </td>
                  <td className="px-4 py-3">
                    {row.source_url ? (
                      <a
                        href={row.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        {t('contextDashboard.signalsPanel.actions.view')}
                        <ExternalLink className="h-3.5 w-3.5 ml-1" />
                      </a>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <p className="text-slate-600 dark:text-slate-300">{t('contextDashboard.common.total').replace('{count}', data?.count || 0)}</p>
        <div className="flex items-center gap-2">
          <button
            disabled={!data?.previous}
            onClick={() => onPageChange((filters.page || 1) - 1)}
            className="px-3 py-1.5 rounded-md border border-slate-300 dark:border-slate-600 disabled:opacity-50 text-slate-700 dark:text-slate-200"
          >
            {t('contextDashboard.common.previous')}
          </button>
          <span className="text-slate-600 dark:text-slate-300">{t('contextDashboard.common.page').replace('{page}', filters.page || 1)}</span>
          <button
            disabled={!data?.next}
            onClick={() => onPageChange((filters.page || 1) + 1)}
            className="px-3 py-1.5 rounded-md border border-slate-300 dark:border-slate-600 disabled:opacity-50 text-slate-700 dark:text-slate-200"
          >
            {t('contextDashboard.common.next')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExternalSignalsPanel;
