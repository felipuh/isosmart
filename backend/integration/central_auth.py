"""CH: cryptographic receiver isolation plus Decision A live authentication.

ADMIN_APPS_SSO requires explicit BASE_URL, ISSUER, CLIENT_ID and AUDIENCE.
Local session envelopes retain a central access proof and never outlive it.
No central refresh token is stored; expiry requires central reauthentication.
"""
import time
import uuid
from functools import wraps
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from rest_framework.exceptions import AuthenticationFailed, APIException

from .trust_jwt import CONTRACT, decode, trust

PRODUCT = 'ISO_SMART'


class AuthorityUnavailable(APIException):
    status_code = 503
    default_detail = 'No fue posible validar la autenticación central.'
    default_code = 'central_auth_unavailable'


def authority_errors(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except APIException:
            raise
        except Exception:
            raise AuthorityUnavailable() from None
    return wrapped


def configuration():
    config = getattr(settings, 'ADMIN_APPS_SSO', {})
    if not isinstance(config, dict):
        raise AuthorityUnavailable()
    if any(not isinstance(config.get(k), str) or not config[k].strip()
           for k in ('BASE_URL', 'ISSUER', 'CLIENT_ID', 'AUDIENCE')):
        raise AuthorityUnavailable()
    url = urlsplit(config['BASE_URL'])
    if url.scheme not in ('http', 'https') or not url.netloc or url.username or url.password:
        raise AuthorityUnavailable()
    if url.scheme != 'https' and not getattr(settings, 'DEBUG', False):
        raise AuthorityUnavailable()
    central, _ = trust('CENTRAL')
    if central.get('PRIVATE_KEY') or central['ISSUER'] != config['ISSUER']:
        raise AuthorityUnavailable()
    return config


def central_request(endpoint, payload):
    config = configuration()
    integration = getattr(settings, 'ADMIN_APPS_INTEGRATION', {})
    if not isinstance(integration.get('API_KEY'), str) or not integration['API_KEY']:
        raise AuthorityUnavailable()
    payload = dict(payload, client_id=config['CLIENT_ID'], audience=[config['AUDIENCE']],
                   product=PRODUCT, contract_version=CONTRACT)
    try:
        response = requests.post(
            config['BASE_URL'].rstrip('/') + endpoint,
            json=payload, headers={'X-API-Key': integration.get('API_KEY', '')},
            timeout=integration.get('TIMEOUT', 10), allow_redirects=False,
        )
        if response.status_code in (400, 401, 403, 404):
            raise AuthenticationFailed('Autenticación central rechazada.')
        if response.status_code != 200:
            raise AuthorityUnavailable()
        data = response.json()
        if not isinstance(data, dict) or data.get('error') or data.get('two_fa_bypassed') is True:
            raise AuthorityUnavailable()
        return data
    except (AuthenticationFailed, AuthorityUnavailable):
        raise
    except Exception:
        raise AuthorityUnavailable() from None


def validate_proof(proof, *, organization_id=None, email=None):
    config = configuration()
    if not isinstance(proof, str) or not proof:
        raise AuthenticationFailed('Se requiere autenticación central nueva.')
    signed = decode(proof, family='CENTRAL', audience=config['AUDIENCE'], product=PRODUCT,
                    client_id=config['CLIENT_ID'])
    validate_lifecycle(signed)
    data = central_request('/sso/introspect/', {'token': proof})
    # Both signature and authenticated live authority must agree before projection.
    for key in ('auth_contract', 'token_family', 'token_type', 'product', 'client_id', 'iss', 'aud',
                'sub', 'tenant_id', 'organization_id', 'exp', 'iat', 'jti', 'amr', 'mfa_generation',
                'email', 'role', 'lifecycle', 'sid', 'sg', 'av', 'auth_time'):
        if data.get(key) != signed.get(key):
            raise AuthenticationFailed('Respuesta central inconsistente.')
    if (data.get('active') is not True or data.get('auth_contract') != CONTRACT
            or data.get('iss') != config['ISSUER']
            or data.get('client_id') != config['CLIENT_ID']
            or data.get('aud') != [config['AUDIENCE']]
            or not isinstance(data.get('amr'), list) or 'pwd' not in data['amr']):
        raise AuthenticationFailed('Prueba central inválida.')
    try:
        uuid.UUID(data['sub'])
        uuid.UUID(data['organization_id'])
        if type(data['exp']) is not int or data['exp'] <= time.time():
            raise ValueError()
        if not isinstance(data['email'], str) or not data['email']:
            raise ValueError()
    except (KeyError, TypeError, ValueError, AttributeError):
        raise AuthenticationFailed('Contexto central inválido.') from None
    if organization_id is not None and str(organization_id) != data['organization_id']:
        raise AuthenticationFailed('El cambio de organización requiere autenticación central.')
    if email is not None and email.lower() != data['email'].lower():
        raise AuthenticationFailed('Identidad central incompatible.')
    if getattr(settings, 'OWNER_ORGANIZATION_ONLY_ACCESS', False):
        owner = getattr(settings, 'OWNER_ORGANIZATION_EXTERNAL_ID', '')
        if not isinstance(owner, str) or not owner:
            raise AuthorityUnavailable()
        if data['organization_id'] != owner:
            raise AuthenticationFailed('Organización fuera del alcance de esta instancia.')
    products = data.get('products')
    product_code = 'ISO_SMART'
    if not isinstance(products, list) or not any(
        isinstance(p, dict) and p.get('code') == product_code and p.get('access_allowed') is True
        for p in products
    ):
        raise AuthenticationFailed('Acceso de producto denegado.')
    return data


def login(attrs, request=None):
    configuration()
    org_id = attrs.get('organization_id')
    if org_id:
        from core.models import Organization
        try:
            uuid.UUID(str(org_id))
        except (ValueError, TypeError, AttributeError):
            org_id = Organization.objects.get(pk=org_id, is_active=True).external_id
    requested_org = str(org_id) if org_id else None
    challenge = attrs.get('challenge_token')
    if challenge:
        if not attrs.get('otp_code'):
            raise AuthenticationFailed('Se requiere código TOTP o de respaldo.')
        data = central_request('/sso/login/verify-2fa/', {
            'challenge_token': challenge, 'otp_code': attrs['otp_code'],
        })
    else:
        if not attrs.get('email') or not attrs.get('password'):
            raise AuthenticationFailed('Email y contraseña requeridos.')
        data = central_request('/sso/login/', {
            'email': attrs['email'], 'password': attrs['password'],
            'organization_id': requested_org,
        })
    if data.get('requires_2fa') is True:
        if data.get('tokens') or not isinstance(data.get('challenge_token'), str) or not data['challenge_token']:
            raise AuthorityUnavailable()
        return {'challenge': {'requires_2fa': True, 'challenge_token': data['challenge_token'],
                              'challenge_expires_in': data.get('challenge_expires_in', 300)}}
    if data.get('requires_2fa') is not False or data.get('two_fa_bypassed') is not False:
        raise AuthorityUnavailable()
    tokens = data.get('tokens')
    if not isinstance(tokens, dict):
        raise AuthorityUnavailable()
    proof = tokens.get('access_token')
    verified = validate_proof(proof, organization_id=requested_org, email=attrs.get('email'))
    user, profile = sync_identity(verified)
    if request is not None:
        request.admin_apps_data = {'user': {'id': verified['sub'], 'email': verified['email']},
                                   'organization': {'id': verified['organization_id']},
                                   'organizations': verified.get('memberships', []), 'role': verified.get('role')}
    return {'user': user, 'profile': profile, 'central_proof': proof, 'central_exp': verified['exp']}


@transaction.atomic
def sync_identity(data):
    from authentication.models import User, UserProfile
    from core.models import Organization
    from integration.backends import ROLE_MAP
    org = Organization.objects.filter(external_id=data['organization_id']).first()
    if org is None:
        slug = slugify(data.get('organization_code') or data['organization_id'])[:80]
        if Organization.objects.filter(slug=slug).exists():
            raise AuthenticationFailed('Conflicto de identidad de organización.')
        org = Organization.objects.create(external_id=data['organization_id'], slug=slug,
                                          name=data.get('organization_name') or slug, is_active=True)
    if not org.is_active:
        raise AuthenticationFailed('Organización local inactiva.')
    # An email is not an immutable central subject. Existing projections require
    # an explicit mapping; never take over a local account by matching email.
    username = 'adminapps:' + data['sub']
    user = User.objects.filter(username=username).first()
    created = False
    if user is None:
        user = User.objects.filter(email=data['email'].lower()).first()
        if user is not None:
            require_user_binding(user, data['sub'])
        else:
            full_name = str(data.get('full_name') or '').split(' ', 1)
            user = User.objects.create(username=username, email=data['email'].lower(), is_active=True,
                                       first_name=full_name[0], last_name=full_name[1] if len(full_name)>1 else '')
            created = True
    if user.email.lower() != data['email'].lower():
        raise AuthenticationFailed('Conflicto de identidad de usuario.')
    if not user.is_active:
        raise AuthenticationFailed('Usuario local inactivo.')
    if user.is_locked():
        raise AuthenticationFailed('Cuenta local temporalmente bloqueada.')
    from django.utils import timezone
    expiry = user.get_temporary_password_expiry()
    if expiry is not None and timezone.now() >= expiry:
        raise AuthenticationFailed('Contraseña temporal expirada; requiere recuperación central.')
    if created or user.has_usable_password():
        user.set_unusable_password()
        user.save(update_fields=['password'])
    role = ROLE_MAP.get(data.get('role'))
    if role is None:
        raise AuthenticationFailed('Rol central desconocido.')
    profile, _ = UserProfile.objects.update_or_create(user=user, organization=org,
                                                    defaults={'role': role, 'is_active': True})
    return user, profile


@authority_errors
def validate_session(token, user=None):
    if (token.get('auth_contract') != CONTRACT or token.get('token_family') != 'LOCAL'
            or token.get('product') != PRODUCT):
        raise AuthenticationFailed('Se requiere autenticación central nueva.')
    from authentication.models import User, UserProfile
    user = user or User.objects.get(pk=token['user_id'], is_active=True)
    profile = UserProfile.objects.select_related('organization').get(
        pk=token['profile_id'], user=user, organization_id=token['organization_id'],
        is_active=True, organization__is_active=True,
    )
    data = validate_proof(token.get('central_proof'), organization_id=profile.organization.external_id,
                          email=user.email)
    if (token.get('central_sub') != data['sub'] or token.get('sub') != data['sub']
            or token.get('tenant_id') != data['organization_id'] or token['exp'] > data['exp']):
        raise AuthenticationFailed('Sujeto central incompatible.')
    if any(token.get(k) != data.get(k) for k in ('sid', 'sg', 'av', 'auth_time', 'lifecycle')):
        raise AuthenticationFailed('Generación de sesión no vigente.')
    require_user_binding(user, data['sub'])
    from integration.backends import ROLE_MAP
    if token.get('role') != profile.role or ROLE_MAP.get(data.get('role')) != profile.role:
        raise AuthenticationFailed('Rol de sesión no vigente.')
    return data


@authority_errors
def bind_session(refresh, proof, profile, user):
    data = validate_proof(proof, organization_id=profile.organization.external_id, email=user.email)
    require_user_binding(user, data['sub'])
    from .local_tokens import bind_claims
    bind_claims(refresh, data)
    refresh['auth_contract'] = CONTRACT
    refresh['central_sub'] = data['sub']
    refresh['central_proof'] = proof
    refresh['exp'] = min(refresh['exp'], data['exp'])
    return refresh


def require_user_binding(user, subject):
    mapping = getattr(settings, 'ADMIN_APPS_USER_BINDINGS', {})
    if user.username != 'adminapps:' + subject and (
        not isinstance(mapping, dict) or mapping.get(subject) != user.pk
    ):
        raise AuthenticationFailed('Proyección local sin identidad central verificable.')


@authority_errors
def session_pair(user, profile, proof):
    # Validate before creating even a local outstanding-refresh record.
    from .local_tokens import LocalRefreshToken as RefreshToken
    data = validate_proof(proof, organization_id=profile.organization.external_id, email=user.email)
    require_user_binding(user, data['sub'])
    refresh = RefreshToken.for_user(user)
    from .local_tokens import bind_claims
    bind_claims(refresh, data)
    refresh['auth_contract'] = CONTRACT
    refresh['central_sub'] = data['sub']
    refresh['central_proof'] = proof
    refresh['exp'] = min(refresh['exp'], data['exp'])
    refresh['organization_id'] = profile.organization_id
    refresh['role'] = profile.role
    refresh['profile_id'] = profile.id
    access = refresh.access_token
    access['exp'] = min(access['exp'], data['exp'])
    return refresh, access


def validate_lifecycle(data):
    try:
        if (data.get('lifecycle') != 'rec-sso-03b-v1'
                or str(uuid.UUID(data['sid'])) != data['sid']
                or any(type(data.get(k)) is not int or data[k] <= 0 for k in ('sg', 'av', 'auth_time'))
                or data['auth_time'] > data['iat'] or data['exp'] > data['auth_time'] + 300):
            raise ValueError()
    except (KeyError, ValueError, TypeError, AttributeError):
        raise AuthenticationFailed('Estado durable de sesión requerido.') from None


@authority_errors
def rotate_session(refresh):
    old = validate_session(refresh)
    result = central_request('/sso/rotate/', {'token': refresh['central_proof']})
    proof = result.get('tokens', {}).get('access_token')
    current = validate_proof(proof, organization_id=old['tenant_id'], email=old['email'])
    if (any(current[k] != old[k] for k in ('sid', 'sub', 'tenant_id', 'av', 'auth_time', 'exp'))
            or current['sg'] <= old['sg']):
        raise AuthenticationFailed('Rotación central inconsistente.')
    from .local_tokens import bind_claims
    bind_claims(refresh, current)
    refresh['central_proof'] = proof
    refresh.set_jti()
    refresh['exp'] = min(refresh['exp'], current['exp'])
    access = refresh.access_token
    access['exp'] = min(access['exp'], current['exp'])
    return refresh, access


@authority_errors
def logout_session(token):
    # Token supplied by authenticated request, never a body-selected subject.
    result = central_request('/sso/logout/', {'token': token['central_proof']})
    if result.get('revoked') is not True:
        raise AuthorityUnavailable()
