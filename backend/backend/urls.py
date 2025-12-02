from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', views.health_check, name='health'),
    
    # API endpoints
    path('api/', views.dashboard_summary, name='api-root'),
    path('api/dashboard/', views.dashboard_summary, name='dashboard-summary'),
    path('api/risks/', views.risk_matrix_list, name='risk-matrix-list'),
    path('api/context/latest/', views.context_analysis_latest, name='context-latest'),
    path('api/context/analyze/', views.trigger_context_analysis, name='trigger-analysis'),
    path('api/sie/', include('ai_modules.sie.urls')),
]