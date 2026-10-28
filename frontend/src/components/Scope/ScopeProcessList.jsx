import React from 'react';
import { Plus, Edit2, Trash2, Settings, Truck, BarChart3 } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const ScopeProcessList = ({ processes, locations, loading, onAddProcess, onEditProcess, onDeleteProcess, onAddLocation, onEditLocation, onDeleteLocation }) => {
  const { t } = useI18n();
  
  const getProcessTypeIcon = (type) => {
    switch(type) {
      case 'strategic': return <BarChart3 className="h-4 w-4 text-purple-500" />;
      case 'operational': return <Settings className="h-4 w-4 text-blue-500" />;
      case 'support': return <Truck className="h-4 w-4 text-green-500" />;
      default: return <Settings className="h-4 w-4 text-gray-500" />;
    }
  };

  const getProcessTypeLabel = (type) => {
    switch(type) {
      case 'strategic': return t('processForm.types.strategic');
      case 'operational': return t('processForm.types.operational');
      case 'support': return t('processForm.types.support');
      default: return type;
    }
  };

  const getLocationTypeLabel = (type) => {
    const types = {
      headquarters: t('scopeProcessList.locationTypes.headquarters'),
      branch: t('scopeProcessList.locationTypes.branch'),
      warehouse: t('scopeProcessList.locationTypes.warehouse'),
      plant: t('scopeProcessList.locationTypes.plant'),
      office: t('scopeProcessList.locationTypes.office'),
      remote: t('scopeProcessList.locationTypes.remote')
    };
    return types[type] || type;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 animate-pulse transition-colors">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-slate-100 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-100 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 animate-pulse transition-colors">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-slate-100 dark:bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-100 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Procesos */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 transition-colors">
        <div className="p-4 border-b dark:border-slate-700 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800 dark:text-white">{t('scopeProcessList.processes.title')}</h3>
          <button
            onClick={onAddProcess}
            className="flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-1" />
            {t('common.buttons.add')}
          </button>
        </div>
        <div className="p-4">
          {processes && processes.length > 0 ? (
            <div className="space-y-3">
              {processes.map((process) => (
                <div 
                  key={process.id} 
                  className={'p-3 rounded-lg border transition-colors ' + (process.is_included ? 'bg-slate-50 dark:bg-slate-700 dark:border-slate-600 border-slate-200' : 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700')}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      {getProcessTypeIcon(process.process_type)}
                      <div>
                        <p className="font-medium text-slate-900 dark:text-white">{process.process_name}</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {process.process_code && <span className="mr-2">{process.process_code}</span>}
                          <span className="text-xs bg-slate-200 dark:bg-slate-600 dark:text-slate-300 px-2 py-0.5 rounded">
                            {getProcessTypeLabel(process.process_type)}
                          </span>
                        </p>
                        {process.owner && (
                          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{t('scopeProcessList.processes.owner')}: {process.owner}</p>
                        )}
                        {!process.is_included && (
                          <p className="text-xs text-red-600 dark:text-red-400 mt-1">{t('scopeProcessList.processes.excluded')}: {process.exclusion_reason}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => onEditProcess(process)}
                        className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-colors"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDeleteProcess(process)}
                        className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              <Settings className="h-12 w-12 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
              <p>{t('scopeProcessList.processes.empty')}</p>
              <button
                onClick={onAddProcess}
                className="mt-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm transition-colors"
              >
                {t('scopeProcessList.processes.addFirst')}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Ubicaciones */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 transition-colors">
        <div className="p-4 border-b dark:border-slate-700 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800 dark:text-white">{t('scopeProcessList.locations.title')}</h3>
          <button
            onClick={onAddLocation}
            className="flex items-center px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-1" />
            {t('common.buttons.add')}
          </button>
        </div>
        <div className="p-4">
          {locations && locations.length > 0 ? (
            <div className="space-y-3">
              {locations.map((location) => (
                <div 
                  key={location.id} 
                  className={'p-3 rounded-lg border transition-colors ' + (location.is_included ? 'bg-slate-50 dark:bg-slate-700 dark:border-slate-600 border-slate-200' : 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700')}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">{location.location_name}</p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        {location.city}, {location.country}
                        <span className="ml-2 text-xs bg-slate-200 dark:bg-slate-600 dark:text-slate-300 px-2 py-0.5 rounded">
                          {getLocationTypeLabel(location.location_type)}
                        </span>
                      </p>
                      {location.employee_count > 0 && (
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{location.employee_count} {t('scopeProcessList.locations.employees')}</p>
                      )}
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => onEditLocation(location)}
                        className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-colors"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDeleteLocation(location)}
                        className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              <Truck className="h-12 w-12 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
              <p>{t('scopeProcessList.locations.empty')}</p>
              <button
                onClick={onAddLocation}
                className="mt-2 text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 text-sm transition-colors"
              >
                {t('scopeProcessList.locations.addFirst')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScopeProcessList;