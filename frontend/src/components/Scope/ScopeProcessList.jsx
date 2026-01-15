import React from 'react';
import { Plus, Edit2, Trash2, Settings, Truck, BarChart3 } from 'lucide-react';

const ScopeProcessList = ({ processes, locations, loading, onAddProcess, onEditProcess, onDeleteProcess, onAddLocation, onEditLocation, onDeleteLocation }) => {
  
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
      case 'strategic': return 'Estratégico';
      case 'operational': return 'Operativo';
      case 'support': return 'Apoyo';
      default: return type;
    }
  };

  const getLocationTypeLabel = (type) => {
    const types = {
      'headquarters': 'Sede Principal',
      'branch': 'Sucursal',
      'warehouse': 'Almacén',
      'plant': 'Planta',
      'office': 'Oficina',
      'remote': 'Remoto'
    };
    return types[type] || type;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-100 rounded"></div>
            <div className="h-16 bg-gray-100 rounded"></div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-100 rounded"></div>
            <div className="h-16 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Procesos */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">Procesos en Alcance</h3>
          <button
            onClick={onAddProcess}
            className="flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-1" />
            Agregar
          </button>
        </div>
        <div className="p-4">
          {processes && processes.length > 0 ? (
            <div className="space-y-3">
              {processes.map((process) => (
                <div 
                  key={process.id} 
                  className={'p-3 rounded-lg border ' + (process.is_included ? 'bg-gray-50' : 'bg-red-50 border-red-200')}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      {getProcessTypeIcon(process.process_type)}
                      <div>
                        <p className="font-medium text-gray-900">{process.process_name}</p>
                        <p className="text-sm text-gray-500">
                          {process.process_code && <span className="mr-2">{process.process_code}</span>}
                          <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">
                            {getProcessTypeLabel(process.process_type)}
                          </span>
                        </p>
                        {process.owner && (
                          <p className="text-xs text-gray-400 mt-1">Responsable: {process.owner}</p>
                        )}
                        {!process.is_included && (
                          <p className="text-xs text-red-600 mt-1">Excluido: {process.exclusion_reason}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => onEditProcess(process)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDeleteProcess(process)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Settings className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No hay procesos definidos</p>
              <button
                onClick={onAddProcess}
                className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
              >
                Agregar primer proceso
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Ubicaciones */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">Ubicaciones en Alcance</h3>
          <button
            onClick={onAddLocation}
            className="flex items-center px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
          >
            <Plus className="h-4 w-4 mr-1" />
            Agregar
          </button>
        </div>
        <div className="p-4">
          {locations && locations.length > 0 ? (
            <div className="space-y-3">
              {locations.map((location) => (
                <div 
                  key={location.id} 
                  className={'p-3 rounded-lg border ' + (location.is_included ? 'bg-gray-50' : 'bg-red-50 border-red-200')}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{location.location_name}</p>
                      <p className="text-sm text-gray-500">
                        {location.city}, {location.country}
                        <span className="ml-2 text-xs bg-gray-200 px-2 py-0.5 rounded">
                          {getLocationTypeLabel(location.location_type)}
                        </span>
                      </p>
                      {location.employee_count > 0 && (
                        <p className="text-xs text-gray-400 mt-1">{location.employee_count} empleados</p>
                      )}
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => onEditLocation(location)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDeleteLocation(location)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Truck className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No hay ubicaciones definidas</p>
              <button
                onClick={onAddLocation}
                className="mt-2 text-green-600 hover:text-green-800 text-sm"
              >
                Agregar primera ubicación
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScopeProcessList;
