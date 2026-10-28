from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'scopes', views.ScopeDefinitionViewSet, basename='scope-definition')
router.register(r'processes', views.ProcessScopeViewSet, basename='process-scope')
router.register(r'locations', views.LocationScopeViewSet, basename='location-scope')

app_name = 'asb'

urlpatterns = [
    path('', include(router.urls)),
    path('generate/', views.run_scope_analysis, name='generate-scope'),
    path('statement/', views.get_scope_statement, name='scope-statement'),
    path('audit/', views.run_scope_audit, name='scope-audit'),
    path('analyze/', views.run_scope_analysis, name='run-analysis'),
    path('latest/', views.get_latest_scope, name='latest-scope'),
]