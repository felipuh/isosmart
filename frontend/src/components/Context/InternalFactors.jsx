import React from 'react';
import { Building, CheckCircle, AlertCircle } from 'lucide-react';

const InternalFactors = ({ fortalezas, debilidades, loading }) => {
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

  // Función para extraer texto
  const getItemText = (item) => {
    if (typeof item === 'string') return item;
    if (typeof item === 'object' && item !== null) {
      return item.texto || item.descripcion || JSON.stringify(item);
    }
    return String(item);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-6 flex items-center">
        <Building className="mr-2 h-6 w-6 text-purple-500" />
        Factores Internos
      </h3>

      <div className="space-y-6">
        
        {/* Fortalezas */}
        <div>
          <div className="flex items-center mb-4">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            <h4 className="text-lg font-semibold text-gray-900">
              Fortalezas ({fortalezas?.length || 0})
            </h4>
          </div>
          
          {!fortalezas || fortalezas.length === 0 ? (
            <p className="text-gray-500 text-sm ml-7">No se identificaron fortalezas internas</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 ml-7">
              {fortalezas.map((item, idx) => (
                <div 
                  key={idx}
                  className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-start"
                >
                  <span className="text-green-600 mr-2 mt-0.5">✓</span>
                  <span className="text-sm text-gray-700">{getItemText(item)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Debilidades */}
        <div>
          <div className="flex items-center mb-4">
            <AlertCircle className="h-5 w-5 text-orange-500 mr-2" />
            <h4 className="text-lg font-semibold text-gray-900">
              Debilidades ({debilidades?.length || 0})
            </h4>
          </div>
          
          {!debilidades || debilidades.length === 0 ? (
            <p className="text-gray-500 text-sm ml-7">No se identificaron debilidades internas</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 ml-7">
              {debilidades.map((item, idx) => (
                <div 
                  key={idx}
                  className="bg-orange-50 border border-orange-200 rounded-lg p-3 flex items-start"
                >
                  <span className="text-orange-600 mr-2 mt-0.5">!</span>
                  <span className="text-sm text-gray-700">{getItemText(item)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InternalFactors;