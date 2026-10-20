"""Consumer session family, independent of the legacy SIMPLE_JWT signing key."""
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken, Token
from rest_framework_simplejwt.exceptions import TokenBackendError

from .trust_jwt import CONTRACT, decode, encode, leeway, trust


def context():
    from .central_auth import configuration, PRODUCT
    central = configuration()
    local, _ = trust('LOCAL')
    if local['AUDIENCE'] == central['AUDIENCE']:
        from .trust_jwt import TrustUnavailable
        raise TrustUnavailable()
    return local, central, PRODUCT


class LocalBackend:
    def __init__(self, token_type):
        self.token_type = token_type

    def get_leeway(self):
        return leeway()

    def encode(self, payload):
        local, central, product = context()
        return encode(payload, family='LOCAL', audience=local['AUDIENCE'], product=product,
                      client_id=central['CLIENT_ID'])

    def decode(self, token, verify=True):
        # Never expose an unverified path, even when a caller passes verify=False.
        local, central, product = context()
        try:
            return decode(token, family='LOCAL', audience=local['AUDIENCE'], product=product,
                          client_id=central['CLIENT_ID'], token_type=self.token_type)
        except APIException as exc:
            if exc.status_code == 503:
                raise
            raise TokenBackendError('Invalid local session.') from None


class LocalAccessToken(AccessToken):
    def get_token_backend(self):
        return LocalBackend('access')


class LocalRefreshToken(RefreshToken):
    access_token_class = LocalAccessToken

    @classmethod
    def for_user(cls, user):
        # Central state owns revocation. Do not persist complete local JWTs in
        # SimpleJWT outstanding-token records.
        return Token.for_user.__func__(cls, user)

    def check_blacklist(self):
        # Every use must call validate_session/rotate_session at the authority.
        return None

    def get_token_backend(self):
        return LocalBackend('refresh')


def bind_claims(token, data):
    local, central, product = context()
    token['auth_contract'] = CONTRACT
    token['token_family'] = 'LOCAL'
    token['iss'] = local['ISSUER']
    token['aud'] = [local['AUDIENCE']]
    token['client_id'] = central['CLIENT_ID']
    token['product'] = product
    token['sub'] = data['sub']
    token['tenant_id'] = data['organization_id']
    token['amr'] = data['amr']

    for key in ('lifecycle', 'sid', 'sg', 'av', 'auth_time'):
        token[key] = data[key]
