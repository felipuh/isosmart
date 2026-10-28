/**
 * UserMenu - Componente de menú de usuario para el header
 * Muestra información del usuario, organización actual y opciones
 */

import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import { Link, useNavigate } from 'react-router-dom';

const UserMenu = () => {
  const { t } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const [showOrgSelector, setShowOrgSelector] = useState(false);
  const menuRef = useRef(null);
  const navigate = useNavigate();
  
  const { 
    user, 
    profile, 
    organizations, 
    currentOrganization,
    logout, 
    switchOrganization 
  } = useAuth();

  // Cerrar menú al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
        setShowOrgSelector(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSwitchOrg = async (orgId) => {
    const result = await switchOrganization(orgId);
    if (result.success) {
      setShowOrgSelector(false);
      setIsOpen(false);
      navigate('/', { replace: true });
    }
  };

  const closeMenu = () => {
    setIsOpen(false);
    setShowOrgSelector(false);
  };

  const getRoleColor = (role) => {
    const colors = {
      org_admin: 'text-purple-400 bg-purple-500/20',
      iso_manager: 'text-cyan-400 bg-cyan-500/20',
      auditor: 'text-amber-400 bg-amber-500/20',
      user: 'text-green-400 bg-green-500/20',
      viewer: 'text-slate-400 bg-slate-500/20',
    };
    return colors[role] || colors.viewer;
  };

  if (!user) return null;

  return (
    <div className="relative" ref={menuRef}>
      {/* Botón del menú */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
      >
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white font-semibold shadow-lg shadow-cyan-500/20">
          {user.first_name?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase()}
        </div>
        
        {/* Info */}
        <div className="hidden md:block text-left">
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            {user.first_name} {user.last_name}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {currentOrganization?.name || t('auth.userMenu.noOrganization')}
          </p>
        </div>

        {/* Flecha */}
        <svg
          className={`w-4 h-4 text-slate-500 dark:text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Menú desplegable */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700/50 rounded-xl shadow-2xl overflow-hidden z-50">
          {/* Header del menú */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-700/50">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white font-bold text-lg">
                {user.first_name?.[0]?.toUpperCase()}
              </div>
              <div>
                <p className="font-medium text-slate-900 dark:text-white">
                  {user.first_name} {user.last_name}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{user.email}</p>
                {profile && (
                  <span className={`inline-block px-2 py-0.5 mt-1 text-xs rounded-full ${getRoleColor(profile.role)}`}>
                    {profile.role_display}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Selector de organización */}
          {organizations.length > 1 && (
            <div className="p-2 border-b border-slate-200 dark:border-slate-700/50">
              <button
                onClick={() => setShowOrgSelector(!showOrgSelector)}
                className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-slate-500 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <span className="text-sm text-slate-800 dark:text-white">{currentOrganization?.name}</span>
                </div>
                <svg
                  className={`w-4 h-4 text-slate-500 dark:text-slate-400 transition-transform ${showOrgSelector ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Lista de organizaciones */}
              {showOrgSelector && (
                <div className="mt-1 space-y-1">
                  {organizations.map((org) => (
                    <button
                      key={org.id}
                      onClick={() => handleSwitchOrg(org.id)}
                      disabled={org.is_current}
                      className={`w-full flex items-center justify-between p-2 rounded-lg text-left text-sm transition-colors ${
                        org.is_current
                          ? 'bg-blue-100 text-blue-700 dark:bg-cyan-500/20 dark:text-cyan-400'
                          : 'hover:bg-slate-100 dark:hover:bg-slate-700/50 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <span>{org.name}</span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">{org.role_display}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Opciones del menú */}
          <div className="p-2">
            <Link
              to="/settings"
              onClick={closeMenu}
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>{t('auth.userMenu.settings')}</span>
            </Link>

            <Link
              to="/profile"
              onClick={closeMenu}
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span>{t('auth.userMenu.profile')}</span>
            </Link>

            <Link
              to="/profile#password"
              onClick={closeMenu}
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c1.657 0 3-1.343 3-3S13.657 5 12 5s-3 1.343-3 3 1.343 3 3 3z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a7 7 0 0114 0" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 11l2 2 4-4" />
              </svg>
              <span>{t('settings.users.password.title')}</span>
            </Link>

            <hr className="my-2 border-slate-200 dark:border-slate-700/50" />

            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-red-500/20 transition-colors text-red-400"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>{t('auth.userMenu.logout')}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserMenu;