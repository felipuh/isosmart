from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import UserProfile
from ai_modules.sie.models.stakeholder import StakeholderProfile as AIStakeholderProfile
from ai_modules.sie.models.stakeholder import StakeholderChangeLog as AIStakeholderChangeLog
from core.models import (
    AuditLog,
    ContextAnalysis,
    ISOClauseConfig,
    NotificationDelivery,
    OnboardingInsightSnapshot,
    Organization,
    OrganizationSettings,
    ProcessMap,
    QualityObjective,
    RiskMatrix,
    StakeholderProfile,
)
from core.services.billing_notifications import notify_payment_registered
from core.services.notifications import send_email_notification
from planning.models import ObjectiveAction as PlanningObjectiveAction
from planning.models import QualityObjective as PlanningQualityObjective
from planning.models import RiskOpportunity
from backend.tasks import evaluate_operational_notifications_task


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


class NotificationFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='notify-user@isosmart.local',
            password='StrongPass@123',
            first_name='Notify',
            last_name='User',
        )
        self.organization = Organization.objects.create(
            name='Notify Org',
            slug='notify-org',
            email='org@isosmart.local',
        )
        self.settings = OrganizationSettings.objects.create(
            organization=self.organization,
            notification_email='alerts@isosmart.local',
            notify_risk_critical=True,
            notify_risk_high=True,
            notify_objective_deadline=True,
            notify_stakeholder_change=True,
        )
        UserProfile.objects.create(
            user=self.user,
            organization=self.organization,
            role='org_admin',
            is_active=True,
            notifications_enabled=True,
            email_notifications=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_send_email_notification_records_delivery(self):
        delivery = send_email_notification(
            organization=self.organization,
            event_type='risk_critical',
            event_key='risk:test:1',
            subject='Critical risk',
            message='Risk details',
            users=[self.user],
            metadata={'risk_id': 1},
        )

        self.assertEqual(delivery.status, 'sent')
        self.assertEqual(NotificationDelivery.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(sorted(mail.outbox[0].to), ['alerts@isosmart.local', 'notify-user@isosmart.local', 'org@isosmart.local'])

    def test_send_email_notification_deduplicates_by_event_key(self):
        first = send_email_notification(
            organization=self.organization,
            event_type='risk_high',
            event_key='risk:test:dedupe',
            subject='High risk',
            message='First send',
        )
        second = send_email_notification(
            organization=self.organization,
            event_type='risk_high',
            event_key='risk:test:dedupe',
            subject='High risk duplicate',
            message='Second send',
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(NotificationDelivery.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_billing_notification_uses_tracked_delivery(self):
        from core.models import BillingPayment, BillingSubscription

        subscription = BillingSubscription.objects.create(
            organization=self.organization,
            payer_email='payer@isosmart.local',
            monthly_price='99.00',
            currency='USD',
        )
        payment = BillingPayment.objects.create(
            subscription=subscription,
            status='pending',
            amount='99.00',
            currency='USD',
        )

        notify_payment_registered(payment)

        delivery = NotificationDelivery.objects.get(event_type='billing_payment_registered')
        self.assertEqual(delivery.status, 'sent')
        self.assertIn('payer@isosmart.local', delivery.recipients)
        self.assertEqual(len(mail.outbox), 1)

    def test_operational_notification_task_sends_risk_objective_and_stakeholder_alerts(self):
        risk = RiskOpportunity.objects.create(
            organization_id=self.organization.id,
            organization_name=self.organization.name,
            item_type='risk',
            code='R-001',
            title='Critical supplier disruption',
            description='A key supplier may stop delivering.',
            context='external',
            category='operational',
            probability=4,
            impact=5,
            owner=self.user,
            status='identified',
        )
        objective = PlanningQualityObjective.objects.create(
            organization_id=self.organization.id,
            organization_name=self.organization.name,
            code='OBJ-001',
            title='Reduce complaints',
            description='Reduce customer complaints by 20%.',
            is_specific=True,
            is_measurable=True,
            is_achievable=True,
            is_relevant=True,
            is_time_bound=True,
            alignment='customer',
            metric='Complaints',
            target='20.00',
            owner=self.user,
            start_date=date.today(),
            target_date=date.today() + timedelta(days=3),
            status='in_progress',
            progress_percentage=40,
        )
        PlanningObjectiveAction.objects.create(
            organization_id=self.organization.id,
            objective=objective,
            action_number=1,
            description='Call key customers',
            what_will_be_done='Reach out to affected customers',
            responsible=self.user,
            due_date=date.today() + timedelta(days=2),
            status='planned',
        )
        stakeholder = AIStakeholderProfile.objects.create(
            organization_id=self.organization.id,
            name='Critical customer',
            stakeholder_type='cliente',
            influence_score=0.9,
            power='alto',
            interest='alto',
            satisfaction_score=2.0,
        )
        AIStakeholderChangeLog.objects.create(
            stakeholder=stakeholder,
            change_type='expectation_alto',
            previous_state={'expectation': 'stable'},
            new_state={'expectation': 'critical'},
            similarity_score=0.2,
        )

        result = evaluate_operational_notifications_task()

        self.assertGreaterEqual(result['risk_notifications'], 1)
        self.assertGreaterEqual(result['objective_notifications'], 2)
        self.assertGreaterEqual(result['stakeholder_alerts'], 1)
        self.assertEqual(NotificationDelivery.objects.filter(event_type='risk_critical').count(), 1)
        self.assertEqual(NotificationDelivery.objects.filter(event_type='objective_deadline').count(), 2)
        self.assertEqual(NotificationDelivery.objects.filter(event_type='stakeholder_change').count(), 1)
        self.assertEqual(len(mail.outbox), 4)

    def test_notification_history_endpoint_returns_recent_deliveries(self):
        send_email_notification(
            organization=self.organization,
            event_type='risk_high',
            event_key='history:test:1',
            subject='History entry',
            message='History message',
            users=[self.user],
        )

        response = self.client.get(
            reverse('settings-notification-history'),
            {'organization_id': self.organization.id, 'limit': 5},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['event_key'], 'history:test:1')


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

    def test_update_standards_enforces_iso9001_only(self):
        response = self.client.post(
            reverse('settings-update-standards'),
            {
                'organization_id': self.org_a.id,
                'enabled_standards': ['ISO27001_2022', 'ISO45001_2018'],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['enabled_standards'], ['ISO9001_2015'])

        settings = OrganizationSettings.objects.get(organization=self.org_a)
        self.assertEqual(settings.enabled_standards, ['ISO9001_2015'])

    def test_onboarding_status_exposes_commercially_available_standards(self):
        response = self.client.get(reverse('settings-onboarding-status'), {'organization_id': self.org_a.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['commercially_available_standards'], ['ISO9001_2015'])

    def test_update_standards_allows_org_specific_override(self):
        with self.settings(
            COMMERCIAL_ENABLED_STANDARDS=['ISO9001_2015'],
            COMMERCIAL_ENABLED_STANDARDS_BY_ORG={
                str(self.org_a.id): ['ISO9001_2015', 'ISO27001_2022'],
            },
        ):
            response = self.client.post(
                reverse('settings-update-standards'),
                {
                    'organization_id': self.org_a.id,
                    'enabled_standards': ['ISO27001_2022'],
                },
                format='json',
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['enabled_standards'], ['ISO9001_2015', 'ISO27001_2022'])

            status_response = self.client.get(
                reverse('settings-onboarding-status'),
                {'organization_id': self.org_a.id},
            )
            self.assertEqual(status_response.status_code, 200)
            self.assertEqual(
                status_response.data['commercially_available_standards'],
                ['ISO9001_2015', 'ISO27001_2022'],
            )

    def test_initialize_standards_enforces_iso9001_only(self):
        response = self.client.post(
            reverse('iso-clause-initialize-standards'),
            {
                'organization_id': self.org_a.id,
                'standards': ['ISO27001_2022'],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['standards'], ['ISO9001_2015'])
        self.assertFalse(
            ISOClauseConfig.objects.filter(
                organization=self.org_a,
                standard_code='ISO27001_2022',
            ).exists()
        )
        self.assertTrue(
            ISOClauseConfig.objects.filter(
                organization=self.org_a,
                standard_code='ISO9001_2015',
            ).exists()
        )

    def test_complete_onboarding_saves_profile_and_marks_completed(self):
        payload = {
            'organization_id': self.org_a.id,
            'enabled_standards': ['ISO9001_2015'],
            'preferred_language': 'es-LATAM',
            'preferred_response_tone': 'manager',
            'onboarding_profile': {
                'role': 'quality_manager',
                'expertise_level': 'intermediate',
                'size_range': '51-200',
                'sector': 'manufacturing',
                'employees_count': 120,
                'sites_count': 2,
                'countries': ['Costa Rica'],
                'certification_status': 'in_progress',
            },
        }
        response = self.client.post(
            reverse('settings-complete-onboarding'),
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['organization_id'], self.org_a.id)

        settings = OrganizationSettings.objects.get(organization=self.org_a)
        self.assertTrue(settings.onboarding_completed)
        self.assertIsNotNone(settings.onboarding_completed_at)
        self.assertEqual(settings.onboarding_completed_by, self.user)
        self.assertEqual(settings.preferred_response_tone, 'manager')
        self.assertEqual(settings.preferred_language, 'es-LATAM')
        self.assertEqual(settings.onboarding_profile['role'], 'quality_manager')
        self.assertEqual(settings.onboarding_profile['employees_count'], 120)

    def test_complete_onboarding_rejects_invalid_tone(self):
        payload = {
            'organization_id': self.org_a.id,
            'preferred_response_tone': 'informal',
        }
        response = self.client.post(
            reverse('settings-complete-onboarding'),
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_complete_onboarding_rejects_non_dict_profile(self):
        payload = {
            'organization_id': self.org_a.id,
            'onboarding_profile': 'not-a-dict',
        }
        response = self.client.post(
            reverse('settings-complete-onboarding'),
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_run_onboarding_orchestration_creates_snapshot(self):
        # Set up profile first
        settings = OrganizationSettings.objects.get(organization=self.org_a)
        settings.onboarding_profile = {
            'role': 'quality_manager',
            'expertise_level': 'intermediate',
            'size_range': '51-200',
            'sector': 'manufacturing',
            'employees_count': 120,
            'sites_count': 1,
            'countries': ['Costa Rica'],
            'certification_status': 'in_progress',
        }
        settings.save()

        response = self.client.post(
            reverse('settings-run-onboarding-orchestration'),
            {'organization_id': self.org_a.id},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.data)
        self.assertIn('snapshot', response.data)
        self.assertIn('version', response.data['snapshot'])

        # Snapshot must be persisted
        snapshot_count = OnboardingInsightSnapshot.objects.filter(organization=self.org_a).count()
        self.assertEqual(snapshot_count, 1)

    def test_run_onboarding_orchestration_increments_version(self):
        """Running orchestration twice → version increments."""
        settings = OrganizationSettings.objects.get(organization=self.org_a)
        settings.onboarding_profile = {'role': 'ceo', 'expertise_level': 'novice', 'size_range': '10-50'}
        settings.save()

        self.client.post(
            reverse('settings-run-onboarding-orchestration'),
            {'organization_id': self.org_a.id},
            format='json',
        )
        response2 = self.client.post(
            reverse('settings-run-onboarding-orchestration'),
            {'organization_id': self.org_a.id},
            format='json',
        )
        self.assertEqual(response2.status_code, 201)
        self.assertEqual(response2.data['snapshot']['version'], 2)

    def test_run_onboarding_orchestration_forbidden_for_foreign_org(self):
        response = self.client.post(
            reverse('settings-run-onboarding-orchestration'),
            {'organization_id': self.org_b.id},
            format='json',
        )
        self.assertEqual(response.status_code, 403)


class BusinessReportTests(TestCase):
    """Tests for GET /api/reports/ — PDF, XLSX, and CSV report generation."""

    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='report_user',
            email='report_user@isosmart.local',
            password='StrongPass@123',
            first_name='Report',
            last_name='User',
        )
        self.org = Organization.objects.create(
            name='Report Test Org',
            slug='report-test-org',
            is_active=True,
        )
        from authentication.models import UserProfile
        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={'role': 'org_admin', 'organization': self.org},
        )
        self.client.force_authenticate(user=self.user)

        # Seed a risk and objective so the reports have data
        self.risk = RiskMatrix.objects.create(
            organization=self.org,
            source_module='MANUAL',
            risk_description='Test critical risk',
            risk_category='Operacional',
            probability='alta',
            impact='alto',
            risk_level='critico',
            mitigation_actions='Mitigar de inmediato',
            responsible='Risk Owner',
            iso_clause='6.1',
            status='identified',
        )
        self.objective = QualityObjective.objects.create(
            organization=self.org,
            source_module='MANUAL',
            objective_description='Test objective',
            indicator_name='Coverage',
            measurement_unit='%',
            baseline_value=50,
            target_value=100,
            current_value=80,
            measurement_frequency='monthly',
            responsible='Quality Owner',
            deadline=date.today() + timedelta(days=30),
            status='in_progress',
        )

    def _get_report(self, report_type, fmt, **extra_params):
        params = {'organization_id': self.org.id, 'type': report_type, 'file_format': fmt}
        params.update(extra_params)
        return self.client.get(reverse('settings-business-report'), params)

    # --- PDF ---
    def test_sgq_executive_pdf_returns_200_and_correct_content_type(self):
        response = self._get_report('sgq_executive', 'pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.pdf', response['Content-Disposition'])
        # PDF magic bytes
        self.assertTrue(b'%PDF' in response.content[:10])

    def test_risks_pdf_returns_200_and_valid_pdf(self):
        response = self._get_report('risks', 'pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(b'%PDF' in response.content[:10])

    def test_objectives_pdf_returns_200_and_valid_pdf(self):
        response = self._get_report('objectives', 'pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(b'%PDF' in response.content[:10])

    # --- XLSX ---
    def test_sgq_executive_xlsx_returns_200_and_correct_content_type(self):
        response = self._get_report('sgq_executive', 'xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
        self.assertIn('.xlsx', response['Content-Disposition'])
        # XLSX = ZIP format, starts with PK magic bytes
        self.assertTrue(response.content[:2] == b'PK')

    def test_risks_xlsx_returns_200_and_valid_xlsx(self):
        response = self._get_report('risks', 'xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
        self.assertTrue(response.content[:2] == b'PK')

    def test_objectives_xlsx_returns_200_and_valid_xlsx(self):
        response = self._get_report('objectives', 'xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
        self.assertTrue(response.content[:2] == b'PK')

    # --- CSV ---
    def test_sgq_executive_csv_returns_200_and_correct_content_type(self):
        response = self._get_report('sgq_executive', 'csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('.csv', response['Content-Disposition'])
        content = response.content.decode('utf-8-sig')
        self.assertIn('Organizaci', content)

    def test_risks_csv_contains_risk_data(self):
        response = self._get_report('risks', 'csv')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Test critical risk', content)
        self.assertIn('CRITICO', content)

    def test_objectives_csv_contains_objective_data(self):
        response = self._get_report('objectives', 'csv')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Test objective', content)

    # --- Validation ---
    def test_invalid_format_returns_400(self):
        response = self._get_report('risks', 'docx')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_invalid_report_type_returns_400(self):
        response = self._get_report('nonexistent', 'pdf')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_date_filters_applied_correctly(self):
        response = self._get_report('risks', 'csv',
                                    date_from='2030-01-01', date_to='2030-12-31')
        self.assertEqual(response.status_code, 200)
        # Risks created today won't appear in the future range
        content = response.content.decode('utf-8-sig')
        self.assertNotIn('Test critical risk', content)

    def test_unauthenticated_request_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(
            reverse('settings-business-report'),
            {'organization_id': self.org.id, 'type': 'risks', 'file_format': 'pdf'},
        )
        self.assertEqual(response.status_code, 401)

    def test_report_creates_audit_log(self):
        self._get_report('risks', 'xlsx')
        log = AuditLog.objects.filter(
            organization=self.org,
            action='export',
            module='reports',
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.new_values['type'], 'risks')
        self.assertEqual(log.new_values['format'], 'xlsx')


class BackendRoleAuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()

        self.admin = user_model.objects.create_user(
            username='role_admin',
            email='role_admin@isosmart.local',
            password='StrongPass@123',
        )
        self.manager = user_model.objects.create_user(
            username='role_manager',
            email='role_manager@isosmart.local',
            password='StrongPass@123',
        )
        self.viewer = user_model.objects.create_user(
            username='role_viewer',
            email='role_viewer@isosmart.local',
            password='StrongPass@123',
        )

        self.org = Organization.objects.create(
            name='Role Auth Org',
            slug='role-auth-org',
            is_active=True,
        )

        UserProfile.objects.create(user=self.admin, organization=self.org, role='org_admin', is_active=True)
        UserProfile.objects.create(user=self.manager, organization=self.org, role='iso_manager', is_active=True)
        UserProfile.objects.create(user=self.viewer, organization=self.org, role='viewer', is_active=True)

        OrganizationSettings.objects.create(
            organization=self.org,
            notify_risk_critical=True,
            notify_risk_high=True,
        )

    def test_settings_update_notifications_denied_for_viewer(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post(
            reverse('settings-update-notifications'),
            {
                'organization_id': self.org.id,
                'notify_risk_critical': False,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_settings_update_notifications_allowed_for_manager(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            reverse('settings-update-notifications'),
            {
                'organization_id': self.org.id,
                'notify_risk_critical': False,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        settings = OrganizationSettings.objects.get(organization=self.org)
        self.assertFalse(settings.notify_risk_critical)

    def test_user_management_list_denied_for_manager(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(reverse('user-management-list'), {'organization': self.org.id})
        self.assertEqual(response.status_code, 403)

    def test_user_management_list_allowed_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('user-management-list'), {'organization': self.org.id})
        self.assertEqual(response.status_code, 200)

    def test_user_management_create_denied_for_viewer(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post(
            reverse('user-management-create-user'),
            {
                'organization_id': self.org.id,
                'username': 'blocked_user',
                'email': 'blocked_user@isosmart.local',
                'password': 'StrongPass@123',
                'role': 'user',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_billing_update_payer_denied_for_viewer(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post(
            reverse('billing-update-payer'),
            {
                'organization_id': self.org.id,
                'payer_name': 'Viewer Blocked',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_billing_update_payer_allowed_for_manager(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            reverse('billing-update-payer'),
            {
                'organization_id': self.org.id,
                'payer_name': 'Manager Allowed',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)

    def test_iso_initialize_standards_denied_for_viewer(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post(
            reverse('iso-clause-initialize-standards'),
            {
                'organization_id': self.org.id,
                'standards': ['ISO9001_2015'],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_iso_initialize_standards_allowed_for_manager(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            reverse('iso-clause-initialize-standards'),
            {
                'organization_id': self.org.id,
                'standards': ['ISO9001_2015'],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)


class RoleEndpointMatrixTests(TestCase):
    """Formal role-to-endpoint matrix with parameterized assertions."""

    ROLE_ORDER = ['org_admin', 'iso_manager', 'auditor', 'user', 'viewer']

    MATRIX = [
        {
            'name': 'settings_update_notifications',
            'method': 'post',
            'url_name': 'settings-update-notifications',
            'payload': lambda org: {'organization_id': org.id, 'notify_risk_high': False},
            'allowed_roles': {'org_admin', 'iso_manager'},
        },
        {
            'name': 'user_management_list',
            'method': 'get',
            'url_name': 'user-management-list',
            'query': lambda org: {'organization': org.id},
            'allowed_roles': {'org_admin'},
        },
        {
            'name': 'billing_update_payer',
            'method': 'post',
            'url_name': 'billing-update-payer',
            'payload': lambda org: {'organization_id': org.id, 'payer_name': 'Matrix QA'},
            'allowed_roles': {'org_admin', 'iso_manager'},
        },
        {
            'name': 'iso_initialize_standards',
            'method': 'post',
            'url_name': 'iso-clause-initialize-standards',
            'payload': lambda org: {'organization_id': org.id, 'standards': ['ISO9001_2015']},
            'allowed_roles': {'org_admin', 'iso_manager'},
        },
        {
            'name': 'organization_list',
            'method': 'get',
            'url_name': 'organization-list',
            'query': lambda org: {},
            'allowed_roles': {'org_admin', 'iso_manager', 'auditor', 'user', 'viewer'},
        },
        {
            'name': 'organization_partial_update',
            'method': 'patch',
            'url_name': 'organization-detail',
            'url_kwargs': lambda org: {'pk': org.id},
            'payload': lambda org: {'name': 'Role Auth Org Updated'},
            'allowed_roles': {'org_admin'},
        },
    ]

    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()

        self.org = Organization.objects.create(
            name='Matrix Role Org',
            slug='matrix-role-org',
            is_active=True,
        )
        OrganizationSettings.objects.create(
            organization=self.org,
            notify_risk_high=True,
        )

        self.users_by_role = {}
        for role in self.ROLE_ORDER:
            user = user_model.objects.create_user(
                username=f'matrix_{role}',
                email=f'matrix_{role}@isosmart.local',
                password='StrongPass@123',
            )
            UserProfile.objects.create(
                user=user,
                organization=self.org,
                role=role,
                is_active=True,
            )
            self.users_by_role[role] = user

    def _call_case(self, role, case):
        self.client.force_authenticate(user=self.users_by_role[role])
        url = reverse(case['url_name'], kwargs=case.get('url_kwargs', lambda _: {})(self.org))

        method = case['method'].lower()
        if method == 'get':
            params = case.get('query', lambda _: {})(self.org)
            return self.client.get(url, params)
        if method == 'post':
            data = case.get('payload', lambda _: {})(self.org)
            return self.client.post(url, data, format='json')
        if method == 'patch':
            data = case.get('payload', lambda _: {})(self.org)
            return self.client.patch(url, data, format='json')
        raise ValueError(f"Unsupported method in matrix: {method}")

    def test_role_endpoint_matrix(self):
        for case in self.MATRIX:
            for role in self.ROLE_ORDER:
                with self.subTest(case=case['name'], role=role):
                    response = self._call_case(role, case)
                    if role in case['allowed_roles']:
                        self.assertNotEqual(
                            response.status_code,
                            403,
                            msg=f"Expected allowed access for role={role} in case={case['name']}",
                        )
                    else:
                        self.assertEqual(
                            response.status_code,
                            403,
                            msg=f"Expected denied access for role={role} in case={case['name']}",
                        )



# =====================================================
# Feature Flags tests
# =====================================================

from core.models import FeatureFlag


class FeatureFlagManagerTests(TestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(name='Flag Org A', slug='flag-org-a')
        self.org_b = Organization.objects.create(name='Flag Org B', slug='flag-org-b')

    def test_is_enabled_returns_false_when_no_flag(self):
        self.assertFalse(FeatureFlag.objects.is_enabled('nonexistent'))

    def test_global_flag_visible_to_all(self):
        FeatureFlag.objects.create(name='global_feature', scope='global', enabled=True)
        self.assertTrue(FeatureFlag.objects.is_enabled('global_feature', organization=self.org_a))
        self.assertTrue(FeatureFlag.objects.is_enabled('global_feature', organization=self.org_b))
        self.assertTrue(FeatureFlag.objects.is_enabled('global_feature'))

    def test_org_override_takes_precedence_over_global(self):
        FeatureFlag.objects.create(name='beta_module', scope='global', enabled=False)
        FeatureFlag.objects.create(name='beta_module', scope='organization', organization=self.org_a, enabled=True)
        self.assertTrue(FeatureFlag.objects.is_enabled('beta_module', organization=self.org_a))
        self.assertFalse(FeatureFlag.objects.is_enabled('beta_module', organization=self.org_b))

    def test_resolve_all_returns_dict(self):
        FeatureFlag.objects.create(name='feat_x', scope='global', enabled=True)
        FeatureFlag.objects.create(name='feat_y', scope='global', enabled=False)
        FeatureFlag.objects.create(name='feat_y', scope='organization', organization=self.org_a, enabled=True)
        result = FeatureFlag.objects.resolve_all(organization=self.org_a)
        self.assertEqual(result, {'feat_x': True, 'feat_y': True})
        result_b = FeatureFlag.objects.resolve_all(organization=self.org_b)
        self.assertEqual(result_b, {'feat_x': True, 'feat_y': False})


class FeatureFlagsEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='flag_user',
            email='flag_user@isosmart.local',
            password='Pass@12345',
        )
        self.org = Organization.objects.create(name='Flag Test Org', slug='flag-test-org')
        UserProfile.objects.filter(user=self.user).update(organization=self.org)

    def test_unauthenticated_returns_401(self):
        response = self.client.get('/api/feature-flags/')
        self.assertEqual(response.status_code, 401)

    def test_authenticated_empty_flags(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/feature-flags/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)

    def test_returns_resolved_flags(self):
        FeatureFlag.objects.create(name='new_dashboard', scope='global', enabled=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/feature-flags/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('new_dashboard', response.data)
        self.assertTrue(response.data['new_dashboard'])


class RequestIDMiddlewareTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_generates_request_id_when_missing(self):
        response = self.client.get('/api/feature-flags/')

        self.assertEqual(response.status_code, 401)
        self.assertIn('X-Request-ID', response)
        self.assertTrue(response['X-Request-ID'])

    def test_echoes_incoming_request_id_header(self):
        response = self.client.get('/api/feature-flags/', HTTP_X_REQUEST_ID='req-isosmart-001')

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response['X-Request-ID'], 'req-isosmart-001')
