import React from 'react';
import { CheckCircle2, Download, RefreshCw } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const EnvironmentalAlertsPanel = ({
  loading,
  data,
  filters,
  onFilterChange,
  onPageChange,
  onRefresh,
  onAcknowledge,
  onExport,
  acknowledgingAlertId,
}) => {
  const { t } = useI18n();
  const rows = data?.results || [];

  const formatSeverity = (severity) => {
    const normalized = String(severity || '').toLowerCase();
    const severityMap = {
      critical: t('contextDashboard.alertsPanel.filters.critical'),
      high: t('contextDashboard.alertsPanel.filters.high'),
      medium: t('contextDashboard.alertsPanel.filters.medium'),
      low: t('contextDashboard.alertsPanel.filters.low'),
    };
    return severityMap[normalized] || severity;
  };

  const formatStatus = (status) => {
    const normalized = String(status || '').toLowerCase();
    const statusMap = {
      open: t('contextDashboard.alertsPanel.filters.open'),
      in_progress: t('contextDashboard.alertsPanel.filters.inProgress'),
      acknowledged: t('contextDashboard.alertsPanel.filters.acknowledged'),
      closed: t('contextDashboard.alertsPanel.filters.closed'),
    };
    return statusMap[normalized] || status;
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow dark:shadow-slate-900/50 p-5 border border-slate-200/60 dark:border-slate-700/60">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{t('contextDashboard.alertsPanel.title')}</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">{t('contextDashboard.alertsPanel.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="inline-flex items-center px-3 py-2 text-sm rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-600"
          >
            <RefreshCw className="h-4 w-4 mr-1.5" />
            {t('contextDashboard.alertsPanel.actions.refresh')}
          </button>
          <button
            onClick={onExport}
            className="inline-flex items-center px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            <Download className="h-4 w-4 mr-1.5" />
            {t('contextDashboard.alertsPanel.actions.export')}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <select
          value={filters.severity}
          onChange={(e) => onFilterChange({ ...filters, severity: e.target.value, page: 1 })}
          className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-sm text-slate-700 dark:text-slate-100"
        >
          <option value="">{t('contextDashboard.alertsPanel.filters.allSeverities')}</option>
          <option value="critical">{t('contextDashboard.alertsPanel.filters.critical')}</option>
          <option value="high">{t('contextDashboard.alertsPanel.filters.high')}</option>
          <option value="medium">{t('contextDashboard.alertsPanel.filters.medium')}</option>
          <option value="low">{t('contextDashboard.alertsPanel.filters.low')}</option>
        </select>

        <select
          value={filters.status}
          onChange={(e) => onFilterChange({ ...filters, status: e.target.value, page: 1 })}
          className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-sm text-slate-700 dark:text-slate-100"
        >
          <option value="">{t('contextDashboard.alertsPanel.filters.allStatuses')}</option>
          <option value="open">{t('contextDashboard.alertsPanel.filters.open')}</option>
          <option value="in_progress">{t('contextDashboard.alertsPanel.filters.inProgress')}</option>
          <option value="acknowledged">{t('contextDashboard.alertsPanel.filters.acknowledged')}</option>
          <option value="closed">{t('contextDashboard.alertsPanel.filters.closed')}</option>
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
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.alertsPanel.table.alert')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.alertsPanel.table.type')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.alertsPanel.table.severity')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.alertsPanel.table.status')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.alertsPanel.table.risk')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300">{t('contextDashboard.alertsPanel.table.action')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700 bg-white dark:bg-slate-800">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-500 dark:text-slate-400">{t('contextDashboard.alertsPanel.states.loading')}</td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-500 dark:text-slate-400">{t('contextDashboard.alertsPanel.states.empty')}</td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200 max-w-xl">
                    <p className="font-medium">{row.title}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{row.description}</p>
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{row.alert_type}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${
                      row.severity === 'critical'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                        : row.severity === 'high'
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    }`}>
                      {formatSeverity(row.severity)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{formatStatus(row.status)}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">{row.linked_risk_id || '-'}</td>
                  <td className="px-4 py-3">
                    {(row.status === 'open' || row.status === 'in_progress') ? (
                      <button
                        onClick={() => onAcknowledge(row.id)}
                        disabled={acknowledgingAlertId === row.id}
                        className="inline-flex items-center px-2.5 py-1.5 text-xs rounded-md bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                        {acknowledgingAlertId === row.id ? t('contextDashboard.alertsPanel.actions.acknowledging') : t('contextDashboard.alertsPanel.actions.acknowledge')}
                      </button>
                    ) : (
                      <span className="text-xs text-slate-500 dark:text-slate-400">{t('contextDashboard.alertsPanel.states.noAction')}</span>
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

export default EnvironmentalAlertsPanel;
