import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, AlertCircle, FileText, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import contextService from '../../services/contextService';
import { useI18n } from '../../context/I18nContext';

const ContextAnalysis = () => {
  const { t, language } = useI18n();
  const { currentOrganization } = useAuth();
  const organizationId = currentOrganization?.id || null;
  const [contextData, setContextData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    loadContextAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [organizationId]);

  const loadContextAnalysis = async () => {
    if (!organizationId) {
      setContextData(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await contextService.getLatest(organizationId);
      setContextData(data);
    } catch (error) {
      console.error('Error loading context analysis:', error);
      setContextData(null);
    } finally {
      setLoading(false);
    }
  };

  const triggerAnalysis = async () => {
    if (!organizationId) return;

    try {
      setTriggering(true);
      await contextService.triggerAnalysis(organizationId);

      // Esperar 5 segundos y recargar
      setTimeout(() => {
        loadContextAnalysis();
        setTriggering(false);
      }, 5000);
    } catch (error) {
      console.error('Error triggering analysis:', error);
      setTriggering(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/3"></div>
          <div className="h-32 bg-slate-100 dark:bg-slate-800 rounded"></div>
          <div className="h-32 bg-slate-100 dark:bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  if (!contextData) {
    return (
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Brain className="w-6 h-6 text-purple-600" />
          {t('dashboard.contextAnalysis.title')}
        </h2>
        <div className="text-center py-12">
          <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500 mb-4">{t('dashboard.contextAnalysis.empty')}</p>
          <button
            onClick={triggerAnalysis}
            disabled={triggering}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50"
          >
            {triggering ? (
              <span className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin" />
                {t('dashboard.contextAnalysis.analyzing')}
              </span>
            ) : (
              t('dashboard.contextAnalysis.start')
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Brain className="w-6 h-6 text-purple-600" />
          {t('dashboard.contextAnalysis.intelligentTitle')}
        </h2>
        <button
          onClick={triggerAnalysis}
          disabled={triggering}
          className="px-4 py-2 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg font-semibold border-2 border-slate-300 dark:border-slate-600 hover:border-blue-500 hover:text-blue-600 transition-all disabled:opacity-50"
        >
          {triggering ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fortalezas */}
        <div className="p-4 bg-green-50 rounded-lg border-2 border-green-200">
          <h3 className="font-bold text-green-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            {t('dashboard.contextAnalysis.strengthsTitle')}
          </h3>
          <div className="space-y-2">
            {contextData.internal_insights?.fortalezas?.length > 0 ? (
              contextData.internal_insights.fortalezas.slice(0, 3).map((item, i) => (
                <div key={i} className="p-3 bg-white dark:bg-slate-800 rounded border border-green-200 dark:border-green-900">
                  <p className="text-sm text-slate-700 dark:text-slate-300">{item.texto}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-slate-500 dark:text-slate-400">{item.fuente}</span>
                    <span className="text-xs font-semibold text-green-600">
                      {Math.round(item.confianza * 100)}% {t('dashboard.contextAnalysis.confidenceSuffix')}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">{t('dashboard.contextAnalysis.noStrengths')}</p>
            )}
          </div>
        </div>

        {/* Riesgos */}
        <div className="p-4 bg-red-50 rounded-lg border-2 border-red-200">
          <h3 className="font-bold text-red-900 mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {t('dashboard.contextAnalysis.risksTitle')}
          </h3>
          <div className="space-y-2">
            {contextData.internal_insights?.riesgos_identificados?.length > 0 ? (
              contextData.internal_insights.riesgos_identificados.slice(0, 3).map((item, i) => (
                <div key={i} className="p-3 bg-white dark:bg-slate-800 rounded border border-red-200 dark:border-red-900">
                  <p className="text-sm text-slate-700 dark:text-slate-300">{item.texto}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-slate-500 dark:text-slate-400">{item.fuente}</span>
                    <span className="text-xs font-semibold text-red-600">
                      {t('dashboard.contextAnalysis.severityLabel')}: {item.severidad}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">{t('dashboard.contextAnalysis.noRisks')}</p>
            )}
          </div>
        </div>
      </div>

      {/* Info del análisis */}
      <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700">
        <div className="flex items-center justify-between text-sm text-slate-600 dark:text-slate-400">
          <span className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            {t('dashboard.contextAnalysis.documentsProcessed', { count: contextData.total_documents_processed || 0 })}
          </span>
          <span>
            {t('dashboard.contextAnalysis.lastUpdate')}: {contextData.timestamp ? new Date(contextData.timestamp).toLocaleString(language === 'es-LATAM' ? 'es-ES' : language) : t('dashboard.contextAnalysis.notAvailable')}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ContextAnalysis;