"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
import sys

def health_check(request):
    """Endpoint de health check"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'isosmart-backend',
        'python_version': sys.version,
    })

@never_cache
def api_root(request):
    """Root de la API"""
    return JsonResponse({
        'message': 'ISO Smart API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'health': '/health',
            'docs': '/api/docs/',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', health_check, name='health'),
    path('api/', api_root, name='api-root'),
    # Aquí agregaremos las rutas de los módulos de IA
]