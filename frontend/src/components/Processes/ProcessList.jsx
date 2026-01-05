import React from 'react';
import { Package, Briefcase, Settings, AlertCircle, Target, Users } from 'lucide-react';

const ProcessList = ({ processesByType, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!processesByType) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500 text-center py-8">No hay procesos disponibles</p>
      </div>
    );
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'strategic': return <Target className="h-5 w-5" />;
      case 'operational': return <Briefcase className="h-5 w-5" />;
      case 'support': return <Settings className="h-5 w-5" />;
      default: return <Package className="h-5 w-5" />;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'strategic': return 'border-purple-200 bg-purple-50';
      case 'operational': return 'border-blue-200 bg-blue-50';
      case 'support': return 'border-green-200 bg-green-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getTypeBadgeColor = (type) => {
    switch (type) {
      case 'strategic': return 'bg-purple-100 text-purple-800';
      case 'operational': return 'bg-blue-100 text-blue-800';
      case 'support': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const typeNames = {
    'strategic': 'Procesos Estratégicos',
    'operational': 'Procesos Operativos',
    'support': 'Procesos de Apoyo'
  };

  return (
    <div className="space-y-6">
      {Object.entries(processesByType).map(([type, processes]) => (
        <div key={type} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <div className={`p-2 rounded-lg ${getTypeBadgeColor(type)} mr-3`}>
              {getTypeIcon(type)}
            </div>
            <h3 className="text-lg font-semibold text-gray-900">
              {typeNames[type]} ({processes.length})
            </h3>
          </div>

          {processes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {processes.map((process) => (
                <div
                  key={process.id}
                  className={`border-2 rounded-lg p-4 ${getTypeColor(type)} hover:shadow-md transition-shadow`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <span className="font-mono text-sm font-semibold text-gray-700 mr-2">
                          {process.code}
                        </span>
                        {process.is_critical && (
                          <span className="flex items-center text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            CRÍTICO
                          </span>
                        )}
                      </div>
                      <h4 className="font-semibold text-gray-900 mt-1">
                        {process.name}
                      </h4>
                    </div>
                  </div>

                  {process.objective && (
                    <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                      {process.objective}
                    </p>
                  )}

                  <div className="flex items-center text-sm text-gray-600 mb-2">
                    <Users className="h-4 w-4 mr-1" />
                    <span className="font-medium">Responsable:</span>
                    <span className="ml-1">{process.owner}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                    <div>
                      <span className="font-medium">Entradas:</span> {process.inputs?.length || 0}
                    </div>
                    <div>
                      <span className="font-medium">Salidas:</span> {process.outputs?.length || 0}
                    </div>
                    <div>
                      <span className="font-medium">KPIs:</span> {process.kpis?.length || 0}
                    </div>
                    <div>
                      <span className="font-medium">Actividades:</span> {process.activities_count || 0}
                    </div>
                  </div>

                  {process.criticality_score !== undefined && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600">Criticidad:</span>
                        <div className="flex items-center">
                          <div className="w-24 h-2 bg-gray-200 rounded-full mr-2">
                            <div
                              className={`h-2 rounded-full ${
                                process.criticality_score >= 0.7 ? 'bg-red-500' :
                                process.criticality_score >= 0.5 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${process.criticality_score * 100}%` }}
                            />
                          </div>
                          <span className="font-semibold">
                            {(process.criticality_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm italic">No hay procesos en esta categoría</p>
          )}
        </div>
      ))}
    </div>
  );
};

export default ProcessList;