"""D session successors: real RSA A/C/H/B validation plus functional gate."""
import importlib.util,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
spec=importlib.util.spec_from_file_location('b',Path.cwd()/'integration/tests_b_offline.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
h=b.h;ch=b.ch
from integration import authorization as a
from integration.authorization_contract import CONTRACT

class SessionDTests(b.ConsumerBTests):
    def test_signed_live_session_reaches_granular_permission(self):
        refresh,access=self.pair();self.profiles();self.user.is_authenticated=True
        data=ch.introspection(self.data)
        data['authorization']={k:data[k] for k in ('sub','tenant_id','client_id','product','role','sid','sg','av')}
        data['authorization'].update(contract=CONTRACT,state='active',principal_type='user',scopes=[h.PRODUCT+':resources.resource:read'])
        self.response(data)
        request=NS(user=self.user,auth=access,query_params={},data={})
        view=NS(queryset=NS(model=NS(_meta=NS(label_lower='resources.resource'))),action='retrieve')
        result=a.authorize_request(request,view)
        self.assertEqual(result['scopes'],[h.PRODUCT+':resources.resource:read'])
        self.assertEqual(request.organization_id,self.profile.organization_id)
        # Same valid signature/session cannot authorize a write or absent grant.
        self.response(data);view.action='partial_update'
        with self.assertRaises(a.PermissionDenied):a.authorize_request(request,view)
        view.action='retrieve';data['authorization']['scopes']=[];self.response(data)
        with self.assertRaises(a.PermissionDenied):a.authorize_request(request,view)
        data['active']=False;self.response(data)
        with self.assertRaises(h.AuthenticationFailed):a.authorize_request(request,view)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SessionDTests))
    summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),database_attempts=h.db.call_count,network_attempts=sum(g.call_count for g in h.guards))
    print(json.dumps(summary));sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
