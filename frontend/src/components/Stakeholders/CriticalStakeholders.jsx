import React from 'react';
import { AlertTriangle, TrendingUp, Users, Activity } from 'lucide-react';

const CriticalStakeholders = ({ stakeholders, loading }) => {
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

  if (!stakeholders || stakeholders.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Users className="mr-2 h-5 w-5" />
          Stakeholders Críticos
        </h3>
        <p className="text-gray-500 text-center py-8">
          No hay stakeholders críticos identificados
        </p>
      </div>
    );
  }

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'CRÍTICO': return 'bg-red-100 text-red-800 border-red-300';
      case 'ALTO': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'MEDIO': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default: return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  const getInfluenceColor = (score) => {
    if (score >= 0.8) return 'text-red-600';
    if (score >= 0.6) return 'text-orange-600';
    return 'text-yellow-600';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <AlertTriangle className="mr-2 h-5 w-5 text-red-500" />
        Stakeholders Críticos ({stakeholders.length})
      </h3>

      <div className="space-y-4">
        {stakeholders.map((sh) => (
          <div
            key={sh.stakeholder_id || sh.id}
            className={`border-l-4 rounded-lg p-4 ${getRiskColor(sh.risk_level)} transition-all hover:shadow-md`}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">{sh.name}</h4>
                <p className="text-sm text-gray-600 capitalize">{sh.type}</p>
              </div>
              <div className="flex flex-col items-end">
                <span className={`text-2xl font-bold ${getInfluenceColor(sh.composite_score)}`}>
                  {(sh.composite_score * 100).toFixed(0)}%
                </span>
                <span className="text-xs text-gray-500">Influencia</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="flex items-center text-sm">
                <TrendingUp className="h-4 w-4 mr-1 text-gray-500" />
                <span className="text-gray-600">Poder:</span>
                <span className="ml-1 font-medium capitalize">{sh.power}</span>
              </div>
              <div className="flex items-center text-sm">
                <Activity className="h-4 w-4 mr-1 text-gray-500" />
                <span className="text-gray-600">Interés:</span>
                <span className="ml-1 font-medium capitalize">{sh.interest}</span>
              </div>
            </div>

            {sh.engagement_strategy && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Estrategia:</span> {sh.engagement_strategy}
                </p>
              </div>
            )}

            <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200">
              <span className="text-xs font-medium px-2 py-1 rounded bg-gray-100">
                {sh.is_hub && '🌟 Hub'} {sh.is_broker && '🔗 Broker'}
              </span>
              <span className="text-xs text-gray-500">
                {sh.connections} conexiones
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CriticalStakeholders;