import React, { useCallback, useState, useEffect } from 'react';
import { RefreshCw, Download, PlayCircle, FileText, Network, Target, Plus } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import processService from '../../services/processService';
import { showAlert, showConfirm } from '../../services/dialogs';
import ProcessDiagram from './ProcessDiagram';
import ProcessList from './ProcessList';
import ProcessRecommendations from './ProcessRecommendations';
import ProcessForm from './ProcessForm';

const ProcessDashboard = () => {
  const { t, language } = useI18n();
  const { currentOrganization } = useAuth();
  const [processMap, setProcessMap] = useState(null);
  const [processes, setProcesses] = useState([]);
  const [processesByType, setProcessesByType] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingProcess, setEditingProcess] = useState(null);

  const loadData = useCallback(async () => {
    if (!currentOrganization?.id) return;
    
    setLoading(true);
    try {
      const [latestResponse] = await Promise.all([
        processService.getLatest(currentOrganization.id),
        processService.getStats(currentOrganization.id)
      ]);

      if (latestResponse.status === 'success') {
        setProcessMap(latestResponse.data);
        
        // Cargar procesos
        if (latestResponse.data?.id) {
          const [procs, processesByTypeData] = await Promise.all([
            processService.getProcesses(latestResponse.data.id, currentOrganization.id),
            processService.getProcessesByType(latestResponse.data.id, currentOrganization.id)
          ]);
          setProcesses(Array.isArray(procs) ? procs : procs.results || []);
          setProcessesByType(processesByTypeData);
        }
      }
      
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  }, [currentOrganization?.id]);

  useEffect(() => {
    if (currentOrganization?.id) {
      loadData();
    }
  }, [currentOrganization?.id, loadData]);

  const handleRunMapping = async () => {
    const confirmed = await showConfirm(t('processDashboard.messages.confirmRunMapping'));
    if (!confirmed) {
      return;
    }

    setAnalyzing(true);
    try {
      const result = await processService.runMapping({}, currentOrganization?.id);
      console.log('Process mapping completed:', result);

      if (result.status === 'success') {
        await loadData();

        await showAlert(
          t('processDashboard.messages.mappingCompleted')
            .replace('{total}', result.total_processes || 0)
            .replace('{strategic}', result.strategic_count || 0)
            .replace('{operational}', result.operational_count || 0)
            .replace('{support}', result.support_count || 0)
            .replace('{interactions}', result.total_interactions || 0)
            .replace('{critical}', result.critical_processes_count || 0),
          { icon: 'success' }
        );
      } else {
        await showAlert(result.message, { icon: 'info' });
      }
    } catch (error) {
      console.error('Error running process mapping:', error);
      await showAlert(t('processDashboard.messages.mappingError'), { icon: 'error' });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAddProcess = () => {
    setEditingProcess(null);
    setShowForm(true);
  };

  const handleEditProcess = (process) => {
    setEditingProcess(process);
    setShowForm(true);
  };

  const handleSaveProcess = async (formData) => {
    try {
      if (editingProcess) {
        await processService.updateProcess(editingProcess.id, formData, currentOrganization?.id);
        await showAlert(t('processDashboard.messages.processUpdated'), { icon: 'success' });
      } else {
        await processService.createProcess(formData, currentOrganization?.id);
        await showAlert(t('processDashboard.messages.processCreated'), { icon: 'success' });
      }
      setShowForm(false);
      setEditingProcess(null);
      await loadData();
    } catch (error) {
      console.error('Error saving process:', error);
      await showAlert(t('processDashboard.messages.processSaveError'), { icon: 'error' });
      throw error;
    }
  };

  const handleDeleteProcess = async (process) => {
    const processLabel = process?.name || process?.code || process?.id || '-';
    const confirmed = await showConfirm(t('processDashboard.messages.confirmDeleteProcess').replace('{name}', processLabel));
    if (!confirmed) {
      return;
    }
    try {
      await processService.deleteProcess(process.id, currentOrganization?.id);
      await showAlert(t('processDashboard.messages.processDeleted'), { icon: 'success' });
      await loadData();
    } catch (error) {
      console.error('Error deleting process:', error);
      await showAlert(t('processDashboard.messages.processDeleteError'), { icon: 'error' });
    }
  };

  const formatDate = (date) => {
    if (!date) return t('processDashboard.notAvailable');
    const locale = language === 'es-LATAM' ? 'es-ES' : language;
    return new Intl.DateTimeFormat(locale, {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    }).format(new Date(date));
  };

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen transition-colors duration-300">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          {t('processDashboard.title')}
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          {t('processDashboard.subtitle')}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('processDashboard.stats.totalProcesses')}</p>
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {processMap?.total_processes || processes.length || 0}
              </p>
            </div>
            <Network className="h-10 w-10 text-blue-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('processDashboard.stats.strategic')}</p>
              <p className="text-3xl font-bold text-purple-600">
                {processMap?.strategic_count || 0}
              </p>
            </div>
            <Target className="h-10 w-10 text-purple-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('processDashboard.stats.operational')}</p>
              <p className="text-3xl font-bold text-blue-600">
                {processMap?.operational_count || 0}
              </p>
            </div>
            <PlayCircle className="h-10 w-10 text-blue-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{t('processDashboard.stats.support')}</p>
              <p className="text-3xl font-bold text-green-600">
                {processMap?.support_count || 0}
              </p>
            </div>
            <FileText className="h-10 w-10 text-green-400" />
          </div>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-4 mb-6 transition-colors">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunMapping}
              disabled={analyzing}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
            >
              <PlayCircle className={'mr-2 h-4 w-4 ' + (analyzing ? 'animate-spin' : '')} />
              {analyzing ? t('processDashboard.actions.mapping') : t('processDashboard.actions.mapWithAi')}
            </button>

            <button
              onClick={handleAddProcess}
              disabled={!processMap}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors"
            >
              <Plus className="mr-2 h-4 w-4" />
              {t('processDashboard.actions.newProcess')}
            </button>

            <button
              onClick={loadData}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              {t('common.buttons.update')}
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-600 dark:text-slate-400">
              {t('processDashboard.lastUpdate')}: {formatDate(processMap?.updated_at)}
            </span>
            <button className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
              <Download className="mr-2 h-4 w-4" />
              {t('common.buttons.export')}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {processMap ? (
        <div className="space-y-6">
          {/* Mapa de Procesos */}
          <ProcessDiagram 
            diagramData={processMap?.interaction_analysis}
            processes={processes}
            loading={loading}
          />

          {/* Recomendaciones */}
          <ProcessRecommendations 
            recommendations={processMap?.recommendations} 
            loading={loading}
          />

          {/* Lista de Procesos */}
          <ProcessList 
            processesByType={processesByType}
            processes={processes}
            loading={loading}
            onEdit={handleEditProcess}
            onDelete={handleDeleteProcess}
          />
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-12 text-center transition-colors">
          <Network className="h-16 w-16 text-slate-400 dark:text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
            {t('processDashboard.empty.title')}
          </h3>
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            {t('processDashboard.empty.description')}
          </p>
          <button
            onClick={handleRunMapping}
            disabled={analyzing}
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
          >
            <PlayCircle className={'mr-2 h-5 w-5 ' + (analyzing ? 'animate-spin' : '')} />
            {analyzing ? t('processDashboard.actions.mapping') : t('processDashboard.actions.mapWithAi')}
          </button>
        </div>
      )}

      {/* Modal Form */}
      {showForm && (
        <ProcessForm
          process={editingProcess}
          mapId={processMap?.id}
          onSave={handleSaveProcess}
          onClose={() => { setShowForm(false); setEditingProcess(null); }}
        />
      )}
    </div>
  );
};

export default ProcessDashboard;