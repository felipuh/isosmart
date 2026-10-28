"""Offline consumer contracts: actual serializers, views and JWT authentication.
Run with the consumer venv; synthetic settings, dummy DB, network blocked.
"""
import ast
import copy
import importlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS
import unittest
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

ROOT=Path.cwd()
sys.path.insert(0,str(ROOT))
sys.dont_write_bytecode=True
guards=[patch(t,side_effect=AssertionError('Network forbidden')).start() for t in
        ('socket.socket.connect','socket.socket.connect_ex','socket.create_connection','socket.getaddrinfo')]
from django.conf import settings
settings.configure(SECRET_KEY='synthetic-only-decision-a-key-never-deploy',DEBUG=True,
    INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','authentication','core','integration'],
    AUTH_USER_MODEL='authentication.User',DATABASES={'default':{'ENGINE':'django.db.backends.dummy'}},
    LOGGING_CONFIG=None,USE_TZ=True,REST_FRAMEWORK={},AUTH_COOKIE_SAMESITE='Lax',
    ADMIN_APPS_INTEGRATION={'API_KEY':'synthetic-key','TIMEOUT':1},
    ADMIN_APPS_SSO={'BASE_URL':'https://central.invalid/api/integration','ISSUER':'https://central.invalid',
                    'CLIENT_ID':'synthetic-client','AUDIENCE':'synthetic-audience'})
from django.db.backends.base.base import BaseDatabaseWrapper
db=patch.object(BaseDatabaseWrapper,'connect',side_effect=AssertionError('Database forbidden')).start()
import django
django.setup()
from rest_framework.exceptions import APIException,AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIRequestFactory
from authentication.serializers import LoginSerializer
from authentication import views
from integration import central_auth as c
from integration.backends import AdminAppsAuthBackend
from integration.sso_auth import Smart3AISSOAuthentication
from django.core.exceptions import PermissionDenied

ORG='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
SUB='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
PRODUCT='MEDSUPPLIER' if ROOT.parent.name=='ISO_Smart_MedSupplier' else 'ISO_SMART'
def evidence():
    return {'active':True,'auth_contract':'decision-a-v1','amr':['pwd','otp'],'iss':'https://central.invalid',
            'aud':['synthetic-audience'],'client_id':'synthetic-client','sub':SUB,'organization_id':ORG,
            'email':'person@example.invalid','exp':int(time.time())+600,'role':'viewer',
            'products':[{'code':PRODUCT,'access_allowed':True}]}
def complete():
    return {'requires_2fa':False,'two_fa_bypassed':False,'tokens':{'access_token':'synthetic-central-proof'}}

class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.user=NS(id=1,pk=1,username='adminapps:'+SUB,email='person@example.invalid',is_active=True)
        self.profile=NS(id=2,organization_id=3,organization=NS(external_id=ORG),role='viewer')
        transport=patch.object(c.requests,'post')
        self.transport=transport.start()
        self.addCleanup(transport.stop)
        self.real_sync=c.sync_identity.__wrapped__
        sync=patch.object(c,'sync_identity',return_value=(self.user,self.profile))
        self.sync=sync.start()
        self.addCleanup(sync.stop)
        self.response(complete(),evidence())
    def response(self,*values):
        self.transport.side_effect=[NS(status_code=200,json=lambda v=v:copy.deepcopy(v)) for v in values]
    def serializer(self,**attrs):
        s=LoginSerializer(data=attrs,context={'request':NS()})
        s.is_valid(raise_exception=True)
        return s
    def test_complete_central_login(self):
        s=self.serializer(email=self.user.email,password=' local secret ')
        self.assertIs(s.validated_data['user'],self.user)
        self.assertEqual(self.transport.call_args_list[0].kwargs['json']['password'],' local secret ')
        self.sync.assert_called_once()
    def test_challenge_is_not_session(self):
        self.response({'requires_2fa':True,'challenge_token':'synthetic-challenge'})
        s=self.serializer(email=self.user.email,password='password')
        self.assertNotIn('user',s.validated_data)
        self.sync.assert_not_called()
        with ExitStack() as stack:
            stack.enter_context(patch.object(views,'LoginSerializer',return_value=s))
            mint=stack.enter_context(patch.object(views.RefreshToken,'for_user'))
            if PRODUCT=='ISO_SMART':stack.enter_context(patch.object(views.CookieJWTAuthentication,'enforce_csrf'))
            r=views.LoginView().post(NS(data={}))
            self.assertTrue(r.data['requires_2fa'])
            self.assertNotIn('access',r.data)
            mint.assert_not_called()
    def test_verify_totp_or_backup_through_central(self):
        for code in ('123456','backup-synthetic'):
            self.response(complete(),evidence())
            s=self.serializer(challenge_token='synthetic-challenge',otp_code=code)
            self.assertIn('user',s.validated_data)
            sent=self.transport.call_args_list[-2].kwargs['json']
            self.assertEqual(sent['otp_code'],code)
            self.assertEqual(sent['client_id'],'synthetic-client')
    def test_local_password_and_flags_never_rescue(self):
        for code in (401,403,503):
            self.transport.side_effect=None
            self.transport.return_value=NS(status_code=code,json=lambda:{'valid':True})
            with patch.object(settings,'ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS',True,create=True),\
                 patch('authentication.serializers.authenticate',return_value=self.user) as local:
                with self.assertRaises(APIException):
                    self.serializer(email=self.user.email,password='known-local-password')
                local.assert_not_called()
        self.sync.assert_not_called()
    def test_transport_and_json_errors_are_sanitized(self):
        for error in (TimeoutError('SECRET'),ValueError('SECRET')):
            self.transport.side_effect=error
            with self.assertRaises(c.AuthorityUnavailable) as caught:
                self.serializer(email=self.user.email,password='password')
            self.assertNotIn('SECRET',str(caught.exception))
        self.sync.assert_not_called()
    def test_malformed_and_contradictory_login(self):
        for data in ({'valid':True}, {'requires_2fa':'false'},
                     {'requires_2fa':True,'challenge_token':'challenge','tokens':{'access_token':'x'}},
                     dict(complete(),two_fa_bypassed=True), dict(complete(),requires_2fa=None)):
            self.response(data)
            with self.assertRaises(APIException):
                self.serializer(email=self.user.email,password='password')
        self.sync.assert_not_called()
    def test_invalid_receiver_identity_and_product(self):
        for key,value in [('active','true'),('auth_contract',None),('iss','foreign'),('client_id','foreign'),
                          ('aud',['other']),('aud','synthetic-audience'),('sub','bad'),('organization_id','bad'),
                          ('exp',int(time.time())-1),('exp',True),('amr',[]),('products',[]),('email','other@example.invalid')]:
            data=evidence();data[key]=value
            self.response(complete(),data)
            with self.subTest(key=key),self.assertRaises(APIException):
                self.serializer(email=self.user.email,password='password')
        self.sync.assert_not_called()
    def test_no_configuration_no_default_receiver(self):
        with patch.object(settings,'ADMIN_APPS_SSO',{}):
            with self.assertRaises(c.AuthorityUnavailable):
                self.serializer(email=self.user.email,password='password')
        self.transport.assert_not_called()
    def test_direct_backend_stops_local_chain(self):
        with self.assertRaises(PermissionDenied):
            AdminAppsAuthBackend().authenticate(NS(),email=self.user.email,password='local')
        self.assertIsNone(AdminAppsAuthBackend().get_user(1))
    def test_old_access_session_rejected(self):
        from rest_framework_simplejwt.authentication import JWTAuthentication
        with patch.object(JWTAuthentication,'get_user',return_value=self.user):
            with self.assertRaises(AuthenticationFailed):
                Smart3AISSOAuthentication().get_user({'user_id':1,'organization_id':3,'role':'viewer'})
        self.transport.assert_not_called()
    def test_old_refresh_never_issues_access(self):
        token=RefreshToken();token['user_id']=1
        if PRODUCT=='ISO_SMART':
            req=NS(COOKIES={'isosmart_refresh':str(token)})
            with patch.object(views.CookieJWTAuthentication,'enforce_csrf'),patch.object(views.RefreshTokenBlacklist.objects,'filter') as blacklist:
                blacklist.return_value.exists.return_value=False
                with self.assertRaises(AuthenticationFailed):views.RefreshTokenView().post(req)
        else:
            req=NS(data={'refresh':str(token)})
            with patch.object(views.RefreshTokenBlacklist.objects,'filter') as blacklist:
                blacklist.return_value.exists.return_value=False
                with self.assertRaises(AuthenticationFailed):views.RefreshTokenView().post(req)
        self.transport.assert_not_called()
    def test_cross_tenant_binding_rejected(self):
        self.response(evidence())
        profile=copy.deepcopy(self.profile);profile.organization.external_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc'
        with self.assertRaises(AuthenticationFailed):c.bind_session(RefreshToken(),'proof',profile,self.user)
    def test_refresh_bound_by_central_expiry(self):
        self.response(evidence())
        refresh=c.bind_session(RefreshToken(),'proof',self.profile,self.user)
        self.assertLessEqual(refresh['exp'],evidence()['exp'])
        self.assertEqual(refresh.access_token['auth_contract'],'decision-a-v1')
    def test_no_email_takeover_without_subject_binding(self):
        user=copy.deepcopy(self.user);user.username='legacy-local-person'
        with self.assertRaises(AuthenticationFailed):c.require_user_binding(user,SUB)
        with patch.object(settings,'ADMIN_APPS_USER_BINDINGS',{SUB:1},create=True):
            c.require_user_binding(user,SUB)
        with patch.object(settings,'ADMIN_APPS_USER_BINDINGS',{SUB:2},create=True):
            with self.assertRaises(AuthenticationFailed):c.require_user_binding(user,SUB)
    def test_current_session_live_revocation_and_role(self):
        from authentication.models import UserProfile
        token={'auth_contract':'decision-a-v1','user_id':1,'organization_id':3,'profile_id':2,
               'role':'viewer','central_proof':'proof','central_sub':SUB}
        with patch.object(UserProfile.objects,'select_related') as orm:
            orm.return_value.get.return_value=self.profile
            self.response(evidence())
            self.assertEqual(c.validate_session(token,self.user)['sub'],SUB)
            for key,value in [('active',False),('role','org_admin'),('organization_id','cccccccc-cccc-4ccc-8ccc-cccccccccccc')]:
                data=evidence();data[key]=value;self.response(data)
                with self.assertRaises(AuthenticationFailed):c.validate_session(token,self.user)
            data=evidence();self.response(data)
            bad=dict(token,central_sub='cccccccc-cccc-4ccc-8ccc-cccccccccccc')
            with self.assertRaises(AuthenticationFailed):c.validate_session(bad,self.user)
    def test_failed_binding_mints_no_local_token(self):
        self.response(dict(evidence(),active=False))
        with patch.object(RefreshToken,'for_user') as mint:
            with self.assertRaises(AuthenticationFailed):c.session_pair(self.user,self.profile,'proof')
            mint.assert_not_called()
    def test_projection_rejects_email_and_slug_collision(self):
        from authentication.models import User,UserProfile
        from core.models import Organization
        with patch.object(Organization.objects,'filter') as orgs,patch.object(Organization.objects,'create') as create,patch.object(User.objects,'filter') as users:
            orgs.return_value.first.return_value=None
            orgs.return_value.exists.return_value=True
            with self.assertRaises(AuthenticationFailed):self.real_sync(evidence())
            create.assert_not_called();users.assert_not_called()
            orgs.return_value.first.return_value=NS(is_active=True)
            local=copy.deepcopy(self.user);local.username='existing-email-account'
            users.return_value.first.side_effect=[None,local]
            with patch.object(UserProfile.objects,'update_or_create') as profiles:
                with self.assertRaises(AuthenticationFailed):self.real_sync(evidence())
                profiles.assert_not_called()
    def test_missing_profile_or_schema_fails_sanitized(self):
        from authentication.models import UserProfile
        token={'auth_contract':'decision-a-v1','profile_id':2,'user_id':1,'organization_id':3}
        with patch.object(UserProfile.objects,'select_related',side_effect=RuntimeError('private-schema')):
            with self.assertRaises(c.AuthorityUnavailable) as caught:c.validate_session(token,self.user)
            self.assertNotIn('private-schema',str(caught.exception))
        response=views.LoginView().handle_exception(RuntimeError('private-schema'))
        self.assertEqual(response.status_code,503)
        self.assertNotIn('private-schema',str(response.data))
    def test_owner_policy_cannot_be_bypassed(self):
        with patch.object(settings,'OWNER_ORGANIZATION_ONLY_ACCESS',True,create=True):
            with patch.object(settings,'OWNER_ORGANIZATION_EXTERNAL_ID','cccccccc-cccc-4ccc-8ccc-cccccccccccc',create=True):
                self.response(evidence())
                with self.assertRaises(AuthenticationFailed):c.validate_proof('proof')
            with patch.object(settings,'OWNER_ORGANIZATION_EXTERNAL_ID','',create=True):
                self.response(evidence())
                with self.assertRaises(c.AuthorityUnavailable):c.validate_proof('proof')
    def test_local_password_discriminant(self):
        import authentication.serializers as serializers_module
        baseline='--baseline' in sys.argv
        if baseline:
            source=ROOT.parent.parent/'adminapps/docs/security/REC-SSO-03A-IMPLEMENTATION/before'/ROOT.parent.name/'backend/authentication/serializers.py'
            spec=importlib.util.spec_from_file_location('authentication.baseline_serializers',source)
            serializers_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(serializers_module)
        candidate=MagicMock()
        candidate.is_locked.return_value=False
        candidate.check_password.return_value=True
        candidate.is_active=True
        candidate.get_temporary_password_expiry.return_value=None
        candidate.id=1;candidate.email=self.user.email
        req=NS(headers={},get_host=lambda:'localhost')
        queryset=MagicMock();queryset.exists.return_value=True;queryset.filter.return_value=queryset
        queryset.select_related.return_value=queryset;queryset.first.return_value=self.profile
        payload={'user':{'id':1,'email':self.user.email},'organization':{'id':ORG},'organizations':[{'id':ORG}],'role':'viewer'}
        self.transport.side_effect=None;self.transport.return_value=NS(status_code=403,json=lambda:{'valid':False})
        with patch.object(serializers_module.User.objects,'get',return_value=candidate),\
             patch.object(serializers_module.UserProfile.objects,'filter',return_value=queryset),\
             patch.object(serializers_module,'authenticate',return_value=None):
            if baseline and PRODUCT=='MEDSUPPLIER':
                with patch.object(serializers_module.LoginSerializer,'_build_local_adminapps_payload',return_value=payload):
                    with self.assertRaises(APIException):
                        s=serializers_module.LoginSerializer(data={'email':self.user.email,'password':'known-local-password'},context={'request':req})
                        s.is_valid(raise_exception=True)
            else:
                with self.assertRaises(APIException):
                    s=serializers_module.LoginSerializer(data={'email':self.user.email,'password':'known-local-password'},context={'request':req})
                    s.is_valid(raise_exception=True)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerTests) if '--baseline' not in sys.argv else unittest.TestSuite([ConsumerTests('test_local_password_discriminant')])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
                      'scope':'offline actual consumer code; NOT E2E','db_attempts':db.call_count}))
    sys.exit(not result.wasSuccessful() or db.call_count)
