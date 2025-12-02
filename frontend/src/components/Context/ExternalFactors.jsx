import React from 'react';
import { Globe, TrendingUp, Users, Briefcase, Scale, Zap } from 'lucide-react';

const ExternalFactors = ({ factors, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const getIcon = (type) => {
    const normalizedType = (type || '').toLowerCase();
    switch (normalizedType) {
      case 'económico':
      case 'economico':
        return <TrendingUp className="h-6 w-6" />;
      case 'social':
        return <Users className="h-6 w-6" />;
      case 'político':
      case 'politico':
        return <Scale className="h-6 w-6" />;
      case 'tecnológico':
      case 'tecnologico':
        return <Zap className="h-6 w-6" />;
      case 'competitivo':
        return <Briefcase className="h-6 w-6" />;
      default:
        return <Globe className="h-6 w-6" />;
    }
  };

  const getColorClass = (impact) => {
    const normalizedImpact = (impact || '').toLowerCase();
    if (normalizedImpact === 'alto') return 'bg-red-100 text-red-800 border-red-300';
    if (normalizedImpact === 'medio') return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-blue-100 text-blue-800 border-blue-300';
  };

  const getText = (value) => {
    if (typeof value === 'string') return value;
    if (typeof value === 'object' && value !== null) {
      return value.texto || value.descripcion || JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-6 flex items-center">
        <Globe className="mr-2 h-6 w-6 text-blue-500" />
        Factores Externos
      </h3>

      {!factors || factors.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No se identificaron factores externos</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {factors.map((factor, idx) => (
            <div 
              key={idx}
              className={`border-l-4 rounded-lg p-4 ${getColorClass(factor.impacto)} transition-all hover:shadow-md`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center">
                  {getIcon(factor.tipo)}
                  <span className="ml-2 font-semibold capitalize">{getText(factor.tipo)}</span>
                </div>
                <span className="text-xs px-2 py-1 rounded bg-white bg-opacity-50 capitalize">
                  {getText(factor.impacto)}
                </span>
              </div>
              <p className="text-sm text-gray-700">{getText(factor.descripcion)}</p>
              {factor.tendencia && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-600">
                    <span className="font-medium">Tendencia:</span> {getText(factor.tendencia)}
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

export default ExternalFactors;