import React, { useState } from 'react';

const RiskList = ({ risks, filters, onFilterChange, onEdit, onDelete, onStatusChange, onRefresh }) => {
  const [expandedRisk, setExpandedRisk] = useState(null);

  const statusLabels = {
    identified: 'Identificado',
    under_analysis: 'En Análisis',
    mitigated: 'Mitigado',
    accepted: 'Aceptado',
    closed: 'Cerrado',
  };

  const statusColors = {
    identified: 'bg-blue-100 text-blue-700',
    under_analysis: 'bg-yellow-100 text-yellow-700',
    mitigated: 'bg-green-100 text-green-700',
    accepted: 'bg-purple-100 text-purple-700',
    closed: 'bg-gray-100 text-gray-700',
  };

  const levelColors = {
    critico: 'bg-red-100 text-red-700',
    alto: 'bg-orange-100 text-orange-700',
    medio: 'bg-yellow-100 text-yellow-700',
    bajo: 'bg-green-100 text-green-700',
  };

  const sourceIcons = {
    SCA: { icon: '🔍', label: 'Context Analyzer' },
    SIE: { icon: '👥', label: 'Stakeholder Intelligence' },
    SPM: { icon: '⚙️', label: 'Process Mapper' },
    MANUAL: { icon: '✏️', label: 'Manual' },
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('es-ES', { 
      day: 'numeric',
      month: 'short', 
      year: 'numeric' 
    });
  };

  if (risks.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No hay riesgos registrados</h3>
        <p className="text-gray-500">Comienza agregando un nuevo riesgo al sistema.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
        <div className="col-span-4">Riesgo</div>
        <div className="col-span-2">Nivel</div>
        <div className="col-span-2">Fuente</div>
        <div className="col-span-2">Fecha</div>
        <div className="col-span-2 text-right">Acciones</div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-gray-100">
        {risks.map((risk) => (
          <div key={risk.id} className="hover:bg-gray-50 transition-colors">
            {/* Main Row */}
            <div 
              className="grid grid-cols-12 gap-4 px-6 py-4 items-center cursor-pointer"
              onClick={() => setExpandedRisk(expandedRisk === risk.id ? null : risk.id)}
            >
              {/* Risk Info */}
              <div className="col-span-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {risk.risk_description?.substring(0, 60)}{risk.risk_description?.length > 60 ? '...' : ''}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {risk.risk_category || 'Sin categoría'} • ISO {risk.iso_clause || '6.1'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Level */}
              <div className="col-span-2">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${levelColors[risk.risk_level] || 'bg-gray-100 text-gray-700'}`}>
                  {risk.risk_level?.charAt(0).toUpperCase() + risk.risk_level?.slice(1) || 'N/A'}
                </span>
              </div>

              {/* Source */}
              <div className="col-span-2">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{sourceIcons[risk.source_module]?.icon || '📋'}</span>
                  <span className="text-sm text-gray-600">{sourceIcons[risk.source_module]?.label || risk.source_module}</span>
                </div>
              </div>

              {/* Date */}
              <div className="col-span-2">
                <div className="flex items-center text-sm text-gray-500">
                  <svg className="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {formatDate(risk.detection_date)}
                </div>
              </div>

              {/* Actions */}
              <div className="col-span-2 flex items-center justify-end space-x-2">
                <button
                  onClick={(e) => { e.stopPropagation(); onEdit(risk); }}
                  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Editar"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(risk.id); }}
                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Eliminar"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedRisk === risk.id && (
              <div className="px-6 pb-4 bg-gray-50 border-t border-gray-100">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Evaluación</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Probabilidad:</span>
                        <span className="font-medium">{risk.probability || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Impacto:</span>
                        <span className="font-medium">{risk.impact || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Responsable:</span>
                        <span className="font-medium">{risk.responsible || 'Sin asignar'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Estado</h4>
                    <div className="space-y-3">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColors[risk.status]}`}>
                        {statusLabels[risk.status] || risk.status}
                      </span>
                      <select
                        value=""
                        onChange={(e) => { if (e.target.value) onStatusChange(risk.id, e.target.value); }}
                        className="w-full mt-2 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Cambiar estado...</option>
                        {Object.entries(statusLabels).filter(([key]) => key !== risk.status).map(([key, label]) => (
                          <option key={key} value={key}>{label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Mitigación</h4>
                    <p className="text-sm text-gray-600">
                      {risk.mitigation_actions || 'No se han definido acciones de mitigación.'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default RiskList;
