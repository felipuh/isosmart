from django.contrib import admin
from django.urls import path, include
from core import views
from ai_modules.spm import views as spm_views
from ai_modules.sie import views as sie_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', views.health_check, name='health'),
    
    # Explicit routes for stats and latest endpoints (before includes to take priority)
    path('api/maps/stats/', spm_views.ProcessMapViewSet.as_view({'get': 'stats'}), name='maps-stats'),
    path('api/maps/latest/', spm_views.get_latest_map, name='latest-map-detailed'),
    path('api/processes/maps/latest/', spm_views.get_latest_map, name='latest-map-processes-detailed'),
    path('api/latest/', spm_views.get_latest_map, name='latest-map-alias'),
    
    # Module includes
    path('api/sca/', include('ai_modules.sca.urls')),
    path('api/', include('core.urls')),
    path('api/sie/', include('ai_modules.sie.urls')),
    path('api/stakeholders/', include('ai_modules.sie.urls')),  # Alias for frontend compatibility
    path('api/change-logs/', include('ai_modules.sie.urls')),  # Alias for change-logs endpoints
    path('api/context/', include('ai_modules.sca.urls')),
    path('api/scope/', include('ai_modules.asb.urls')),
    path('api/scopes/', include('ai_modules.asb.urls')),  # Alias for frontend compatibility
    path('api/processes/', include('ai_modules.spm.urls')),
    path('api/maps/', include('ai_modules.spm.urls')),  # Alias for frontend compatibility
    
    # Explicit aliases for frontend endpoints without duplicated prefixes
    path('api/stakeholders/critical/', sie_views.StakeholderProfileViewSet.as_view({'get': 'critical'}), name='stakeholders-critical'),
    path('api/stakeholders/matrix/', sie_views.StakeholderProfileViewSet.as_view({'get': 'matrix'}), name='stakeholders-matrix'),
    path('api/change-logs/recent/', sie_views.StakeholderChangeLogViewSet.as_view({'get': 'recent'}), name='change-logs-recent'),
    path('api/leadership/', include('leadership.urls')),
    path('api/auth/', include('authentication.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)