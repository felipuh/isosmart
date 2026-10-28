"""Decision B consumer successors; historical A/CH files remain unchanged."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS

spec = importlib.util.spec_from_file_location('ch', Path.cwd() / 'integration/tests_ch_offline.py')
ch = importlib.util.module_from_spec(spec); spec.loader.exec_module(ch)
h = ch.h
original_claims = ch.claims


def claims(**changes):
    result = original_claims(lifecycle='rec-sso-03b-v1', sid='dddddddd-dddd-4ddd-8ddd-dddddddddddd',
                             sg=1, av=1, auth_time=int(time.time()))
    result.update(changes)
    return result


ch.claims = claims


class ConsumerBTests(ch.ConsumerCHTests):
    def profiles(self):
        p = patch.object(ch.UserProfile.objects, 'select_related'); query = p.start(); self.addCleanup(p.stop)
        query.return_value.get.return_value = self.profile
        p = patch.object(ch.User.objects, 'get', return_value=self.user); p.start(); self.addCleanup(p.stop)

    def test_refresh_live_authority_and_revocation(self):
        refresh, _ = self.pair(); self.profiles()
        new = dict(self.data, sg=2, jti='new-synthetic-jti')
        self.response(ch.introspection(self.data), {'tokens': {'access_token': ch.proof(new)}}, ch.introspection(new))
        req = NS(COOKIES={'isosmart_refresh': str(refresh)}, data={'refresh': str(refresh)})
        csrf = patch.object(h.views.CookieJWTAuthentication, 'enforce_csrf') if h.PRODUCT == 'ISO_SMART' else patch.object(h.views, 'logger')
        with csrf:
            response = h.views.RefreshTokenView().post(req)
            self.assertEqual(response.status_code, 200)
            token = response.cookies['isosmart_refresh'].value if h.PRODUCT == 'ISO_SMART' else response.data['refresh']
            rotated = ch.LocalRefreshToken(token)
            self.assertEqual(rotated['sg'], 2)
            self.assertEqual(rotated['exp'], refresh['exp'])
            self.assertNotEqual(rotated['jti'], refresh['jti'])
            self.assertTrue(any(c.args[0].endswith('/sso/rotate/') for c in self.transport.call_args_list))
            self.response(dict(ch.introspection(self.data), active=False))
            with self.assertRaises(h.AuthenticationFailed): h.views.RefreshTokenView().post(req)

    def test_central_generation_binding_and_legacy_rejection(self):
        refresh, _ = self.pair(); self.profiles()
        for key, value in [('sid', 'other'), ('sg', 2), ('av', 2), ('auth_time', 1), ('lifecycle', 'old')]:
            self.response(ch.introspection(self.data))
            with self.assertRaises(h.AuthenticationFailed):
                h.c.validate_session(dict(refresh.payload, **{key: value}), self.user)
        for key in ('sid', 'sg', 'av', 'auth_time', 'lifecycle'):
            data = dict(self.data); data.pop(key)
            with self.assertRaises(h.AuthenticationFailed): h.c.validate_proof(ch.proof(data))

    def test_logout_calls_central_for_authenticated_session(self):
        _, access = self.pair()
        self.response({'revoked': True})
        response = h.views.LogoutView().post(NS(auth=access, user=self.user, data={'refresh': 'foreign'}))
        self.assertEqual(response.status_code, 200)
        call = self.transport.call_args
        self.assertTrue(call.args[0].endswith('/sso/logout/'))
        self.assertEqual(call.kwargs['json']['token'], access['central_proof'])
        if h.PRODUCT == 'ISO_SMART': self.assertEqual(response.cookies['isosmart_access']['max-age'], 0)

    def test_logout_outage_is_not_reported_success(self):
        _, access = self.pair()
        self.transport.side_effect = RuntimeError('private upstream failure')
        with self.assertRaises(h.c.AuthorityUnavailable) as caught: h.c.logout_session(access)
        self.assertNotIn('private', str(caught.exception))

    def test_rotation_cannot_change_authority_or_extend_expiry(self):
        self.profiles()
        for key, value in [('sid', 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee'), ('av', 2),
                           ('sg', 1), ('auth_time', self.data['auth_time'] - 1), ('exp', self.data['exp'] - 1)]:
            refresh, _ = self.pair(); new = dict(self.data, sg=2, jti='new'); new[key] = value
            self.response(ch.introspection(self.data), {'tokens': {'access_token': ch.proof(new)}}, ch.introspection(new))
            with self.assertRaises(h.AuthenticationFailed): h.c.rotate_session(refresh)

    def test_rotation_outage_mints_no_tokens(self):
        refresh, _ = self.pair(); self.profiles()
        self.response(ch.introspection(self.data))
        with self.assertRaises(h.c.AuthorityUnavailable): h.c.rotate_session(refresh)
        self.assertEqual(refresh['sg'], 1)

    def test_denial_does_not_allow_reuse_cached_authority(self):
        refresh, _ = self.pair(); self.profiles()
        self.response(ch.introspection(self.data)); self.assertEqual(h.c.validate_session(refresh)['sg'], 1)
        self.response(dict(ch.introspection(self.data), active=False))
        with self.assertRaises(h.AuthenticationFailed): h.c.validate_session(refresh)
        self.transport.side_effect = RuntimeError('offline')
        with self.assertRaises(h.c.AuthorityUnavailable): h.c.validate_session(refresh)

    def test_cookie_real_signing_size_and_expiry(self):
        if h.PRODUCT != 'ISO_SMART':
            refresh, access = self.pair()
            self.assertEqual(ch.LocalAccessToken(str(access))['product'], 'MEDSUPPLIER')
            return
        from authentication.cookies import set_auth_cookies
        from rest_framework.response import Response
        refresh, access = self.pair()
        response = set_auth_cookies(Response({}), access=access, refresh=refresh)
        measured = {k: len(v.OutputString().encode()) for k, v in response.cookies.items()}
        self.assertLessEqual(max(measured.values()), 4096)
        self.assertLessEqual(response.cookies['isosmart_refresh']['max-age'], 300)
        # Real RSA signing, maximum representative email/client/audience/issuer.
        big = dict(self.data, email='a'*240+'@example.test', client_id='c'*100,
                   iss='https://central.invalid/'+'p'*476, aud=['a'*255])
        from integration.local_tokens import bind_claims
        central_cfg = dict(ch.CENTRAL, ISSUER=big['iss'])
        config = dict(h.settings.ADMIN_APPS_SSO, ISSUER=big['iss'], CLIENT_ID=big['client_id'], AUDIENCE=big['aud'][0])
        with patch.object(h.settings, 'SSO_CENTRAL_TRUST', central_cfg), patch.object(h.settings, 'ADMIN_APPS_SSO', config):
            self.user.email = big['email']; self.response(ch.introspection(big))
            large_refresh, large_access = h.c.session_pair(self.user, self.profile, ch.proof(big))
            lengths = {'access': len(str(large_access)), 'refresh': len(str(large_refresh))}
            with self.assertRaises(h.APIException): set_auth_cookies(Response({}), access=large_access, refresh=large_refresh)
        print('COOKIE_MEASUREMENTS ' + json.dumps({'typical_set_cookie_bytes': measured, 'representative_max_signed_value_bytes': lengths,
              'max_case': 'DENY_OVERSIZE', 'browser_e2e': 'NOT_EVIDENCED'}))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerBTests))
    summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'database_attempts': h.db.call_count, 'network_attempts': sum(x.call_count for x in h.guards),
               'scope': 'offline real JWT/views, simulated central transport; NOT HTTP E2E'}
    print(json.dumps(summary))
    sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
