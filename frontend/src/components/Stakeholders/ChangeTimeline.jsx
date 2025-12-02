import React from 'react';
import { Clock, AlertCircle, TrendingDown, TrendingUp, Activity } from 'lucide-react';

const ChangeTimeline = ({ changes, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!changes || changes.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Clock className="mr-2 h-5 w-5" />
          Cambios Recientes
        </h3>
        <p className="text-gray-500 text-center py-8">No hay cambios registrados</p>
      </div>
    );
  }

  const getChangeIcon = (changeType) => {
    if (changeType.includes('alto')) return <AlertCircle className="h-5 w-5 text-red-500" />;
    if (changeType.includes('drop')) return <TrendingDown className="h-5 w-5 text-red-500" />;
    if (changeType.includes('increase')) return <TrendingUp className="h-5 w-5 text-green-500" />;
    return <Activity className="h-5 w-5 text-blue-500" />;
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'alto': return 'bg-red-100 text-red-800 border-red-300';
      case 'medio': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'bajo': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `Hace ${diffMins} minutos`;
    if (diffHours < 24) return `Hace ${diffHours} horas`;
    if (diffDays < 7) return `Hace ${diffDays} días`;
    return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <Clock className="mr-2 h-5 w-5 text-blue-500" />
        Cambios Recientes ({changes.length})
      </h3>

      <div className="space-y-4">
        {changes.slice(0, 10).map((change, index) => (
          <div
            key={index}
            className="border-l-4 border-gray-300 pl-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <div className="mt-1">{getChangeIcon(change.change_type)}</div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-gray-900">{change.stakeholder_name}</h4>
                    {change.severity && (
                      <span className={`text-xs px-2 py-1 rounded border ${getSeverityColor(change.severity)}`}>
                        {change.severity.toUpperCase()}
                      </span>
                    )}
                  </div>
                  
                  {change.new_expectations && change.new_expectations.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm text-gray-600">Nuevas expectativas:</p>
                      <ul className="list-disc list-inside text-sm text-gray-700">
                        {change.new_expectations.map((exp, idx) => (
                          <li key={idx}>{exp}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {change.removed_expectations && change.removed_expectations.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm text-gray-600">Expectativas removidas:</p>
                      <ul className="list-disc list-inside text-sm text-gray-500 line-through">
                        {change.removed_expectations.map((exp, idx) => (
                          <li key={idx}>{exp}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {change.recommendation && (
                    <div className="mt-2 p-2 bg-blue-50 rounded text-sm text-blue-800">
                      💡 {change.recommendation}
                    </div>
                  )}
                </div>
              </div>
              
              <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                {formatDate(change.change_date)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChangeTimeline;
