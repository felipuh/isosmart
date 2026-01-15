import React, { useMemo } from 'react';
import { ArrowRight, GitBranch } from 'lucide-react';

const ProcessDiagram = ({ diagramData, processes, loading }) => {
  
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
            owner: p.owner || 'Sin asignar',
            is_critical: p.is_critical || false
          })),
          operational: operational.map(p => ({
            id: p.code || p.id,
            name: p.name,
            owner: p.owner || 'Sin asignar',
            is_critical: p.is_critical || false
          })),
          support: support.map(p => ({
            id: p.code || p.id,
            name: p.name,
            owner: p.owner || 'Sin asignar',
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
  }, [processes, diagramData]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-96 bg-gray-200 rounded"></div>
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
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Mapa de Procesos</h3>
        <p className="text-gray-500 text-center py-8">No hay procesos disponibles. Ejecuta el mapeo con IA o agrega procesos manualmente.</p>
      </div>
    );
  }

  const { layers, statistics } = combinedData;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold">Mapa de Procesos</h3>
        <div className="flex items-center text-sm text-gray-600">
          <GitBranch className="h-4 w-4 mr-1" />
          <span>{statistics?.total_interactions || 0} interacciones</span>
        </div>
      </div>

      {/* Diagrama por capas */}
      <div className="space-y-4">
        {/* Procesos Estratégicos */}
        {layers.strategic && layers.strategic.length > 0 && (
          <div className="border-2 border-purple-200 rounded-lg p-4 bg-purple-50">
            <h4 className="text-sm font-semibold text-purple-900 mb-3">
              ESTRATÉGICOS ({layers.strategic.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {layers.strategic.map((process, index) => (
                <div
                  key={process.id || index}
                  className={'p-3 rounded-lg border-2 ' + (
                    process.is_critical
                      ? 'bg-red-50 border-red-300'
                      : 'bg-white border-purple-200'
                  )}
                >
                  <div className="text-xs font-mono text-purple-700 mb-1">{process.id}</div>
                  <div className="text-sm font-semibold text-gray-900">{process.name}</div>
                  <div className="text-xs text-gray-600 mt-1">{process.owner}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Flecha hacia abajo */}
        {layers.strategic && layers.strategic.length > 0 && layers.operational && layers.operational.length > 0 && (
          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
          </div>
        )}

        {/* Procesos Operativos */}
        {layers.operational && layers.operational.length > 0 && (
          <div className="border-2 border-blue-200 rounded-lg p-4 bg-blue-50">
            <h4 className="text-sm font-semibold text-blue-900 mb-3">
              OPERATIVOS ({layers.operational.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {layers.operational.map((process, index) => (
                <div
                  key={process.id || index}
                  className={'p-3 rounded-lg border-2 ' + (
                    process.is_critical
                      ? 'bg-red-50 border-red-300'
                      : 'bg-white border-blue-200'
                  )}
                >
                  <div className="text-xs font-mono text-blue-700 mb-1">{process.id}</div>
                  <div className="text-sm font-semibold text-gray-900">{process.name}</div>
                  <div className="text-xs text-gray-600 mt-1">{process.owner}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Flecha hacia abajo */}
        {layers.operational && layers.operational.length > 0 && layers.support && layers.support.length > 0 && (
          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
          </div>
        )}

        {/* Procesos de Apoyo */}
        {layers.support && layers.support.length > 0 && (
          <div className="border-2 border-green-200 rounded-lg p-4 bg-green-50">
            <h4 className="text-sm font-semibold text-green-900 mb-3">
              APOYO ({layers.support.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {layers.support.map((process, index) => (
                <div
                  key={process.id || index}
                  className={'p-3 rounded-lg border-2 ' + (
                    process.is_critical
                      ? 'bg-red-50 border-red-300'
                      : 'bg-white border-green-200'
                  )}
                >
                  <div className="text-xs font-mono text-green-700 mb-1">{process.id}</div>
                  <div className="text-sm font-semibold text-gray-900">{process.name}</div>
                  <div className="text-xs text-gray-600 mt-1">{process.owner}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Estadísticas */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-purple-600">
              {statistics?.total_processes || 0}
            </p>
            <p className="text-xs text-gray-600">Total Procesos</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-red-600">
              {statistics?.critical_processes || 0}
            </p>
            <p className="text-xs text-gray-600">Críticos</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-blue-600">
              {statistics?.total_interactions || 0}
            </p>
            <p className="text-xs text-gray-600">Interacciones</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">
              {((statistics?.network_density || 0) * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-600">Densidad Red</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessDiagram;