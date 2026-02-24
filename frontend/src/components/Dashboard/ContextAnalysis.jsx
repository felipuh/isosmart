import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, AlertCircle, FileText, RefreshCw } from 'lucide-react';
import { apiService } from '../../services/api';
import { useI18n } from '../../context/I18nContext';

const ContextAnalysis = () => {
  const { t } = useI18n();
  const [contextData, setContextData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    loadContextAnalysis();
  }, []);

  const loadContextAnalysis = async () => {
    try {
      setLoading(true);
      const response = await apiService.getLatestContextAnalysis();
      setContextData(response.data);
    } catch (error) {
      console.error('Error loading context analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerAnalysis = async () => {
    try {
      setTriggering(true);
      await apiService.triggerContextAnalysis();
      
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
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-100 rounded"></div>
          <div className="h-32 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (!contextData) {
    return (
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Brain className="w-6 h-6 text-purple-600" />
          Análisis de Contexto (ISO 4.1)
        </h2>
        <div className="text-center py-12">
          <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500 mb-4">{t('literals.No hay análisis de contexto disponible')}</p>
          <button
            onClick={triggerAnalysis}
            disabled={triggering}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50"
          >
            {triggering ? (
              <span className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin" />
                Analizando...
              </span>
            ) : (
              'Iniciar Análisis'
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="w-6 h-6 text-purple-600" />
          Análisis de Contexto Inteligente (ISO 4.1)
        </h2>
        <button
          onClick={triggerAnalysis}
          disabled={triggering}
          className="px-4 py-2 bg-white text-gray-700 rounded-lg font-semibold border-2 border-gray-300 hover:border-blue-500 hover:text-blue-600 transition-all disabled:opacity-50"
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
            Fortalezas Identificadas
          </h3>
          <div className="space-y-2">
            {contextData.internal_insights?.fortalezas?.length > 0 ? (
              contextData.internal_insights.fortalezas.slice(0, 3).map((item, i) => (
                <div key={i} className="p-3 bg-white rounded border border-green-200">
                  <p className="text-sm text-gray-700">{item.texto}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-500">{item.fuente}</span>
                    <span className="text-xs font-semibold text-green-600">
                      {Math.round(item.confianza * 100)}% confianza
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">{t('literals.No se identificaron fortalezas')}</p>
            )}
          </div>
        </div>

        {/* Riesgos */}
        <div className="p-4 bg-red-50 rounded-lg border-2 border-red-200">
          <h3 className="font-bold text-red-900 mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Riesgos Identificados
          </h3>
          <div className="space-y-2">
            {contextData.internal_insights?.riesgos_identificados?.length > 0 ? (
              contextData.internal_insights.riesgos_identificados.slice(0, 3).map((item, i) => (
                <div key={i} className="p-3 bg-white rounded border border-red-200">
                  <p className="text-sm text-gray-700">{item.texto}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-500">{item.fuente}</span>
                    <span className="text-xs font-semibold text-red-600">
                      Severidad: {item.severidad}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">{t('literals.No se identificaron riesgos')}</p>
            )}
          </div>
        </div>
      </div>

      {/* Info del análisis */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            {contextData.total_documents_processed || 0} documentos procesados
          </span>
          <span>
            Última actualización: {contextData.timestamp ? new Date(contextData.timestamp).toLocaleString('es-ES') : 'No disponible'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ContextAnalysis;