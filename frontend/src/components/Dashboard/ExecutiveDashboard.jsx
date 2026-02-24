import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Download, Shield } from 'lucide-react';
import { apiService } from '../../services/api';
import MetricsGrid from './MetricsGrid';
import RiskMatrix from './RiskMatrix';
import QualityObjectives from './QualityObjectives';
import ContextAnalysis from './ContextAnalysis';

const ExecutiveDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  const loadDashboardData = useCallback(async () => {
    try {
      const response = await apiService.getDashboardSummary();
      setDashboardData(response.data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    queueMicrotask(() => {
      void loadDashboardData();
    });
    
    // Actualizar cada 2 minutos
    const interval = setInterval(() => {
      void loadDashboardData();
    }, 120000);
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  const handleRefresh = () => {
    setLoading(true);
    loadDashboardData();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 transition-colors duration-300">
      {/* Header del Dashboard */}
      <div className="bg-white dark:bg-slate-800 shadow-sm dark:shadow-slate-900/50 border-b border-slate-200 dark:border-slate-700 mb-8 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                Dashboard Ejecutivo
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-1">
                Sistema Inteligente de Gobierno de la Calidad - ISO 9001:2015
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              {lastUpdate && (
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  Última actualización: {lastUpdate.toLocaleTimeString('es-ES')}
                </span>
              )}
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="px-4 py-2 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg font-semibold border-2 border-slate-300 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 transition-all flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Actualizar
              </button>
              <button className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg flex items-center gap-2">
                <Download className="w-4 h-4" />
                Exportar Reporte
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Contenido del Dashboard */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12 space-y-8">
        {/* Grid de Métricas */}
        <MetricsGrid data={dashboardData} loading={loading} />

        {/* Análisis de Contexto */}
        <ContextAnalysis />

        {/* Matriz de Riesgos y Objetivos */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <div>
            <RiskMatrix />
          </div>
          <div>
            <QualityObjectives objectives={dashboardData?.objectives_data || []} />
          </div>
        </div>

        {/* Footer con Cumplimiento ISO */}
        <div className="card bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Shield className="w-12 h-12" />
              <div>
                <h3 className="text-xl font-bold mb-2">Estado de Cumplimiento ISO 9001:2015</h3>
                <p className="text-blue-100">
                  Cláusulas 4.1-4.4, 6.1-6.3 • Cumplimiento ISO/IEC 42001:2023 (IA Responsable)
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-5xl font-bold">95%</div>
              <div className="text-blue-100 text-lg">Cumplimiento Global</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExecutiveDashboard;