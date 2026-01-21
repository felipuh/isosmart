import React, { useState, useEffect } from 'react';
import riskService from '../../services/riskService';

const RiskList = ({ risks, filters, onFilterChange, onEdit, onDelete, onStatusChange, onRefresh }) => {
  const [categories, setCategories] = useState([]);
  const [expandedRisk, setExpandedRisk] = useState(null);

  const sourceOptions = [
    { value: '', label: 'Todos los módulos' },
    { value: 'SCA', label: 'Context Analyzer' },
    { value: 'SIE', label: 'Stakeholder Intelligence' },
    { value: 'SPM', label: 'Process Mapper' },
    { value: 'MANUAL', label: 'Entrada Manual' },
  ];

  const levelOptions = [
    { value: '', label: 'Todos los niveles' },
    { value: 'critico', label: 'Crítico' },
    { value: 'alto', label: 'Alto' },
    { value: 'medio', label: 'Medio' },
    { value: 'bajo', label: 'Bajo' },
  ];

  const statusOptions = [
    { value: '', label: 'Todos los estados' },
    { value: 'identified', label: 'Identificado' },
    { value: 'under_analysis', label: 'En Análisis' },
    { value: 'mitigated', label: 'Mitigado' },
    { value: 'accepted', label: 'Aceptado' },
    { value: 'closed', label: 'Cerrado' },
  ];

  const statusColors = {
    identified: 'bg-blue-100 text-blue-800',
    under_analysis: 'bg-yellow-100 text-yellow-800',
    mitigated: 'bg-green-100 text-green-800',
    accepted: 'bg-purple-100 text-purple-800',
    closed: 'bg-gray-100 text-gray-800',
  };

  const levelColors = {
    critico: 'bg-red-100 text-red-800 border-red-300',
    alto: 'bg-orange-100 text-orange-800 border-orange-300',
    medio: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    bajo: 'bg-green-100 text-green-800 border-green-300',
  };

  const sourceIcons = { SCA: '🔍', SIE: '👥', SPM: '⚙️', MANUAL: '✏️' };

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await riskService.getCategories();
      setCategories(data);
    } catch (err) {
      console.error('Error cargando categorías:', err);
    }
  };

  const handleFilterChange = (field, value) => {
    onFilterChange({ ...filters, [field]: value });
  };

  const clearFilters = () => {
    onFilterChange({ source: '', level: '', status: '', category: '' });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-ES', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[150px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Módulo Fuente</label>
            <select value={filters.source} onChange={(e) => handleFilterChange('source', e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
              {sourceOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </div>
          <div className="flex-1 min-w-[150px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Nivel de Riesgo</label>
            <select value={filters.level} onChange={(e) => handleFilterChange('level', e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
              {levelOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </div>
          <div className="flex-1 min-w-[150px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Estado</label>
            <select value={filters.status} onChange={(e) => handleFilterChange('status', e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
              {statusOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </div>
          <div className="flex gap-2">
            {hasActiveFilters && <button onClick={clearFilters} className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md">Limpiar</button>}
            <button onClick={onRefresh} className="px-3 py-2 text-sm bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-md">Actualizar</button>
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-600">Mostrando <span className="font-medium">{risks.length}</span> riesgos</p>

      {risks.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">No se encontraron riesgos</p>
        </div>
      ) : (
        <div className="space-y-3">
          {risks.map((risk) => (
            <div key={risk.id} className={`bg-white rounded-lg shadow border-l-4 ${levelColors[risk.risk_level]?.split(' ')[2] || 'border-gray-300'}`}>
              <div className="p-4 cursor-pointer" onClick={() => setExpandedRisk(expandedRisk === risk.id ? null : risk.id)}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{sourceIcons[risk.source_module]}</span>
                      <span className="text-sm font-medium text-gray-500">#{risk.id}</span>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded ${levelColors[risk.risk_level]}`}>{risk.risk_level?.toUpperCase()}</span>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded ${statusColors[risk.status]}`}>{statusOptions.find(s => s.value === risk.status)?.label}</span>
                    </div>
                    <p className="text-gray-900 font-medium">{risk.risk_description}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>📁 {risk.risk_category || 'Sin categoría'}</span>
                      <span>👤 {risk.responsible || 'Sin asignar'}</span>
                      <span>📅 {formatDate(risk.detection_date)}</span>
                    </div>
                  </div>
                  <svg className={`w-5 h-5 text-gray-400 transition-transform ${expandedRisk === risk.id ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {expandedRisk === risk.id && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Evaluación</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between"><span className="text-gray-500">Probabilidad:</span><span className="font-medium">{risk.probability}</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">Impacto:</span><span className="font-medium">{risk.impact}</span></div>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Acciones de Mitigación</h4>
                      <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">{risk.mitigation_actions || 'No definidas'}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100">
                    <button onClick={(e) => { e.stopPropagation(); onEdit(risk); }} className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100">Editar</button>
                    <select value="" onChange={(e) => { if (e.target.value) onStatusChange(risk.id, e.target.value); }} onClick={(e) => e.stopPropagation()} className="px-3 py-1.5 text-sm border border-gray-300 rounded">
                      <option value="">Cambiar estado...</option>
                      {statusOptions.filter(s => s.value && s.value !== risk.status).map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                    <button onClick={(e) => { e.stopPropagation(); onDelete(risk.id); }} className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 rounded hover:bg-red-100 ml-auto">Eliminar</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RiskList;
