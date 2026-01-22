import React, { useState, useEffect } from 'react';
import riskService from '../../services/riskService';
import RiskMatrixVisual from './RiskMatrixVisual';
import RiskList from './RiskList';
import RiskForm from './RiskForm';

const RiskDashboard = () => {
  const [activeTab, setActiveTab] = useState('list');
  const [stats, setStats] = useState(null);
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingRisk, setEditingRisk] = useState(null);
  const [filters, setFilters] = useState({
    source: '',
    level: '',
    status: '',
    category: ''
  });

  useEffect(() => {
    loadData();
  }, [filters]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, risksData] = await Promise.all([
        riskService.getStats(),
        riskService.getRisks(filters)
      ]);
      setStats(statsData);
      setRisks(Array.isArray(risksData) ? risksData : (risksData.results || []));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRisk = () => {
    setEditingRisk(null);
    setShowForm(true);
  };

  const handleEditRisk = (risk) => {
    setEditingRisk(risk);
    setShowForm(true);
  };

  const handleFormSubmit = async (riskData) => {
    try {
      if (editingRisk) {
        await riskService.updateRisk(editingRisk.id, riskData);
      } else {
        await riskService.createRisk(riskData);
      }
      setShowForm(false);
      setEditingRisk(null);
      loadData();
    } catch (err) {
      throw err;
    }
  };

  const handleDeleteRisk = async (id) => {
    if (window.confirm('¿Está seguro de eliminar este riesgo?')) {
      try {
        await riskService.deleteRisk(id);
        loadData();
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      await riskService.changeStatus(id, newStatus);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const StatCard = ({ icon, iconBg, value, label, valueColor = 'text-gray-900' }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className={`text-3xl font-bold mt-1 ${valueColor}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-xl ${iconBg}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Gestión de Riesgos</h1>
        <p className="text-gray-500 mt-1">
          Administra los riesgos y oportunidades del SGC según ISO 9001:2015 - Cláusula 6.1
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard
          icon={<svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
          iconBg="bg-blue-50"
          value={stats?.total_risks || 0}
          label="Total Riesgos"
        />
        <StatCard
          icon={<svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
          iconBg="bg-yellow-50"
          value={stats?.active_risks || 0}
          label="Activos"
        />
        <StatCard
          icon={<svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          iconBg="bg-red-50"
          value={stats?.by_level?.critico || 0}
          label="Críticos"
          valueColor="text-red-600"
        />
        <StatCard
          icon={<svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          iconBg="bg-green-50"
          value={stats?.by_status?.mitigated || 0}
          label="Mitigados"
          valueColor="text-green-600"
        />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <button
          onClick={handleCreateRisk}
          className="inline-flex items-center px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Riesgo
        </button>
        <button
          onClick={loadData}
          className="inline-flex items-center px-4 py-2.5 bg-white text-gray-700 text-sm font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Actualizar
        </button>

        {/* Tabs */}
        <div className="ml-auto flex bg-white rounded-lg border border-gray-200 p-1">
          <button
            onClick={() => setActiveTab('list')}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === 'list' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Lista
          </button>
          <button
            onClick={() => setActiveTab('matrix')}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === 'matrix' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Matriz Visual
          </button>
        </div>

        {/* Filter */}
        <select
          value={filters.level}
          onChange={(e) => setFilters({...filters, level: e.target.value})}
          className="px-4 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Todos los niveles</option>
          <option value="critico">Crítico</option>
          <option value="alto">Alto</option>
          <option value="medio">Medio</option>
          <option value="bajo">Bajo</option>
        </select>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Main Content */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {activeTab === 'list' && (
            <RiskList
              risks={risks}
              filters={filters}
              onFilterChange={setFilters}
              onEdit={handleEditRisk}
              onDelete={handleDeleteRisk}
              onStatusChange={handleStatusChange}
              onRefresh={loadData}
            />
          )}
          {activeTab === 'matrix' && (
            <RiskMatrixVisual onRiskClick={handleEditRisk} />
          )}
        </>
      )}

      {/* Info Card */}
      <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-100">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Gestión de Riesgos con IA</h3>
            <p className="text-sm text-gray-600 mt-1">
              Los riesgos pueden ser identificados automáticamente por los módulos SCA (Context Analyzer), 
              SIE (Stakeholder Intelligence) y SPM (Process Mapper) para un análisis integral del SGC.
            </p>
            <a href="/context" className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700 mt-2 font-medium">
              Ir a Análisis de Contexto
              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
        </div>
      </div>

      {/* Modal Form */}
      {showForm && (
        <RiskForm
          risk={editingRisk}
          onSubmit={handleFormSubmit}
          onCancel={() => { setShowForm(false); setEditingRisk(null); }}
        />
      )}
    </div>
  );
};

export default RiskDashboard;
