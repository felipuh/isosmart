import React from 'react';
import { AlertTriangle, Shield, TrendingUp } from 'lucide-react';

const IdentifiedRisks = ({ riesgos, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const getSeverityColor = (severidad) => {
    switch (severidad?.toLowerCase()) {
      case 'crítico':
      case 'alto':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'medio':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'bajo':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getSeverityIcon = (severidad) => {
    switch (severidad?.toLowerCase()) {
      case 'crítico':
      case 'alto':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'medio':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Shield className="h-5 w-5 text-blue-500" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-6 flex items-center">
        <AlertTriangle className="mr-2 h-6 w-6 text-red-500" />
        Riesgos Identificados ({riesgos?.length || 0})
      </h3>

      {!riesgos || riesgos.length === 0 ? (
        <div className="text-center py-8">
          <Shield className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <p className="text-gray-500">No se identificaron riesgos críticos</p>
        </div>
      ) : (
        <div className="space-y-4">
          {riesgos.map((riesgo, idx) => (
            <div 
              key={idx}
              className={`border-l-4 rounded-lg p-4 ${getSeverityColor(riesgo.severidad)} transition-all hover:shadow-md`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center flex-1">
                  {getSeverityIcon(riesgo.severidad)}
                  <h4 className="ml-2 font-semibold text-gray-900">{riesgo.texto}</h4>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full font-semibold ${getSeverityColor(riesgo.severidad)}`}>
                  {riesgo.severidad?.toUpperCase()}
                </span>
              </div>

              {riesgo.descripcion && (
                <p className="text-sm text-gray-700 mb-3 ml-7">{riesgo.descripcion}</p>
              )}

              {riesgo.mitigacion && (
                <div className="ml-7 mt-3 pt-3 border-t border-gray-200">
                  <div className="flex items-start">
                    <TrendingUp className="h-4 w-4 text-green-600 mr-2 mt-0.5" />
                    <div>
                      <p className="text-xs font-medium text-gray-600 mb-1">Plan de Mitigación:</p>
                      <p className="text-sm text-gray-700">{riesgo.mitigacion}</p>
                    </div>
                  </div>
                </div>
              )}

              {riesgo.categoria && (
                <div className="mt-3 ml-7">
                  <span className="text-xs bg-white bg-opacity-50 px-2 py-1 rounded">
                    Categoría: {riesgo.categoria}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default IdentifiedRisks;