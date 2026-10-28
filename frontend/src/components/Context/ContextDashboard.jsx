import React, { useCallback, useState, useEffect } from 'react';
import { RefreshCw, Download, TrendingUp, AlertCircle, CheckCircle, FileText, Leaf, Radio, Bell } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import contextService from '../../services/contextService';
import { showAlert } from '../../services/dialogs';
import FODAAnalysis from './FODAAnalysis';
import ExternalFactors from './ExternalFactors';
import InternalFactors from './InternalFactors';
import IdentifiedRisks from './IdentifiedRisks';
import Recommendations from './Recommendations';
import EnvironmentalKpiStrip from './EnvironmentalKpiStrip';
import ExternalSignalsPanel from './ExternalSignalsPanel';
import EnvironmentalAlertsPanel from './EnvironmentalAlertsPanel';
import ClimateInsightsPanel from './ClimateInsightsPanel';

const TAB_OPTIONS = ['overview', 'signals', 'alerts', 'radar'];
const AUTO_REFRESH_OPTIONS = [0, 2, 5, 10, 15, 30];

const ContextDashboard = () => {
  const { t, language } = useI18n();
  const { user, currentOrganization } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [contextData, setContextData] = useState(null);
  const [environmentalDashboard, setEnvironmentalDashboard] = useState(null);
  const [signalsData, setSignalsData] = useState({ count: 0, results: [] });
  const [alertsData, setAlertsData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [acknowledgingAlertId, setAcknowledgingAlertId] = useState(null);
  const [autoRefreshMinutes, setAutoRefreshMinutes] = useState(5);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [signalsFilters, setSignalsFilters] = useState({
    page: 1,
    pageSize: 10,
    sourceType: '',
    impactLevel: '',
  });
  const [alertsFilters, setAlertsFilters] = useState({
    page: 1,
    pageSize: 10,
    severity: '',
    status: '',
  });

  const activeTab = TAB_OPTIONS.includes(searchParams.get('tab'))
    ? searchParams.get('tab')
    : 'overview';

  const refreshStorageKey = `isosmart_context_autorefresh_${user?.id || 'user'}_${currentOrganization?.id || 'org'}`;

  const loadContextData = useCallback(async () => {
    setLoading(true);
    try {
      const [data, envDashboard, signals, alerts] = await Promise.all([
        contextService.getLatest(currentOrganization.id),
        contextService.getEnvironmentalDashboard(currentOrganization.id),
        contextService.getExternalSignals({
          organizationId: currentOrganization.id,
          page: signalsFilters.page,
          pageSize: signalsFilters.pageSize,
          sourceType: signalsFilters.sourceType,
          impactLevel: signalsFilters.impactLevel,
        }),
        contextService.getEnvironmentalAlerts({
          organizationId: currentOrganization.id,
          page: alertsFilters.page,
          pageSize: alertsFilters.pageSize,
          severity: alertsFilters.severity,
          status: alertsFilters.status,
        }),
      ]);
      setContextData(data);
      setEnvironmentalDashboard(envDashboard);
      setSignalsData(signals);
      setAlertsData(alerts);
      if (data.timestamp) {
        setLastUpdate(new Date(data.timestamp));
      }
    } catch (error) {
      console.error('Error cargando datos de contexto:', error);
    } finally {
      setLoading(false);
    }
  }, [
    currentOrganization?.id,
    signalsFilters.page,
    signalsFilters.pageSize,
    signalsFilters.sourceType,
    signalsFilters.impactLevel,
    alertsFilters.page,
    alertsFilters.pageSize,
    alertsFilters.severity,
    alertsFilters.status,
  ]);

  useEffect(() => {
    if (currentOrganization?.id) {
      loadContextData();
    }
  }, [currentOrganization?.id, loadContextData]);

  useEffect(() => {
    if (TAB_OPTIONS.includes(searchParams.get('tab'))) {
      return;
    }
    const params = new URLSearchParams(searchParams);
    params.set('tab', 'overview');
    setSearchParams(params, { replace: true });
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    const saved = localStorage.getItem(refreshStorageKey);
    if (!saved) {
      setAutoRefreshMinutes(5);
      return;
    }
    const parsed = Number(saved);
    setAutoRefreshMinutes(Number.isFinite(parsed) && AUTO_REFRESH_OPTIONS.includes(parsed) ? parsed : 5);
  }, [refreshStorageKey]);

  useEffect(() => {
    localStorage.setItem(refreshStorageKey, String(autoRefreshMinutes));
  }, [autoRefreshMinutes, refreshStorageKey]);

  useEffect(() => {
    if (!currentOrganization?.id || autoRefreshMinutes <= 0) {
      return undefined;
    }

    const intervalId = setInterval(() => {
      loadContextData();
    }, autoRefreshMinutes * 60 * 1000);

    return () => clearInterval(intervalId);
  }, [currentOrganization?.id, autoRefreshMinutes, loadContextData]);

const handleRunAnalysis = async () => {
  // Verificar si hay documentos
  if (!contextData || contextData.total_documents_processed === 0) {
    await showAlert(t('contextDashboard.messages.noDocuments'), { icon: 'warning' });
    return;
  }

  setAnalyzing(true);
  try {
    const result = await contextService.triggerAnalysis(currentOrganization.id);
    console.log('Context analysis completed:', result);
    
    await loadContextData();

    await showAlert(
      t('contextDashboard.messages.analysisCompleted')
        .replace('{documents}', result.total_documents || 0)
        .replace('{strengths}', result.internal_insights?.fortalezas?.length || 0)
        .replace('{risks}', result.internal_insights?.riesgos_identificados?.length || 0),
      { icon: 'success' }
    );
  } catch (error) {
    console.error('Error running context analysis:', error);
    
    // Mensaje más informativo
    if (error.response?.status === 500) {
      await showAlert(t('contextDashboard.messages.serverError'), { icon: 'error' });
    } else {
      await showAlert(t('contextDashboard.messages.runError'), { icon: 'error' });
    }
  } finally {
    setAnalyzing(false);
  }
};

  const downloadCsv = (filename, rows, columns) => {
    const headers = columns.map((c) => c.label).join(',');
    const lines = rows.map((row) => columns.map((c) => {
      const value = c.value(row);
      const stringValue = value === null || value === undefined ? '' : String(value);
      return `"${stringValue.replace(/"/g, '""')}"`;
    }).join(','));

    const csv = [headers, ...lines].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportSignals = () => {
    const rows = signalsData?.results || [];
    downloadCsv('external-signals.csv', rows, [
      { label: t('contextDashboard.exports.common.id'), value: (r) => r.id },
      { label: t('contextDashboard.signalsPanel.table.source'), value: (r) => r.source_name },
      { label: t('contextDashboard.exports.signals.type'), value: (r) => r.source_type },
      { label: t('contextDashboard.signalsPanel.table.impact'), value: (r) => r.impact_level },
      { label: t('contextDashboard.exports.signals.title'), value: (r) => r.title },
      { label: t('contextDashboard.signalsPanel.table.date'), value: (r) => r.published_at },
      { label: t('contextDashboard.exports.common.url'), value: (r) => r.source_url },
    ]);
  };

  const handleExportAlerts = () => {
    const rows = alertsData?.results || [];
    downloadCsv('environmental-alerts.csv', rows, [
      { label: t('contextDashboard.exports.common.id'), value: (r) => r.id },
      { label: t('contextDashboard.alertsPanel.table.type'), value: (r) => r.alert_type },
      { label: t('contextDashboard.alertsPanel.table.severity'), value: (r) => r.severity },
      { label: t('contextDashboard.alertsPanel.table.status'), value: (r) => r.status },
      { label: t('contextDashboard.exports.alerts.title'), value: (r) => r.title },
      { label: t('contextDashboard.exports.alerts.linkedRisk'), value: (r) => r.linked_risk_id },
      { label: t('contextDashboard.exports.alerts.createdAt'), value: (r) => r.created_at },
    ]);
  };

  const handleAcknowledgeAlert = async (alertId) => {
    if (!alertId) return;
    setAcknowledgingAlertId(alertId);
    try {
      await contextService.acknowledgeEnvironmentalAlert(alertId, currentOrganization.id);
      await loadContextData();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      await showAlert(t('contextDashboard.messages.acknowledgeError'), { icon: 'error' });
    } finally {
      setAcknowledgingAlertId(null);
    }
  };

  const selectTab = (tabKey) => {
    const params = new URLSearchParams(searchParams);
    params.set('tab', tabKey);
    setSearchParams(params, { replace: true });
  };

  const getAutoRefreshLabel = () => {
    if (autoRefreshMinutes <= 0) return t('contextDashboard.autoRefresh.off');
    return `${autoRefreshMinutes} min`;
  };

  const escapeHtml = (rawValue) => {
    const value = rawValue === null || rawValue === undefined ? '' : String(rawValue);
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  };

  const handlePrintExecutiveView = () => {
    const summary = environmentalDashboard?.summary || {};
    const climate = contextData?.climate_context || {};
    const topSignals = (signalsData?.results || []).slice(0, 8);
    const topAlerts = (alertsData?.results || []).slice(0, 8);
    const orgName = currentOrganization?.name || t('contextDashboard.print.orgFallback');

    const popup = window.open('', '_blank', 'width=1200,height=900');
    if (!popup) {
      showAlert(t('contextDashboard.print.popupBlocked'), { icon: 'warning' });
      return;
    }

    const printLabels = {
      title: t('contextDashboard.print.title'),
      organization: t('contextDashboard.print.organization'),
      generated: t('contextDashboard.print.generated'),
      lastUpdate: t('contextDashboard.print.lastUpdate'),
      kpisTitle: t('contextDashboard.print.kpisTitle'),
      signalsExternal: t('contextDashboard.print.signalsExternal'),
      signalsHighCritical: t('contextDashboard.print.signalsHighCritical'),
      alertsOpen: t('contextDashboard.print.alertsOpen'),
      alertsCritical: t('contextDashboard.print.alertsCritical'),
      climateContext: t('contextDashboard.print.climateContext'),
      indicatorsTitle: t('contextDashboard.print.indicatorsTitle'),
      regulatoryTrends: t('contextDashboard.print.regulatoryTrends'),
      supplySignals: t('contextDashboard.print.supplySignals'),
      digitalSignals: t('contextDashboard.print.digitalSignals'),
      topSignalsTitle: t('contextDashboard.print.topSignalsTitle'),
      topAlertsTitle: t('contextDashboard.print.topAlertsTitle'),
      tableSource: t('contextDashboard.print.tableSource'),
      tableSignal: t('contextDashboard.print.tableSignal'),
      tableImpact: t('contextDashboard.print.tableImpact'),
      tableDate: t('contextDashboard.print.tableDate'),
      tableAlert: t('contextDashboard.print.tableAlert'),
      tableType: t('contextDashboard.print.tableType'),
      tableSeverity: t('contextDashboard.print.tableSeverity'),
      tableStatus: t('contextDashboard.print.tableStatus'),
      noRecordsSignals: t('contextDashboard.print.noRecordsSignals'),
      noRecordsAlerts: t('contextDashboard.print.noRecordsAlerts'),
      note: t('contextDashboard.print.note'),
      footer: t('contextDashboard.print.footer'),
    };

    const signalRows = topSignals.map((item) => `
      <tr>
        <td>${escapeHtml(item.source_name)}</td>
        <td>${escapeHtml(item.title)}</td>
        <td>${escapeHtml(item.impact_level)}</td>
        <td>${escapeHtml(item.published_at ? new Date(item.published_at).toLocaleString() : '-')}</td>
      </tr>
    `).join('');

    const alertRows = topAlerts.map((item) => `
      <tr>
        <td>${escapeHtml(item.title)}</td>
        <td>${escapeHtml(item.alert_type)}</td>
        <td>${escapeHtml(item.severity)}</td>
        <td>${escapeHtml(item.status)}</td>
      </tr>
    `).join('');

    popup.document.write(`
      <!doctype html>
      <html lang="${escapeHtml(language)}">
        <head>
          <meta charset="UTF-8" />
          <title>${escapeHtml(printLabels.title)} - ${escapeHtml(orgName)}</title>
          <style>
            :root {
              --ink: #0f172a;
              --muted: #475569;
              --line: #cbd5e1;
              --bg-soft: #f8fafc;
            }
            * { box-sizing: border-box; }
            body { margin: 0; font-family: 'Segoe UI', Tahoma, sans-serif; color: var(--ink); background: white; }
            .page { max-width: 1080px; margin: 0 auto; padding: 28px; }
            .header { border-bottom: 2px solid var(--ink); padding-bottom: 14px; margin-bottom: 18px; }
            h1 { margin: 0 0 8px; font-size: 28px; }
            h2 { margin: 28px 0 10px; font-size: 18px; }
            .meta { font-size: 12px; color: var(--muted); display: flex; gap: 18px; flex-wrap: wrap; }
            .kpi-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
            .kpi { background: var(--bg-soft); border: 1px solid var(--line); border-radius: 8px; padding: 10px; }
            .kpi .label { font-size: 11px; color: var(--muted); text-transform: uppercase; }
            .kpi .value { margin-top: 6px; font-size: 22px; font-weight: 700; }
            .card-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
            .card { background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
            .card p { margin: 0 0 6px; font-size: 12px; color: var(--muted); }
            .card strong { font-size: 22px; }
            table { width: 100%; border-collapse: collapse; font-size: 12px; }
            th, td { border: 1px solid var(--line); padding: 8px; vertical-align: top; text-align: left; }
            th { background: var(--bg-soft); }
            .section-note { margin-top: 8px; font-size: 12px; color: var(--muted); }
            .footer { margin-top: 24px; font-size: 11px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 10px; }
            @media print {
              @page { size: A4 landscape; margin: 12mm; }
              .page { max-width: none; padding: 0; }
            }
          </style>
        </head>
        <body>
          <div class="page">
            <div class="header">
              <h1>${escapeHtml(printLabels.title)}</h1>
              <div class="meta">
                <span><strong>${escapeHtml(printLabels.organization)}:</strong> ${escapeHtml(orgName)}</span>
                <span><strong>${escapeHtml(printLabels.generated)}:</strong> ${escapeHtml(new Date().toLocaleString())}</span>
                <span><strong>${escapeHtml(printLabels.lastUpdate)}:</strong> ${escapeHtml(formatDate(lastUpdate))}</span>
              </div>
            </div>

            <h2>${escapeHtml(printLabels.kpisTitle)}</h2>
            <div class="kpi-grid">
              <div class="kpi"><div class="label">${escapeHtml(printLabels.signalsExternal)}</div><div class="value">${escapeHtml(summary.signals_total || 0)}</div></div>
              <div class="kpi"><div class="label">${escapeHtml(printLabels.signalsHighCritical)}</div><div class="value">${escapeHtml(summary.signals_high_critical || 0)}</div></div>
              <div class="kpi"><div class="label">${escapeHtml(printLabels.alertsOpen)}</div><div class="value">${escapeHtml(summary.alerts_open || 0)}</div></div>
              <div class="kpi"><div class="label">${escapeHtml(printLabels.alertsCritical)}</div><div class="value">${escapeHtml(summary.alerts_critical || 0)}</div></div>
              <div class="kpi"><div class="label">${escapeHtml(printLabels.climateContext)}</div><div class="value">${escapeHtml((contextData?.climate_context?.external_signals_count || 0))}</div></div>
            </div>

            <h2>${escapeHtml(printLabels.indicatorsTitle)}</h2>
            <div class="card-grid">
              <div class="card"><p>${escapeHtml(printLabels.regulatoryTrends)}</p><strong>${escapeHtml((climate.regulatory_trends || []).length)}</strong></div>
              <div class="card"><p>${escapeHtml(printLabels.supplySignals)}</p><strong>${escapeHtml((climate.supply_chain_signals || []).length)}</strong></div>
              <div class="card"><p>${escapeHtml(printLabels.digitalSignals)}</p><strong>${escapeHtml((climate.digital_transformation_signals || []).length)}</strong></div>
            </div>

            <h2>${escapeHtml(printLabels.topSignalsTitle)}</h2>
            <table>
              <thead>
                <tr><th>${escapeHtml(printLabels.tableSource)}</th><th>${escapeHtml(printLabels.tableSignal)}</th><th>${escapeHtml(printLabels.tableImpact)}</th><th>${escapeHtml(printLabels.tableDate)}</th></tr>
              </thead>
              <tbody>
                ${signalRows || `<tr><td colspan="4">${escapeHtml(printLabels.noRecordsSignals)}</td></tr>`}
              </tbody>
            </table>

            <h2>${escapeHtml(printLabels.topAlertsTitle)}</h2>
            <table>
              <thead>
                <tr><th>${escapeHtml(printLabels.tableAlert)}</th><th>${escapeHtml(printLabels.tableType)}</th><th>${escapeHtml(printLabels.tableSeverity)}</th><th>${escapeHtml(printLabels.tableStatus)}</th></tr>
              </thead>
              <tbody>
                ${alertRows || `<tr><td colspan="4">${escapeHtml(printLabels.noRecordsAlerts)}</td></tr>`}
              </tbody>
            </table>
            <p class="section-note">${escapeHtml(printLabels.note)}</p>

            <div class="footer">
              ${escapeHtml(printLabels.footer)}
            </div>
          </div>
        </body>
      </html>
    `);

    popup.document.close();
    popup.focus();
    setTimeout(() => {
      popup.print();
    }, 250);
  };

  const formatDate = (date) => {
    if (!date) return t('contextDashboard.notAvailable');
    const locale = language === 'es-LATAM' ? 'es-ES' : language;
    return new Intl.DateTimeFormat(locale, {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  // Extraer datos del contexto
  const internalInsights = contextData?.internal_insights || {};
  const externalInsights = contextData?.external_insights || {};

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          {t('contextDashboard.title')}
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          {t('contextDashboard.subtitle')}
        </p>
      </div>

      {/* Core Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70 border border-white/20 dark:border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('contextDashboard.stats.documentsAnalyzed')}</p>
              <p className="text-3xl font-bold text-blue-600">
                {contextData?.total_documents_processed || 0}
              </p>
            </div>
            <FileText className="h-10 w-10 text-blue-400" />
          </div>
        </div>

        <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70 border border-white/20 dark:border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('contextDashboard.stats.strengths')}</p>
              <p className="text-3xl font-bold text-green-600">
                {internalInsights.fortalezas?.length || 0}
              </p>
            </div>
            <CheckCircle className="h-10 w-10 text-green-400" />
          </div>
        </div>

        <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70 border border-white/20 dark:border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('contextDashboard.stats.risks')}</p>
              <p className="text-3xl font-bold text-red-600">
                {internalInsights.riesgos_identificados?.length || 0}
              </p>
            </div>
            <AlertCircle className="h-10 w-10 text-red-400" />
          </div>
        </div>

        <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70 border border-white/20 dark:border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('contextDashboard.stats.externalFactors')}</p>
              <p className="text-3xl font-bold text-purple-600">
                {externalInsights.factores_externos?.length || 0}
              </p>
            </div>
            <TrendingUp className="h-10 w-10 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Environmental KPI Strip */}
      <div className="mb-6">
        <EnvironmentalKpiStrip
          summary={environmentalDashboard?.summary}
          contextData={contextData}
        />
      </div>

      {/* Actions Bar */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-4 mb-6 transition-colors">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? t('contextDashboard.actions.analyzing') : t('contextDashboard.actions.runAiAnalysis')}
            </button>

            <button
              onClick={loadContextData}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              {t('contextDashboard.actions.refresh')}
            </button>

            <label className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-sm text-slate-700 dark:text-slate-200">
              <span className="font-medium">{t('contextDashboard.autoRefresh.label')}</span>
              <select
                value={autoRefreshMinutes}
                onChange={(e) => setAutoRefreshMinutes(Number(e.target.value))}
                className="bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-md px-2 py-1 text-sm"
              >
                {AUTO_REFRESH_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option === 0
                      ? t('contextDashboard.autoRefresh.off')
                      : t('contextDashboard.autoRefresh.everyMinutes').replace('{minutes}', option)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-600 dark:text-slate-400">
              {t('contextDashboard.lastUpdate')}: {formatDate(lastUpdate)}
            </span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
              {t('contextDashboard.autoRefresh.current').replace('{value}', getAutoRefreshLabel())}
            </span>
            <button
              onClick={() => {
                if (activeTab === 'signals') {
                  handleExportSignals();
                } else if (activeTab === 'alerts') {
                  handleExportAlerts();
                }
              }}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <Download className="mr-2 h-4 w-4" />
              {t('contextDashboard.actions.export')}
            </button>
            <button
              onClick={handlePrintExecutiveView}
              className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
            >
              <FileText className="mr-2 h-4 w-4" />
              {t('contextDashboard.print.executivePdf')}
            </button>
          </div>
        </div>
      </div>

      {/* Advanced Tabs */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow dark:shadow-slate-900/50 p-2 mb-6 border border-slate-200/70 dark:border-slate-700/70">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
          <button
            onClick={() => selectTab('overview')}
            className={`inline-flex items-center justify-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'overview'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <Leaf className="h-4 w-4 mr-1.5" />
            {t('contextDashboard.tabs.overview')}
          </button>
          <button
            onClick={() => selectTab('signals')}
            className={`inline-flex items-center justify-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'signals'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <Radio className="h-4 w-4 mr-1.5" />
            {t('contextDashboard.tabs.signals')}
          </button>
          <button
            onClick={() => selectTab('alerts')}
            className={`inline-flex items-center justify-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'alerts'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <Bell className="h-4 w-4 mr-1.5" />
            {t('contextDashboard.tabs.alerts')}
          </button>
          <button
            onClick={() => selectTab('radar')}
            className={`inline-flex items-center justify-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'radar'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <TrendingUp className="h-4 w-4 mr-1.5" />
            {t('contextDashboard.tabs.radar')}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        {activeTab === 'signals' && (
          <ExternalSignalsPanel
            loading={loading}
            data={signalsData}
            filters={signalsFilters}
            onFilterChange={setSignalsFilters}
            onPageChange={(page) => setSignalsFilters((prev) => ({ ...prev, page }))}
            onRefresh={loadContextData}
            onExport={handleExportSignals}
          />
        )}

        {activeTab === 'alerts' && (
          <EnvironmentalAlertsPanel
            loading={loading}
            data={alertsData}
            filters={alertsFilters}
            onFilterChange={setAlertsFilters}
            onPageChange={(page) => setAlertsFilters((prev) => ({ ...prev, page }))}
            onRefresh={loadContextData}
            onAcknowledge={handleAcknowledgeAlert}
            onExport={handleExportAlerts}
            acknowledgingAlertId={acknowledgingAlertId}
          />
        )}

        {activeTab === 'radar' && (
          <ClimateInsightsPanel
            contextData={contextData}
            dashboardData={environmentalDashboard}
          />
        )}

        {(activeTab === 'overview' || activeTab === 'radar') && (
          <>
        {/* FODA Analysis */}
        <FODAAnalysis
          fortalezas={internalInsights.fortalezas}
          oportunidades={externalInsights.oportunidades}
          debilidades={internalInsights.debilidades}
          amenazas={externalInsights.amenazas}
          loading={loading}
        />

        {/* Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* External Factors */}
          <ExternalFactors
            factors={externalInsights.factores_externos}
            loading={loading}
          />

          {/* Internal Factors */}
          <InternalFactors
            fortalezas={internalInsights.fortalezas}
            debilidades={internalInsights.debilidades}
            loading={loading}
          />
        </div>

        {/* Risks and Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <IdentifiedRisks
            riesgos={internalInsights.riesgos_identificados}
            loading={loading}
          />

          <Recommendations
            recomendaciones={internalInsights.recomendaciones || contextData?.recommendations}
            loading={loading}
          />
        </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ContextDashboard;