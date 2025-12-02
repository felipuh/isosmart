import React from 'react';
import { Lightbulb, ArrowRight, CheckCircle2 } from 'lucide-react';

const Recommendations = ({ recomendaciones, loading }) => {
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

  const getPriorityColor = (prioridad) => {
    switch (prioridad?.toLowerCase()) {
      case 'alta':
        return 'border-l-red-500 bg-red-50';
      case 'media':
        return 'border-l-yellow-500 bg-yellow-50';
      case 'baja':
        return 'border-l-blue-500 bg-blue-50';
      default:
        return 'border-l-gray-500 bg-gray-50';
    }
  };

  const getPriorityBadge = (prioridad) => {
    switch (prioridad?.toLowerCase()) {
      case 'alta':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'media':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'baja':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-6 flex items-center">
        <Lightbulb className="mr-2 h-6 w-6 text-yellow-500" />
        Recomendaciones de IA ({recomendaciones?.length || 0})
      </h3>

      {!recomendaciones || recomendaciones.length === 0 ? (
        <div className="text-center py-8">
          <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <p className="text-gray-500">No hay recomendaciones pendientes</p>
          <p className="text-sm text-gray-400 mt-2">¡Todo está en orden!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {recomendaciones.map((rec, idx) => (
            <div 
              key={idx}
              className={`border-l-4 rounded-lg p-4 ${getPriorityColor(rec.prioridad)} transition-all hover:shadow-md`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <Lightbulb className="h-4 w-4 text-yellow-600 mr-2" />
                    <span className={`text-xs px-2 py-1 rounded border font-semibold ${getPriorityBadge(rec.prioridad)}`}>
                      {rec.prioridad?.toUpperCase() || 'MEDIA'}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-gray-900 mb-2">
                    {rec.texto || rec.recomendacion}
                  </p>
                  {rec.descripcion && (
                    <p className="text-sm text-gray-600">{rec.descripcion}</p>
                  )}
                </div>
              </div>

              {rec.acciones && rec.acciones.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs font-medium text-gray-600 mb-2">Acciones sugeridas:</p>
                  <ul className="space-y-1">
                    {rec.acciones.map((accion, actionIdx) => (
                      <li key={actionIdx} className="flex items-start text-sm text-gray-700">
                        <ArrowRight className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                        <span>{accion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {rec.beneficio && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-600">
                    <span className="font-medium">Beneficio esperado:</span> {rec.beneficio}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Recommendations;