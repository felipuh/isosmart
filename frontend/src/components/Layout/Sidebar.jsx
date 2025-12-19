import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Users, Target, TrendingUp, FileText, Settings, Network } from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: Home },
    { name: 'Stakeholders', path: '/stakeholders', icon: Network },
    { name: 'Contexto', path: '/context', icon: TrendingUp },
    { name: 'Alcance SGC', path: '/scope', icon: Target },
    { name: 'Riesgos', path: '/risks', icon: FileText },
    { name: 'Objetivos', path: '/objectives', icon: Target },
    { name: 'Configuración', path: '/settings', icon: Settings },
  ];

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold">ISO Smart</h1>
        <p className="text-sm text-gray-400">Sistema de Gobierno de Calidad</p>
      </div>

      {/* Menu Items */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <p className="text-xs text-gray-400 text-center">
          ISO 9001:2015 | ISO/IEC 42001:2023
        </p>
      </div>
    </div>
  );
};

export default Sidebar;