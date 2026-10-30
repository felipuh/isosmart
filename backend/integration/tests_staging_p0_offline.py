"""Offline real client and startup guard regressions, no databases or network."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS

spec = importlib.util.spec_from_file_location('h', Path.cwd() / 'integration/tests_decision_a_offline.py')
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
from backend.security_policy import validate_startup_environment, local_fallback_allowed, UNSAFE_FLAGS
from integration.client import AdminAppsClient
PRODUCT = h.PRODUCT
FLAG = 'ALLOW_LOCAL_AUTH_FALLBACK' if PRODUCT == 'ISO_SMART' else 'ADMIN_APPS_ALLOW_LOCAL_FALLBACK'

def staging():
    env = dict.fromkeys(UNSAFE_FLAGS, 'false')
    env.update(DJANGO_ENV='staging', DJANGO_SETTINGS_MODULE='backend.settings', ADMIN_APPS_BASE_URL='https://staging-authority.invalid/api/integration', ADMIN_APPS_API_KEY='synthetic-qa-only', SECRET_KEY='synthetic-settings-only')
    return env

class PolicyTests(unittest.TestCase):
    def test_baseline_staging_guard_and_per_call_override_reproduce(self):
        source = (Path(__file__).parent / 'fixtures/fallback_before_p0.py.txt').read_text()
        nodes=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='_local_fallback_allowed']
        namespace={'settings':NS(ENVIRONMENT='staging', IS_PRODUCTION=False, ALLOW_LOCAL_AUTH_FALLBACK=True, ADMIN_APPS_INTEGRATION={'ALLOW_LOCAL_FALLBACK':True})}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'baseline','exec'),namespace)
        self.assertTrue(namespace['_local_fallback_allowed'](None))
        self.assertIn("else bool(allow_local_fallback) and not getattr(settings, 'IS_PRODUCTION', False)", source)

    def test_safe_staging_and_production_configuration(self):
        for envname in ('staging','production','stage','prod'):
            env=staging();env['DJANGO_ENV']=envname
            self.assertIn(validate_startup_environment(env,PRODUCT),('staging','production'))

    def test_every_unsafe_flag_and_malformed_boolean_rejected(self):
        for name in UNSAFE_FLAGS:
            for value in ('true','1','unexpected',''):
                env=staging();env[name]=value
                with self.subTest(flag=name,value=value),self.assertRaises(RuntimeError):validate_startup_environment(env,PRODUCT)
        env=staging();env.pop(FLAG)
        with self.assertRaises(RuntimeError):validate_startup_environment(env,PRODUCT)

    def test_environment_conflict_unknown_and_test_settings_rejected(self):
        for delta in ({'ENVIRONMENT':'development'},{'DJANGO_ENV':'stagin'},{'DJANGO_SETTINGS_MODULE':'backend.settings_test'},{'DJANGO_SETTINGS_MODULE':''}):
            with self.subTest(delta=delta),self.assertRaises(RuntimeError):validate_startup_environment(dict(staging(),**delta),PRODUCT)

    def test_authority_product_and_secrets_configuration(self):
        for delta in ({'ADMIN_APPS_BASE_URL':'http://staging.invalid'},{'ADMIN_APPS_BASE_URL':'https://user:SECRET@staging.invalid'},{'ADMIN_APPS_API_KEY':''}, {'ISO_SMART_PRODUCT_CODE':'MEDSUPPLIER'} if PRODUCT=='ISO_SMART' else {'ADMIN_APPS_REQUIRE_IDENTITY_SOURCE':'false'}):
            with self.assertRaises(RuntimeError) as caught:validate_startup_environment(dict(staging(),**delta),PRODUCT)
            self.assertNotIn('SECRET',str(caught.exception))

    def test_real_settings_load_safe_staging_without_session_auth(self):
        with patch.dict(os.environ,staging(),clear=True),patch('dotenv.load_dotenv'),patch.object(Path,'mkdir'):
            loaded=runpy.run_module('backend.settings')
        self.assertEqual(loaded['ENVIRONMENT'],'staging')
        self.assertFalse(loaded['ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS'])
        self.assertNotIn('rest_framework.authentication.SessionAuthentication',loaded['REST_FRAMEWORK']['DEFAULT_AUTHENTICATION_CLASSES'])
        self.assertTrue(all(d['ENGINE']=='django.db.backends.postgresql' for d in loaded['DATABASES'].values()))

    def test_real_test_settings_cannot_override_staging(self):
        with patch.dict(os.environ,dict(staging(),DJANGO_SETTINGS_MODULE='backend.settings_test'),clear=True),patch('dotenv.load_dotenv'),self.assertRaises(RuntimeError):
            runpy.run_module('backend.settings_test')

    def test_fail_closed_fallback_even_with_per_call_override(self):
        for env in ('staging','production','development','unexpected',None):
            with patch.object(h.settings,'ENVIRONMENT',env,create=True),patch.object(h.settings,'IS_PRODUCTION',False,create=True),patch.object(h.settings,'ALLOW_LOCAL_AUTH_FALLBACK',True,create=True),patch.object(h.settings,'ADMIN_APPS_INTEGRATION',{'ALLOW_LOCAL_FALLBACK':True}):
                client=AdminAppsClient()
                self.assertFalse(client._local_fallback_allowed())
                with patch.object(client,'_make_request',return_value={'error':'offline','code':'connection_error'}),patch.object(client,'_resolve_adminapps_org_id',return_value='qa'),patch.object(client,'_validate_product_access_local') as local,patch.object(client,'_get_organizations_local') as orgs:
                    for override in (None,True,False,'true'):
                        self.assertIs(client.validate_product_access('qa',PRODUCT,allow_local_fallback=override)['allowed'],False)
                    client.get_organizations()
                    local.assert_not_called();orgs.assert_not_called()

    def test_only_explicit_test_demo_fallback_allowed(self):
        for env in ('test','demo'):
            self.assertTrue(local_fallback_allowed(NS(ENVIRONMENT=env,IS_PRODUCTION=False),True))
            for value in (False,'true',1,None):
                self.assertFalse(local_fallback_allowed(NS(ENVIRONMENT=env,IS_PRODUCTION=False),value))
        self.assertFalse(local_fallback_allowed(NS(),True))

    def test_authority_allow_denial_and_uncached_entitlements(self):
        with patch.object(h.settings,'ENVIRONMENT','staging',create=True):
            client=AdminAppsClient();client.base_url='https://qa.invalid'
            with patch.object(client,'_resolve_adminapps_org_id',return_value='qa'),patch.object(client,'_validate_product_access_local') as local:
                for allowed in (True,False):
                    with patch.object(client,'_make_request',return_value={'allowed':allowed}):
                        self.assertIs(client.validate_product_access('qa',PRODUCT,allow_local_fallback=True)['allowed'],allowed)
                local.assert_not_called()
            with patch('integration.client.cache.get',return_value={'allowed':True}) as cache,patch('integration.client.requests.get',side_effect=RuntimeError('SYNTHETIC_SECRET')):
                result=client._make_request('GET','/organizations/qa/products/'+PRODUCT+'/validate/',use_cache=True,cache_key='entitlement')
                self.assertIn('error',result);self.assertNotIn('SYNTHETIC_SECRET',str(result));cache.assert_not_called()


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PolicyTests))
    summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),database_attempts=h.db.call_count,network_attempts=sum(x.call_count for x in h.guards))
    print(json.dumps(summary));sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
