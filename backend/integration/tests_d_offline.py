"""Run from backend with its venv. Real DRF/model code; dummy ORM and no I/O."""
import ast,copy,importlib,inspect,json,sys,unittest,uuid
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch,MagicMock
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from django.conf import settings
apps=next(ast.literal_eval(n.value) for n in ast.parse((ROOT/'backend/settings.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INSTALLED_APPS' for t in n.targets))
guards=[patch(t,side_effect=AssertionError('Network forbidden')).start() for t in ('socket.socket.connect','socket.socket.connect_ex','socket.create_connection','socket.getaddrinfo')]
from django.db.backends.base.base import BaseDatabaseWrapper
db=patch.object(BaseDatabaseWrapper,'connect',side_effect=AssertionError('Database forbidden')).start()
settings.configure(SECRET_KEY='offline-d-tests-key-never-deploy',INSTALLED_APPS=apps,AUTH_USER_MODEL='authentication.User',DATABASES={'default':{'ENGINE':'django.db.backends.dummy'}},LOGGING_CONFIG=None,USE_TZ=True,REST_FRAMEWORK={},ADMIN_APPS_INTEGRATION={},ROOT_URLCONF='backend.urls',MEDIA_URL='/media/',STATIC_URL='/static/',ALLOWED_HOSTS=['testserver'],DEBUG=False,BASE_DIR=ROOT)
import django;django.setup()
from rest_framework.test import APIRequestFactory,force_authenticate
from rest_framework.exceptions import APIException,PermissionDenied,NotFound
from integration import authorization as a
from integration.authorization_contract import CONTRACT,ACTIONS,CATALOG,role_scopes
from core.organization_scoping import OrganizationScopedViewSetMixin
from authentication.models import User
from resources.models import Resource
from resources.views import ResourceViewSet
from django.urls import get_resolver,URLResolver
PRODUCT=a.central_auth.PRODUCT
TENANT='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';SUB='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
# Frozen acceptance fixture: do NOT derive expected ALLOW from action_enabled.
# Any widening of the runtime policy must break these tests until reviewed.
EXPECTED_READ_ACTIONS = {
    'resources.resource': {'by_type'},
    'resources.infrastructure': {'maintenance_due'},
    'resources.competence': {'gaps', 'by_user'},
    'resources.training': {'upcoming'},
    'resources.communication': {'pending'},
    'core.document': {'stats'},
    'performance.measurement': {'dashboard_stats'},
}
def expected_read(resource, action):
    return (not resource.startswith('integration.')
            and (action in {'list', 'retrieve'}
                 or action in EXPECTED_READ_ACTIONS.get(resource, ())))


def evidence(resource='resources.resource',operation='read',role='viewer'):
    data=dict(active=True,sub=SUB,tenant_id=TENANT,client_id='test-client',product=PRODUCT,
              role=role,sid='dddddddd-dddd-4ddd-8ddd-dddddddddddd',sg=1,av=1)
    data['authorization']=dict(data,contract=CONTRACT,state='active',principal_type='user',scopes=[f'{PRODUCT}:{resource}:{operation}'])
    return data


class OfflineQuery:
    """Bounded in-memory substitute for ORM selection, never SQL evidence."""
    model=Resource
    ordered=True
    def __init__(self,rows):self.rows=rows
    def all(self):return OfflineQuery(self.rows[:])
    def none(self):return OfflineQuery([])
    def filter(self,**kw):
        return OfflineQuery([r for r in self.rows if all(str(getattr(r,k))==str(v) for k,v in kw.items())])
    def get(self,**kw):
        rows=self.filter(**kw).rows
        if len(rows)!=1:raise Resource.DoesNotExist()
        return rows[0]
    def __iter__(self):return iter(self.rows)
    def __len__(self):return len(self.rows)


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.user=User(id=5,username='adminapps:'+SUB,email='test@example.invalid',is_active=True)
        self.token={'organization_id':3,'role':'viewer'}
        self.data=evidence();p=patch.object(a.central_auth,'validate_session',side_effect=lambda *args:copy.deepcopy(self.data));self.live=p.start();self.addCleanup(p.stop)
        self.factory=APIRequestFactory()
        if PRODUCT == 'MEDSUPPLIER':
            from medsupplier.permissions import MedSupplierContext
            p=patch('medsupplier.views.resolve_medsupplier_context',return_value=MedSupplierContext(3,'supplier','supplier_admin',()))
            p.start();self.addCleanup(p.stop)
    def request(self,method='get',body=None,path='/api/resources/resources/'):
        raw=getattr(self.factory,method)(path,body or {},format='json');force_authenticate(raw,user=self.user,token=self.token);return raw
    def invoke(self,method='get',body=None,pk=None,rows=None,path='/api/resources/resources/'):
        action={'get':'retrieve' if pk else 'list','post':'create','patch':'partial_update','delete':'destroy'}[method]
        qs=OfflineQuery(rows or [Resource(id=7,organization_id=3,name='own',resource_type='material'),Resource(id=8,organization_id=4,name='foreign',resource_type='material')])
        return ResourceViewSet.as_view({method:action},queryset=qs,filter_backends=[],pagination_class=None)(self.request(method,body,path),**({'pk':pk} if pk else {}))
    def test_real_list_reaches_policy_and_filters_foreign_tenant(self):
        response=self.invoke();self.assertEqual(response.status_code,200);self.assertEqual([r['id'] for r in response.data],[7]);self.live.assert_called_once()
    def test_real_detail_foreign_id_is_404(self):
        response=self.invoke(pk=8);self.assertEqual(response.status_code,404);self.assertNotIn('foreign',str(response.data))
    def test_real_detail_own_id_allows_without_other_permissions(self):
        response=self.invoke(pk=7);self.assertEqual(response.status_code,200);self.assertEqual(response.data['id'],7);self.assertEqual(self.data['authorization']['scopes'],[f'{PRODUCT}:resources.resource:read'])
    def test_read_cannot_create_patch_delete_before_save(self):
        with patch.object(Resource,'save') as save,patch.object(Resource,'delete') as delete:
            for method in ('post','patch','delete'):
                response=self.invoke(method,{'name':'changed'},pk=7 if method!='post' else None);self.assertEqual(response.status_code,403)
            save.assert_not_called();delete.assert_not_called()
    def test_scopes_empty_unknown_foreign_wildcard_duplicates(self):
        other='MEDSUPPLIER' if PRODUCT=='ISO_SMART' else 'ISO_SMART'
        for scopes in ([],['unknown'],[f'{other}:resources.resource:read'],['*'],[f'{PRODUCT}:resources.resource:read']*2,None,'read'):
            self.data=evidence();self.data['authorization']['scopes']=scopes
            self.assertEqual(self.invoke().status_code,403)
    def test_binding_state_principal_role_injection(self):
        for key,value in [('contract','v0'),('state','unknown'),('principal_type','service'),('tenant_id','other'),('sub','other'),('client_id','other'),('product','OTHER'),('role','org_admin'),('sid','old'),('sg',0),('av',0)]:
            self.data=evidence();self.data['authorization'][key]=value;self.assertEqual(self.invoke().status_code,403,key)
        self.data=evidence();self.data['authorization']['scopes']=[f'{PRODUCT}:resources.resource:update'];self.assertEqual(self.invoke().status_code,403)
    def test_absent_grants_and_inactive_authority(self):
        for field,value in [('authorization',None),('active',False)]:
            self.data=evidence();self.data[field]=value;self.assertEqual(self.invoke().status_code,403)
    def test_permission_resolution_error_denies_without_effects(self):
        self.live.side_effect=a.central_auth.AuthorityUnavailable()
        self.assertEqual(self.invoke().status_code,503)
    def test_query_and_body_tenant_and_contract_fields_rejected(self):
        for query in ('organization_id=4','organization=4','role=org_admin','scopes=all','tenant_id=other'):
            self.assertEqual(self.invoke(path='/api/resources/resources/?'+query).status_code,403)
        self.data=evidence(operation='create',role='user')
        for body in ({'organization_id':4},{'organization':4},{'status':'approved'},{'scopes':['*']},{'uploaded_by':9},{'metadata':{'role':'admin'}},{'documentation':'foreign-file'}):
            self.assertEqual(self.invoke('post',body).status_code,403)
    def test_real_create_authorized_resource_binds_tenant_before_save(self):
        self.data=evidence(operation='create',role='user')
        captured=[]
        def create(**kw):captured.append(kw);return Resource(id=9,**kw)
        with patch.object(Resource.objects,'create',side_effect=create), patch('django.db.models.query.QuerySet.exists',return_value=False):
            response=self.invoke('post',{'name':'new','resource_type':'material','code':'D-1','organization_name':'test'})
        self.assertEqual(response.status_code,201,response.data);self.assertEqual(captured[0]['organization_id'],3)
    def test_real_partial_update_authorized_own_object(self):
        self.data=evidence(operation='update',role='user')
        with patch.object(Resource,'save') as save:
            response=self.invoke('patch',{'name':'changed'},pk=7)
        self.assertEqual(response.status_code,200,response.data);save.assert_called_once()
    def test_object_checks_fail_closed_for_missing_and_foreign_nested_tenant(self):
        view=NS(organization_lookup_field='parent__organization_id');request=NS(organization_id=3)
        for obj in (NS(),NS(parent=NS(organization_id=4))):
            with self.assertRaises(NotFound):a.authorize_object(request,view,obj)
        if PRODUCT=='ISO_SMART':a.authorize_object(request,view,NS(parent=NS(organization_id=3)))
    def test_nested_queryset_uses_authenticated_tenant_not_query(self):
        class Base:
            def get_queryset(self):return self.query
        class Nested(OrganizationScopedViewSetMixin,Base):organization_lookup_field='parent__organization_id'
        view=Nested();view.request=NS(organization_id=3,query_params={});view.query=MagicMock();view.get_queryset();view.query.filter.assert_called_once_with(parent__organization_id=3)
        view.request=NS(query_params={'organization_id':'3'})
        with self.assertRaises(PermissionDenied):view.get_organization_id()
    def test_sensitive_related_user_and_reparenting_denied(self):
        from authentication.models import UserProfile
        class Base:
            def validate(self,attrs):return attrs
        class Serializer(a.AuthorizedSerializerMixin,Base):pass
        serializer=Serializer();serializer.instance=None;serializer.context={'request':NS(organization_id=3,functional_authorization=True),'view':ResourceViewSet()}
        with patch.object(UserProfile.objects,'filter') as q:
            q.return_value.exists.return_value=False
            with self.assertRaises(PermissionDenied):serializer.validate({'responsible':self.user})
            q.return_value.exists.return_value=True
            self.assertEqual(serializer.validate({'responsible':self.user}),{'responsible':self.user})
        serializer.instance=NS(responsible=NS(pk=6))
        with self.assertRaises(PermissionDenied):serializer.validate({'responsible':self.user})


# Every mounted mixin route gets a real permission-layer test. We distinguish
# denial-only routes from read ALLOW + absent-scope DENY; aliases share handler.
coverage=[]
def walk(patterns,prefix=''):
    for p in patterns:
        route=prefix+str(p.pattern)
        if isinstance(p,URLResolver):yield from walk(p.url_patterns,route)
        else:yield route,p.callback


def endpoint_test(cls,method,action):
    def test(self):
        resource=cls.queryset.model._meta.label_lower;operation=ACTIONS.get(PRODUCT,{}).get(resource,{}).get(action)
        view=cls();view.action_map={method:action};view.kwargs={};view.args=();view.format_kwarg=None
        raw=self.request(method if method!='head' else 'get');raw.method=method.upper()
        request=view.initialize_request(raw);view.request=request
        self.data=evidence(resource,'read')
        if expected_read(resource,action):
            view.check_permissions(request)
            # Exercise the object's actual permission chain for each handler.
            obj=NS(organization_id=3,account=NS(id=11,organization_id=3),visibility='customer_shared')
            current=obj
            parts=view.organization_lookup_field.split('__')
            for part in parts[:-1]:
                child=NS();setattr(current,part,child);current=child
            setattr(current,parts[-1],3)
            view.check_object_permissions(request,obj)
            setattr(current,parts[-1],4)
            with self.assertRaises(NotFound):view.check_object_permissions(request,obj)
            self.data['authorization']['scopes']=[]
            with self.assertRaises(PermissionDenied):view.check_permissions(request)
        else:
            with self.assertRaises(APIException):view.check_permissions(request)
            # Also dispatch through DRF: a denied operation must never invoke
            # the handler that can persist, export, enqueue or emit an event.
            with patch.object(cls,action,side_effect=AssertionError('Denied handler reached')) as handler:
                response=cls.as_view({method:action})(self.request(method if method!='head' else 'get'))
            self.assertIn(response.status_code,(401,403))
            handler.assert_not_called()
    return test
seen={}
for route,callback in walk(get_resolver().url_patterns):
    cls=getattr(callback,'cls',None)
    if not cls or not issubclass(cls,OrganizationScopedViewSetMixin):continue
    for method,action in getattr(callback,'actions',{}).items():
        key=(cls.__module__,cls.__name__,method,action)
        name='test_endpoint_'+str(len(seen)) if key not in seen else seen[key]
        if key not in seen:
            seen[key]=name;setattr(AuthorizationTests,name,endpoint_test(cls,method,action))
        resource=cls.queryset.model._meta.label_lower;op=ACTIONS.get(PRODUCT,{}).get(resource,{}).get(action)
        coverage.append(dict(route=route,method=method.upper(),handler=cls.__module__+'.'+cls.__name__,action=action,resource=resource,scope=f'{PRODUCT}:{resource}:{op}',test=name,kind='READ_PERMISSION_ALLOW_DENY' if expected_read(resource,action) else 'DENIAL_ONLY'))

if PRODUCT=='MEDSUPPLIER':
    from medsupplier import permissions as mp,models as mm
    class MedSupplierTests(unittest.TestCase):
        def user(self):return NS(is_authenticated=True,is_superuser=True)
        def test_no_superuser_or_profile_fallback(self):
            with patch.object(mm.MedSupplierUserScope.objects,'filter') as q:
                q.return_value.values.return_value=[]
                with self.assertRaises(PermissionDenied):mp.resolve_medsupplier_context(self.user(),3)
        def test_unknown_roles_and_mixed_assignments_denied(self):
            for scopes in ([dict(side='supplier',role='unknown',account_id=None)], [dict(side='supplier',role='supplier_admin',account_id=None),dict(side='customer',role='customer_viewer',account_id=1)], [dict(side='customer',role='customer_admin',account_id=1),dict(side='customer',role='customer_viewer',account_id=2)]):
                with patch.object(mm.MedSupplierUserScope.objects,'filter') as q:
                    q.return_value.values.return_value=scopes
                    with self.assertRaises(PermissionDenied):mp.resolve_medsupplier_context(self.user(),3)
        def test_customer_relationship_does_not_grant_other_account_or_private_data(self):
            context=mp.MedSupplierContext(3,'customer','customer_viewer',(11,))
            own=mm.SupplierAccount(id=11,organization_id=3,visibility='customer_shared')
            self.assertTrue(mp.assert_object_allowed(own,context))
            for obj in (mm.SupplierAccount(id=12,organization_id=3),NS(organization_id=4,account=own),NS(organization_id=3,account=own,visibility='supplier_private')):
                with self.assertRaises(PermissionDenied):mp.assert_object_allowed(obj,context)
            with self.assertRaises(PermissionDenied):mp.assert_can_mutate(context)
        def test_supplier_account_restriction_is_not_organization_wide(self):
            context=mp.MedSupplierContext(3,'supplier','supplier_sales',(11,))
            self.assertFalse(context.has_account_scope(12))
            with self.assertRaises(PermissionDenied):mp.assert_object_allowed(NS(organization_id=3,account=NS(id=12,organization_id=3)),context)
        def test_function_endpoints_require_grant_before_business_queries(self):
            from medsupplier import views
            raw=APIRequestFactory().get('/api/medsupplier/dashboard/')
            force_authenticate(raw,user=User(id=5),token={'organization_id':3})
            for name in ('effective_permissions','dashboard_summary','private_cockpit','integration_status'):
                with patch.object(a.central_auth,'validate_session',return_value=dict(evidence(),authorization=None)):
                    response=getattr(views,name)(raw)
                self.assertEqual(response.status_code,403,name)
        def test_aggregate_requires_all_scopes(self):
            data=evidence('medsupplier.supplieraccount')
            request=NS(user=User(id=5),auth={'organization_id':3},query_params={},data={})
            with patch.object(a.central_auth,'validate_session',return_value=data):
                with self.assertRaises(PermissionDenied):a.authorize_resources(request,('medsupplier.supplieraccount','medsupplier.supplierquote'))
                data['authorization']['scopes'].append(PRODUCT+':medsupplier.supplierquote:read')
                self.assertEqual(len(a.authorize_resources(request,('medsupplier.supplieraccount','medsupplier.supplierquote'))['scopes']),2)
        def test_supplier_foreign_tenant_denied(self):
            context=mp.MedSupplierContext(3,'supplier','supplier_admin',())
            with self.assertRaises(PermissionDenied):mp.assert_object_allowed(NS(organization_id=4),context)
        def test_customer_queryset_scopes_account_and_visibility(self):
            context=mp.MedSupplierContext(3,'customer','customer_viewer',(11,))
            q=MagicMock();q.model=mm.SupplierDocument;q.filter.return_value=q
            mp.filter_queryset_for_context(q,context)
            self.assertEqual(q.filter.call_args_list[0].kwargs,{'organization_id':3})
            self.assertEqual(q.filter.call_args_list[1].kwargs,{'account_id__in':(11,)})
            self.assertEqual(q.filter.call_args_list[2].kwargs,{'visibility__in':mp.CUSTOMER_VISIBLE_VISIBILITIES})

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(AuthorizationTests)
    if PRODUCT=='MEDSUPPLIER':suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(MedSupplierTests))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(coverage,indent=2))
    print(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),database_attempts=db.call_count,network_attempts=sum(g.call_count for g in guards))))
    sys.exit(bool(result.failures or result.errors or db.call_count or any(g.call_count for g in guards)))
