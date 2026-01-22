import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './components/Dashboard/Dashboard';
import StakeholderDashboard from './components/Stakeholders/StakeholderDashboard';
import ContextDashboard from './components/Context/ContextDashboard';
import ScopeDashboard from './components/Scope/ScopeDashboard';
import ProcessDashboard from './components/Processes/ProcessDashboard';
import DocumentDashboard from './components/Documents/DocumentDashboard';
import RiskDashboard from './components/Risks/RiskDashboard';
import ObjectiveDashboard from './components/Objectives/ObjectiveDashboard';
import { SettingsDashboard } from './components/Settings';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="flex h-screen bg-gray-100 dark:bg-slate-900 transition-colors duration-300">
          <Sidebar />
          <div className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stakeholders" element={<StakeholderDashboard />} />
              <Route path="/context" element={<ContextDashboard />} />
              <Route path="/scope" element={<ScopeDashboard />} /> 
              <Route path="/processes" element={<ProcessDashboard />} />
              <Route path="/documents" element={<DocumentDashboard />} />
              <Route path="/risks" element={<RiskDashboard />} />
              <Route path="/objectives" element={<ObjectiveDashboard />} />
              <Route path="/settings" element={<SettingsDashboard />} />
            </Routes>
          </div>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;