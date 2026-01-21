import React, { useState, useEffect } from 'react';
import riskService from '../../services/riskService';
import RiskMatrixVisual from './RiskMatrixVisual';
import RiskList from './RiskList';
import RiskForm from './RiskForm';
import RiskStats from './RiskStats';

const RiskDashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
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
      setRisks(risksData.results || risksData);
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

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'matrix', label: 'Matriz Visual', icon: '🎯' },
    { id: 'list', label: 'Lista de Riesgos', icon: '📋' },
  ];

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Gestión de Riesgos</h1>
              <p className="text-sm text-gray-500 mt-1">ISO 9001:2015 - Cláusula 6.1 | Matriz de Riesgos y Oportunidades</p>
            </div>
            <button
              onClick={handleCreateRisk}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Nuevo Riesgo
            </button>
          </div>
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && <RiskStats stats={stats} onRefresh={loadData} />}
            {activeTab === 'matrix' && <RiskMatrixVisual onRiskClick={handleEditRisk} />}
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
          </>
        )}
      </div>

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
