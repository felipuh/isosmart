"""Only existing authentication and reviewed resource handlers are exposed."""
from django.urls import include, path
from rest_framework.routers import SimpleRouter
from resources.views import ResourceViewSet

router = SimpleRouter()
router.register('resources', ResourceViewSet)
urlpatterns = [path('api/auth/', include('authentication.urls')),
               path('api/', include(router.urls))]
