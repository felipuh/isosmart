import React, { useState, useEffect } from 'react';
import { RefreshCw, Download, Plus, Search } from 'lucide-react';
import stakeholderService from '../../services/stakeholderService';
import CriticalStakeholders from './CriticalStakeholders';
import PowerInterestMatrix from './PowerInterestMatrix';
import InfluenceMetrics from './InfluenceMetrics';
import ChangeTimeline from './ChangeTimeline';

const StakeholderDashboard = () => {
  const [stakeholders, setStakeholders] = useState([]);
  const [criticalStakeholders, setCriticalStakeholders] = useState([]);
  const [matrixData, setMatrixData] = useState(null);
  const [recentChanges, setRecentChanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Cargar datos iniciales
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [shData, criticalData, matrix, changes] = await Promise.all([
        stakeholderService.getAll(),
        stakeholderService.getCritical(),
        stakeholderService.getMatrix(),
        stakeholderService.getRecentChanges()
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
  };

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      const result = await stakeholderService.runAnalysis();
      console.log('Análisis completado:', result);
      
      // Recargar datos después del análisis
      await loadAllData();
      
      alert(`✅ Análisis completado!\n\n` +
            `Stakeholders analizados: ${result.stakeholders_analyzed}\n` +
            `Críticos detectados: ${result.critical_stakeholders?.length || 0}\n` +
            `Cambios detectados: ${result.changes_detected?.length || 0}`);
    } catch (error) {
      console.error('Error ejecutando análisis:', error);
      alert('❌ Error al ejecutar el análisis');
    } finally {
      setAnalyzing(false);
    }
  };

  const filteredStakeholders = stakeholders.filter(sh =>
    sh.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    sh.stakeholder_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Dashboard de Stakeholders
        </h1>
        <p className="text-gray-600">
          Análisis inteligente de partes interesadas - ISO 4.2
        </p>
      </div>

      {/* Actions Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'Analizando...' : 'Ejecutar Análisis IA'}
            </button>

            <button
              onClick={loadAllData}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Actualizar
            </button>

            <button className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              <Plus className="mr-2 h-4 w-4" />
              Nuevo Stakeholder
            </button>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar stakeholders..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <button className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              <Download className="mr-2 h-4 w-4" />
              Exportar
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Left Column - Stakeholders Críticos */}
        <div className="lg:col-span-1">
          <CriticalStakeholders 
            stakeholders={criticalStakeholders} 
            loading={loading}
          />
        </div>

        {/* Right Column - Matriz y Métricas */}
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
        />
        
        <ChangeTimeline 
          changes={recentChanges} 
          loading={loading}
        />
      </div>
    </div>
  );
};

export default StakeholderDashboard;