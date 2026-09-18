import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import VirtualAssistantPanel from '../Assistant/VirtualAssistantPanel';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const content = children ?? <Outlet />;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 transition-colors duration-300 dark:bg-slate-950 dark:text-white">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[70] focus:rounded-lg focus:bg-blue-800 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
      >
        {typeof document !== 'undefined' && document.documentElement.lang === 'en' ? 'Skip to content' : 'Saltar al contenido'}
      </a>
      <Header onMenuClick={() => setSidebarOpen((value) => !value)} sidebarOpen={sidebarOpen} />
      
      <div className="flex pt-16">
        {sidebarOpen && (
          <button
            type="button"
            className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden"
            aria-hidden="true"
            tabIndex={-1}
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        <main id="main-content" className="flex-1 transition-all duration-300 lg:ml-72" tabIndex={-1}>
          <div className="mx-auto w-full max-w-[1520px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
            {content}
          </div>
        </main>
      </div>

      <VirtualAssistantPanel />
    </div>
  );
};

export default Layout;
