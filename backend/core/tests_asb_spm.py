from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from authentication.models import UserProfile
from core.models import Organization
from ai_modules.asb.models import ScopeDefinition, ProcessScope
from ai_modules.spm.models import ProcessMap, Process


class ASBSPMTenantScopeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.auth_client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='tenant_scope_user',
            email='tenant_scope_user@isosmart.local',
            password='StrongPass@123',
        )

        self.org_a = Organization.objects.create(
            name='Tenant Org A',
            slug='tenant-org-a',
            email='tenant-a@isosmart.local',
        )
        self.org_b = Organization.objects.create(
            name='Tenant Org B',
            slug='tenant-org-b',
            email='tenant-b@isosmart.local',
        )

        UserProfile.objects.create(
            user=self.user,
            organization=self.org_a,
            role='org_admin',
            is_active=True,
        )

        self.scope_a = ScopeDefinition.objects.create(
            organization_id=self.org_a.id,
            title='Scope A',
            version='1.0',
            effective_date=date.today(),
            organizational_boundaries={'sites': ['A']},
            products_services=['Service A'],
            applicable_requirements={'clauses': ['4.3']},
            exclusions=[],
            scope_statement='Scope statement A',
            coverage_analysis={'coverage_percentage': 90},
            status='active',
            created_by='test',
        )
        self.scope_b = ScopeDefinition.objects.create(
            organization_id=self.org_b.id,
            title='Scope B',
            version='1.0',
            effective_date=date.today(),
            organizational_boundaries={'sites': ['B']},
            products_services=['Service B'],
            applicable_requirements={'clauses': ['4.3']},
            exclusions=[],
            scope_statement='Scope statement B',
            coverage_analysis={'coverage_percentage': 80},
            status='active',
            created_by='test',
        )

        ProcessScope.objects.create(
            scope_definition=self.scope_a,
            process_name='Process Scope A',
            process_code='PS-A',
            process_type='strategic',
            inputs=['in'],
            outputs=['out'],
            kpis=['kpi'],
        )

        self.map_a = ProcessMap.objects.create(
            organization_id=self.org_a.id,
            title='Process Map A',
            version='1.0',
            total_processes=1,
            strategic_count=1,
            operational_count=0,
            support_count=0,
            interaction_analysis={},
            critical_processes=[],
            recommendations=[],
            status='active',
            scope_definition=self.scope_a,
            created_by='test',
        )
        self.map_b = ProcessMap.objects.create(
            organization_id=self.org_b.id,
            title='Process Map B',
            version='1.0',
            total_processes=1,
            strategic_count=1,
            operational_count=0,
            support_count=0,
            interaction_analysis={},
            critical_processes=[],
            recommendations=[],
            status='active',
            scope_definition=self.scope_b,
            created_by='test',
        )

        Process.objects.create(
            process_map=self.map_a,
            code='A-01',
            name='Tenant A Process',
            process_type='strategic',
            owner='Owner A',
            inputs=[],
            outputs=[],
            resources=[],
            kpis=[],
            risks=[],
            controls=[],
        )

        self.auth_client.force_authenticate(user=self.user)

    def test_asb_spm_latest_endpoints_require_authentication(self):
        scope_resp = self.client.get('/api/scope/latest/', {'organization_id': self.org_a.id})
        process_resp = self.client.get('/api/processes/latest/', {'organization_id': self.org_a.id})

        self.assertEqual(scope_resp.status_code, 401)
        self.assertEqual(process_resp.status_code, 401)

    def test_asb_spm_latest_endpoints_require_and_enforce_org_scope(self):
        scope_missing = self.auth_client.get('/api/scope/latest/')
        process_missing = self.auth_client.get('/api/processes/latest/')
        self.assertEqual(scope_missing.status_code, 400)
        self.assertEqual(process_missing.status_code, 400)

        scope_forbidden = self.auth_client.get('/api/scope/latest/', {'organization_id': self.org_b.id})
        process_forbidden = self.auth_client.get('/api/processes/latest/', {'organization_id': self.org_b.id})
        self.assertEqual(scope_forbidden.status_code, 403)
        self.assertEqual(process_forbidden.status_code, 403)

        scope_ok = self.auth_client.get('/api/scope/latest/', {'organization_id': self.org_a.id})
        process_ok = self.auth_client.get('/api/processes/latest/', {'organization_id': self.org_a.id})
        self.assertEqual(scope_ok.status_code, 200)
        self.assertEqual(process_ok.status_code, 200)
        self.assertEqual(scope_ok.data['data']['organization_id'], self.org_a.id)
        self.assertEqual(process_ok.data['data']['organization_id'], self.org_a.id)

    def test_asb_spm_list_endpoints_return_only_active_org_data(self):
        scopes = self.auth_client.get('/api/scope/scopes/', {'organization_id': self.org_a.id})
        maps = self.auth_client.get('/api/processes/maps/', {'organization_id': self.org_a.id})
        processes = self.auth_client.get('/api/processes/processes/', {
            'organization_id': self.org_a.id,
            'map_id': self.map_b.id,
        })

        self.assertEqual(scopes.status_code, 200)
        self.assertEqual(maps.status_code, 200)
        self.assertEqual(processes.status_code, 200)

        self.assertEqual(scopes.data['count'], 1)
        self.assertEqual(maps.data['count'], 1)
        self.assertEqual(processes.data['count'], 0)

    def test_asb_child_scope_endpoints_are_tenant_isolated(self):
        own_scope_items = self.auth_client.get('/api/scope/processes/', {
            'organization_id': self.org_a.id,
            'scope_id': self.scope_a.id,
        })
        foreign_scope_items = self.auth_client.get('/api/scope/processes/', {
            'organization_id': self.org_a.id,
            'scope_id': self.scope_b.id,
        })

        self.assertEqual(own_scope_items.status_code, 200)
        self.assertEqual(foreign_scope_items.status_code, 200)
        self.assertEqual(own_scope_items.data['count'], 1)
        self.assertEqual(foreign_scope_items.data['count'], 0)
