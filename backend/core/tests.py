from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import UserProfile
from core.models import (
    AuditLog,
    ContextAnalysis,
    OnboardingInsightSnapshot,
    Organization,
    OrganizationSettings,
    ProcessMap,
    QualityObjective,
    RiskMatrix,
    StakeholderProfile,
)


class LegacyScopedEndpointsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.auth_client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='scope_user',
            email='scope_user@isosmart.local',
            password='StrongPass@123',
        )

        self.org_a = Organization.objects.create(
            name='Organization A',
            slug='organization-a',
            email='a@isosmart.local',
        )
        self.org_b = Organization.objects.create(
            name='Organization B',
            slug='organization-b',
            email='b@isosmart.local',
        )

        UserProfile.objects.create(
            user=self.user,
            organization=self.org_a,
            role='org_admin',
            is_active=True,
        )

        # Seed data so context latest can return 200 in authorized tests.
        self.context_a = ContextAnalysis.objects.create(
            status='completed',
            total_documents_processed=0,
            created_by=self.user,
            organization=self.org_a,
        )
        ContextAnalysis.objects.create(
            status='completed',
            total_documents_processed=0,
            created_by=self.user,
            organization=self.org_b,
        )

        self.risk_a = RiskMatrix.objects.create(
            organization=self.org_a,
            source_module='MANUAL',
            risk_description='Risk A',
            risk_category='operational',
            probability='alta',
            impact='alto',
            risk_level='alto',
            mitigation_actions='Mitigate A',
            responsible='Owner A',
            iso_clause='6.1',
            status='identified',
        )
        self.risk_b = RiskMatrix.objects.create(
            organization=self.org_b,
            source_module='MANUAL',
            risk_description='Risk B',
            risk_category='financial',
            probability='media',
            impact='medio',
            risk_level='medio',
            mitigation_actions='Mitigate B',
            responsible='Owner B',
            iso_clause='6.1',
            status='under_analysis',
        )

        QualityObjective.objects.create(
            organization=self.org_a,
            source_module='MANUAL',
            objective_description='Objective A',
            indicator_name='Indicator A',
            measurement_unit='%',
            baseline_value=0,
            target_value=100,
            current_value=20,
            measurement_frequency='monthly',
            responsible='Owner A',
            deadline=date.today() + timedelta(days=30),
            status='active',
        )
        QualityObjective.objects.create(
            organization=self.org_b,
            source_module='MANUAL',
            objective_description='Objective B',
            indicator_name='Indicator B',
            measurement_unit='%',
            baseline_value=0,
            target_value=100,
            current_value=50,
            measurement_frequency='monthly',
            responsible='Owner B',
            deadline=date.today() + timedelta(days=30),
            status='active',
        )

        StakeholderProfile.objects.create(
            organization=self.org_a,
            name='Stakeholder A',
            stakeholder_type='cliente',
            influence_score=0.9,
            power='alto',
            interest='alto',
        )
        StakeholderProfile.objects.create(
            organization=self.org_b,
            name='Stakeholder B',
            stakeholder_type='proveedor',
            influence_score=0.2,
            power='bajo',
            interest='bajo',
        )

        ProcessMap.objects.create(
            organization=self.org_a,
            process_id='PROC-A',
            process_name='Process A',
            process_data={},
            owner='Owner A',
            health_status='healthy',
        )
        ProcessMap.objects.create(
            organization=self.org_b,
            process_id='PROC-B',
            process_name='Process B',
            process_data={},
            owner='Owner B',
            health_status='warning',
        )

        self.auth_client.force_authenticate(user=self.user)

        self.endpoints = [
            reverse('dashboard-summary'),
            reverse('risk-matrix'),
            reverse('risk-stats'),
            reverse('context-latest'),
        ]

    def test_legacy_endpoints_require_authentication(self):
        for endpoint in self.endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 401, msg=f'Expected 401 in {endpoint}')

    def test_legacy_endpoints_require_organization_scope(self):
        for endpoint in self.endpoints:
            response = self.auth_client.get(endpoint)
            self.assertEqual(response.status_code, 400, msg=f'Expected 400 in {endpoint}')
            self.assertIn('organization_id', response.data)

    def test_legacy_endpoints_block_foreign_organization(self):
        for endpoint in self.endpoints:
            response = self.auth_client.get(endpoint, {'organization_id': self.org_b.id})
            self.assertEqual(response.status_code, 403, msg=f'Expected 403 in {endpoint}')

    def test_legacy_endpoints_allow_member_organization(self):
        for endpoint in self.endpoints:
            response = self.auth_client.get(endpoint, {'organization_id': self.org_a.id})
            self.assertEqual(response.status_code, 200, msg=f'Expected 200 in {endpoint}')
            self.assertEqual(response.data.get('organization_id'), self.org_a.id)

    def test_legacy_endpoints_return_only_requested_organization_data(self):
        summary = self.auth_client.get(reverse('dashboard-summary'), {'organization_id': self.org_a.id})
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data.get('total_risks'), 1)
        self.assertEqual(summary.data.get('total_objectives'), 1)
        self.assertEqual(summary.data.get('total_stakeholders'), 1)
        self.assertEqual(summary.data.get('total_processes'), 1)

        matrix = self.auth_client.get(reverse('risk-matrix'), {'organization_id': self.org_a.id})
        self.assertEqual(matrix.status_code, 200)
        self.assertEqual(matrix.data.get('total'), 1)

        stats = self.auth_client.get(reverse('risk-stats'), {'organization_id': self.org_a.id})
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.data.get('total_risks'), 1)

        latest = self.auth_client.get(reverse('context-latest'), {'organization_id': self.org_a.id})
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(latest.data.get('id'), self.context_a.id)

    def test_risk_viewset_isolates_tenant_data(self):
        risk_list = self.auth_client.get(reverse('risk-list'), {'organization_id': self.org_a.id})
        self.assertEqual(risk_list.status_code, 200)
        self.assertEqual(risk_list.data.get('count'), 1)
        self.assertEqual(risk_list.data.get('results')[0].get('risk_description'), 'Risk A')

        foreign_detail = self.auth_client.get(
            reverse('risk-detail', args=[self.risk_b.id]),
            {'organization_id': self.org_a.id},
        )
        self.assertEqual(foreign_detail.status_code, 404)


class SettingsBackupHistoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='settings_user',
            email='settings_user@isosmart.local',
            password='StrongPass@123',
            first_name='Settings',
            last_name='Admin',
        )

        self.org_a = Organization.objects.create(
            name='Settings Org A',
            slug='settings-org-a',
            email='settings-a@isosmart.local',
        )
        self.org_b = Organization.objects.create(
            name='Settings Org B',
            slug='settings-org-b',
            email='settings-b@isosmart.local',
        )

        UserProfile.objects.create(
            user=self.user,
            organization=self.org_a,
            role='org_admin',
            is_active=True,
        )

        OrganizationSettings.objects.create(organization=self.org_a)
        OrganizationSettings.objects.create(organization=self.org_b)

        self.client.force_authenticate(user=self.user)

    def test_trigger_backup_updates_settings_and_creates_audit_log(self):
        response = self.client.post(
            reverse('settings-trigger-backup'),
            {'organization_id': self.org_a.id},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('last_backup_at'))
        self.assertIn('history_entry', response.data)

        settings = OrganizationSettings.objects.get(organization=self.org_a)
        self.assertIsNotNone(settings.last_backup_at)

        audit_log = AuditLog.objects.get(organization=self.org_a, action='backup', module='settings')
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.description, 'Backup manual ejecutado desde configuracion')
        self.assertEqual(response.data['history_entry']['id'], audit_log.id)

    def test_backups_action_returns_only_requested_organization_history(self):
        AuditLog.objects.create(
            organization=self.org_a,
            user=self.user,
            action='backup',
            module='settings',
            description='Backup org A',
        )
        AuditLog.objects.create(
            organization=self.org_b,
            user=self.user,
            action='backup',
            module='settings',
            description='Backup org B',
        )

        response = self.client.get(reverse('settings-backups'), {'organization_id': self.org_a.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['description'], 'Backup org A')
        self.assertEqual(response.data['results'][0]['organization'], self.org_a.id)

    def test_settings_actions_reject_foreign_organization(self):
        response = self.client.get(reverse('settings-backups'), {'organization_id': self.org_b.id})
        self.assertEqual(response.status_code, 403)

    def test_export_data_creates_export_audit_log(self):
        response = self.client.get(reverse('export-data'), {'organization_id': self.org_a.id, 'type': 'all'})

        self.assertEqual(response.status_code, 200)
        audit_log = AuditLog.objects.get(organization=self.org_a, action='export', module='settings')
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.new_values['export_type'], 'all')

    def test_onboarding_endpoints_return_empty_payloads_when_no_snapshot(self):
        insights = self.client.get(reverse('settings-onboarding-insights'), {'organization_id': self.org_a.id})
        self.assertEqual(insights.status_code, 200)
        self.assertIsNone(insights.data)

        iso_skeleton = self.client.get(reverse('settings-onboarding-iso-skeleton'), {'organization_id': self.org_a.id})
        self.assertEqual(iso_skeleton.status_code, 200)
        self.assertEqual(iso_skeleton.data['organization_id'], self.org_a.id)
        self.assertIsNone(iso_skeleton.data['snapshot_version'])
        self.assertIsNone(iso_skeleton.data['iso_skeleton'])

        adaptive_route = self.client.get(reverse('settings-onboarding-adaptive-route'), {'organization_id': self.org_a.id})
        self.assertEqual(adaptive_route.status_code, 200)
        self.assertEqual(adaptive_route.data['organization_id'], self.org_a.id)
        self.assertIsNone(adaptive_route.data['snapshot_version'])
        self.assertIsNone(adaptive_route.data['adaptive_route'])

    def test_onboarding_endpoints_return_snapshot_data_when_available(self):
        OnboardingInsightSnapshot.objects.create(
            organization=self.org_a,
            generated_by=self.user,
            version=1,
            summary_output={
                'iso_skeleton': {'scope_draft': 'Scope draft example'},
                'adaptive_route': {
                    'mode': 'guided',
                    'cadence': 'weekly',
                    'title': 'Ruta guiada',
                    'description': 'Descripcion de ruta',
                    'recommended_actions': ['Accion 1'],
                },
            },
        )

        insights = self.client.get(reverse('settings-onboarding-insights'), {'organization_id': self.org_a.id})
        self.assertEqual(insights.status_code, 200)
        self.assertEqual(insights.data['version'], 1)

        iso_skeleton = self.client.get(reverse('settings-onboarding-iso-skeleton'), {'organization_id': self.org_a.id})
        self.assertEqual(iso_skeleton.status_code, 200)
        self.assertEqual(iso_skeleton.data['snapshot_version'], 1)
        self.assertEqual(iso_skeleton.data['iso_skeleton']['scope_draft'], 'Scope draft example')

        adaptive_route = self.client.get(reverse('settings-onboarding-adaptive-route'), {'organization_id': self.org_a.id})
        self.assertEqual(adaptive_route.status_code, 200)
        self.assertEqual(adaptive_route.data['snapshot_version'], 1)
        self.assertEqual(adaptive_route.data['adaptive_route']['mode'], 'guided')

