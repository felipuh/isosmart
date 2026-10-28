import React, { useCallback, useState, useEffect } from 'react';
import { RefreshCw, Download, Plus, Search } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import stakeholderService from '../../services/stakeholderService';
import { showAlert } from '../../services/dialogs';
import CriticalStakeholders from './CriticalStakeholders';
import PowerInterestMatrix from './PowerInterestMatrix';
import InfluenceMetrics from './InfluenceMetrics';
import ChangeTimeline from './ChangeTimeline';
import StakeholderForm from './StakeholderForm';

const StakeholderDashboard = () => {
  const { t } = useI18n();
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
      console.error('Error loading stakeholders data:', error);
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
      console.log('Analysis completed:', result);
      await loadAllData();
      await showAlert(
        t('stakeholderDashboard.messages.analysisCompleted')
          .replace('{analyzed}', result.stakeholders_analyzed || 0)
          .replace('{critical}', result.critical_stakeholders?.length || 0)
          .replace('{changes}', result.changes_detected?.length || 0),
        { icon: 'success' }
      );
    } catch (error) {
      console.error('Error running analysis:', error);
      await showAlert(t('stakeholderDashboard.messages.analysisError'), { icon: 'error' });
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
        await showAlert(t('stakeholderDashboard.messages.stakeholderUpdated'), { icon: 'success' });
      } else {
        await stakeholderService.create(formData);
        await showAlert(t('stakeholderDashboard.messages.stakeholderCreated'), { icon: 'success' });
      }
      setShowForm(false);
      setEditingStakeholder(null);
      await loadAllData();
    } catch (error) {
      console.error('Error saving stakeholder:', error);
      await showAlert(t('stakeholderDashboard.messages.saveError'), { icon: 'error' });
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
          {t('stakeholderDashboard.title')}
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          {(currentOrganization?.name || t('dashboard.noOrganization'))} | {t('stakeholderDashboard.subtitle')}
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
              {analyzing ? t('stakeholderDashboard.actions.analyzing') : t('stakeholderDashboard.actions.runAiAnalysis')}
            </button>

            <button
              onClick={loadAllData}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              {t('stakeholderDashboard.actions.refresh')}
            </button>

            <button 
              onClick={handleNewStakeholder}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Plus className="mr-2 h-4 w-4" />
              {t('stakeholderDashboard.actions.newStakeholder')}
            </button>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
              <input
                type="text"
                placeholder={t('stakeholderDashboard.searchPlaceholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:focus:ring-blue-400 transition-colors"
              />
            </div>

            <button className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
              <Download className="mr-2 h-4 w-4" />
              {t('stakeholderDashboard.actions.export')}
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