import React, { useState, useEffect } from 'react';
import { RefreshCw, Download, TrendingUp, AlertCircle, CheckCircle, FileText } from 'lucide-react';
import contextService from '../../services/contextService';
import FODAAnalysis from './FODAAnalysis';
import ExternalFactors from './ExternalFactors';
import InternalFactors from './InternalFactors';
import IdentifiedRisks from './IdentifiedRisks';
import Recommendations from './Recommendations';

const ContextDashboard = () => {
  const [contextData, setContextData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    loadContextData();
  }, []);

  const loadContextData = async () => {
    setLoading(true);
    try {
      const data = await contextService.getLatest();
      setContextData(data);
      if (data.timestamp) {
        setLastUpdate(new Date(data.timestamp));
      }
    } catch (error) {
      console.error('Error cargando datos de contexto:', error);
    } finally {
      setLoading(false);
    }
  };

const handleRunAnalysis = async () => {
  // Verificar si hay documentos
  if (!contextData || contextData.total_documents_processed === 0) {
    alert('⚠️ No hay documentos para analizar\n\n' +
          'Para ejecutar el análisis de contexto, primero debes subir documentos organizacionales.\n\n' +
          'Tipos de documentos recomendados:\n' +
          '- Políticas de calidad\n' +
          '- Manuales de procesos\n' +
          '- Informes de gestión\n' +
          '- Análisis FODA previos\n' +
          '- Planes estratégicos');
    return;
  }

  setAnalyzing(true);
  try {
    const result = await contextService.triggerAnalysis();
    console.log('Análisis completado:', result);
    
    await loadContextData();
    
    alert(`✅ Análisis de contexto completado!\n\n` +
          `Documentos procesados: ${result.total_documents || 0}\n` +
          `Fortalezas: ${result.internal_insights?.fortalezas?.length || 0}\n` +
          `Riesgos: ${result.internal_insights?.riesgos_identificados?.length || 0}`);
  } catch (error) {
    console.error('Error ejecutando análisis:', error);
    
    // Mensaje más informativo
    if (error.response?.status === 500) {
      alert('❌ Error en el servidor al ejecutar el análisis\n\n' +
            'Posibles causas:\n' +
            '- No hay documentos en el sistema\n' +
            '- Error en el procesamiento de IA\n' +
            '- Problema con ChromaDB\n\n' +
            'Por favor, contacta al administrador del sistema.');
    } else {
      alert('❌ Error al ejecutar el análisis de contexto\n\n' + 
            'Verifica tu conexión e intenta nuevamente.');
    }
  } finally {
    setAnalyzing(false);
  }
};

  const formatDate = (date) => {
    if (!date) return 'No disponible';
    return new Intl.DateTimeFormat('es-ES', {
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
          Análisis de Contexto Organizacional
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          ISO 4.1 - Comprensión de la organización y su contexto
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70 border border-white/20 dark:border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Documentos Analizados</p>
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
              <p className="text-sm text-slate-600 dark:text-slate-400">Fortalezas</p>
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
              <p className="text-sm text-slate-600 dark:text-slate-400">Riesgos</p>
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
              <p className="text-sm text-slate-600 dark:text-slate-400">Factores Externos</p>
              <p className="text-3xl font-bold text-purple-600">
                {externalInsights.factores_externos?.length || 0}
              </p>
            </div>
            <TrendingUp className="h-10 w-10 text-purple-400" />
          </div>
        </div>
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
              {analyzing ? 'Analizando...' : 'Ejecutar Análisis IA'}
            </button>

            <button
              onClick={loadContextData}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Actualizar
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-600 dark:text-slate-400">
              Última actualización: {formatDate(lastUpdate)}
            </span>
            <button className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
              <Download className="mr-2 h-4 w-4" />
              Exportar
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
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
      </div>
    </div>
  );
};

export default ContextDashboard;