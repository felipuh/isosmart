import React from 'react';
import { Building, MapPin, Package, Users } from 'lucide-react';
import { useI18n } from '../../context/I18nContext';

const OrganizationalBoundaries = ({ boundaries, loading }) => {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
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
      case 'geographic': return t('organizationalBoundaries.types.geographic');
      case 'functional': return t('organizationalBoundaries.types.functional');
      case 'product_lines': return t('organizationalBoundaries.types.productLines');
      case 'organizational_units': return t('organizationalBoundaries.types.organizationalUnits');
      default: return type;
    }
  };

  const getBoundaryColor = (type) => {
    switch (type) {
      case 'geographic': return 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-300';
      case 'functional': return 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700 text-green-700 dark:text-green-300';
      case 'product_lines': return 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300';
      case 'organizational_units': return 'bg-orange-50 dark:bg-orange-900/30 border-orange-200 dark:border-orange-700 text-orange-700 dark:text-orange-300';
      default: return 'bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300';
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow dark:shadow-slate-900/50 p-6 transition-colors">
      <h3 className="text-xl font-semibold mb-6 dark:text-white">{t('organizationalBoundaries.title')}</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(boundaries).map(([type, items]) => (
          <div key={type} className={`border-2 rounded-lg p-4 transition-colors ${getBoundaryColor(type)}`}>
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
              <p className="text-sm italic opacity-75">{t('organizationalBoundaries.notDefined')}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrganizationalBoundaries;