import React from 'react';
import { TrendingUp, TrendingDown, Shield, AlertTriangle } from 'lucide-react';

const FODAAnalysis = ({ fortalezas, oportunidades, debilidades, amenazas, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-40 bg-gray-200 rounded"></div>
            <div className="h-40 bg-gray-200 rounded"></div>
            <div className="h-40 bg-gray-200 rounded"></div>
            <div className="h-40 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // Función para extraer texto de un item (puede ser string u objeto)
  const getItemText = (item) => {
    if (typeof item === 'string') return item;
    if (typeof item === 'object' && item !== null) {
      return item.texto || item.descripcion || JSON.stringify(item);
    }
    return String(item);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-6">Análisis FODA</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Fortalezas */}
        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-5">
          <div className="flex items-center mb-4">
            <div className="bg-green-500 rounded-full p-2 mr-3">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-green-900">Fortalezas</h4>
          </div>
          <ul className="space-y-2">
            {fortalezas && fortalezas.length > 0 ? (
              fortalezas.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  <span className="text-sm text-gray-700">{getItemText(item)}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-gray-500 italic">No se identificaron fortalezas</li>
            )}
          </ul>
        </div>

        {/* Oportunidades */}
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-5">
          <div className="flex items-center mb-4">
            <div className="bg-blue-500 rounded-full p-2 mr-3">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-blue-900">Oportunidades</h4>
          </div>
          <ul className="space-y-2">
            {oportunidades && oportunidades.length > 0 ? (
              oportunidades.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span className="text-sm text-gray-700">{getItemText(item)}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-gray-500 italic">No se identificaron oportunidades</li>
            )}
          </ul>
        </div>

        {/* Debilidades */}
        <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-5">
          <div className="flex items-center mb-4">
            <div className="bg-yellow-500 rounded-full p-2 mr-3">
              <TrendingDown className="h-5 w-5 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-yellow-900">Debilidades</h4>
          </div>
          <ul className="space-y-2">
            {debilidades && debilidades.length > 0 ? (
              debilidades.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-yellow-600 mr-2">•</span>
                  <span className="text-sm text-gray-700">{getItemText(item)}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-gray-500 italic">No se identificaron debilidades</li>
            )}
          </ul>
        </div>

        {/* Amenazas */}
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-5">
          <div className="flex items-center mb-4">
            <div className="bg-red-500 rounded-full p-2 mr-3">
              <AlertTriangle className="h-5 w-5 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-red-900">Amenazas</h4>
          </div>
          <ul className="space-y-2">
            {amenazas && amenazas.length > 0 ? (
              amenazas.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  <span className="text-sm text-gray-700">{getItemText(item)}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-gray-500 italic">No se identificaron amenazas</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FODAAnalysis;