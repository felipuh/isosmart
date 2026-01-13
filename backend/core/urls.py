from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/summary/', views.dashboard_summary, name='dashboard-summary'),
    path('risks/matrix/', views.risk_matrix_list, name='risk-matrix'),
    path('context/latest/', views.context_analysis_latest, name='context-latest'),
    path('health/', views.health_check, name='health-check'),
]