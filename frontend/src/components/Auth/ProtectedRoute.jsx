/**
 * ProtectedRoute - Componente para proteger rutas
 * Redirige a login si no está autenticado
 * Opcionalmente verifica roles
 */

import { Link, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';

// Spinner de carga
const LoadingSpinner = () => {
  const { t } = useI18n();
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-slate-400">{t('auth.protectedRoute.verifying')}</p>
      </div>
    </div>
  );
};

// Página de acceso denegado
const AccessDenied = ({ requiredRoles }) => {
  const { t } = useI18n();
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="bg-slate-800/50 backdrop-blur-sm border border-red-500/30 rounded-xl p-8 max-w-md text-center">
        <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-white mb-2">{t('auth.protectedRoute.accessDenied')}</h2>
        <p className="text-slate-400 mb-4">
          {t('auth.protectedRoute.noPermission')}
          {requiredRoles && (
            <span className="block mt-2 text-sm">
              {t('auth.protectedRoute.requiredRoles')}: {requiredRoles.join(', ')}
            </span>
          )}
        </p>
        <Link
          to="/"
          className="inline-block px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
        >
          {t('auth.protectedRoute.backHome')}
        </Link>
      </div>
    </div>
  );
};

/**
 * Componente ProtectedRoute
 * 
 * @param {React.ReactNode} children - Componentes hijos a renderizar si está autenticado
 * @param {string[]} allowedRoles - Roles permitidos para acceder (opcional)
 * @param {string} redirectTo - Ruta de redirección si no está autenticado
 */
const ProtectedRoute = ({ 
  children, 
  allowedRoles = null,
  redirectTo = '/login' 
}) => {
  const { isAuthenticated, loading, hasRole } = useAuth();
  const location = useLocation();

  // Mostrar spinner mientras carga
  if (loading) {
    return <LoadingSpinner />;
  }

  // Redirigir a login si no está autenticado
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Verificar roles si se especificaron
  if (allowedRoles && !hasRole(allowedRoles)) {
    return <AccessDenied requiredRoles={allowedRoles} />;
  }

  // Renderizar contenido protegido
  return children;
};

/**
 * Componente PublicRoute
 * Redirige a home si ya está autenticado (útil para login/registro)
 */
export const PublicRoute = ({ children, redirectTo = '/' }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (isAuthenticated) {
    // Redirigir a donde venía o al home
    const from = location.state?.from?.pathname || redirectTo;
    return <Navigate to={from} replace />;
  }

  return children;
};

export default ProtectedRoute;