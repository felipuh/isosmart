from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'risks', views.RiskMatrixViewSet, basename='risk')
router.register(r'objectives', views.QualityObjectiveViewSet, basename='objective')
router.register(r'organizations', views.OrganizationViewSet, basename='organization')
router.register(r'users', views.UserManagementViewSet, basename='user-management')
router.register(r'settings', views.SettingsViewSet, basename='settings')
router.register(r'billing', views.BillingViewSet, basename='billing')
router.register(r'iso-clauses', views.ISOClauseConfigViewSet, basename='iso-clause')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('dashboard/summary/', views.dashboard_summary, name='dashboard-summary'),
    path('dashboard/', views.dashboard_summary, name='dashboard-summary-alias'),
    path('risks/matrix/', views.risk_matrix_list, name='risk-matrix'),
    path('risks/stats/', views.risk_stats, name='risk-stats'),
    path('context/latest/', views.context_analysis_latest, name='context-latest'),
    path('health/', views.health_check, name='health-check'),
    path('export/', views.export_data, name='export-data'),
    path('feature-flags/', views.feature_flags_view, name='feature-flags'),
    path('', include(router.urls)),
]
