from django.urls import path
from . import views

urlpatterns = [
    path('latest/', views.get_latest_analysis, name='context-latest'),
    path('internal-factors/', views.get_latest_analysis, name='internal-factors'),
    path('analyze/', views.trigger_analysis, name='context-analyze'),
    path('history/', views.get_analysis_history, name='context-history'),
]