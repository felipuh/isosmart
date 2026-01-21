import React, { useState, useEffect } from 'react';
import riskService from '../../services/riskService';

const RiskMatrixVisual = ({ onRiskClick }) => {
  const [matrixData, setMatrixData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);

  const probabilityLabels = {
    muy_alta: 'Muy Alta',
    alta: 'Alta',
    media: 'Media',
    baja: 'Baja',
    muy_baja: 'Muy Baja'
  };

  const impactLabels = {
    muy_bajo: 'Muy Bajo',
    bajo: 'Bajo',
    medio: 'Medio',
    alto: 'Alto',
    muy_alto: 'Muy Alto'
  };

  const probOrder = ['muy_alta', 'alta', 'media', 'baja', 'muy_baja'];
  const impactOrder = ['muy_bajo', 'bajo', 'medio', 'alto', 'muy_alto'];

  const getCellColor = (prob, impact) => {
    const probIndex = probOrder.indexOf(prob);
    const impactIndex = impactOrder.indexOf(impact);
    const riskScore = (4 - probIndex) + impactIndex;

    if (riskScore >= 6) return 'bg-red-500 hover:bg-red-600';
    if (riskScore >= 4) return 'bg-orange-500 hover:bg-orange-600';
    if (riskScore >= 2) return 'bg-yellow-400 hover:bg-yellow-500';
    return 'bg-green-500 hover:bg-green-600';
  };

  const getRiskLevelLabel = (prob, impact) => {
    const probIndex = probOrder.indexOf(prob);
    const impactIndex = impactOrder.indexOf(impact);
    const riskScore = (4 - probIndex) + impactIndex;

    if (riskScore >= 6) return 'Crítico';
    if (riskScore >= 4) return 'Alto';
    if (riskScore >= 2) return 'Medio';
    return 'Bajo';
  };

  useEffect(() => {
    loadMatrixData();
  }, []);

  const loadMatrixData = async () => {
    setLoading(true);
    try {
      const data = await riskService.getMatrixData();
      setMatrixData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCellClick = (prob, impact) => {
    if (matrixData?.matrix?.[prob]?.[impact]?.count > 0) {
      setSelectedCell({ prob, impact });
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
        <p className="text-red-600">{error}</p>
        <button onClick={loadMatrixData} className="mt-2 text-sm text-red-700 underline">Reintentar</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Leyenda de Niveles de Riesgo</h3>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center"><div className="w-4 h-4 bg-red-500 rounded mr-2"></div><span className="text-sm text-gray-600">Crítico</span></div>
          <div className="flex items-center"><div className="w-4 h-4 bg-orange-500 rounded mr-2"></div><span className="text-sm text-gray-600">Alto</span></div>
          <div className="flex items-center"><div className="w-4 h-4 bg-yellow-400 rounded mr-2"></div><span className="text-sm text-gray-600">Medio</span></div>
          <div className="flex items-center"><div className="w-4 h-4 bg-green-500 rounded mr-2"></div><span className="text-sm text-gray-600">Bajo</span></div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 overflow-x-auto">
        <h3 className="text-lg font-medium text-gray-900 mb-6 text-center">Matriz de Riesgos - Probabilidad vs Impacto</h3>
        
        <div className="min-w-[600px]">
          <div className="flex">
            <div className="w-28 flex-shrink-0"></div>
            <div className="flex-1 grid grid-cols-5 gap-1 mb-1">
              {impactOrder.map((impact) => (
                <div key={impact} className="text-center text-xs font-medium text-gray-600 py-2">{impactLabels[impact]}</div>
              ))}
            </div>
          </div>

          <div className="flex">
            <div className="w-28 flex-shrink-0 flex flex-col gap-1">
              {probOrder.map((prob) => (
                <div key={prob} className="h-16 flex items-center justify-end pr-3 text-xs font-medium text-gray-600">{probabilityLabels[prob]}</div>
              ))}
            </div>

            <div className="flex-1">
              {probOrder.map((prob) => (
                <div key={prob} className="grid grid-cols-5 gap-1 mb-1">
                  {impactOrder.map((impact) => {
                    const cellData = matrixData?.matrix?.[prob]?.[impact];
                    const count = cellData?.count || 0;
                    const isSelected = selectedCell?.prob === prob && selectedCell?.impact === impact;

                    return (
                      <div
                        key={`${prob}-${impact}`}
                        onClick={() => handleCellClick(prob, impact)}
                        className={`h-16 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${getCellColor(prob, impact)} ${count > 0 ? 'hover:scale-105' : 'opacity-70'} ${isSelected ? 'ring-4 ring-blue-600' : ''}`}
                      >
                        <span className="text-xl font-bold text-white">{count}</span>
                        <span className="text-xs text-white opacity-80">{count === 1 ? 'riesgo' : 'riesgos'}</span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-center mt-4">
            <span className="text-sm font-medium text-gray-600">→ IMPACTO</span>
          </div>
        </div>
      </div>

      {selectedCell && matrixData?.matrix?.[selectedCell.prob]?.[selectedCell.impact]?.count > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Riesgos: {probabilityLabels[selectedCell.prob]} probabilidad, {impactLabels[selectedCell.impact]} impacto
              </h3>
              <p className="text-sm text-gray-500">Nivel: <span className="font-medium">{getRiskLevelLabel(selectedCell.prob, selectedCell.impact)}</span></p>
            </div>
            <button onClick={() => setSelectedCell(null)} className="text-gray-400 hover:text-gray-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="space-y-3">
            {matrixData.matrix[selectedCell.prob][selectedCell.impact].risks.map((risk) => (
              <div key={risk.id} onClick={() => onRiskClick && onRiskClick(risk)} className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer">
                <span className="text-sm font-medium text-gray-900">#{risk.id}</span>
                <p className="text-sm text-gray-600 mt-1">{risk.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskMatrixVisual;
