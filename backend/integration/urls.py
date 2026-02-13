"""
URLs for Admin Apps integration
"""

from django.urls import path
from . import views

app_name = 'integration'

urlpatterns = [
    path('health/', views.admin_apps_health, name='adminapps-health'),
    path('organizations/', views.organizations, name='adminapps-organizations'),
    path('organizations/<int:org_id>/', views.organization_detail, name='adminapps-organization-detail'),
    path('organizations/<int:org_id>/users/', views.organization_users, name='adminapps-organization-users'),
    path('organizations/<int:org_id>/modules/', views.organization_modules, name='adminapps-organization-modules'),
]
