from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'maps', views.ProcessMapViewSet, basename='process-map')
router.register(r'processes', views.ProcessViewSet, basename='process')
router.register(r'interactions', views.ProcessInteractionViewSet, basename='interaction')
router.register(r'activities', views.ProcessActivityViewSet, basename='activity')

app_name = 'spm'

urlpatterns = [
    path('', include(router.urls)),
    path('analyze/', views.run_process_mapping, name='run-mapping'),
    path('latest/', views.get_latest_map, name='latest-map'),
]