"""CH consumer contracts, synthetic RSA, real adapters/serializers/JWT/views.
Run from backend with .venv/bin/python -B integration/tests_ch_offline.py.
--coordinated receives proofs issued by the real central endpoint code via stdin;
proofs and private key material are never written to logs or fixture files.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT = Path.cwd()
spec = importlib.util.spec_from_file_location('decision_a', ROOT / 'integration/tests_decision_a_offline.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt
from integration import trust_jwt as crypto
from integration.local_tokens import LocalAccessToken, LocalRefreshToken
from authentication.models import User, UserProfile


def keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return (key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode(),
            key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode())


PRIVATE, PUBLIC = keypair()
LOCAL_PRIVATE, LOCAL_PUBLIC = keypair()
CENTRAL = {'ALGORITHM': 'RS256', 'ISSUER': 'https://central.invalid', 'PUBLIC_KEYS': {'synthetic-central': PUBLIC}}
LOCAL = {'ALGORITHM': 'RS256', 'ISSUER': 'https://' + h.PRODUCT.lower() + '.invalid',
         'AUDIENCE': h.PRODUCT + '-session', 'SIGNING_KID': 'synthetic-local', 'PRIVATE_KEY': LOCAL_PRIVATE,
         'PUBLIC_KEYS': {'synthetic-local': LOCAL_PUBLIC}}


def claims(**changes):
    result = {'auth_contract': crypto.CONTRACT, 'token_family': 'CENTRAL', 'token_type': 'access',
              'product': h.PRODUCT, 'iss': CENTRAL['ISSUER'], 'aud': ['synthetic-audience'],
              'client_id': 'synthetic-client', 'sub': h.SUB, 'user_id': h.SUB, 'tenant_id': h.ORG, 'organization_id': h.ORG,
              'email': 'person@example.invalid', 'role': 'viewer', 'amr': ['pwd', 'otp'],
              'mfa_generation': 'synthetic-generation', 'iat': int(time.time()), 'exp': int(time.time()) + 300,
              'jti': 'synthetic-jti', 'full_name': 'Synthetic Person'}
    result.update(changes)
    return result


def proof(data):
    return jwt.encode(data, PRIVATE, algorithm='RS256', headers={'kid': 'synthetic-central'})


def introspection(data):
    return dict(data, active=True, products=[{'code': h.PRODUCT, 'access_allowed': True}])


class ConsumerCHTests(unittest.TestCase):
    def setUp(self):
        for name, value in [('SSO_CENTRAL_TRUST', CENTRAL.copy()), ('SSO_LOCAL_TRUST', LOCAL.copy()), ('AUTH_COOKIE_SECURE', True),
                            ('AUTH_ACCESS_COOKIE_AGE', 300), ('AUTH_REFRESH_COOKIE_AGE', 300)]:
            p = patch.object(h.settings, name, value, create=True); p.start(); self.addCleanup(p.stop)
        self.user = NS(id=1, pk=1, username='adminapps:' + h.SUB, email='person@example.invalid', is_active=True)
        self.profile = NS(id=2, organization_id=3, organization=NS(external_id=h.ORG), role='viewer')
        self.data = claims(); self.proof = proof(self.data)
        p = patch.object(h.c.requests, 'post'); self.transport = p.start(); self.addCleanup(p.stop)
        self.real_sync = h.c.sync_identity.__wrapped__
        p = patch.object(h.c, 'sync_identity', return_value=(self.user, self.profile)); self.sync = p.start(); self.addCleanup(p.stop)
        self.response(introspection(self.data))

    def response(self, *values):
        self.transport.side_effect = [NS(status_code=200, json=lambda v=v: copy.deepcopy(v)) for v in values]

    def serializer(self, **attrs):
        s = h.LoginSerializer(data=attrs, context={'request': NS()}); s.is_valid(raise_exception=True); return s

    def complete(self):
        return {'requires_2fa': False, 'two_fa_bypassed': False, 'tokens': {'access_token': self.proof}}

    def pair(self):
        self.response(introspection(self.data))
        return h.c.session_pair(self.user, self.profile, self.proof)

    def test_valid_login_real_signature_before_projection(self):
        self.response(self.complete(), introspection(self.data))
        result = self.serializer(email=self.user.email, password=' local secret ')
        self.assertIs(result.validated_data['user'], self.user)
        self.sync.assert_called_once()
        for call in self.transport.call_args_list:
            self.assertEqual(call.kwargs['json']['product'], h.PRODUCT)
            self.assertEqual(call.kwargs['json']['contract_version'], crypto.CONTRACT)
            self.assertEqual(call.kwargs['headers']['X-API-Key'], 'synthetic-key')
            self.assertFalse(call.kwargs['allow_redirects'])
        self.assertEqual(self.transport.call_args_list[0].kwargs['json']['password'], ' local secret ')

    def test_tampered_signature_denied_before_transport(self):
        bad = self.proof[:-20] + ('A' if self.proof[-20] != 'A' else 'B') + self.proof[-19:]
        with self.assertRaises(h.AuthenticationFailed): h.c.validate_proof(bad)
        self.transport.assert_not_called(); self.sync.assert_not_called()

    def test_foreign_product_audience_tenant_and_issuer(self):
        for key, value in [('product', 'ISO_SMART' if h.PRODUCT == 'MEDSUPPLIER' else 'MEDSUPPLIER'),
                           ('aud', ['other']), ('aud', None), ('aud', 'synthetic-audience'), ('iss', 'https://evil.invalid'),
                           ('client_id', 'foreign'), ('token_family', 'LOCAL'), ('sub', 'not-uuid'),
                           ('tenant_id', 'cccccccc-cccc-4ccc-8ccc-cccccccccccc'), ('exp', int(time.time()) - 1),
                           ('auth_contract', 'decision-a-v1'), ('amr', [])]:
            with self.subTest(key=key):
                data = claims(**{key: value})
                with self.assertRaises(h.APIException): h.c.validate_proof(proof(data))
        self.transport.assert_not_called()

    def test_alg_none_hmac_unknown_kid(self):
        for token in [jwt.encode(self.data, '', algorithm='none'),
                      jwt.encode(self.data, 'synthetic-hmac-key-never-deploy', algorithm='HS256', headers={'kid': 'synthetic-central'}),
                      jwt.encode(self.data, PRIVATE, algorithm='RS256', headers={'kid': 'unknown'})]:
            with self.assertRaises(h.AuthenticationFailed): h.c.validate_proof(token)
        self.transport.assert_not_called()

    def test_introspection_disagreement_and_revocation(self):
        for key, value in [('active', False), ('sub', 'cccccccc-cccc-4ccc-8ccc-cccccccccccc'), ('role', 'org_admin'),
                           ('tenant_id', 'cccccccc-cccc-4ccc-8ccc-cccccccccccc'), ('product', 'OTHER'), ('amr', ['pwd']),
                           ('exp', self.data['exp'] + 1), ('jti', 'foreign'), ('products', [])]:
            self.response(dict(introspection(self.data), **{key: value}))
            with self.subTest(key=key), self.assertRaises(h.AuthenticationFailed): h.c.validate_proof(self.proof)
        self.sync.assert_not_called()

    def test_requested_tenant_cannot_be_substituted(self):
        self.response(self.complete(), introspection(self.data))
        with self.assertRaises(h.AuthenticationFailed):
            self.serializer(email=self.user.email, password='synthetic', organization_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc')
        self.sync.assert_not_called()

    def test_missing_config_credentials_or_key_material(self):
        for field, config in [('SSO_CENTRAL_TRUST', {}), ('SSO_LOCAL_TRUST', {}), ('ADMIN_APPS_SSO', {}),
                               ('ADMIN_APPS_INTEGRATION', {'API_KEY': ''}),
                               ('SSO_CENTRAL_TRUST', dict(CENTRAL, PRIVATE_KEY=PRIVATE))]:
            with patch.object(h.settings, field, config):
                with self.assertRaises(h.APIException):
                    self.pair()

    def test_central_and_local_keys_must_be_distinct(self):
        with patch.object(h.settings, 'SSO_LOCAL_TRUST', dict(LOCAL, PRIVATE_KEY=PRIVATE, PUBLIC_KEYS={'synthetic-local': PUBLIC})):
            with self.assertRaises(h.APIException): self.pair()
        with patch.object(h.settings, 'SSO_LOCAL_TRUST', dict(LOCAL, ISSUER=CENTRAL['ISSUER'])):
            with self.assertRaises(h.APIException): self.pair()
        with patch.object(h.settings, 'SSO_LOCAL_TRUST', dict(LOCAL, AUDIENCE='synthetic-audience')):
            with self.assertRaises(h.APIException): self.pair()

    def test_local_pair_is_tenant_subject_and_expiry_bound(self):
        refresh, access = self.pair()
        for token, cls in [(refresh, LocalRefreshToken), (access, LocalAccessToken)]:
            decoded = cls(str(token))
            self.assertEqual(decoded['token_family'], 'LOCAL')
            self.assertEqual(decoded['product'], h.PRODUCT)
            self.assertEqual(decoded['sub'], h.SUB)
            self.assertEqual(decoded['tenant_id'], h.ORG)
            self.assertLessEqual(decoded['exp'], self.data['exp'])
            self.assertEqual(decoded['role'], 'viewer')
            self.assertNotIn('is_superuser', decoded.payload)
        self.assertEqual(jwt.get_unverified_header(str(access))['kid'], 'synthetic-local')

    def test_local_as_central_and_central_as_local(self):
        _, access = self.pair()
        self.transport.reset_mock()
        with self.assertRaises(h.AuthenticationFailed): h.c.validate_proof(str(access))
        with self.assertRaises(h.AuthenticationFailed): h.Smart3AISSOAuthentication().get_validated_token(self.proof)
        self.transport.assert_not_called()

    def test_old_generic_tokens_never_become_local(self):
        old = h.RefreshToken(); old['user_id'] = 1; old['auth_contract'] = 'decision-a-v1'
        with self.assertRaises(h.AuthenticationFailed): h.Smart3AISSOAuthentication().get_validated_token(str(old.access_token))
        from rest_framework_simplejwt.exceptions import TokenError
        with self.assertRaises(TokenError): LocalRefreshToken(str(old))

    def test_refresh_live_authority_and_revocation(self):
        refresh, _ = self.pair()
        with patch.object(User.objects, 'get', return_value=self.user), \
             patch.object(UserProfile.objects, 'select_related') as profiles, \
             patch.object(h.views.RefreshTokenBlacklist.objects, 'filter') as blacklist, \
             patch.object(h.views.RefreshTokenBlacklist.objects, 'get_or_create'), \
             patch.object(h.settings, 'SIMPLE_JWT', {'ROTATE_REFRESH_TOKENS': True}, create=True):
            profiles.return_value.get.return_value = self.profile
            blacklist.return_value.exists.return_value = False
            req = NS(COOKIES={'isosmart_refresh': str(refresh)}, data={'refresh': str(refresh)})
            csrf = patch.object(h.views.CookieJWTAuthentication, 'enforce_csrf') if h.PRODUCT == 'ISO_SMART' else patch.object(h.views, 'logger')
            with csrf:
                self.response(introspection(self.data))
                response = h.views.RefreshTokenView().post(req)
                self.assertEqual(response.status_code, 200)
                rotated = response.cookies['isosmart_refresh'].value if h.PRODUCT == 'ISO_SMART' else response.data['refresh']
                parsed = LocalRefreshToken(rotated)
                self.assertLessEqual(parsed['exp'], self.data['exp'])
                self.assertNotEqual(parsed['jti'], refresh['jti'])
                self.response(dict(introspection(self.data), active=False))
                with self.assertRaises(h.AuthenticationFailed): h.views.RefreshTokenView().post(req)

    def test_expired_central_never_mints_local(self):
        data = claims(exp=int(time.time()) - 1)
        with patch.object(LocalRefreshToken, 'for_user') as mint:
            with self.assertRaises(h.AuthenticationFailed): h.c.session_pair(self.user, self.profile, proof(data))
            mint.assert_not_called()
        self.transport.assert_not_called()

    def test_tenant_switch_and_uuid_binding(self):
        profile = copy.deepcopy(self.profile); profile.organization.external_id = 'cccccccc-cccc-4ccc-8ccc-cccccccccccc'
        with self.assertRaises(h.AuthenticationFailed): h.c.session_pair(self.user, profile, self.proof)
        self.response(introspection(self.data)); self.user.username = 'unbound-local'
        with self.assertRaises(h.AuthenticationFailed): h.c.session_pair(self.user, self.profile, self.proof)

    def test_session_profile_role_tenant_and_subject(self):
        refresh, _ = self.pair()
        with patch.object(UserProfile.objects, 'select_related') as profiles:
            profiles.return_value.get.return_value = self.profile
            self.response(introspection(self.data))
            self.assertEqual(h.c.validate_session(refresh, self.user)['sub'], h.SUB)
            for key, value in [('role', 'org_admin'), ('central_sub', 'foreign'), ('tenant_id', 'foreign'), ('exp', self.data['exp'] + 99)]:
                changed = dict(refresh.payload, **{key: value}); self.response(introspection(self.data))
                with self.assertRaises(h.AuthenticationFailed): h.c.validate_session(changed, self.user)

    def test_schema_failure_sanitized(self):
        refresh, _ = self.pair()
        with patch.object(UserProfile.objects, 'select_related', side_effect=RuntimeError('private-schema')):
            with self.assertRaises(h.c.AuthorityUnavailable) as caught: h.c.validate_session(refresh, self.user)
            self.assertNotIn('private-schema', str(caught.exception))

    def test_challenge_and_verify_flow(self):
        self.response({'requires_2fa': True, 'challenge_token': 'synthetic-challenge'})
        result = self.serializer(email=self.user.email, password='synthetic')
        self.assertIn('challenge', result.validated_data); self.sync.assert_not_called()
        for code in ('123456', 'synthetic-backup'):
            self.response(self.complete(), introspection(self.data))
            self.assertIn('user', self.serializer(challenge_token='synthetic-challenge', otp_code=code).validated_data)

    def test_owner_policy(self):
        with patch.object(h.settings, 'OWNER_ORGANIZATION_ONLY_ACCESS', True, create=True), \
             patch.object(h.settings, 'OWNER_ORGANIZATION_EXTERNAL_ID', 'cccccccc-cccc-4ccc-8ccc-cccccccccccc', create=True):
            with self.assertRaises(h.AuthenticationFailed): h.c.validate_proof(self.proof)

    def test_session_transport_preserved(self):
        refresh, access = self.pair()
        req = h.APIRequestFactory().get('/', HTTP_AUTHORIZATION='Bearer ' + str(access))
        if h.PRODUCT == 'ISO_SMART':
            from authentication.cookie_auth import CookieJWTAuthentication
            self.assertIsNone(h.Smart3AISSOAuthentication().authenticate(req))
            self.assertIsNone(CookieJWTAuthentication().authenticate(req))
            req.user = NS(is_authenticated=True)
            with self.assertRaises(h.AuthenticationFailed): h.Smart3AISSOAuthentication().authenticate(req)
            from rest_framework.response import Response
            response = h.views.set_auth_cookies(Response({}), access=access, refresh=refresh)
            self.assertTrue(response.cookies['isosmart_access']['httponly'])
            req = h.APIRequestFactory().post('/', {}, format='json')
            req.COOKIES['isosmart_access'] = str(access)
            req._dont_enforce_csrf_checks = False
            with self.assertRaises(h.APIException): CookieJWTAuthentication().authenticate(req)
        else:
            with patch.object(h.Smart3AISSOAuthentication, 'get_user', return_value=self.user):
                user, token = h.Smart3AISSOAuthentication().authenticate(req)
                self.assertIs(user, self.user); self.assertEqual(token['token_family'], 'LOCAL')

    def test_middleware_uses_verified_local_family(self):
        from authentication.middleware import OrganizationMiddleware
        refresh, access = self.pair()
        req = h.APIRequestFactory().get('/', HTTP_AUTHORIZATION='Bearer ' + str(access))
        req.COOKIES['isosmart_access'] = str(access)
        with patch.object(h.Smart3AISSOAuthentication, 'get_user', return_value=self.user), \
             patch.object(UserProfile.objects, 'select_related') as profiles:
            profiles.return_value.get.return_value = self.profile
            middleware = OrganizationMiddleware(lambda request: None)
            middleware.process_request(req)
            self.assertEqual(req.organization_id, 3)
            self.assertEqual(req.user_role, 'viewer')
            req.COOKIES['isosmart_access'] = self.proof
            req.META['HTTP_AUTHORIZATION'] = 'Bearer ' + self.proof
            middleware.process_request(req)
            self.assertIsNone(req.organization_id)
            self.assertIsNone(req.user_role)

    def test_refresh_with_expired_embedded_proof_is_denied(self):
        refresh, _ = self.pair()
        refresh['central_proof'] = proof(claims(exp=int(time.time()) - 1))
        # Simulate a still-valid local envelope containing an expired central proof.
        parsed = LocalRefreshToken(str(refresh))
        with patch.object(UserProfile.objects, 'select_related') as profiles:
            profiles.return_value.get.return_value = self.profile
            with self.assertRaises(h.AuthenticationFailed): h.c.validate_session(parsed, self.user)

    def test_local_header_algorithm_and_key_restrictions(self):
        from rest_framework_simplejwt.exceptions import TokenError
        refresh, _ = self.pair()
        for token in [jwt.encode(refresh.payload, '', algorithm='none'),
                      jwt.encode(refresh.payload, 'synthetic-local-hmac', algorithm='HS256', headers={'kid': 'synthetic-local'}),
                      jwt.encode(refresh.payload, LOCAL_PRIVATE, algorithm='RS256', headers={'kid': 'unknown'}),
                      jwt.encode(refresh.payload, PRIVATE, algorithm='RS256', headers={'kid': 'synthetic-local'})]:
            with self.assertRaises(TokenError): LocalRefreshToken(token)

    # Unchanged Decision A probes reused with the new setup, without editing history.
    test_local_password_and_flags_never_rescue = h.ConsumerTests.test_local_password_and_flags_never_rescue
    test_transport_and_json_errors_are_sanitized = h.ConsumerTests.test_transport_and_json_errors_are_sanitized
    test_direct_backend_stops_local_chain = h.ConsumerTests.test_direct_backend_stops_local_chain
    test_no_email_takeover_without_subject_binding = h.ConsumerTests.test_no_email_takeover_without_subject_binding
    test_projection_rejects_email_and_slug_collision = h.ConsumerTests.test_projection_rejects_email_and_slug_collision
    test_local_password_discriminant = h.ConsumerTests.test_local_password_discriminant


def coordinated():
    payload = json.load(sys.stdin)
    own, foreign = payload['own'], payload['foreign']
    h.settings.SSO_CENTRAL_TRUST = dict(CENTRAL, PUBLIC_KEYS={'synthetic-central': payload['public_key']})
    h.settings.SSO_LOCAL_TRUST = LOCAL
    h.settings.ADMIN_APPS_SSO = dict(h.settings.ADMIN_APPS_SSO, CLIENT_ID=own['client_id'], AUDIENCE=own['audience'])
    data = own['introspection']
    assert data['sub'] != foreign['introspection']['sub']
    assert data['tenant_id'] != foreign['introspection']['tenant_id']
    with patch.object(h.c.requests, 'post', return_value=NS(status_code=200, json=lambda: data)) as transport:
        verified = h.c.validate_proof(own['proof'])
        assert verified['sub'] == data['sub'] and verified['tenant_id'] == data['organization_id']
        user = NS(id=1, pk=1, username='adminapps:' + data['sub'], email=data['email'], is_active=True)
        profile = NS(id=2, organization_id=3, organization=NS(external_id=data['organization_id']), role=data['role'])
        refresh, access = h.c.session_pair(user, profile, own['proof'])
        assert LocalAccessToken(str(access))['sub'] == data['sub']
        assert access['role'] == 'viewer' and access['exp'] <= data['exp']
        calls = transport.call_count
        for token in (foreign['proof'], str(access)):
            try:
                h.c.validate_proof(token)
            except h.AuthenticationFailed:
                pass
            else:
                raise AssertionError('Cross product/family proof accepted')
        assert transport.call_count == calls
        try:
            h.c.validate_proof(own['proof'], organization_id='ffffffff-ffff-4fff-8fff-ffffffffffff')
        except h.AuthenticationFailed:
            pass
        else:
            raise AssertionError('Cross tenant proof accepted')
    assert not h.db.call_count and not any(x.call_count for x in h.guards)
    print('CROSS_PRODUCT_PASS ' + h.PRODUCT + ': own ALLOW, foreign/local DENY, tenant DENY, viewer preserved')


if __name__ == '__main__':
    if '--coordinated' in sys.argv:
        coordinated()
    else:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerCHTests))
        summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                   'database_attempts': h.db.call_count, 'network_attempts': sum(x.call_count for x in h.guards),
                   'scope': 'offline consumer; NOT HTTP E2E'}
        print(json.dumps(summary))
        sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
