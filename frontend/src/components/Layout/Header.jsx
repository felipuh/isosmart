import React from 'react';
import { Activity, Bell, Settings, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import UserMenu from '../Auth/UserMenu';

const Header = () => {
  const { user, profile, currentOrganization } = useAuth();

  return (
    <header className="bg-white dark:bg-slate-800 shadow-md dark:shadow-slate-900 border-b border-slate-200 dark:border-slate-700 transition-colors duration-300 fixed top-0 left-0 right-0 z-50">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">ISO Smart</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {currentOrganization?.name || 'Sistema Inteligente de Gobierno de Calidad'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button className="relative p-2 text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            <Link 
              to="/settings"
              className="p-2 text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5" />
            </Link>

            <UserMenu />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
