import React from 'react';
import { Target, TrendingUp, Users, ShieldCheck } from 'lucide-react';

const CoverageAnalysis = ({ coverageData, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-4 gap-4">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!coverageData) {
    return null;
  }

  const overallScore = coverageData.overall_score || 0;
  const gaps = coverageData.gaps || [];
  const recommendations = coverageData.recommendations || [];

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 90) return 'bg-green-50';
    if (score >= 70) return 'bg-blue-50';
    if (score >= 50) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-6">Análisis de Cobertura</h3>

      {/* Score General */}
      <div className={`${getScoreBg(overallScore)} rounded-lg p-6 mb-6 text-center`}>
        <p className="text-sm text-gray-600 mb-2">Cobertura General del Alcance</p>
        <p className={`text-5xl font-bold ${getScoreColor(overallScore)}`}>
          {overallScore.toFixed(1)}%
        </p>
        <p className="text-sm text-gray-600 mt-2">
          {overallScore >= 90 ? 'Excelente cobertura' :
           overallScore >= 70 ? 'Buena cobertura' :
           overallScore >= 50 ? 'Cobertura aceptable' : 'Requiere mejoras'}
        </p>
      </div>

      {/* Desglose por categoría */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Target className="h-6 w-6 text-blue-500" />
            <span className="text-sm font-semibold text-blue-800">
              {coverageData.products_coverage?.score?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs text-gray-700">Productos/Servicios</p>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Users className="h-6 w-6 text-green-500" />
            <span className="text-sm font-semibold text-green-800">
              {coverageData.stakeholder_coverage?.score?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs text-gray-700">Stakeholders</p>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="h-6 w-6 text-purple-500" />
            <span className="text-sm font-semibold text-purple-800">
              {coverageData.process_coverage?.score?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs text-gray-700">Procesos</p>
        </div>

        <div className="bg-orange-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <ShieldCheck className="h-6 w-6 text-orange-500" />
            <span className="text-sm font-semibold text-orange-800">
              {coverageData.risk_coverage?.score?.toFixed(0) || 0}%
            </span>
          </div>
          <p className="text-xs text-gray-700">Riesgos</p>
        </div>
      </div>

      {/* Gaps identificados */}
      {gaps.length > 0 && (
        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-3">Brechas Identificadas</h4>
          <div className="space-y-2">
            {gaps.map((gap, idx) => (
              <div key={idx} className="flex items-start bg-red-50 border-l-4 border-red-400 p-3 rounded">
                <span className="text-red-600 mr-2">⚠</span>
                <span className="text-sm text-red-800">{gap}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recomendaciones */}
      {recommendations.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-900 mb-3">Recomendaciones</h4>
          <div className="space-y-2">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="flex items-start bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
                <span className="text-blue-600 mr-2">💡</span>
                <span className="text-sm text-blue-800">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CoverageAnalysis;