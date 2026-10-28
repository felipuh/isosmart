import re
import uuid
from django.utils.deprecation import MiddlewareMixin

from backend.request_context import set_request_id

class CsrfExemptAPIMiddleware(MiddlewareMixin):
    """
    Middleware para proteger rutas /api/* — CSRF está habilitado pero HTTP-only cookies
    con JWT no requieren verificación CSRF explícita (JWT va en header Authorization)
    """
    def process_request(self, request):
        # DEPRECATED: Esta clase no hace nada; CSRF está habilitado globalmente.
        # JWT en headers Authorization no requiere CSRF (no hay cookies de sesión).
        pass


class RequestIDMiddleware(MiddlewareMixin):
    """Attach and propagate a request id for traceability across services."""

    header_name = 'HTTP_X_REQUEST_ID'

    def process_request(self, request):
        request_id = request.META.get(self.header_name) or str(uuid.uuid4())
        request.request_id = request_id
        request.META[self.header_name] = request_id
        set_request_id(request_id)

    def process_response(self, request, response):
        request_id = getattr(request, 'request_id', None)
        if request_id:
            response['X-Request-ID'] = request_id
        return response
