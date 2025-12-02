from django.urls import path
from . import views

urlpatterns = [
    path('latest/', views.get_latest_analysis, name='context-latest'),
    path('analyze/', views.trigger_analysis, name='context-analyze'),
]