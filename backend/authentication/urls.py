"""
URLs de Autenticación para ISO Smart
"""

from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Auth endpoints
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='refresh'),
    path('me/', views.MeView.as_view(), name='me'),
    
    # Organization management
    path('switch-organization/', views.SwitchOrganizationView.as_view(), name='switch-organization'),
    
    # Password management
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/request/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # User management (org_admin only)
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
]
