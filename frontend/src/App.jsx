import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import ProtectedRoute, { PublicRoute } from './components/Auth/ProtectedRoute'
import OnboardingGuard from './components/Auth/OnboardingGuard';
const LoginPage = lazy(() => import('./pages/LoginPage'));
const OnboardingPage = lazy(() => import('./pages/OnboardingPage'));
import Layout from './components/Layout/Layout'
import { useI18n } from './context/I18nContext';

const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'));
const StakeholderDashboard = lazy(() => import('./components/Stakeholders/StakeholderDashboard'));
const ContextDashboard = lazy(() => import('./components/Context/ContextDashboard'));
const ScopeDashboard = lazy(() => import('./components/Scope/ScopeDashboard'));
const ProcessDashboard = lazy(() => import('./components/Processes/ProcessDashboard'));
const DocumentDashboard = lazy(() => import('./components/Documents/DocumentDashboard'));
const RiskDashboard = lazy(() => import('./components/Risks/RiskDashboard'));
const ObjectiveDashboard = lazy(() => import('./components/Objectives/ObjectiveDashboard'));
const SettingsDashboard = lazy(() => import('./components/Settings').then((module) => ({ default: module.SettingsDashboard })));
const LeadershipDashboard = lazy(() => import('./features/leadership/pages/LeadershipDashboard'));
const PoliciesPage = lazy(() => import('./features/leadership/pages/PoliciesPage'));
const RolesPage = lazy(() => import('./features/leadership/pages/RolesPage'));
const RoleAssignmentsPage = lazy(() => import('./features/leadership/pages/RoleAssignmentsPage'));
const RACIMatricesPage = lazy(() => import('./features/leadership/pages/RACIMatricesPage'));
const RACIEntriesPage = lazy(() => import('./features/leadership/pages/RACIEntriesPage'));
const CommitmentsPage = lazy(() => import('./features/leadership/pages/CommitmentsPage'));
const CustomerFocusPage = lazy(() => import('./features/leadership/pages/CustomerFocusPage'));
const ResourcesDashboard = lazy(() => import('./features/resources/pages/ResourcesDashboard'));
const ResourcesPage = lazy(() => import('./features/resources/pages/ResourcesPage'));
const InfrastructurePage = lazy(() => import('./features/resources/pages/InfrastructurePage'));
const WorkEnvironmentPage = lazy(() => import('./features/resources/pages/WorkEnvironmentPage'));
const CompetencesPage = lazy(() => import('./features/resources/pages/CompetencesPage'));
const TrainingsPage = lazy(() => import('./features/resources/pages/TrainingsPage'));
const AwarenessPage = lazy(() => import('./features/resources/pages/AwarenessPage'));
const CommunicationsPage = lazy(() => import('./features/resources/pages/CommunicationsPage'));
const PlanningDashboard = lazy(() => import('./features/planning/pages/PlanningDashboard'));
const RisksOpportunitiesPage = lazy(() => import('./features/planning/pages/RisksOpportunitiesPage'));
const QualityObjectivesPage = lazy(() => import('./features/planning/pages/QualityObjectivesPage'));
const ObjectiveActionsPage = lazy(() => import('./features/planning/pages/ObjectiveActionsPage'));
const ChangeControlPage = lazy(() => import('./features/planning/pages/ChangeControlPage'));
const OperationsDashboard = lazy(() => import('./features/operations/pages/OperationsDashboard'));
const CustomerRequirementsPage = lazy(() => import('./features/operations/pages/CustomerRequirementsPage'));
const DesignProjectsPage = lazy(() => import('./features/operations/pages/DesignProjectsPage'));
const ExternalProvidersPage = lazy(() => import('./features/operations/pages/ExternalProvidersPage'));
const NonconformitiesPage = lazy(() => import('./features/operations/pages/NonconformitiesPage'));
const ProductReleasesPage = lazy(() => import('./features/operations/pages/ProductReleasesPage'));
const ProductionControlsPage = lazy(() => import('./features/operations/pages/ProductionControlsPage'));
const PerformanceDashboard = lazy(() => import('./features/performance/pages/PerformanceDashboard'));
const IndicatorsPage = lazy(() => import('./features/performance/pages/IndicatorsPage'));
const MeasurementsPage = lazy(() => import('./features/performance/pages/MeasurementsPage'));
const AnalysesPage = lazy(() => import('./features/performance/pages/AnalysesPage'));
const AuditsPage = lazy(() => import('./features/performance/pages/AuditsPage'));
const FindingsPage = lazy(() => import('./features/performance/pages/FindingsPage'));
const ReviewsPage = lazy(() => import('./features/performance/pages/ReviewsPage'));
const ImprovementDashboard = lazy(() => import('./features/improvement/pages/ImprovementDashboard'));
const ImprovementNonconformitiesPage = lazy(() => import('./features/improvement/pages/ImprovementNonconformitiesPage'));
const ImprovementCorrectiveActionsPage = lazy(() => import('./features/improvement/pages/ImprovementCorrectiveActionsPage'));
const ImprovementContinualPage = lazy(() => import('./features/improvement/pages/ImprovementContinualPage'));

function App() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen text-slate-300">Cargando...</div>}>
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
            <OnboardingGuard>
              <Layout />
            </OnboardingGuard>
          </ProtectedRoute>
        }
      >
        <Route path="onboarding" element={<OnboardingPage />} />
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

        {/* Improvement Module */}
        <Route path="improvement" element={<ImprovementDashboard />} />
        <Route path="improvement/nonconformities" element={<ImprovementNonconformitiesPage />} />
        <Route path="improvement/nonconformities/new" element={<ImprovementNonconformitiesPage />} />
        <Route path="improvement/corrective-actions" element={<ImprovementCorrectiveActionsPage />} />
        <Route path="improvement/corrective-actions/new" element={<ImprovementCorrectiveActionsPage />} />
        <Route path="improvement/continual" element={<ImprovementContinualPage />} />
        <Route path="improvement/continual/new" element={<ImprovementContinualPage />} />
        
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
    </Suspense>
  )
}

export default App;