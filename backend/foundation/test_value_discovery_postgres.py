"""PostgreSQL integration coverage for the Step 11 Value Discovery boundary.

These checks deliberately exercise the real migration, restricted application
role, RLS context, and persistence services.  The provider is controlled only
at the inference edge; no domain persistence or onboarding API is replaced.
"""

import json
from unittest.mock import Mock
from uuid import uuid4

from django.db import connections

from foundation.audit import ImmutableAuditLog
from foundation.models import (
    DomainEvent,
    OnboardingWorkflow,
    TransactionalOutbox,
    ValueDiscoveryExecution,
)
from foundation.onboarding import (
    ONBOARDING_STEPS,
    OnboardingWorkflowService,
    OrganizationProfileCommandService,
)
from foundation.tenant_context import trusted_tenant_context
from foundation.test_source_artifact_postgres_integration import (
    SourceArtifactPostgreSQLIntegrationTests,
)
from foundation.value_discovery import (
    ControlledValueDiscoveryProvider,
    ProviderFailed,
    ValueDiscoveryError,
    ValueDiscoveryService,
)


class ValueDiscoveryPostgreSQLTests(SourceArtifactPostgreSQLIntegrationTests):
    """Step 11 remains an atomic, tenant-scoped extension—not an AgentRun."""

    def complete_step_ten(self):
        workflow = OnboardingWorkflowService(using="app")
        for step in ONBOARDING_STEPS[:9]:
            workflow.transition(
                identity=self.identity,
                user_id=self.user_projection_id,
                step_key=step.key,
                to_status="complete",
                event_id=uuid4(),
                event_type="test.onboarding.prerequisite",
                source_reference=f"fixture:{step.key}",
                actor_id=self.actor_id,
                trace_id=uuid4(),
            )
        profile = {
            "role": "quality_manager",
            "expertise_level": "intermediate",
            "size_range": "51-200",
            "sites_count": 2,
            "countries": ["Costa Rica"],
            "sector": "manufacturing",
            "certification_status": "in_progress",
            "employees_count": 120,
        }
        return OrganizationProfileCommandService(using="app").save_profile(
            identity=self.identity,
            organization_id=self.organization_id,
            user_id=self.user_projection_id,
            profile=profile,
            event_id=uuid4(),
            actor_id=self.actor_id,
            trace_id=uuid4(),
        )[0]

    def execute(self, *, provider=None, event_id=None, purpose="Provide dependable services."):
        return ValueDiscoveryService(
            using="app", provider=provider or ControlledValueDiscoveryProvider(),
        ).execute(
            identity=self.identity,
            organization_id=self.organization_id,
            user_id=self.user_projection_id,
            declared_purpose=purpose,
            event_id=event_id or uuid4(),
            actor_id=self.actor_id,
            trace_id=uuid4(),
        )

    def test_migration_0038_creates_restricted_tenant_execution_table(self):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                "WHERE oid='onboarding.value_discovery_execution'::regclass"
            )
            self.assertEqual(cursor.fetchone(), (True, True))
            cursor.execute(
                "SELECT conname FROM pg_constraint WHERE conrelid="
                "'onboarding.value_discovery_execution'::regclass"
            )
            constraints = {row[0] for row in cursor.fetchall()}
            self.assertTrue({
                "onboarding_value_discovery_org_fk",
                "onboarding_value_discovery_user_fk",
                "onboarding_value_discovery_result_object",
            }.issubset(constraints))
            cursor.execute(
                "SELECT roles, cmd FROM pg_policies WHERE schemaname='onboarding' "
                "AND tablename='value_discovery_execution'"
            )
            policies = cursor.fetchall()
        self.assertEqual(len(policies), 1)
        self.assertEqual(policies[0][1], "ALL")

    def test_controlled_execution_persists_evidence_transition_event_outbox_and_audit(self):
        workflow = self.complete_step_ten()
        execution, replay = self.execute()
        self.assertFalse(replay)
        result = execution.result
        self.assertEqual(execution.execution_mode, "CONTROLLED_TEST")
        self.assertEqual(result["profile_input_hash"], workflow.state["organizational_profile"]["profile_hash"])
        self.assertEqual(result["preliminary_opportunity_count"], 0)
        self.assertEqual(
            result["impact_savings_result"]["financial_assessment"],
            {
                "status": "NOT_ASSESSED",
                "amount": None,
                "currency": None,
                "reason": "NO_AUTHORIZED_FINANCIAL_BASELINE",
            },
        )
        self.assertEqual(result["impact_savings_result"]["preliminary_improvement_opportunities"], [])
        self.assertEqual(result["result_hash"], execution.result_hash)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            persisted = ValueDiscoveryExecution.objects.using("app").get(pk=execution.id)
            state = OnboardingWorkflow.objects.using("app").get(pk=workflow.id).state["value_discovery"]
            event = DomainEvent.objects.using("app").get(
                aggregate_id=workflow.id, event_type="onboarding.value_discovery.completed",
            )
            self.assertTrue(TransactionalOutbox.objects.using("app").filter(domain_event_id=event.event_id).exists())
            audit = ImmutableAuditLog.objects.using("app").get(entity_id=execution.id)
        self.assertEqual(str(persisted.evidence_id), state["evidence_id"])
        self.assertEqual(str(persisted.id), state["agent_run_id"])
        self.assertEqual(event.payload["result_hash"], execution.result_hash)
        self.assertEqual(
            json.loads(audit.metadata_canonical)["value"]["evidence_id"],
            str(execution.evidence_id),
        )
        self.assertEqual(state["status"], "complete")
        self.assertEqual("document_data_ingestion", OnboardingWorkflowService(using="app").ensure(
            identity=self.identity, user_id=self.user_projection_id,
            actor_id=self.actor_id, trace_id=uuid4(),
        ).current_step)

    def test_replay_is_idempotent_and_conflicting_or_second_completion_is_rejected(self):
        self.complete_step_ten()
        event_id = uuid4()
        execution, replay = self.execute(event_id=event_id)
        replayed, was_replayed = self.execute(event_id=event_id)
        self.assertTrue(was_replayed)
        self.assertEqual(replayed.id, execution.id)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertEqual(ValueDiscoveryExecution.objects.using("app").count(), 1)
        with self.assertRaisesRegex(ValueDiscoveryError, "different"):
            self.execute(event_id=event_id, purpose="A changed declared purpose.")
        with self.assertRaisesRegex(ValueDiscoveryError, "already complete"):
            self.execute(event_id=uuid4())

    def test_tenant_context_prevents_cross_tenant_execution_and_read_leakage(self):
        self.complete_step_ten()
        execution, _ = self.execute()
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(ValueDiscoveryExecution.objects.using("app").filter(pk=execution.id).exists())
        with self.assertRaises(ValueDiscoveryError):
            ValueDiscoveryService(using="app", provider=ControlledValueDiscoveryProvider()).execute(
                identity=self.other_identity,
                organization_id=self.organization_id,
                user_id=self.other_user_projection_id,
                declared_purpose="Foreign tenant attempt",
                event_id=uuid4(),
                actor_id=self.other_actor_id,
                trace_id=uuid4(),
            )
        connection = connections["app"]
        connection.close()
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM onboarding.value_discovery_execution")
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_provider_or_financial_validation_failure_leaves_no_authoritative_effects(self):
        self.complete_step_ten()
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            executions_before = ValueDiscoveryExecution.objects.using("app").count()
            events_before = DomainEvent.objects.using("app").filter(
                event_type="onboarding.value_discovery.completed",
            ).count()
        failing_provider = Mock()
        failing_provider.analyze.side_effect = ProviderFailed("AI_PROVIDER_UNAVAILABLE", "controlled outage")
        failing_provider.provider_name = "controlled-failure"
        failing_provider.model_identifier = "controlled-failure"
        failing_provider.execution_mode = "CONTROLLED_TEST"
        with self.assertRaisesRegex(ValueDiscoveryError, "controlled outage"):
            self.execute(provider=failing_provider)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertEqual(ValueDiscoveryExecution.objects.using("app").count(), executions_before)
            self.assertEqual(DomainEvent.objects.using("app").filter(
                event_type="onboarding.value_discovery.completed",
            ).count(), events_before)
            self.assertNotIn("value_discovery", OnboardingWorkflow.objects.using("app").get(
                tenant_id=self.tenant_id, user_id=self.user_projection_id,
            ).completed_steps)

        invalid_provider = ControlledValueDiscoveryProvider()
        original = invalid_provider.analyze

        def monetary_output(*, capability, context):
            payload = original(capability=capability, context=context)
            if capability == "impact_savings":
                payload["financial_assessment"]["amount"] = "100"
            return payload

        invalid_provider.analyze = monetary_output
        with self.assertRaisesRegex(ValueDiscoveryError, "financial assessment"):
            self.execute(provider=invalid_provider)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertEqual(ValueDiscoveryExecution.objects.using("app").count(), executions_before)


# The fixture base supplies the disposable tenant setup.  It also contains the
# Foundation matrix, which must not be silently re-executed as Step 11 tests.
for _name in dir(SourceArtifactPostgreSQLIntegrationTests):
    if _name.startswith("test") and _name not in ValueDiscoveryPostgreSQLTests.__dict__:
        setattr(ValueDiscoveryPostgreSQLTests, _name, None)
