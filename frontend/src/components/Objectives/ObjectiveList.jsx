import React, { useState } from 'react';

const ObjectiveList = ({ objectives, onEdit, onDelete, onUpdateProgress }) => {
  const [expandedId, setExpandedId] = useState(null);
  const [editingProgress, setEditingProgress] = useState(null);
  const [progressValue, setProgressValue] = useState('');

  const statusLabels = {
    active: 'Activo',
    in_progress: 'En Progreso',
    achieved: 'Logrado',
    delayed: 'Retrasado',
    cancelled: 'Cancelado',
  };

  const statusColors = {
    active: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-yellow-100 text-yellow-700',
    achieved: 'bg-green-100 text-green-700',
    delayed: 'bg-red-100 text-red-700',
    cancelled: 'bg-gray-100 text-gray-700',
  };

  const sourceIcons = {
    SCA: { icon: '🔍', label: 'Context Analyzer' },
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

  const getProgressColor = (progress) => {
    if (progress >= 100) return 'bg-green-500';
    if (progress >= 75) return 'bg-blue-500';
    if (progress >= 50) return 'bg-yellow-500';
    if (progress >= 25) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const handleProgressSubmit = (id) => {
    if (progressValue !== '') {
      onUpdateProgress(id, parseFloat(progressValue));
      setEditingProgress(null);
      setProgressValue('');
    }
  };

  if (objectives.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No hay objetivos registrados</h3>
        <p className="text-gray-500">Comienza agregando un nuevo objetivo de calidad.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
        <div className="col-span-4">Objetivo / Indicador</div>
        <div className="col-span-2">Progreso</div>
        <div className="col-span-2">Estado</div>
        <div className="col-span-2">Fecha Límite</div>
        <div className="col-span-2 text-right">Acciones</div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-gray-100">
        {objectives.map((objective) => {
          const progress = objective.progress_percentage || 0;
          
          return (
            <div key={objective.id} className="hover:bg-gray-50 transition-colors">
              {/* Main Row */}
              <div 
                className="grid grid-cols-12 gap-4 px-6 py-4 items-center cursor-pointer"
                onClick={() => setExpandedId(expandedId === objective.id ? null : objective.id)}
              >
                {/* Objective Info */}
                <div className="col-span-4">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {objective.indicator_name}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5 truncate">
                        {objective.objective_description?.substring(0, 50)}{objective.objective_description?.length > 50 ? '...' : ''}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Progress */}
                <div className="col-span-2">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${getProgressColor(progress)} transition-all duration-300`}
                        style={{ width: `${Math.min(progress, 100)}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-700 w-12 text-right">
                      {progress.toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {objective.current_value || 0} / {objective.target_value} {objective.measurement_unit}
                  </p>
                </div>

                {/* Status */}
                <div className="col-span-2">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${statusColors[objective.status]}`}>
                    {statusLabels[objective.status] || objective.status}
                  </span>
                </div>

                {/* Deadline */}
                <div className="col-span-2">
                  <div className="flex items-center text-sm text-gray-500">
                    <svg className="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {formatDate(objective.deadline)}
                  </div>
                </div>

                {/* Actions */}
                <div className="col-span-2 flex items-center justify-end space-x-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); setEditingProgress(objective.id); setProgressValue(objective.current_value || ''); }}
                    className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                    title="Actualizar Progreso"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); onEdit(objective); }}
                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Editar"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); onDelete(objective.id); }}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Eliminar"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Progress Update Modal */}
              {editingProgress === objective.id && (
                <div className="px-6 pb-4 bg-green-50 border-t border-green-100">
                  <div className="flex items-center gap-4 mt-4">
                    <label className="text-sm font-medium text-gray-700">Actualizar valor actual:</label>
                    <input
                      type="number"
                      step="0.01"
                      value={progressValue}
                      onChange={(e) => setProgressValue(e.target.value)}
                      className="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
                      placeholder={`Meta: ${objective.target_value}`}
                    />
                    <span className="text-sm text-gray-500">{objective.measurement_unit}</span>
                    <button
                      onClick={() => handleProgressSubmit(objective.id)}
                      className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700"
                    >
                      Guardar
                    </button>
                    <button
                      onClick={() => { setEditingProgress(null); setProgressValue(''); }}
                      className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-300"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}

              {/* Expanded Details */}
              {expandedId === objective.id && editingProgress !== objective.id && (
                <div className="px-6 pb-4 bg-gray-50 border-t border-gray-100">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Medición</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Línea Base:</span>
                          <span className="font-medium">{objective.baseline_value} {objective.measurement_unit}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Meta:</span>
                          <span className="font-medium">{objective.target_value} {objective.measurement_unit}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Actual:</span>
                          <span className="font-medium">{objective.current_value || 0} {objective.measurement_unit}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Frecuencia:</span>
                          <span className="font-medium">{objective.measurement_frequency}</span>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Responsable</h4>
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{objective.responsible || 'Sin asignar'}</p>
                          <p className="text-xs text-gray-500">ISO {objective.iso_clause || '6.2'}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Fuente</h4>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{sourceIcons[objective.source_module]?.icon || '📋'}</span>
                        <span className="text-sm text-gray-600">{sourceIcons[objective.source_module]?.label || objective.source_module}</span>
                      </div>
                      {objective.process_id && (
                        <p className="text-xs text-gray-500 mt-2">Proceso: {objective.process_id}</p>
                      )}
                    </div>
                  </div>
                  {objective.objective_description && (
                    <div className="mt-4 bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Descripción del Objetivo</h4>
                      <p className="text-sm text-gray-600">{objective.objective_description}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ObjectiveList;
