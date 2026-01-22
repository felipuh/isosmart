import React, { useState, useEffect } from 'react';
import { RefreshCw, Download, PlayCircle, FileText, Network, Target, Plus } from 'lucide-react';
import processService from '../../services/processService';
import ProcessDiagram from './ProcessDiagram';
import ProcessList from './ProcessList';
import ProcessRecommendations from './ProcessRecommendations';
import ProcessForm from './ProcessForm';

const ProcessDashboard = () => {
  const [processMap, setProcessMap] = useState(null);
  const [processes, setProcesses] = useState([]);
  const [processesByType, setProcessesByType] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingProcess, setEditingProcess] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [latestResponse, statsResponse] = await Promise.all([
        processService.getLatest(),
        processService.getStats()
      ]);

      if (latestResponse.status === 'success') {
        setProcessMap(latestResponse.data);
        
        // Cargar procesos
        if (latestResponse.data?.id) {
          const [procs, processesByTypeData] = await Promise.all([
            processService.getProcesses(latestResponse.data.id),
            processService.getProcessesByType(latestResponse.data.id)
          ]);
          setProcesses(Array.isArray(procs) ? procs : procs.results || []);
          setProcessesByType(processesByTypeData);
        }
      }
      
      setStats(statsResponse);
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunMapping = async () => {
    if (!window.confirm('¿Ejecutar mapeo automático de procesos?\n\nEsto creará un nuevo mapa basado en el contexto y alcance del sistema.')) {
      return;
    }

    setAnalyzing(true);
    try {
      const result = await processService.runMapping({});
      console.log('Mapeo completado:', result);

      if (result.status === 'success') {
        await loadData();
        
        alert('Mapeo de procesos completado!\n\n' +
              'Total procesos: ' + result.total_processes + '\n' +
              'Estratégicos: ' + result.strategic_count + '\n' +
              'Operativos: ' + result.operational_count + '\n' +
              'Apoyo: ' + result.support_count + '\n' +
              'Interacciones: ' + result.total_interactions + '\n' +
              'Procesos críticos: ' + result.critical_processes_count);
      } else {
        alert(result.message);
      }
    } catch (error) {
      console.error('Error ejecutando mapeo:', error);
      alert('Error al ejecutar el mapeo de procesos');
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
        await processService.updateProcess(editingProcess.id, formData);
        alert('Proceso actualizado exitosamente');
      } else {
        await processService.createProcess(formData);
        alert('Proceso creado exitosamente');
      }
      setShowForm(false);
      setEditingProcess(null);
      await loadData();
    } catch (error) {
      console.error('Error guardando proceso:', error);
      alert('Error al guardar el proceso');
      throw error;
    }
  };

  const handleDeleteProcess = async (process) => {
    if (!window.confirm('¿Estás seguro de eliminar el proceso "' + process.name + '"?')) {
      return;
    }
    try {
      await processService.deleteProcess(process.id);
      alert('Proceso eliminado exitosamente');
      await loadData();
    } catch (error) {
      console.error('Error eliminando proceso:', error);
      alert('Error al eliminar el proceso');
    }
  };

  const formatDate = (date) => {
    if (!date) return 'No disponible';
    return new Intl.DateTimeFormat('es-ES', {
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
          Mapa de Procesos del SGC
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          ISO 4.4 - Sistema de gestión de calidad y sus procesos
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Total Procesos</p>
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
              <p className="text-sm text-slate-600 dark:text-slate-400">Estratégicos</p>
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
              <p className="text-sm text-slate-600 dark:text-slate-400">Operativos</p>
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
              <p className="text-sm text-slate-600 dark:text-slate-400">Apoyo</p>
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
              {analyzing ? 'Mapeando...' : 'Mapear Procesos con IA'}
            </button>

            <button
              onClick={handleAddProcess}
              disabled={!processMap}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors"
            >
              <Plus className="mr-2 h-4 w-4" />
              Nuevo Proceso
            </button>

            <button
              onClick={loadData}
              className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Actualizar
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-600 dark:text-slate-400">
              Última actualización: {formatDate(processMap?.updated_at)}
            </span>
            <button className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
              <Download className="mr-2 h-4 w-4" />
              Exportar
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
            No hay mapa de procesos disponible
          </h3>
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            Ejecuta el mapeo automático para crear tu mapa de procesos del SGC
          </p>
          <button
            onClick={handleRunMapping}
            disabled={analyzing}
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
          >
            <PlayCircle className={'mr-2 h-5 w-5 ' + (analyzing ? 'animate-spin' : '')} />
            {analyzing ? 'Mapeando...' : 'Mapear Procesos con IA'}
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