from django.contrib import admin
from django.urls import path, include
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', views.health_check, name='health'),
    path('api/', include('core.urls')),
    path('api/sie/', include('ai_modules.sie.urls')),
    path('api/context/', include('ai_modules.sca.urls')),
    path('api/scope/', include('ai_modules.asb.urls')),
    path('api/processes/', include('ai_modules.spm.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)