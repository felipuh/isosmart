import React from 'react';
import { Routes, Route } from 'react-router-dom';
import ProtectedRoute, { PublicRoute } from './components/Auth/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import Layout from './components/Layout/Layout'

// Dashboards existentes
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
    <Routes>
      {/* Rutas públicas */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />

      {/* Rutas protegidas */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/context" element={<ContextDashboard />} />
                <Route path="/stakeholders" element={<StakeholderDashboard />} />
                <Route path="/scope" element={<ScopeDashboard />} />
                <Route path="/processes" element={<ProcessDashboard />} />
                <Route path="/documents" element={<DocumentDashboard />} />
                <Route path="/objectives" element={<ObjectiveDashboard />} />
                <Route path="/risks" element={<RiskDashboard />} />
                
                {/* Settings - solo para admin */}
                <Route
                  path="/settings"
                  element={
                    <ProtectedRoute allowedRoles={['org_admin', 'iso_manager']}>
                      <SettingsDashboard />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App;