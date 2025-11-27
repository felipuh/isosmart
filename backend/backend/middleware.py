import re
from django.utils.deprecation import MiddlewareMixin

class CsrfExemptAPIMiddleware(MiddlewareMixin):
    """
    Middleware para eximir rutas /api/* de verificación CSRF
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
