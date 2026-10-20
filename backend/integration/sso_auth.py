"""Decision A local session envelopes backed by live central authentication."""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed
from integration.central_auth import validate_session, AuthorityUnavailable

class Smart3AISSOAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Only CookieJWTAuthentication authenticates browser sessions in ISO.
        # Stop the optional development SessionAuthentication chain from granting
        # a local Django session access without a centrally backed cookie.
        raw_request = getattr(request, '_request', request)
        session_user = getattr(raw_request, 'user', None)
        if (not raw_request.COOKIES.get('isosmart_access')
                and getattr(session_user, 'is_authenticated', False)):
            raise AuthenticationFailed('Se requiere sesión central de navegador.')
        return None

    def get_validated_token(self, raw_token):
        from .local_tokens import LocalAccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        try:
            return LocalAccessToken(raw_token)
        except TokenError:
            raise AuthenticationFailed('Sesión local inválida.') from None

    def get_user(self, validated_token):
        try:
            user = super().get_user(validated_token)
            validate_session(validated_token, user)
            return user
        except APIException:
            raise
        except Exception:
            raise AuthorityUnavailable() from None
