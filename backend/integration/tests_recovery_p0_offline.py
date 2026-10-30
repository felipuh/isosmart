"""Real recovery views, synthetic ORM/mail; network and database denied by harness."""
import ast
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from contextlib import ExitStack
from unittest.mock import patch, MagicMock
from types import SimpleNamespace as NS

spec = importlib.util.spec_from_file_location('h', Path.cwd() / 'integration/tests_decision_a_offline.py')
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
v = h.views
source = (Path(__file__).parent / 'fixtures/recovery_before_p0.py.txt').read_text()
legacy = types.ModuleType('legacy_recovery')
legacy.__dict__.update(vars(v))
nodes = [n for n in ast.parse(source).body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in
         {'_request_ip_address', '_local_debug_recovery_allowed', 'PasswordResetRequestView'}]
exec(compile(ast.Module(body=nodes, type_ignores=[]), 'baseline_recovery', 'exec'), legacy.__dict__)

class RecoveryTests(unittest.TestCase):
    def invoke(self, module=v, *, meta=None, query=None, count=0, email_error=False):
        user = NS(email='qa@example.invalid')
        token = MagicMock()
        request = NS(data={'email': user.email}, META=meta or {}, query_params=query or {},
                     get_host=lambda: 'attacker.invalid')
        with ExitStack() as stack:
            orm = stack.enter_context(patch.object(module.PasswordResetToken.objects, 'filter'))
            orm.return_value.count.return_value = count
            users = stack.enter_context(patch.object(module.User.objects, 'filter'))
            users.return_value.first.return_value = user
            issue = stack.enter_context(patch.object(module.PasswordResetToken, 'issue_for_user', return_value=(token, 'SYNTHETIC_TOKEN')))
            stack.enter_context(patch.object(module, '_password_reset_frontend_url', return_value='https://qa.invalid/reset?token=SYNTHETIC_TOKEN'))
            stack.enter_context(patch.object(module, '_audit_password_reset'))
            stack.enter_context(patch.object(module, 'render_to_string', return_value='synthetic mail'))
            mail = stack.enter_context(patch.object(module, 'EmailMultiAlternatives'))
            if email_error:
                mail.return_value.send.side_effect = RuntimeError('SYNTHETIC_SECRET')
            response = module.PasswordResetRequestView().post(request)
        return response, issue, mail, token

    def test_baseline_spoof_reproduces_disclosure_and_throttle_bypass(self):
        with patch.object(h.settings, 'DEBUG', False), patch.object(h.settings, 'ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS', True, create=True):
            response, issue, mail, _ = self.invoke(legacy, count=99, meta={'REMOTE_ADDR':'192.0.2.1', 'HTTP_X_FORWARDED_FOR':'127.0.0.1', 'HTTP_X_DEBUG_RECOVERY':'1'})
        self.assertIn('SYNTHETIC_TOKEN', response.data['debug_reset_url'])
        issue.assert_called_once(); mail.assert_not_called()

    def test_headers_hosts_environments_never_disclose_or_skip_email(self):
        for env in ('development', 'test', 'staging', 'production', 'unexpected'):
            for debug in (True, False):
                for meta in ({}, {'REMOTE_ADDR':'192.0.2.1'}, {'REMOTE_ADDR':'::1'},
                             {'REMOTE_ADDR':'192.0.2.1', 'HTTP_X_FORWARDED_FOR':'127.0.0.1'},
                             {'REMOTE_ADDR':'192.0.2.1', 'HTTP_HOST':'localhost', 'SERVER_NAME':'localhost'}):
                    with self.subTest(env=env, debug=debug, meta=meta), patch.object(h.settings, 'ENVIRONMENT', env, create=True), patch.object(h.settings, 'DEBUG', debug), patch.object(h.settings, 'ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS', True, create=True):
                        response, issue, mail, _ = self.invoke(meta=dict(meta, HTTP_X_DEBUG_RECOVERY='1'), query={'debug_recovery':'1'})
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(set(response.data), {'detail'})
                        self.assertNotIn('SYNTHETIC_TOKEN', str(response.data))
                        issue.assert_called_once(); mail.return_value.send.assert_called_once()

    def test_throttle_denial_mints_no_recovery_token(self):
        for meta in ({}, {'HTTP_X_FORWARDED_FOR':'127.0.0.1', 'REMOTE_ADDR':'192.0.2.1', 'HTTP_X_DEBUG_RECOVERY':'1'}):
            response, issue, mail, _ = self.invoke(meta=meta, query={'debug_recovery':'1'}, count=99)
            issue.assert_not_called(); mail.assert_not_called()
            self.assertEqual(set(response.data), {'detail'})

    def test_untrusted_forwarded_address_ignored(self):
        self.assertEqual(v._request_ip_address(NS(META={'REMOTE_ADDR':'192.0.2.1', 'HTTP_X_FORWARDED_FOR':'127.0.0.1'})), '192.0.2.1')
        for value in ('invalid', '', None):
            self.assertIsNone(v._request_ip_address(NS(META={'REMOTE_ADDR':value})))

    def test_delivery_failure_invalidates_token_and_sanitizes_error(self):
        with self.assertLogs(v.logger, level='WARNING') as logs:
            response, _, _, token = self.invoke(email_error=True)
        token.mark_used.assert_called_once()
        self.assertNotIn('SYNTHETIC_SECRET', str(response.data) + str(logs.output))

    def test_recovery_not_an_alternate_login_when_authority_unavailable(self):
        from authentication.serializers import LoginSerializer
        with patch.object(h.c.requests, 'post', side_effect=RuntimeError('SYNTHETIC_SECRET')), patch.object(v.RefreshToken, 'for_user') as mint, patch.object(v, '_token_pair_for_profile') as pair:
            with self.assertRaises(h.APIException):
                LoginSerializer(data={'email':'qa@example.invalid','password':'recovered'}, context={'request':NS()}).is_valid(raise_exception=True)
            mint.assert_not_called(); pair.assert_not_called()

    def test_no_alternate_debug_endpoint(self):
        source = Path('authentication/views.py').read_text()
        self.assertNotIn('debug_reset_url', source)
        self.assertNotIn('debug_recovery', source)
        routes = Path('authentication/urls.py').read_text()
        self.assertNotIn('debug', routes.lower())

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RecoveryTests))
    summary = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), database_attempts=h.db.call_count, network_attempts=sum(x.call_count for x in h.guards))
    print(json.dumps(summary)); sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
