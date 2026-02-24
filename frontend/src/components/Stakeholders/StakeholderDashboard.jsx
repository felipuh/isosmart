import React, { useCallback, useState, useEffect } from 'react';
import { RefreshCw, Download, Plus, Search } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import stakeholderService from '../../services/stakeholderService';
import CriticalStakeholders from './CriticalStakeholders';
import PowerInterestMatrix from './PowerInterestMatrix';
import InfluenceMetrics from './InfluenceMetrics';
import ChangeTimeline from './ChangeTimeline';
import StakeholderForm from './StakeholderForm';

const StakeholderDashboard = () => {
  const { currentOrganization } = useAuth();
  const [stakeholders, setStakeholders] = useState([]);
  const [criticalStakeholders, setCriticalStakeholders] = useState([]);
  const [matrixData, setMatrixData] = useState(null);
  const [recentChanges, setRecentChanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingStakeholder, setEditingStakeholder] = useState(null);

  const loadAllData = useCallback(async () => {
    if (!currentOrganization?.id) return;
    
    setLoading(true);
    try {
      const [shData, criticalData, matrix, changes] = await Promise.all([
        stakeholderService.getAll(currentOrganization.id),
        stakeholderService.getCritical(currentOrganization.id),
        stakeholderService.getMatrix(currentOrganization.id),
        stakeholderService.getRecentChanges(currentOrganization.id)
      ]);

      setStakeholders(shData);
      setCriticalStakeholders(criticalData.stakeholders || []);
      setMatrixData(matrix);
      setRecentChanges(changes.changes || []);
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  }, [currentOrganization?.id]);

  useEffect(() => {
    if (currentOrganization?.id) {
      loadAllData();
    }
  }, [currentOrganization?.id, loadAllData]);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      const result = await stakeholderService.runAnalysis();
      console.log('Análisis completado:', result);
      await loadAllData();
      alert('✅ Análisis completado!\n\n' +
            'Stakeholders analizados: ' + result.stakeholders_analyzed + '\n' +
            'Críticos detectados: ' + (result.critical_stakeholders?.length || 0) + '\n' +
            'Cambios detectados: ' + (result.changes_detected?.length || 0));
    } catch (error) {
      console.error('Error ejecutando análisis:', error);
      alert('❌ Error al ejecutar el análisis');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleNewStakeholder = () => {
    setEditingStakeholder(null);
    setShowForm(true);
  };

  const handleEditStakeholder = (stakeholder) => {
    setEditingStakeholder(stakeholder);
    setShowForm(true);
  };

  const handleSaveStakeholder = async (formData) => {
    try {
      if (editingStakeholder) {
        await stakeholderService.update(editingStakeholder.id, formData);
        alert('✅ Stakeholder actualizado exitosamente');
      } else {
        await stakeholderService.create(formData);
        alert('✅ Stakeholder creado exitosamente');
      }
      setShowForm(false);
      setEditingStakeholder(null);
      await loadAllData();
    } catch (error) {
      console.error('Error guardando stakeholder:', error);
      alert('❌ Error al guardar el stakeholder');
      throw error;
    }
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingStakeholder(null);
  };

  const filteredStakeholders = stakeholders.filter(sh =>
    sh.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    sh.stakeholder_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          Dashboard de Stakeholders
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          {currentOrganization?.name} | Análisis inteligente de partes interesadas - ISO 4.2
        </p>
      </div>

      {/* Actions Bar */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-4 mb-6 transition-colors">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white rounded-lg disabled:bg-blue-300 dark:disabled:bg-blue-900 transition-colors"
            >
              <RefreshCw className={'mr-2 h-4 w-4 ' + (analyzing ? 'animate-spin' : '')} />
              {analyzing ? 'Analizando...' : 'Ejecutar Análisis IA'}
            </button>

            <button
              onClick={loadAllData}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Actualizar
            </button>

            <button 
              onClick={handleNewStakeholder}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Plus className="mr-2 h-4 w-4" />
              Nuevo Stakeholder
            </button>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
              <input
                type="text"
                placeholder="Buscar stakeholders..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:focus:ring-blue-400 transition-colors"
              />
            </div>

            <button className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
              <Download className="mr-2 h-4 w-4" />
              Exportar
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-1">
          <CriticalStakeholders 
            stakeholders={criticalStakeholders} 
            loading={loading}
            onEdit={handleEditStakeholder}
          />
        </div>

        <div className="lg:col-span-2 space-y-6">
          <PowerInterestMatrix 
            matrixData={matrixData} 
            loading={loading}
          />
        </div>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <InfluenceMetrics 
          stakeholders={filteredStakeholders} 
          loading={loading}
          onEdit={handleEditStakeholder}
        />
        
        <ChangeTimeline 
          changes={recentChanges} 
          loading={loading}
        />
      </div>

      {/* Modal Form */}
      {showForm && (
        <StakeholderForm
          stakeholder={editingStakeholder}
          onSave={handleSaveStakeholder}
          onClose={handleCloseForm}
        />
      )}
    </div>
  );
};

export default StakeholderDashboard;