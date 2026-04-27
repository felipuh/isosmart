import re
import uuid
from django.utils.deprecation import MiddlewareMixin

from backend.request_context import set_request_id

class CsrfExemptAPIMiddleware(MiddlewareMixin):
    """
    Middleware para eximir rutas /api/* de verificación CSRF
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)


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
