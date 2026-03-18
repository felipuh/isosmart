import React, { useMemo } from 'react';
import { ArrowRight, GitBranch } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ProcessDiagram = ({ diagramData, processes, loading }) => {
  const { t } = useI18n();
  
  // Combinar datos del diagrama IA con procesos manuales
  const combinedData = useMemo(() => {
    // Si hay procesos directos, usarlos para construir las capas
    if (processes && processes.length > 0) {
      const strategic = processes.filter(p => p.process_type === 'strategic');
      const operational = processes.filter(p => p.process_type === 'operational');
      const support = processes.filter(p => p.process_type === 'support');
      
      return {
        layers: {
          strategic: strategic.map(p => ({
            id: p.code || p.id,
            name: p.name,
            owner: p.owner || t('processDiagram.unassigned'),
            is_critical: p.is_critical || false
          })),
          operational: operational.map(p => ({
            id: p.code || p.id,
            name: p.name,
            owner: p.owner || t('processDiagram.unassigned'),
            is_critical: p.is_critical || false
          })),
          support: support.map(p => ({
            id: p.code || p.id,
            name: p.name,
            owner: p.owner || t('processDiagram.unassigned'),
            is_critical: p.is_critical || false
          }))
        },
        statistics: {
          total_processes: processes.length,
          critical_processes: processes.filter(p => p.is_critical).length,
          total_interactions: diagramData?.statistics?.total_interactions || 0,
          network_density: diagramData?.statistics?.network_density || 0
        },
        connections: diagramData?.connections || []
      };
    }
    
    // Si no hay procesos directos, usar datos del diagrama IA
    return diagramData;
  }, [diagramData, processes, t]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="h-96 bg-slate-200 dark:bg-slate-700 rounded"></div>
        </div>
      </div>
    );
  }

  const hasData = combinedData && combinedData.layers && (
    (combinedData.layers.strategic && combinedData.layers.strategic.length > 0) ||
    (combinedData.layers.operational && combinedData.layers.operational.length > 0) ||
    (combinedData.layers.support && combinedData.layers.support.length > 0)
  );

  if (!hasData) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">{t('processDiagram.title')}</h3>
        <p className="text-slate-500 dark:text-slate-400 text-center py-8">{t('processDiagram.empty')}</p>
      </div>
    );
  }

  const { layers, statistics } = combinedData;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-slate-900 dark:text-white">{t('processDiagram.title')}</h3>
        <div className="flex items-center text-sm text-slate-600 dark:text-slate-400 transition-colors">
          <GitBranch className="h-4 w-4 mr-1" />
          <span>{statistics?.total_interactions || 0} {t('processDiagram.interactions')}</span>
        </div>
      </div>

      {/* Diagrama por capas */}
      <div className="space-y-4">
        {/* Procesos Estratégicos */}
        {layers.strategic && layers.strategic.length > 0 && (
          <div className="border-2 border-purple-200 dark:border-purple-700 rounded-lg p-4 bg-purple-50 dark:bg-purple-900/30 transition-colors">
            <h4 className="text-sm font-semibold text-purple-900 dark:text-purple-300 mb-3">
              {t('processDiagram.layers.strategic').toUpperCase()} ({layers.strategic.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {layers.strategic.map((process, index) => (
                <div
                  key={process.id || index}
                  className={'p-3 rounded-lg border-2 transition-colors ' + (
                    process.is_critical
                      ? 'bg-red-50 dark:bg-red-900/30 border-red-300 dark:border-red-600'
                      : 'bg-white dark:bg-slate-700 border-purple-200 dark:border-purple-700'
                  )}
                >
                  <div className="text-xs font-mono text-purple-700 dark:text-purple-300 mb-1">{process.id}</div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">{process.name}</div>
                  <div className="text-xs text-gray-600 dark:text-slate-400 mt-1">{process.owner}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Flecha hacia abajo */}
        {layers.strategic && layers.strategic.length > 0 && layers.operational && layers.operational.length > 0 && (
          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-gray-400 dark:text-slate-500 transform rotate-90 transition-colors" />
          </div>
        )}

        {/* Procesos Operativos */}
        {layers.operational && layers.operational.length > 0 && (
          <div className="border-2 border-blue-200 dark:border-blue-700 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/30 transition-colors">
            <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-3">
              {t('processDiagram.layers.operational').toUpperCase()} ({layers.operational.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {layers.operational.map((process, index) => (
                <div
                  key={process.id || index}
                  className={'p-3 rounded-lg border-2 transition-colors ' + (
                    process.is_critical
                      ? 'bg-red-50 dark:bg-red-900/30 border-red-300 dark:border-red-600'
                      : 'bg-white dark:bg-slate-700 border-blue-200 dark:border-blue-700'
                  )}
                >
                  <div className="text-xs font-mono text-blue-700 dark:text-blue-300 mb-1">{process.id}</div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">{process.name}</div>
                  <div className="text-xs text-gray-600 dark:text-slate-400 mt-1">{process.owner}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Flecha hacia abajo */}
        {layers.operational && layers.operational.length > 0 && layers.support && layers.support.length > 0 && (
          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-gray-400 dark:text-slate-500 transform rotate-90 transition-colors" />
          </div>
        )}

        {/* Procesos de Apoyo */}
        {layers.support && layers.support.length > 0 && (
          <div className="border-2 border-green-200 dark:border-green-700 rounded-lg p-4 bg-green-50 dark:bg-green-900/30 transition-colors">
            <h4 className="text-sm font-semibold text-green-900 dark:text-green-300 mb-3">
              {t('processDiagram.layers.support').toUpperCase()} ({layers.support.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {layers.support.map((process, index) => (
                <div
                  key={process.id || index}
                  className={'p-3 rounded-lg border-2 transition-colors ' + (
                    process.is_critical
                      ? 'bg-red-50 dark:bg-red-900/30 border-red-300 dark:border-red-600'
                      : 'bg-white dark:bg-slate-700 border-green-200 dark:border-green-700'
                  )}
                >
                  <div className="text-xs font-mono text-green-700 dark:text-green-300 mb-1">{process.id}</div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">{process.name}</div>
                  <div className="text-xs text-gray-600 dark:text-slate-400 mt-1">{process.owner}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Estadísticas */}
      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-slate-700 transition-colors">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {statistics?.total_processes || 0}
            </p>
            <p className="text-xs text-gray-600 dark:text-slate-400">{t('processDiagram.stats.totalProcesses')}</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">
              {statistics?.critical_processes || 0}
            </p>
            <p className="text-xs text-gray-600 dark:text-slate-400">{t('processDiagram.stats.critical')}</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {statistics?.total_interactions || 0}
            </p>
            <p className="text-xs text-gray-600 dark:text-slate-400">{t('processDiagram.stats.interactions')}</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {((statistics?.network_density || 0) * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-600 dark:text-slate-400">{t('processDiagram.stats.networkDensity')}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessDiagram;