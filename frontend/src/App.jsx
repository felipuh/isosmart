import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './components/Dashboard/Dashboard';
import StakeholderDashboard from './components/Stakeholders/StakeholderDashboard';
import ContextDashboard from './components/Context/ContextDashboard';

// Componentes placeholder para rutas faltantes
const ComingSoon = ({ title }) => (
  <div className="p-6 bg-gray-50 min-h-screen flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">{title}</h1>
      <p className="text-gray-600 mb-8">Este módulo estará disponible próximamente</p>
      <div className="text-6xl mb-4">🚧</div>
      <p className="text-sm text-gray-500">En desarrollo...</p>
    </div>
  </div>
);

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        <div className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/stakeholders" element={<StakeholderDashboard />} />
            <Route path="/context" element={<ContextDashboard />} />
            <Route path="/risks" element={<ComingSoon title="Matriz de Riesgos" />} />
            <Route path="/objectives" element={<ComingSoon title="Objetivos de Calidad" />} />
            <Route path="/settings" element={<ComingSoon title="Configuración" />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;