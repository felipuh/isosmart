import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import objectiveService from '../../services/objectiveService';
import ObjectiveList from './ObjectiveList';
import ObjectiveForm from './ObjectiveForm';

const ObjectiveDashboard = () => {
  const { currentOrganization } = useAuth();
  const [stats, setStats] = useState(null);
  const [objectives, setObjectives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingObjective, setEditingObjective] = useState(null);
  const [filters, setFilters] = useState({ status: '', source: '' });

  useEffect(() => {
    if (currentOrganization?.id) {
      loadData();
    }
  }, [currentOrganization?.id, filters]);

  const loadData = async () => {
    if (!currentOrganization?.id) return;
    
    setLoading(true);
    setError(null);
    try {
      const [statsData, objectivesData] = await Promise.all([
        objectiveService.getStats(currentOrganization.id),
        objectiveService.getObjectives({ ...filters, organization: currentOrganization.id })
      ]);
      setStats(statsData);
      setObjectives(Array.isArray(objectivesData) ? objectivesData : (objectivesData.results || []));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingObjective(null);
    setShowForm(true);
  };

  const handleEdit = (objective) => {
    setEditingObjective(objective);
    setShowForm(true);
  };

  const handleFormSubmit = async (data) => {
    try {
      if (editingObjective) {
        await objectiveService.updateObjective(editingObjective.id, data);
      } else {
        await objectiveService.createObjective(data);
      }
      setShowForm(false);
      setEditingObjective(null);
      loadData();
    } catch (err) {
      throw err;
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Está seguro de eliminar este objetivo?')) {
      try {
        await objectiveService.deleteObjective(id);
        loadData();
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const handleUpdateProgress = async (id, value) => {
    try {
      await objectiveService.updateProgress(id, value);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const StatCard = ({ icon, iconBg, value, label, valueColor = 'text-slate-900 dark:text-white', suffix = '' }) => (
    <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md dark:backdrop-blur-md rounded-xl shadow-sm dark:shadow-slate-900/50 border border-white/20 dark:border-slate-700/50 p-6 transition-all duration-300 hover:shadow-md dark:hover:shadow-slate-900/70 hover:bg-white/80 dark:hover:bg-slate-800/80">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
          <p className={`text-3xl font-bold mt-1 ${valueColor}`}>{value}{suffix}</p>
        </div>
        <div className={`p-3 rounded-xl ${iconBg} dark:bg-opacity-20`}>
          {icon}
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Objetivos de Calidad</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Gestiona los objetivos de calidad del SGC según ISO 9001:2015 - Cláusula 6.2
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard
          icon={<svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>}
          iconBg="bg-blue-50"
          value={stats?.total_objectives || 0}
          label="Total Objetivos"
        />
        <StatCard
          icon={<svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
          iconBg="bg-yellow-50"
          value={stats?.active_count || 0}
          label="En Progreso"
        />
        <StatCard
          icon={<svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          iconBg="bg-green-50"
          value={stats?.achieved_count || 0}
          label="Logrados"
          valueColor="text-green-600"
        />
        <StatCard
          icon={<svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
          iconBg="bg-indigo-50"
          value={stats?.average_progress || 0}
          label="Progreso Promedio"
          valueColor="text-indigo-600"
          suffix="%"
        />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <button
          onClick={handleCreate}
          className="inline-flex items-center px-4 py-2.5 bg-blue-600 dark:bg-blue-700 text-white text-sm font-medium rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors shadow-sm"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Objetivo
        </button>
        <button
          onClick={loadData}
          className="inline-flex items-center px-4 py-2.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Actualizar
        </button>

        {/* Filters */}
        <div className="ml-auto flex items-center gap-3">
          <select
            value={filters.status}
            onChange={(e) => setFilters({...filters, status: e.target.value})}
            className="px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
          >
            <option value="">Todos los estados</option>
            <option value="active">Activo</option>
            <option value="in_progress">En Progreso</option>
            <option value="achieved">Logrado</option>
            <option value="delayed">Retrasado</option>
            <option value="cancelled">Cancelado</option>
          </select>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg flex items-center justify-between transition-colors">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Main Content */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
        </div>
      ) : (
        <ObjectiveList
          objectives={objectives}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onUpdateProgress={handleUpdateProgress}
        />
      )}

      {/* Info Card */}
      <div className="mt-6 bg-gradient-to-r from-green-50/80 dark:from-green-900/30 to-emerald-50/80 dark:to-emerald-900/30 backdrop-blur-md rounded-xl p-5 border border-green-100/50 dark:border-green-700/50 transition-all duration-300 hover:shadow-md dark:hover:shadow-green-900/50">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Objetivos SMART</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Los objetivos de calidad deben ser medibles, coherentes con la política de calidad 
              y pertinentes para la conformidad de productos/servicios y el aumento de la satisfacción del cliente.
            </p>
          </div>
        </div>
      </div>

      {/* Modal Form */}
      {showForm && (
        <ObjectiveForm
          objective={editingObjective}
          onSubmit={handleFormSubmit}
          onCancel={() => { setShowForm(false); setEditingObjective(null); }}
        />
      )}
    </div>
  );
};

export default ObjectiveDashboard;
