import React from 'react';
import { FileText, CheckCircle, XCircle } from 'lucide-react';

const ScopeStatement = ({ scopeData, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!scopeData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Declaración de Alcance</h3>
        <p className="text-gray-500 text-center py-8">No hay definición de alcance disponible</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <FileText className="h-6 w-6 text-blue-500 mr-2" />
          <h3 className="text-xl font-semibold">Declaración de Alcance</h3>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
          scopeData.status === 'active' ? 'bg-green-100 text-green-800' :
          scopeData.status === 'approved' ? 'bg-blue-100 text-blue-800' :
          scopeData.status === 'under_review' ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {scopeData.status === 'active' ? 'ACTIVO' :
           scopeData.status === 'approved' ? 'APROBADO' :
           scopeData.status === 'under_review' ? 'EN REVISIÓN' : 'BORRADOR'}
        </span>
      </div>

      {/* Info del alcance */}
      <div className="grid grid-cols-3 gap-4 mb-6 pb-6 border-b">
        <div>
          <p className="text-sm text-gray-600">Versión</p>
          <p className="text-lg font-semibold">{scopeData.version}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Fecha Vigencia</p>
          <p className="text-lg font-semibold">
            {new Date(scopeData.effective_date).toLocaleDateString('es-ES')}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Cobertura</p>
          <p className="text-lg font-semibold text-blue-600">
            {scopeData.coverage_percentage?.toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Declaración */}
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 mb-3">Declaración Formal</h4>
        <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-blue-500">
          <p className="text-gray-700 whitespace-pre-line leading-relaxed">
            {scopeData.scope_statement}
          </p>
        </div>
      </div>

      {/* Productos y Servicios */}
      {scopeData.products_services && scopeData.products_services.length > 0 && (
        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            Productos y Servicios ({scopeData.products_services.length})
          </h4>
          <ul className="space-y-2">
            {scopeData.products_services.map((product, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                <span className="text-gray-700">{product}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Exclusiones */}
      {scopeData.exclusions && scopeData.exclusions.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
            <XCircle className="h-5 w-5 text-orange-500 mr-2" />
            Exclusiones Permitidas ({scopeData.exclusions.length})
          </h4>
          <div className="space-y-3">
            {scopeData.exclusions.map((exclusion, idx) => (
              <div key={idx} className="bg-orange-50 border-l-4 border-orange-400 p-3 rounded">
                <p className="font-medium text-orange-900">
                  Cláusula {exclusion.clause}: {exclusion.title}
                </p>
                <p className="text-sm text-orange-700 mt-1">
                  <span className="font-medium">Razón:</span> {exclusion.reason}
                </p>
                {exclusion.impact && (
                  <p className="text-xs text-orange-600 mt-1">
                    <span className="font-medium">Impacto:</span> {exclusion.impact}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ScopeStatement;