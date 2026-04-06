from django.urls import path
from . import views

urlpatterns = [
    path('latest/', views.get_latest_analysis, name='context-latest'),
    path('internal-factors/', views.get_latest_analysis, name='internal-factors'),
    path('analyze/', views.trigger_analysis, name='context-analyze'),
    path('history/', views.get_analysis_history, name='context-history'),
    path('external-signals/', views.get_external_signals, name='context-external-signals'),
    path('environmental-alerts/', views.get_environmental_alerts, name='context-environmental-alerts'),
    path('environmental-alerts/<int:alert_id>/acknowledge/', views.acknowledge_environmental_alert, name='context-environmental-alert-ack'),
    path('environmental-dashboard/', views.get_environmental_dashboard, name='context-environmental-dashboard'),
]