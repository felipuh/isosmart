import React from 'react';
import { Building, MapPin, Package, Users } from 'lucide-react';

const OrganizationalBoundaries = ({ boundaries, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!boundaries) {
    return null;
  }

  const getBoundaryIcon = (type) => {
    switch (type) {
      case 'geographic': return <MapPin className="h-5 w-5" />;
      case 'functional': return <Building className="h-5 w-5" />;
      case 'product_lines': return <Package className="h-5 w-5" />;
      case 'organizational_units': return <Users className="h-5 w-5" />;
      default: return <Building className="h-5 w-5" />;
    }
  };

  const getBoundaryTitle = (type) => {
    switch (type) {
      case 'geographic': return 'Límites Geográficos';
      case 'functional': return 'Límites Funcionales';
      case 'product_lines': return 'Líneas de Producto/Servicio';
      case 'organizational_units': return 'Unidades Organizacionales';
      default: return type;
    }
  };

  const getBoundaryColor = (type) => {
    switch (type) {
      case 'geographic': return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'functional': return 'bg-green-50 border-green-200 text-green-700';
      case 'product_lines': return 'bg-purple-50 border-purple-200 text-purple-700';
      case 'organizational_units': return 'bg-orange-50 border-orange-200 text-orange-700';
      default: return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-6">Límites Organizacionales</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(boundaries).map(([type, items]) => (
          <div key={type} className={`border-2 rounded-lg p-4 ${getBoundaryColor(type)}`}>
            <div className="flex items-center mb-3">
              {getBoundaryIcon(type)}
              <h4 className="ml-2 font-semibold">{getBoundaryTitle(type)}</h4>
            </div>
            
            {Array.isArray(items) && items.length > 0 ? (
              <ul className="space-y-2">
                {items.map((item, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="mr-2">•</span>
                    <span className="text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm italic opacity-75">No definido</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrganizationalBoundaries;