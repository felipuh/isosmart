import React from 'react';
import { Activity, Bell, Settings, User } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-white shadow-md border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">ISO Smart</h1>
              <p className="text-xs text-gray-500">Sistema Inteligente de Gobierno de Calidad</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button className="relative p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            <button className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
              <Settings className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-2 pl-4 border-l border-gray-200">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              <div className="hidden md:block">
                <p className="text-sm font-semibold text-gray-900">Admin</p>
                <p className="text-xs text-gray-500">Gerente de Calidad</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
