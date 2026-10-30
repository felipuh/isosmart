"""Regression for reviewed SSO branch e212a5ed, reapplied without merging history."""
import importlib.util,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('h',Path.cwd()/'integration/tests_decision_a_offline.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
v=h.views

class MeTests(unittest.TestCase):
    def test_missing_central_envelope_denied_before_membership_query(self):
        with patch.object(v.UserProfile.objects,'filter') as profiles:
            with self.assertRaises(h.AuthenticationFailed):v.MeView().get(NS(user=NS(),auth=None))
            profiles.assert_not_called()
    def test_revoked_or_foreign_profile_denied(self):
        with patch.object(v.UserProfile.objects,'filter') as profiles:
            profiles.return_value.select_related.return_value.first.return_value=None
            with self.assertRaises(h.AuthenticationFailed):v.MeView().get(NS(user=NS(),auth={'profile_id':7,'organization_id':3},organization_id=999))
            self.assertEqual(profiles.call_args.kwargs['pk'],7)
            self.assertEqual(profiles.call_args.kwargs['organization_id'],3)
    def test_valid_central_profile_preserved_without_primary_fallback(self):
        user=NS();profile=NS(id=7)
        with patch.object(v.UserProfile.objects,'filter') as profiles,patch.object(v,'UserSerializer',return_value=NS(data={'id':1})),patch.object(v,'UserProfileSerializer',return_value=NS(data={'id':7})):
            profiles.return_value.select_related.return_value.first.return_value=profile
            profiles.return_value.select_related.return_value.__iter__.return_value=iter([])
            response=v.MeView().get(NS(user=user,auth={'profile_id':7,'organization_id':3},organization_id=999))
            self.assertEqual(response.data['profile'],{'id':7})
            self.assertEqual(profiles.call_args_list[0].kwargs,dict(pk=7,user=user,organization_id=3,is_active=True))
            profiles.return_value.order_by.assert_not_called()

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MeTests))
    summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),database_attempts=h.db.call_count,network_attempts=sum(x.call_count for x in h.guards))
    print(json.dumps(summary));sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
