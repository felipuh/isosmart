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
import LeadershipDashboard from './features/leadership/pages/LeadershipDashboard';
import PoliciesPage from './features/leadership/pages/PoliciesPage';
import RolesPage from './features/leadership/pages/RolesPage';
import RoleAssignmentsPage from './features/leadership/pages/RoleAssignmentsPage';
import RACIMatricesPage from './features/leadership/pages/RACIMatricesPage';
import RACIEntriesPage from './features/leadership/pages/RACIEntriesPage';
import CommitmentsPage from './features/leadership/pages/CommitmentsPage';
import CustomerFocusPage from './features/leadership/pages/CustomerFocusPage';
import ResourcesDashboard from './features/resources/pages/ResourcesDashboard';
import ResourcesPage from './features/resources/pages/ResourcesPage';
import InfrastructurePage from './features/resources/pages/InfrastructurePage';
import WorkEnvironmentPage from './features/resources/pages/WorkEnvironmentPage';
import CompetencesPage from './features/resources/pages/CompetencesPage';
import TrainingsPage from './features/resources/pages/TrainingsPage';
import AwarenessPage from './features/resources/pages/AwarenessPage';
import CommunicationsPage from './features/resources/pages/CommunicationsPage';
import PlanningDashboard from './features/planning/pages/PlanningDashboard';
import RisksOpportunitiesPage from './features/planning/pages/RisksOpportunitiesPage';
import QualityObjectivesPage from './features/planning/pages/QualityObjectivesPage';
import ObjectiveActionsPage from './features/planning/pages/ObjectiveActionsPage';
import ChangeControlPage from './features/planning/pages/ChangeControlPage';
import OperationsDashboard from './features/operations/pages/OperationsDashboard';
import CustomerRequirementsPage from './features/operations/pages/CustomerRequirementsPage';
import DesignProjectsPage from './features/operations/pages/DesignProjectsPage';
import ExternalProvidersPage from './features/operations/pages/ExternalProvidersPage';
import NonconformitiesPage from './features/operations/pages/NonconformitiesPage';
import ProductReleasesPage from './features/operations/pages/ProductReleasesPage';
import ProductionControlsPage from './features/operations/pages/ProductionControlsPage';
import PerformanceDashboard from './features/performance/pages/PerformanceDashboard';
import IndicatorsPage from './features/performance/pages/IndicatorsPage';
import MeasurementsPage from './features/performance/pages/MeasurementsPage';
import AnalysesPage from './features/performance/pages/AnalysesPage';
import AuditsPage from './features/performance/pages/AuditsPage';
import FindingsPage from './features/performance/pages/FindingsPage';
import ReviewsPage from './features/performance/pages/ReviewsPage';

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
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="context" element={<ContextDashboard />} />
        <Route path="stakeholders" element={<StakeholderDashboard />} />
        <Route path="scope" element={<ScopeDashboard />} />
        <Route path="processes" element={<ProcessDashboard />} />
        <Route path="documents" element={<DocumentDashboard />} />
        <Route path="objectives" element={<ObjectiveDashboard />} />
        <Route path="risks" element={<RiskDashboard />} />
        <Route path="leadership" element={<LeadershipDashboard />} />
        <Route path="leadership/policies" element={<PoliciesPage />} />
        <Route path="leadership/policies/new" element={<PoliciesPage />} />
        <Route path="leadership/roles" element={<RolesPage />} />
        <Route path="leadership/roles/new" element={<RolesPage />} />
        <Route path="leadership/role-assignments" element={<RoleAssignmentsPage />} />
        <Route path="leadership/commitments" element={<CommitmentsPage />} />
        <Route path="leadership/customer-focus" element={<CustomerFocusPage />} />
        <Route path="leadership/raci" element={<RACIMatricesPage />} />
        <Route path="leadership/raci/new" element={<RACIMatricesPage />} />
        <Route path="leadership/raci/:matrixId" element={<RACIEntriesPage />} />
        
        {/* Resources Module */}
        <Route path="resources" element={<ResourcesDashboard />} />
        <Route path="resources/resources" element={<ResourcesPage />} />
        <Route path="resources/resources/new" element={<ResourcesPage />} />
        <Route path="resources/infrastructure" element={<InfrastructurePage />} />
        <Route path="resources/infrastructure/new" element={<InfrastructurePage />} />
        <Route path="resources/work-environment" element={<WorkEnvironmentPage />} />
        <Route path="resources/work-environment/new" element={<WorkEnvironmentPage />} />
        <Route path="resources/competences" element={<CompetencesPage />} />
        <Route path="resources/competences/new" element={<CompetencesPage />} />
        <Route path="resources/trainings" element={<TrainingsPage />} />
        <Route path="resources/trainings/new" element={<TrainingsPage />} />
        <Route path="resources/awareness" element={<AwarenessPage />} />
        <Route path="resources/awareness/new" element={<AwarenessPage />} />
        <Route path="resources/communications" element={<CommunicationsPage />} />
        <Route path="resources/communications/new" element={<CommunicationsPage />} />
        
        {/* Planning Module */}
        <Route path="planning" element={<PlanningDashboard />} />
        <Route path="planning/risks-opportunities" element={<RisksOpportunitiesPage />} />
        <Route path="planning/risks-opportunities/new" element={<RisksOpportunitiesPage />} />
        <Route path="planning/objectives" element={<QualityObjectivesPage />} />
        <Route path="planning/objectives/new" element={<QualityObjectivesPage />} />
        <Route path="planning/actions" element={<ObjectiveActionsPage />} />
        <Route path="planning/actions/new" element={<ObjectiveActionsPage />} />
        <Route path="planning/changes" element={<ChangeControlPage />} />
        <Route path="planning/changes/new" element={<ChangeControlPage />} />
        
        {/* Operations Module */}
        <Route path="operations" element={<OperationsDashboard />} />
        <Route path="operations/requirements" element={<CustomerRequirementsPage />} />
        <Route path="operations/requirements/new" element={<CustomerRequirementsPage />} />
        <Route path="operations/design-projects" element={<DesignProjectsPage />} />
        <Route path="operations/design-projects/new" element={<DesignProjectsPage />} />
        <Route path="operations/providers" element={<ExternalProvidersPage />} />
        <Route path="operations/providers/new" element={<ExternalProvidersPage />} />
        <Route path="operations/nonconformities" element={<NonconformitiesPage />} />
        <Route path="operations/nonconformities/new" element={<NonconformitiesPage />} />
        <Route path="operations/releases" element={<ProductReleasesPage />} />
        <Route path="operations/releases/new" element={<ProductReleasesPage />} />
        <Route path="operations/production" element={<ProductionControlsPage />} />
        <Route path="operations/production/new" element={<ProductionControlsPage />} />

        {/* Performance Module */}
        <Route path="performance" element={<PerformanceDashboard />} />
        <Route path="performance/indicators" element={<IndicatorsPage />} />
        <Route path="performance/measurements" element={<MeasurementsPage />} />
        <Route path="performance/analyses" element={<AnalysesPage />} />
        <Route path="performance/audits" element={<AuditsPage />} />
        <Route path="performance/findings" element={<FindingsPage />} />
        <Route path="performance/reviews" element={<ReviewsPage />} />
        
        {/* Settings - solo para admin */}
        <Route
          path="settings"
          element={
            <ProtectedRoute allowedRoles={['org_admin', 'iso_manager']}>
              <SettingsDashboard />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  )
}

export default App;