import json
import os
import select
import signal
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.core.management import call_command
from django.db import connections
from django.db import DatabaseError
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from foundation.agent_runtime import (
    AgentCatalogCommandService,
    AgentRunCommandService,
)
from foundation.api_views import (
    ApprovalDecisionView,
    DomainEventPublishView,
    EvidenceCreateView,
    FoundationAttemptCreateView,
    OnboardingStatusView,
    RecommendationBasisView,
    RecommendationListView,
)
from foundation.eventing import FoundationCompletionConsumer
from foundation.foundation_gate import FoundationGateCommandService
from foundation.capabilities import (
    CapabilityInvocationService,
    CapabilityRegistry,
    SourceCapabilityCatalogService,
    source_capability_catalog,
)
from foundation.document_evidence import DocumentEvidenceCommandService
from foundation.audit import ImmutableAuditLog
from foundation.human_decision import AgentDecisionCommandService
from foundation.knowledge_layer import KnowledgeLayerCommandService
from foundation.models import (
    Approval,
    AgentDecision,
    Clause,
    ConceptMastery,
    ConsumerReceipt,
    DomainEvent,
    LearningPath,
    Organization,
    OnboardingTransition,
    OnboardingWorkflow,
    QuestionBank,
    QuizAttempt,
    Standard,
    StandardEdition,
    TenantProjection,
    TransactionalOutbox,
    UserProjection,
    RequirementControl,
    QmsAudit, Finding, QmsNonconformity, QmsCorrectiveAction,
)
from foundation.qms_audit import QmsAuditCommandService
from foundation.onboarding import (
    ONBOARDING_STEPS, OnboardingWorkflowError, OnboardingWorkflowService,
    OnboardingEvidenceIngestionService, OrganizationProfileCommandService,
)
from foundation.payment_boundary import HmacPaymentSigner, HmacPaymentVerifier, PaymentBoundaryError, PaymentVerificationService
from foundation.recommendation import RecommendationCommandService
from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context


class SourceArtifactPostgreSQLIntegrationTests(TransactionTestCase):
    databases = {
        "default", "app", "worker", "projector", "human_approver",
        "agent_catalog_curator", "normative_curator",
    }
    reset_sequences = False

    def _fixture_teardown(self):
        call_command("flush", verbosity=0, interactive=False, database="default")

    def setUp(self):
        with connections["default"].cursor() as cursor:
            cursor.execute("TRUNCATE governance.agent_definition CASCADE")
            cursor.execute(
                "TRUNCATE qms.concept_mastery, qms.quiz_attempt, "
                "qms.question_bank, qms.learning_path CASCADE"
            )
        self.now = timezone.now()
        self.tenant_id = uuid4()
        self.external_tenant_id = uuid4()
        self.other_external_tenant_id = uuid4()
        self.other_tenant_id = uuid4()
        self.actor_id = uuid4()
        self.other_actor_id = uuid4()
        self.user_projection_id = uuid4()
        self.other_user_projection_id = uuid4()
        self.organization_id = uuid4()
        self.trace_id = uuid4()

        TenantProjection.objects.using("default").create(
            id=self.tenant_id,
            adminapps_tenant_id=self.external_tenant_id,
            source_version=1,
            source_event_id=uuid4(),
            display_name_snapshot="WP1 integration tenant",
            lifecycle_status=TenantProjection.LifecycleStatus.ACTIVE,
            provisioning_status=TenantProjection.ProvisioningStatus.COMPLETE,
            reconciliation_status=TenantProjection.ReconciliationStatus.IN_SYNC,
            last_synced_at=self.now,
        )
        TenantProjection.objects.using("default").create(
            id=self.other_tenant_id,
            adminapps_tenant_id=self.other_external_tenant_id,
            source_version=1,
            source_event_id=uuid4(),
            display_name_snapshot="Other tenant",
            lifecycle_status=TenantProjection.LifecycleStatus.ACTIVE,
            provisioning_status=TenantProjection.ProvisioningStatus.COMPLETE,
            reconciliation_status=TenantProjection.ReconciliationStatus.IN_SYNC,
            last_synced_at=self.now,
        )
        UserProjection.objects.using("default").create(
            id=self.other_user_projection_id,
            adminapps_user_id=self.other_actor_id,
            tenant_id=self.other_tenant_id,
            source_version=1,
            source_event_id=uuid4(),
            lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
            last_synced_at=self.now,
        )
        UserProjection.objects.using("default").create(
            id=self.user_projection_id,
            adminapps_user_id=self.actor_id,
            tenant_id=self.tenant_id,
            source_version=1,
            source_event_id=uuid4(),
            lifecycle_status=UserProjection.LifecycleStatus.ACTIVE,
            last_synced_at=self.now,
        )
        Organization.objects.using("default").create(
            id=self.organization_id,
            tenant_id=self.tenant_id,
            display_name="WP1 test organization",
        )

        standard = Standard.objects.using("default").create(
            code=f"ISO 9000:2026 WP1 test {self.tenant_id}",
            title="Test standard identity",
            publisher="ISO",
        )
        self.edition = StandardEdition.objects.using("default").create(
            standard_id=standard.id,
            edition="2026",
            status=StandardEdition.Status.DRAFT,
            source_hash="a" * 64,
        )
        self.clause = Clause.objects.using("default").create(
            standard_edition_id=self.edition.id,
            code="4.1",
            title="Context fixture",
        )
        self.requirement = RequirementControl.objects.using("default").create(
            standard_edition_id=self.edition.id,
            clause_id=self.clause.id,
            paraphrase="Test paraphrase; no normative source text",
            applicability_rule={},
            control_type="test_fixture",
            valid_from=self.now,
        )
        stakeholder_clause = Clause.objects.using("default").create(
            standard_edition_id=self.edition.id, code="4.2", title="Stakeholder fixture",
        )
        scope_clause = Clause.objects.using("default").create(
            standard_edition_id=self.edition.id, code="4.3", title="Scope fixture",
        )
        self.stakeholder_requirement = RequirementControl.objects.using("default").create(
            standard_edition_id=self.edition.id, clause_id=stakeholder_clause.id,
            paraphrase="Synthetic stakeholder graph input, not normative content",
            applicability_rule={}, control_type="test_fixture", valid_from=self.now,
        )
        self.scope_requirement = RequirementControl.objects.using("default").create(
            standard_edition_id=self.edition.id, clause_id=scope_clause.id,
            paraphrase="Synthetic scope-link count input, not normative content",
            applicability_rule={}, control_type="test_fixture", valid_from=self.now,
        )
        process_clause = Clause.objects.using("default").create(
            standard_edition_id=self.edition.id, code="4.4.1", title="Process graph fixture",
        )
        self.process_graph_requirement = RequirementControl.objects.using("default").create(
            standard_edition_id=self.edition.id, clause_id=process_clause.id,
            paraphrase="Synthetic process graph input, not normative content",
            applicability_rule={}, control_type="test_fixture", valid_from=self.now,
        )
        self.edition.status = StandardEdition.Status.PUBLISHED
        self.edition.save(using="default", update_fields=("status",))

        curator_trace = uuid4()
        layer_service = KnowledgeLayerCommandService(using="normative_curator")
        self.layer_id = layer_service.create_knowledge_layer(
            standard_edition_id=self.edition.id,
            layer_type="quality_intelligence_test",
            actor_id="wp1-test-curator",
            trace_id=curator_trace,
        )
        self.rule_id = layer_service.create_knowledge_layer_rule(
            knowledge_layer_id=self.layer_id,
            rule_key="wp1.test.guidance",
            version="1",
            actor_id="wp1-test-curator",
            trace_id=curator_trace,
            logic_json={"kind": "test_fixture"},
            evidence_expectation={"source": "test"},
            source_reference="fixture://wp1",
        )
        layer_service.publish_knowledge_layer_rule(
            rule_id=self.rule_id,
            actor_id="wp1-test-curator",
            trace_id=curator_trace,
        )

        self.learning_path = LearningPath.objects.using("default").create(
            standard_edition_id=self.edition.id,
            role_code="quality_manager",
            industry_code="manufacturing",
            required_score=80,
            active=True,
            critical_concepts=["critical_fixture"],
        )
        self.question = QuestionBank.objects.using("default").create(
            learning_path_id=self.learning_path.id,
            concept_key="foundation_fixture",
            industry_code="manufacturing",
            difficulty=1,
            scenario="Choose the correct test answer.",
            options_json=[
                {"id": "yes", "label": "Yes"},
                {"id": "no", "label": "No"},
            ],
            answer_key={"option_ids": ["yes"]},
            explanation="This explanation is returned only after submission.",
            critical=False,
            publication_state=QuestionBank.PublicationState.PUBLISHED,
            version=1,
        )

        self.identity = TrustedTenantIdentity(
            subject=str(self.actor_id), tenant_id=self.tenant_id,
        )
        self.other_identity = TrustedTenantIdentity(
            subject=str(self.other_actor_id), tenant_id=self.other_tenant_id,
        )
        self.claims = {
            "organization_id": str(self.external_tenant_id),
            "user_id": str(self.actor_id),
            "role": "quality_manager",
            "industry_code": "manufacturing",
            "client_id": "wp1-contract-test",
            "scope": "domain:events:publish",
        }
        self.user = SimpleNamespace(is_authenticated=True, pk=self.actor_id)
        self.factory = APIRequestFactory()

    def _worker_process_env(self, configured_tenant_id):
        from postgres_foundation_gate import ROLE_SPECS

        role_options = " ".join(
            f"-c foundation.{key}_role={os.environ[f'FOUNDATION_{key.upper()}_ROLE']}"
            for key, *_ in ROLE_SPECS
        )
        env = os.environ.copy()
        env.update({
            "DJANGO_SETTINGS_MODULE": "backend.settings",
            "DJANGO_ENV": "production",
            "DEBUG": "False",
            "PYTHONUNBUFFERED": "1",
            "USE_SQLITE_DATABASE": "False",
            "SECRET_KEY": "disposable-postgresql-worker-test-only",
            "ALLOWED_HOSTS": "localhost,127.0.0.1",
            "DB_NAME": os.environ["FOUNDATION_DB_NAME"],
            "DB_HOST": os.environ.get("FOUNDATION_DB_HOST", "127.0.0.1"),
            "DB_PORT": os.environ["FOUNDATION_DB_PORT"],
            "DB_USER": os.environ["FOUNDATION_APP_ROLE"],
            "DB_PASSWORD": os.environ["FOUNDATION_APP_PASSWORD"],
            "DB_CONN_MAX_AGE": "0",
            "DB_SESSION_OPTIONS": role_options,
            "WORKER_TENANT_ID": str(configured_tenant_id),
            "INTERNAL_OUTBOX_WORKER_ENABLED": "True",
        })
        return env

    def _worker_command(self, tenant_id, *, once, worker_id, configured_tenant_id=None):
        backend_root = Path(__file__).resolve().parents[1]
        command = [
            sys.executable,
            "manage.py",
            "run_outbox_worker",
            "--tenant-id",
            str(tenant_id),
            "--worker-id",
            worker_id,
        ]
        if once:
            command.append("--once")
        return command, backend_root, self._worker_process_env(
            configured_tenant_id if configured_tenant_id is not None else tenant_id,
        )

    def _run_worker(self, tenant_id, *, once=True, worker_id=None, configured_tenant_id=None):
        command, backend_root, env = self._worker_command(
            tenant_id,
            once=once,
            worker_id=worker_id or f"e08-worker-{uuid4()}",
            configured_tenant_id=configured_tenant_id,
        )
        return subprocess.run(
            command,
            cwd=backend_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def _stop_polling_worker(self, shutdown_signal):
        command, backend_root, env = self._worker_command(
            self.tenant_id, once=False, worker_id=f"e08-signal-{uuid4()}",
        )
        process = subprocess.Popen(
            command,
            cwd=backend_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        try:
            deadline = time.monotonic() + 30
            started = False
            while time.monotonic() < deadline and process.poll() is None:
                ready, _, _ = select.select([process.stdout], [], [], 0.25)
                if ready and "outbox worker started" in process.stdout.readline():
                    started = True
                    break
            if not started:
                if process.poll() is None:
                    process.kill()
                stdout, stderr = process.communicate(timeout=10)
                self.fail(
                    "polling worker did not reach its started state: "
                    f"returncode={process.returncode}, stdout={stdout!r}, stderr={stderr!r}"
                )
            os.kill(process.pid, shutdown_signal)
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stdout + stderr)
            self.assertIsNotNone(process.poll(), "worker process remained alive after shutdown")
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)

    def invoke(self, view, method, path, data=None, *, auth_claims=None, **kwargs):
        if method == "get":
            request = self.factory.get(path, data or {})
        else:
            request = getattr(self.factory, method)(path, data, format="json")
        force_authenticate(request, user=self.user, token=auth_claims or self.claims)
        return view(request, **kwargs)

    def test_qms_audit_to_corrective_action_is_tenant_safe_and_evented(self):
        """The source-field-only QMS slice has no inferred workflow transitions."""
        evidence_response = self.invoke(EvidenceCreateView.as_view(), "post", "/v1/evidence", {
            "organization_id": str(self.organization_id), "source_type": "audit_fixture",
            "content_hash": "d" * 64, "captured_at": self.now.isoformat(),
        })
        self.assertEqual(evidence_response.status_code, 201)
        service = QmsAuditCommandService(using="app")
        audit = service.create_audit(identity=self.identity, organization_id=self.organization_id,
            scope="Production process", criteria="Internal program", status="planned",
            lead_auditor="Auditor fixture", actor_id=self.actor_id, trace_id=uuid4())
        finding = service.create_finding(identity=self.identity, audit_id=audit.entity_id,
            requirement_id=self.requirement.id, finding_type="nonconformity",
            statement="Controlled fixture finding", evidence_id=evidence_response.data["evidence_id"],
            actor_id=self.actor_id, trace_id=uuid4())
        nc = service.create_nonconformity_from_finding(identity=self.identity,
            finding_id=finding.entity_id, description="Controlled fixture NC", severity="major",
            status="detected", actor_id=self.actor_id, trace_id=uuid4())
        capa = service.create_corrective_action(identity=self.identity, nonconformity_id=nc.entity_id,
            cause_id=uuid4(), action="Perform source-backed fixture action", owner_id=self.actor_id,
            due_date=date.today(), actor_id=self.actor_id, trace_id=uuid4())
        self.assertIsNone(audit.event_id)
        # These models are tenant-RLS-protected: assertions must exercise the
        # same trusted context as a real application request.
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertEqual(DomainEvent.objects.using("app").get(event_id=finding.event_id).event_type,
                             "audit.finding.created")
            self.assertEqual(DomainEvent.objects.using("app").get(event_id=nc.event_id).event_type,
                             "nonconformity.detected")
            self.assertEqual(QmsCorrectiveAction.objects.using("app").get(pk=capa.entity_id).nonconformity_id, nc.entity_id)
            self.assertEqual(Finding.objects.using("app").get(pk=finding.entity_id).audit_id, audit.entity_id)
            self.assertEqual(QmsNonconformity.objects.using("app").get(pk=nc.entity_id).source_id, finding.entity_id)
            self.assertEqual(TransactionalOutbox.objects.using("app").filter(
                domain_event_id__in=(finding.event_id, nc.event_id)).count(), 2)
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(QmsAudit.objects.using("app").filter(pk=audit.entity_id).exists())
            self.assertFalse(Finding.objects.using("app").filter(pk=finding.entity_id).exists())
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            with self.assertRaises(DatabaseError):
                QmsAudit.objects.using("app").filter(pk=audit.entity_id).update(status="closed")

    def test_seven_api_contracts_persist_with_tenant_rls_and_outbox(self):
        from decimal import Decimal

        status = self.invoke(
            OnboardingStatusView.as_view(), "get", "/v1/onboarding/status",
        )
        self.assertEqual(status.status_code, 200)
        gate_status = status.data["foundation_gate"]
        self.assertEqual(gate_status["status"], "not_started")
        self.assertEqual(gate_status["paths"][0]["questions"][0]["id"], str(self.question.id))
        self.assertNotIn("answer_key", gate_status["paths"][0]["questions"][0])

        evidence_response = self.invoke(
            EvidenceCreateView.as_view(), "post", "/v1/evidence",
            {
                "organization_id": str(self.organization_id),
                "source_type": "integration_fixture",
                "content_hash": "c" * 64,
                "captured_at": self.now.isoformat(),
                "trust_score": "0.9500",
            },
        )
        self.assertEqual(evidence_response.status_code, 201)
        evidence_id = evidence_response.data["evidence_id"]
        self.assertTrue(evidence_response.data["event_id"])
        self.assertTrue(evidence_response.data["outbox_id"])
        self.assertTrue(evidence_response.data["audit_id"])

        recommendation = RecommendationCommandService(using="app").create_recommendation(
            identity=self.identity,
            organization_id=self.organization_id,
            title="Integration recommendation",
            body="Review the test control evidence.",
            confidence="0.9000",
            assumptions=["PostgreSQL integration fixture"],
            intended_autonomy=2,
            basis=[{
                "standard_edition_id": str(self.edition.id),
                "requirement_control_id": str(self.requirement.id),
                "knowledge_layer_rule_id": str(self.rule_id),
                "evidence_id": evidence_id,
                "rationale": "The fixture evidence supports this test recommendation.",
                "model_identifier": "wp1-test-model",
                "model_version": "1",
                "prompt_version": "1",
                "rule_bundle_version": "1",
            }],
            actor_id=self.actor_id,
            trace_id=uuid4(),
        )

        recommendations = self.invoke(
            RecommendationListView.as_view(), "get", "/v1/recommendations",
            {"clause": "4.1"},
        )
        self.assertEqual(recommendations.status_code, 200)
        self.assertEqual([row["id"] for row in recommendations.data["results"]], [str(recommendation.recommendation_id)])

        basis = self.invoke(
            RecommendationBasisView.as_view(), "get",
            f"/v1/recommendations/{recommendation.recommendation_id}/basis",
            recommendation_id=recommendation.recommendation_id,
        )
        self.assertEqual(basis.status_code, 200)
        self.assertEqual(basis.data["basis"][0]["evidence_id"], evidence_id)
        self.assertEqual(basis.data["basis"][0]["requirement_code"], "4.1")
        other_tenant_basis = self.invoke(
            RecommendationBasisView.as_view(), "get",
            f"/v1/recommendations/{recommendation.recommendation_id}/basis",
            recommendation_id=recommendation.recommendation_id,
            auth_claims={
                "organization_id": str(self.other_external_tenant_id),
                "user_id": str(self.other_actor_id),
                "role": "quality_manager",
            },
        )
        self.assertEqual(other_tenant_basis.status_code, 404)
        self.assertEqual(other_tenant_basis.data["code"], "NOT_FOUND")

        event_id = uuid4()
        event_aggregate_id = uuid4()
        event_trace_id = uuid4()
        event_request = {
            "event_id": str(event_id),
            "event_type": "context.signal.detected",
            "aggregate_type": "context_item",
            "aggregate_id": str(event_aggregate_id),
            "aggregate_version": 1,
            "occurred_at": self.now.isoformat(),
            "trace_id": str(event_trace_id),
            "payload": {"signal": "fixture_detected"},
        }
        event_response = self.invoke(
            DomainEventPublishView.as_view(), "post", "/v1/events",
            event_request,
        )
        self.assertEqual(event_response.status_code, 202)
        self.assertFalse(event_response.data["duplicate"])
        self.assertTrue(event_response.data["outbox_id"])
        replay_response = self.invoke(
            DomainEventPublishView.as_view(), "post", "/v1/events", event_request,
        )
        self.assertEqual(replay_response.status_code, 202)
        self.assertTrue(replay_response.data["duplicate"])
        from foundation.models import DomainEvent
        with trusted_tenant_context(
            self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app",
        ):
            saved_event = DomainEvent.objects.using("app").get(event_id=event_id)
            self.assertEqual((saved_event.tenant_id, saved_event.event_type,
                              saved_event.aggregate_type, saved_event.aggregate_id,
                              saved_event.payload, saved_event.occurred_at),
                             (self.tenant_id, "context.signal.detected", "context_item",
                              event_aggregate_id, {"signal": "fixture_detected"}, self.now))
        with trusted_tenant_context(
            self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app",
        ):
            self.assertFalse(DomainEvent.objects.using("app").filter(event_id=event_id).exists())

        catalog = AgentCatalogCommandService(using="agent_catalog_curator")
        policy_id = catalog.create_model_policy(
            policy_key="wp1-human-gate-test",
            version="1",
            approved_models=["wp1-test-model"],
            data_classes=["quality"],
            guardrails={"allowed_capabilities": ["quality.test"], "autonomy_max": 3},
            human_gate_rules={
                "always_required": True,
                "required_role": "quality_manager",
                "required_autonomy_levels": ["A3"],
            },
            actor_id="wp1-test-curator",
            trace_id=uuid4(),
        )
        catalog.publish_model_policy(
            model_policy_id=policy_id, actor_id="wp1-test-curator", trace_id=uuid4(),
        )
        definition_id = catalog.create_agent_definition(
            agent_key="wp1-quality-test",
            name="WP1 Quality Test Agent",
            version="1",
            purpose="Exercise the existing Human Decision Gate.",
            capability="quality.test",
            autonomy_max=3,
            model_policy_id=policy_id,
            actor_id="wp1-test-curator",
            trace_id=uuid4(),
        )
        catalog.publish_agent_definition(
            agent_definition_id=definition_id,
            actor_id="wp1-test-curator",
            trace_id=uuid4(),
        )
        agent_run = AgentRunCommandService(using="worker").start_agent_run(
            identity=self.identity,
            organization_id=self.organization_id,
            agent_definition_id=definition_id,
            model_policy_id=policy_id,
            capability="quality.test",
            requested_autonomy=3,
            model_provider="fixture",
            model_identifier="wp1-test-model",
            model_version="1",
            prompt_version="1",
            rule_bundle_version="1",
            inputs=[{
                "standard_edition_id": str(self.edition.id),
                "requirement_control_id": str(self.requirement.id),
                "knowledge_layer_rule_id": str(self.rule_id),
                "evidence_id": evidence_id,
            }],
            actor_id=self.actor_id,
            trace_id=uuid4(),
        )
        decision = AgentDecisionCommandService(using="worker").record_agent_decision(
            identity=self.identity,
            agent_run_id=agent_run.agent_run_id,
            decision_type="quality.test_decision",
            payload={"recommendation_id": str(recommendation.recommendation_id)},
            confidence="0.9000",
            explainability={"basis": "integration fixture"},
            decision_autonomy=3,
            actor_id=self.actor_id,
        )
        self.assertTrue(decision.human_gate_required)
        approval = self.invoke(
            ApprovalDecisionView.as_view(), "post",
            f"/v1/approvals/{decision.decision_id}/decision",
            {"decision": "approve", "comments": "Reviewed in isolated contract test."},
            decision_id=decision.decision_id,
        )
        self.assertEqual(approval.status_code, 200)
        self.assertEqual(approval.data["decision"], "approve")
        self.assertTrue(approval.data["outbox_id"])
        self.assertTrue(approval.data["audit_id"])
        with trusted_tenant_context(
            self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="worker",
        ):
            saved_decision = AgentDecision.objects.using("worker").get(id=decision.decision_id)
            decision_event = DomainEvent.objects.using("worker").get(
                aggregate_type="agent_decision", aggregate_id=decision.decision_id,
                event_type="agent_decision.recorded",
            )
            self.assertEqual((saved_decision.agent_run_id, saved_decision.decision_type,
                              saved_decision.payload, saved_decision.confidence,
                              saved_decision.explainability),
                             (agent_run.agent_run_id, "quality.test_decision",
                              {"recommendation_id": str(recommendation.recommendation_id)},
                              Decimal("0.9000"), {"basis": "integration fixture"}))
            self.assertEqual(decision_event.tenant_id, self.tenant_id)
        with trusted_tenant_context(
            self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="worker",
        ):
            self.assertFalse(AgentDecision.objects.using("worker").filter(id=decision.decision_id).exists())

        attempt = self.invoke(
            FoundationAttemptCreateView.as_view(), "post",
            "/v1/learning/iso9000/attempts",
            {
                "learning_path_id": str(self.learning_path.id),
                "answers": [{
                    "question_id": str(self.question.id),
                    "selected_option_ids": ["yes"],
                }],
            },
        )
        self.assertEqual(attempt.status_code, 201)
        self.assertTrue(attempt.data["passed"])
        self.assertEqual(attempt.data["score"], "100.00")
        self.assertEqual(attempt.data["question_bank_version"], 1)
        self.assertTrue(attempt.data["event_id"])
        self.assertTrue(attempt.data["outbox_id"])
        self.assertTrue(attempt.data["audit_id"])
        repeated_attempt = self.invoke(
            FoundationAttemptCreateView.as_view(), "post",
            "/v1/learning/iso9000/attempts",
            {
                "learning_path_id": str(self.learning_path.id),
                "answers": [{
                    "question_id": str(self.question.id),
                    "selected_option_ids": ["yes"],
                }],
            },
        )
        self.assertEqual(repeated_attempt.status_code, 201)
        self.assertTrue(repeated_attempt.data["passed"])
        self.assertIsNone(repeated_attempt.data["event_id"])

        with trusted_tenant_context(
            self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app",
        ):
            saved_attempt = QuizAttempt.objects.using("app").get(id=attempt.data["attempt_id"])
            self.assertTrue(saved_attempt.passed)
            self.assertEqual(saved_attempt.question_bank_version, 1)
            self.assertNotIn("answer_key", saved_attempt.answers[0])
            mastery = ConceptMastery.objects.using("app").get(
                tenant_id=self.tenant_id,
                user_id=self.user_projection_id,
                concept_key="foundation_fixture",
            )
            self.assertEqual(str(mastery.score), "100.00")
            self.assertIsNone(mastery.retraining_due_at)
            self.assertEqual(
                QuizAttempt.objects.using("app").filter(tenant_id=self.tenant_id).count(),
                2,
            )
            self.assertEqual(
                QuizAttempt.objects.using("app").filter(tenant_id=self.other_tenant_id).count(),
                0,
            )
            self.assertFalse(TenantProjection.objects.using("app").filter(
                id=self.other_tenant_id,
            ).exists())
            completion_event = DomainEvent.objects.using("app").get(
                event_id=attempt.data["event_id"],
                event_type="iso9000.foundation.completed",
            )
            self.assertEqual(completion_event.tenant_id, self.tenant_id)
            self.assertEqual(DomainEvent.objects.using("app").filter(
                tenant_id=self.tenant_id,
                event_type="iso9000.foundation.completed",
            ).count(), 1)
            outbox = TransactionalOutbox.objects.using("app").get(
                domain_event_id=completion_event.event_id,
            )
            self.assertEqual(outbox.status, TransactionalOutbox.Status.PENDING)
            self.assertTrue(ImmutableAuditLog.objects.using("app").filter(
                tenant_id=self.tenant_id,
                stream_type="foundation_gate_attempt",
                stream_id=saved_attempt.id,
            ).exists())

        completed_status = self.invoke(
            OnboardingStatusView.as_view(), "get", "/v1/onboarding/status",
        )
        self.assertEqual(completed_status.data["foundation_gate"]["status"], "passed")
        self.assertTrue(completed_status.data["foundation_gate"]["unlocks_quality_baseline"])

        approval_row = Approval.objects.using("default").get(id=approval.data["approval_id"])
        self.assertEqual(approval_row.agent_decision_id, decision.decision_id)
        with trusted_tenant_context(
            self.identity, actor_id=self.actor_id, trace_id=approval_row.trace_id,
            using="human_approver",
        ):
            saved_approval = Approval.objects.using("human_approver").get(id=approval_row.id)
            approval_event = DomainEvent.objects.using("human_approver").get(
                aggregate_type="approval", aggregate_id=approval_row.id,
                event_type="approval.recorded",
            )
            self.assertEqual((saved_approval.tenant_id, saved_approval.agent_decision_id,
                              saved_approval.required_role, saved_approval.decision,
                              saved_approval.decided_by_id, saved_approval.adminapps_user_id_snapshot,
                              saved_approval.actor_type, saved_approval.comments),
                             (self.tenant_id, decision.decision_id, "quality_manager", "approve",
                              self.user_projection_id, self.actor_id, "human",
                              "Reviewed in isolated contract test."))
            self.assertIsNotNone(saved_approval.decided_at)
            self.assertEqual(approval_event.tenant_id, self.tenant_id)
        with trusted_tenant_context(
            self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(),
            using="human_approver",
        ):
            self.assertFalse(Approval.objects.using("human_approver").filter(id=approval_row.id).exists())

    def test_foundation_completion_consumer_is_idempotent_and_tenant_scoped(self):
        from django.db import connections
        from foundation.canonical import canonical_hash
        from foundation.eventing import (
            ConsumerReceiptService,
            FoundationCompletionConsumer,
            FoundationCompletionDelivery,
            PayloadIntegrityConflict,
        )

        empty_queue = self._run_worker(self.tenant_id, worker_id="e08-worker-empty-queue")
        self.assertEqual(empty_queue.returncode, 0, empty_queue.stdout + empty_queue.stderr)
        self.assertIn("outbox worker stopped cleanly", empty_queue.stdout)
        wrong_tenant = self._run_worker(
            self.other_tenant_id,
            worker_id="e08-worker-reject-tenant",
            configured_tenant_id=self.tenant_id,
        )
        self.assertNotEqual(wrong_tenant.returncode, 0)
        self.assertIn("--tenant-id must match", wrong_tenant.stderr)

        result = FoundationGateCommandService(using="app").submit_attempt(
            identity=self.identity,
            user_projection_id=self.user_projection_id,
            learning_path_id=self.learning_path.id,
            answers=[{
                "question_id": str(self.question.id),
                "selected_option_ids": ["yes"],
            }],
            actor_id=self.actor_id,
            trace_id=self.trace_id,
            role_code="quality_manager",
            industry_code="manufacturing",
        )
        self.assertIsNotNone(result.event_id)
        delivery = FoundationCompletionDelivery()
        self.assertIsNone(delivery.deliver_next(identity=self.other_identity, worker_id="wp2-worker", trace_id=uuid4()))
        failed_run = self._run_worker(self.tenant_id, worker_id="e08-worker-failure")
        self.assertNotEqual(failed_run.returncode, 0, failed_run.stdout)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="worker"):
            failed = TransactionalOutbox.objects.using("worker").get(domain_event_id=result.event_id)
            self.assertEqual(failed.status, "failed")
            self.assertEqual(failed.publish_attempts, 1)
        with trusted_tenant_context(
            self.identity, actor_id=self.actor_id, trace_id=self.trace_id, using="app",
        ):
            event = DomainEvent.objects.using("app").get(event_id=result.event_id)
        workflow_service = OnboardingWorkflowService(using="app")
        for number, step in enumerate(("plan_selection", "account_registration", "billing_contact", "payment", "payment_verification", "subscription_activation", "tenant_provisioning", "security_setup"), 1):
            workflow_service.transition(
                identity=self.identity,
                user_id=self.user_projection_id,
                step_key=step,
                to_status="complete",
                event_id=uuid4(),
                event_type="test.onboarding.completed",
                source_reference=f"fixture:step:{number}",
                actor_id=self.actor_id,
                trace_id=self.trace_id,
            )
        consumer = FoundationCompletionConsumer(using="worker")
        retried_run = self._run_worker(self.tenant_id, worker_id="e08-worker-retry")
        self.assertEqual(retried_run.returncode, 0, retried_run.stdout + retried_run.stderr)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="worker"):
            delivered = TransactionalOutbox.objects.using("worker").get(domain_event_id=result.event_id)
            self.assertEqual(delivered.status, "published")
            self.assertEqual(delivered.publish_attempts, 2)
            self.assertIsNone(delivered.last_error_code)
        with self.assertRaises(PayloadIntegrityConflict):
            consumer.consume(identity=self.identity, event_id=event.event_id,
                             payload={**event.payload, "attempt_id": str(uuid4())},
                             actor_id=self.actor_id, trace_id=self.trace_id)
        duplicate = consumer.consume(
            identity=self.identity,
            event_id=event.event_id,
            payload=event.payload,
            actor_id=self.actor_id,
            trace_id=self.trace_id,
        )
        self.assertEqual(duplicate.kind.value, "idempotent_duplicate")
        with trusted_tenant_context(
            self.identity, actor_id=self.actor_id, trace_id=self.trace_id, using="worker",
        ):
            self.assertEqual(
                ConsumerReceipt.objects.using("worker").filter(
                    tenant_id=self.tenant_id,
                    consumer_name=consumer.consumer_name,
                    event_id=event.event_id,
                ).count(),
                1,
            )

        def seed_idempotent_event(version):
            event_id = uuid4()
            trace_id = uuid4()
            payload = {"attempt_id": str(uuid4())}
            with trusted_tenant_context(
                self.identity, actor_id=self.actor_id, trace_id=trace_id, using="app",
            ):
                DomainEvent.objects.using("app").create(
                    event_id=event_id,
                    tenant_id=self.tenant_id,
                    event_type="iso9000.foundation.completed",
                    schema_version=1,
                    aggregate_type="e08_worker_concurrency",
                    aggregate_id=self.organization_id,
                    aggregate_version=version,
                    occurred_at=timezone.now(),
                    trace_id=trace_id,
                    source="e08-postgresql-process-test",
                    payload=payload,
                    payload_hash=canonical_hash(payload),
                )
                TransactionalOutbox.objects.using("app").create(
                    tenant_id=self.tenant_id,
                    domain_event_id=event_id,
                    status=TransactionalOutbox.Status.PENDING,
                    publish_attempts=0,
                    available_at=timezone.now(),
                )
            ConsumerReceiptService(using="worker").receive(
                identity=self.identity,
                consumer_name=FoundationCompletionConsumer.consumer_name,
                event_id=event_id,
                payload=payload,
                trace_id=trace_id,
                handler=lambda _: None,
            )
            return event_id

        concurrent_events = [seed_idempotent_event(1), seed_idempotent_event(2)]
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "CREATE TABLE eventing.e08_worker_claim_window ("
                "id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY, "
                "started_at timestamptz NOT NULL, finished_at timestamptz)"
            )
            cursor.execute(
                """
                CREATE FUNCTION eventing.e08_delay_worker_claim()
                RETURNS trigger
                LANGUAGE plpgsql
                SECURITY DEFINER
                SET search_path = pg_catalog,eventing
                AS $function$
                DECLARE marker_id bigint;
                BEGIN
                    IF NEW.status = 'processing' AND OLD.status IS DISTINCT FROM NEW.status THEN
                        INSERT INTO eventing.e08_worker_claim_window(started_at)
                        VALUES (clock_timestamp()) RETURNING id INTO marker_id;
                        PERFORM pg_sleep(3);
                        UPDATE eventing.e08_worker_claim_window
                        SET finished_at = clock_timestamp()
                        WHERE id = marker_id;
                    END IF;
                    RETURN NEW;
                END;
                $function$
                """
            )
            cursor.execute(
                "CREATE TRIGGER e08_delay_worker_claim "
                "BEFORE UPDATE OF status ON eventing.transactional_outbox "
                "FOR EACH ROW WHEN (NEW.status = 'processing') "
                "EXECUTE FUNCTION eventing.e08_delay_worker_claim()"
            )

        concurrent_processes = []
        try:
            for worker_id in ("e08-concurrent-worker-a", "e08-concurrent-worker-b"):
                command, backend_root, env = self._worker_command(
                    self.tenant_id, once=True, worker_id=worker_id,
                )
                if concurrent_processes:
                    time.sleep(0.1)
                concurrent_processes.append(subprocess.Popen(
                    command,
                    cwd=backend_root,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                ))
            self.assertTrue(all(process.poll() is None for process in concurrent_processes))
            concurrency_output = [
                process.communicate(timeout=30) for process in concurrent_processes
            ]
            self.assertTrue(
                all(process.returncode == 0 for process in concurrent_processes),
                repr(concurrency_output),
            )
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT count(*)
                    FROM eventing.e08_worker_claim_window first
                    JOIN eventing.e08_worker_claim_window second
                      ON first.id < second.id
                     AND first.started_at < second.finished_at
                     AND second.started_at < first.finished_at
                    """
                )
                self.assertEqual(cursor.fetchone()[0], 1)
            with trusted_tenant_context(
                self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="worker",
            ):
                rows = list(
                    TransactionalOutbox.objects.using("worker")
                    .filter(domain_event_id__in=concurrent_events)
                    .order_by("domain_event_id")
                    .values_list("status", "publish_attempts")
                )
                receipts = ConsumerReceipt.objects.using("worker").filter(
                    event_id__in=concurrent_events,
                    consumer_name=FoundationCompletionConsumer.consumer_name,
                    status=ConsumerReceipt.Status.PROCESSED,
                    attempts=1,
                ).count()
                worker_role = os.environ["FOUNDATION_WORKER_ROLE"]
            self.assertEqual(rows, [
                (TransactionalOutbox.Status.PUBLISHED, 1),
                (TransactionalOutbox.Status.PUBLISHED, 1),
            ])
            self.assertEqual(receipts, 2)
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    "SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s",
                    [worker_role],
                )
                self.assertEqual(cursor.fetchone(), (False, False))
        finally:
            for process in concurrent_processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=10)
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    "DROP TRIGGER IF EXISTS e08_delay_worker_claim "
                    "ON eventing.transactional_outbox"
                )
                cursor.execute("DROP FUNCTION IF EXISTS eventing.e08_delay_worker_claim()")
                cursor.execute("DROP TABLE IF EXISTS eventing.e08_worker_claim_window")

        self._stop_polling_worker(signal.SIGTERM)
        self._stop_polling_worker(signal.SIGINT)

        with trusted_tenant_context(
            self.identity, actor_id=self.actor_id, trace_id=self.trace_id, using="app",
        ):
            workflow = OnboardingWorkflow.objects.using("app").get(
                tenant_id=self.tenant_id, user_id=self.user_projection_id,
            )
            workflow.refresh_from_db(using="app")
            self.assertIn("foundation_gate", workflow.completed_steps)
            self.assertEqual(
                OnboardingTransition.objects.using("app").filter(
                    workflow_id=workflow.id, step_key="foundation_gate",
                ).count(),
                1,
            )
        with self.assertRaises(OnboardingWorkflowError):
            workflow_service.transition(
                identity=self.identity,
                user_id=self.user_projection_id,
                step_key="security_setup",
                to_status="in_progress",
                event_id=uuid4(),
                event_type="test.invalid",
                source_reference="fixture:invalid",
                actor_id=self.actor_id,
                trace_id=self.trace_id,
            )
        status = self.invoke(OnboardingStatusView.as_view(), "get", "/v1/onboarding/status")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.data["step_count"], 17)
        self.assertEqual(status.data["steps"][8]["status"], "COMPLETE")

    def test_registered_capability_executes_through_adapter_to_evidence_basis(self):
        evidence = DocumentEvidenceCommandService(using="app").create_evidence(
            identity=self.identity,
            organization_id=self.organization_id,
            source_type="capability_fixture",
            source_uri="fixture://capability/input",
            content_hash="d" * 64,
            captured_at=self.now,
            actor_id=self.actor_id,
            trace_id=self.trace_id,
        )
        catalog = AgentCatalogCommandService(using="agent_catalog_curator")
        policy_id = catalog.create_model_policy(
            policy_key="wp2-capability-policy", version="1",
            approved_models=["wp2-fixture-model"], data_classes=["quality"],
            guardrails={"allowed_capabilities": ["quality.context_assessment"], "autonomy_max": 2},
            human_gate_rules={}, actor_id="wp2-curator", trace_id=uuid4(),
        )
        catalog.publish_model_policy(model_policy_id=policy_id, actor_id="wp2-curator", trace_id=uuid4())
        definition_id = catalog.create_agent_definition(
            agent_key="wp2-context", name="WP2 Context Agent", version="1",
            purpose="Assess a synthetic context requirement.", capability="quality.context_assessment",
            autonomy_max=2, model_policy_id=policy_id, actor_id="wp2-curator", trace_id=uuid4(),
        )
        catalog.publish_agent_definition(agent_definition_id=definition_id, actor_id="wp2-curator", trace_id=uuid4())
        invocation_service = CapabilityInvocationService(using="worker")
        invocation_service.registry.activate(
            identity=self.identity,
            capability="quality.context_assessment",
            actor_id=self.actor_id,
            trace_id=uuid4(),
        )

        input_row = {
            "standard_edition_id": str(self.edition.id),
            "requirement_control_id": str(self.requirement.id),
            "knowledge_layer_rule_id": str(self.rule_id),
            "evidence_id": str(evidence.entity_id),
            "rationale": "The fixture evidence supports this capability result.",
        }

        class FixtureAdapter:
            def execute(self, *, capability, inputs):
                return {
                    "title": "Context assessment",
                    "body": "Synthetic assessment backed by the exact fixture evidence.",
                    "confidence": "0.9000",
                    "assumptions": ["synthetic fixture"],
                    "basis": [input_row],
                }

        result = invocation_service.invoke(
            identity=self.identity, organization_id=self.organization_id,
            capability="quality.context_assessment", model_policy_id=policy_id,
            requested_autonomy=2, model_provider="fixture",
            model_identifier="wp2-fixture-model", model_version="1",
            prompt_version="1", rule_bundle_version="1", inputs=[input_row],
            actor_id=self.actor_id, trace_id=uuid4(), adapter=FixtureAdapter(),
        )
        self.assertTrue(result.agent_run_id)
        self.assertTrue(result.recommendation_id)
        self.assertTrue(result.event_id)
        self.assertTrue(result.outbox_id)
        self.assertTrue(result.audit_id)
        workflow_service = OnboardingWorkflowService(using="app")
        for step in ONBOARDING_STEPS[:15]:
            workflow_service.transition(
                identity=self.identity,
                user_id=self.user_projection_id,
                step_key=step.key,
                to_status="complete",
                event_id=uuid4(),
                event_type="test.onboarding.completed",
                source_reference=f"fixture:{step.key}",
                actor_id=self.actor_id,
                trace_id=uuid4(),
            )
        status = self.invoke(OnboardingStatusView.as_view(), "get", "/v1/onboarding/status")
        self.assertEqual(status.data["steps"][15]["status"], "AVAILABLE")

    def test_source_catalog_registers_all_thirty_three_capabilities(self):
        catalog_rows = source_capability_catalog()
        self.assertEqual(len(catalog_rows), 33)
        catalog = AgentCatalogCommandService(using="agent_catalog_curator")
        policy_id = catalog.create_model_policy(
            policy_key=f"wp2-source-catalog-{self.tenant_id}", version="1",
            approved_models=["wp2-source-model"], data_classes=["quality"],
            guardrails={
                "allowed_capabilities": [row["capability"] for row in catalog_rows],
                "autonomy_max": 4,
            },
            human_gate_rules={}, actor_id="wp2-curator", trace_id=uuid4(),
        )
        catalog.publish_model_policy(model_policy_id=policy_id, actor_id="wp2-curator", trace_id=uuid4())
        definition_ids = SourceCapabilityCatalogService(using="agent_catalog_curator").register(
            model_policy_id=policy_id, actor_id="wp2-curator", trace_id=uuid4(),
        )
        self.assertEqual(len(definition_ids), 33)
        registry = CapabilityRegistry(using="agent_catalog_curator")
        self.assertTrue(all(registry.get_available(capability=row["capability"]) for row in catalog_rows))

    def test_agent_run_recommendation_persists_source_fields_and_run_link(self):
        from decimal import Decimal
        from foundation.models import (
            AgentCatalogCurationAudit, AgentDefinition, AgentRunRecommendation,
            Recommendation, RecommendationBasis,
        )

        catalog = AgentCatalogCommandService(using="agent_catalog_curator")
        policy_id = catalog.create_model_policy(
            policy_key=f"recommendation-contract-{self.tenant_id}", version="1",
            approved_models=["deterministic"], data_classes=["synthetic_test"],
            guardrails={"allowed_capabilities": ["quality.recommendation_test"], "autonomy_max": 2},
            human_gate_rules={}, actor_id="synthetic-curator", trace_id=uuid4(),
        )
        catalog.publish_model_policy(
            model_policy_id=policy_id, actor_id="synthetic-curator", trace_id=uuid4(),
        )
        definition_id = catalog.create_agent_definition(
            agent_key=f"recommendation-contract-{self.tenant_id}",
            name="Synthetic recommendation test", version="1",
            purpose="Exercise source Recommendation fields only.",
            capability="quality.recommendation_test", autonomy_max=2,
            model_policy_id=policy_id, actor_id="synthetic-curator", trace_id=uuid4(),
        )
        catalog.publish_agent_definition(
            agent_definition_id=definition_id, actor_id="synthetic-curator", trace_id=uuid4(),
        )
        definition = AgentDefinition.objects.using("agent_catalog_curator").get(id=definition_id)
        self.assertEqual((definition.agent_key, definition.name, definition.purpose,
                          definition.model_policy_id, definition.autonomy_max),
                         (f"recommendation-contract-{self.tenant_id}",
                          "Synthetic recommendation test",
                          "Exercise source Recommendation fields only.", policy_id, 2))
        self.assertTrue(AgentCatalogCurationAudit.objects.using("agent_catalog_curator").filter(
            entity_type="agent_definition", entity_id=definition_id,
            action="agent_definition.published",
        ).exists())
        evidence = DocumentEvidenceCommandService(using="app").create_evidence(
            identity=self.identity, organization_id=self.organization_id,
            source_type="synthetic_fixture", source_uri="fixture://recommendation/1",
            content_hash="c" * 64, captured_at=self.now, actor_id=self.actor_id, trace_id=uuid4(),
        )
        runtime = AgentRunCommandService(using="worker")
        run_trace_id = uuid4()
        run = runtime.start_agent_run(
            identity=self.identity, organization_id=self.organization_id,
            agent_definition_id=definition_id, model_policy_id=policy_id,
            capability="quality.recommendation_test", requested_autonomy=2,
            model_provider="repository", model_identifier="deterministic",
            model_version="1", prompt_version="synthetic-1", rule_bundle_version="synthetic-1",
            inputs=[{
                "standard_edition_id": str(self.edition.id),
                "requirement_control_id": str(self.requirement.id),
                "knowledge_layer_rule_id": str(self.rule_id),
                "evidence_id": str(evidence.entity_id),
            }],
            actor_id=self.actor_id, trace_id=run_trace_id,
        )
        completed = runtime.complete_agent_run_with_recommendation(
            identity=self.identity, agent_run_id=run.agent_run_id,
            title="Synthetic title", body="Synthetic advisory body.",
            confidence="0.6250", assumptions=["Synthetic assumption"],
            impact="Synthetic impact", basis=[{
                "standard_edition_id": str(self.edition.id),
                "requirement_control_id": str(self.requirement.id),
                "knowledge_layer_rule_id": str(self.rule_id),
                "evidence_id": str(evidence.entity_id),
                "rationale": "Synthetic test provenance.",
            }], actor_id=self.actor_id,
        )
        from foundation.models import AgentRun, DomainEvent
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="worker"):
            run_row = AgentRun.objects.using("worker").get(id=run.agent_run_id)
            run_events = list(DomainEvent.objects.using("worker").filter(
                aggregate_type="agent_run", aggregate_id=run.agent_run_id,
            ).order_by("aggregate_version"))
            self.assertEqual((run_row.tenant_id, run_row.agent_definition_id,
                              run_row.model_version, run_row.prompt_version,
                              run_row.started_at, run_row.completed_at, run_row.trace_id,
                              run_row.status),
                             (self.tenant_id, definition_id, "1", "synthetic-1",
                              run_row.started_at, run_row.completed_at, run_trace_id,
                              AgentRun.Status.COMPLETED))
            self.assertIsNotNone(run_row.completed_at)
            self.assertGreaterEqual(run_row.completed_at, run_row.started_at)
            self.assertEqual([(event.event_type, event.event_id) for event in run_events], [
                ("agent_run.started", run.event_id), ("agent_run.completed", completed.event_id),
            ])
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            recommendation = Recommendation.objects.using("app").get(id=completed.recommendation_id)
            link = AgentRunRecommendation.objects.using("app").get(id=completed.link_id)
            basis = RecommendationBasis.objects.using("app").get(
                recommendation_id=completed.recommendation_id,
            )
            self.assertEqual((recommendation.tenant_id, recommendation.title, recommendation.body,
                              recommendation.confidence, recommendation.impact, recommendation.status),
                             (self.tenant_id, "Synthetic title", "Synthetic advisory body.",
                              Decimal("0.6250"), "Synthetic impact", Recommendation.Status.PROPOSED))
            self.assertEqual(recommendation.assumptions, ["Synthetic assumption"])
            self.assertEqual((link.agent_run_id, link.recommendation_id),
                             (run.agent_run_id, completed.recommendation_id))
            self.assertEqual((basis.recommendation_id, basis.requirement_control_id,
                              basis.knowledge_layer_rule_id, basis.evidence_id, basis.rationale),
                             (completed.recommendation_id, self.requirement.id, self.rule_id,
                              evidence.entity_id, "Synthetic test provenance."))
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(Recommendation.objects.using("app").filter(id=completed.recommendation_id).exists())
            self.assertFalse(AgentRunRecommendation.objects.using("app").filter(id=completed.link_id).exists())
            self.assertFalse(RecommendationBasis.objects.using("app").filter(
                recommendation_id=completed.recommendation_id,
            ).exists())
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="worker"):
            self.assertFalse(AgentRun.objects.using("worker").filter(id=run.agent_run_id).exists())
            self.assertFalse(DomainEvent.objects.using("worker").filter(
                aggregate_type="agent_run", aggregate_id=run.agent_run_id,
            ).exists())

    def test_source_autonomy_policy_dispatch_persists_gate_provenance_and_rls(self):
        from foundation.models import AgentRun, RecommendationBasis
        from foundation.agent_execution_contract import ExecutionStatus
        capability = "source.autonomy_policy_engine"
        catalog = AgentCatalogCommandService()
        policy_id = catalog.create_model_policy(
            policy_key=f"autonomy-{self.tenant_id}", version="1", approved_models=["deterministic"],
            data_classes=["quality"], guardrails={"allowed_capabilities": [capability, "source.stakeholder_intelligence_agent"], "autonomy_max": 4},
            human_gate_rules={}, actor_id="curator", trace_id=uuid4(),
        )
        catalog.publish_model_policy(model_policy_id=policy_id, actor_id="curator", trace_id=uuid4())
        SourceCapabilityCatalogService().register(model_policy_id=policy_id, actor_id="curator", trace_id=uuid4())
        service = CapabilityInvocationService()
        service.registry.activate(identity=self.identity, capability=capability, actor_id=self.actor_id, trace_id=uuid4())
        evidence = DocumentEvidenceCommandService().create_evidence(
            identity=self.identity, organization_id=self.organization_id, source_type="controlled_test",
            source_uri="fixture://policy-input", content_hash="d" * 64,
            captured_at=self.now, actor_id=self.actor_id, trace_id=uuid4(),
        )
        arguments = dict(
            identity=self.identity, organization_id=self.organization_id, capability=capability,
            model_policy_id=policy_id, model_provider="repository", model_identifier="deterministic",
            model_version="1", prompt_version="none", rule_bundle_version="existing-policy-v1",
            inputs=[{"standard_edition_id": str(self.edition.id), "requirement_control_id": str(self.requirement.id),
                     "knowledge_layer_rule_id": str(self.rule_id), "evidence_id": str(evidence.entity_id),
                     "rationale": "Controlled fixture for runtime policy verification, not ISO compliance."}],
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        for level in range(5):
            result = service.invoke_source(**arguments, requested_autonomy=level)
            self.assertEqual(result.status, ExecutionStatus.COMPLETED)
            self.assertEqual(result.deterministic_rule_results[0]["human_gate_required"], str(level == 3).lower())
            self.assertEqual(result.deterministic_rule_results[0]["execution_authorized"], "false")
            with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
                self.assertEqual(AgentRun.objects.using("app").get(id=result.run_id).status, "completed")
                decision = AgentDecision.objects.using("app").get(id=result.deterministic_rule_results[0]["decision_id"])
                self.assertEqual(decision.human_gate_required, level == 3)
                self.assertTrue(RecommendationBasis.objects.using("app").filter(
                    recommendation_id=result.recommendations[0], evidence_id=evidence.entity_id,
                    requirement_control_id=self.requirement.id,
                ).exists())
            with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
                self.assertFalse(AgentRun.objects.using("app").filter(id=result.run_id).exists())
                self.assertFalse(AgentDecision.objects.using("app").filter(id=decision.id).exists())
        with self.assertRaises(ValueError):
            service.invoke_source(**arguments, requested_autonomy=-1)
        with self.assertRaises(PermissionError):
            service.invoke_source(**{**arguments, "capability": "source.context_twin_orchestrator"}, requested_autonomy=2)
        with self.assertRaises(PermissionError):
            service.invoke_source(**{**arguments, "identity": self.other_identity}, requested_autonomy=2)
        with self.assertRaises(ValueError):
            service.invoke_source(**{**arguments, "inputs": []}, requested_autonomy=2)

        from foundation.models import Stakeholder
        stakeholder_capability = "source.stakeholder_intelligence_agent"
        service.registry.activate(identity=self.identity, capability=stakeholder_capability,
                                  actor_id=self.actor_id, trace_id=uuid4())
        stakeholder_arguments = {**arguments, "capability": stakeholder_capability, "requested_autonomy": 2}
        with self.assertRaisesRegex(ValueError, "outside the source agent binding"):
            service.invoke_source(**stakeholder_arguments)
        stakeholder_arguments["inputs"] = [{**arguments["inputs"][0],
            "requirement_control_id": str(self.stakeholder_requirement.id)}]
        with self.assertRaisesRegex(ValueError, "no organization-scoped"):
            service.invoke_source(**stakeholder_arguments)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertTrue(AgentRun.objects.using("app").filter(capability=stakeholder_capability, status="failed").exists())
        for name, kind in (("Customer", "cliente"), ("Supplier", "proveedor")):
            Stakeholder.objects.using("default").create(tenant_id=self.tenant_id, organization_id=self.organization_id,
                                                       name=name, stakeholder_type=kind)
        other_org = Organization.objects.using("default").create(tenant_id=self.other_tenant_id, display_name="Other")
        foreign = Stakeholder.objects.using("default").create(tenant_id=self.other_tenant_id,
            organization_id=other_org.id, name="Excluded stakeholder", stakeholder_type="cliente")
        result = service.invoke_source(**stakeholder_arguments)
        self.assertEqual(result.findings[0].summary, "2 stakeholders; 2 inferred relationships")
        self.assertNotIn(str(foreign.id), result.deterministic_rule_results[0]["input_snapshot"])
        self.assertTrue(result.provenance["stakeholder_snapshot_hash"])
        self.assertEqual(len(json.loads(result.deterministic_rule_results[0]["metrics"])["value"]), 2)
        with self.assertRaises(PermissionError):
            service.invoke_source(**{**stakeholder_arguments, "requested_autonomy": 4})

    def test_context_twin_metadata_adapter_is_deterministic_tenant_scoped_and_side_effect_free(self):
        from foundation.agent_execution_contract import ExecutionStatus
        from foundation.models import (
            AgentRun, AgentRunRecommendation, DomainEvent, Evidence,
            EvidenceCoverage, ImmutableAuditLog, Opportunity, Recommendation,
            RecommendationBasis, Risk, TransactionalOutbox,
        )

        capability = "source.context_twin_orchestrator"
        catalog = AgentCatalogCommandService()
        policy_id = catalog.create_model_policy(
            policy_key=f"context-twin-{self.tenant_id}", version="1",
            approved_models=["deterministic"], data_classes=["evidence_metadata"],
            guardrails={"allowed_capabilities": [capability], "autonomy_max": 4},
            human_gate_rules={}, actor_id="curator", trace_id=uuid4(),
        )
        catalog.publish_model_policy(model_policy_id=policy_id, actor_id="curator", trace_id=uuid4())
        SourceCapabilityCatalogService().register(
            model_policy_id=policy_id, actor_id="curator", trace_id=uuid4(),
        )
        service = CapabilityInvocationService()
        service.registry.activate(
            identity=self.identity, capability=capability,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        evidence_service = DocumentEvidenceCommandService(using="app")
        original = evidence_service.create_evidence(
            identity=self.identity, organization_id=self.organization_id,
            source_type="metadata", source_uri="fixture://cloud-ciberseguridad",
            content_hash="d" * 64, captured_at=self.now,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        arguments = {
            "identity": self.identity, "organization_id": self.organization_id,
            "capability": capability, "model_policy_id": policy_id,
            "requested_autonomy": 2, "model_provider": "repository",
            "model_identifier": "deterministic", "model_version": "1",
            "prompt_version": "none", "rule_bundle_version": "metadata-v1",
            "inputs": [{
                "standard_edition_id": str(self.edition.id),
                "requirement_control_id": str(self.requirement.id),
                "knowledge_layer_rule_id": str(self.rule_id),
                "evidence_id": str(original.entity_id),
            }],
            "actor_id": self.actor_id, "trace_id": uuid4(),
        }
        tracked_models = (
            Recommendation, RecommendationBasis, AgentRunRecommendation,
            Risk, Opportunity, EvidenceCoverage,
        )
        before = {model: model.objects.using("default").count() for model in tracked_models}

        first = service.invoke_source(**arguments)
        second = service.invoke_source(**{**arguments, "trace_id": uuid4()})
        self.assertEqual(first.status, ExecutionStatus.COMPLETED)
        self.assertEqual(first.result_scope, "heuristic_metadata_analysis_only")
        self.assertTrue(first.not_normative_assessment)
        self.assertEqual(first.semantic_result, second.semantic_result)
        self.assertEqual(first.provenance["input_snapshot"], second.provenance["input_snapshot"])
        self.assertEqual(first.provenance["input_snapshot_hash"], second.provenance["input_snapshot_hash"])
        snapshot = json.loads(first.provenance["input_snapshot"])["value"]
        self.assertEqual(set(snapshot["evidence"][0]), {
            "evidence_id", "lineage_id", "revision", "source_type", "source_uri",
        })
        self.assertEqual(snapshot["evidence"][0]["source_uri"], "fixture://cloud-ciberseguridad")
        self.assertEqual(first.semantic_result["digital_metadata_keywords"], ["cloud", "ciberseguridad"])

        completion_event = DomainEvent.objects.using("default").get(event_id=first.emitted_events[0])
        persisted_result = completion_event.payload["execution_result"]
        self.assertEqual(persisted_result["result_scope"], "heuristic_metadata_analysis_only")
        self.assertTrue(persisted_result["not_normative_assessment"])
        self.assertEqual(
            persisted_result["provenance"]["input_snapshot_hash"],
            first.provenance["input_snapshot_hash"],
        )
        self.assertTrue(TransactionalOutbox.objects.using("default").filter(
            domain_event_id=completion_event.event_id,
        ).exists())
        self.assertTrue(ImmutableAuditLog.objects.using("default").filter(
            stream_id=first.run_id, action="agent_run.completed",
        ).exists())
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            first_run = AgentRun.objects.using("app").get(id=first.run_id)
            self.assertEqual(first_run.status, AgentRun.Status.COMPLETED)
            self.assertFalse(AgentRunRecommendation.objects.using("app").filter(agent_run_id=first.run_id).exists())
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(AgentRun.objects.using("app").filter(id=first.run_id).exists())

        revised = evidence_service.supersede_evidence(
            identity=self.identity, evidence_id=original.entity_id,
            source_type="metadata", source_uri="fixture://emisiones",
            content_hash="e" * 64, captured_at=self.now,
            actor_id=self.actor_id, trace_id=uuid4(), change_reason="Changed consumed metadata fixture",
        )
        changed_arguments = {
            **arguments,
            "inputs": [{**arguments["inputs"][0], "evidence_id": str(revised.entity_id)}],
        }
        changed = service.invoke_source(**changed_arguments)
        self.assertNotEqual(first.provenance["input_snapshot_hash"], changed.provenance["input_snapshot_hash"])
        self.assertEqual(
            json.loads(changed.provenance["input_snapshot"])["value"]["evidence"][0]["source_uri"],
            "fixture://emisiones",
        )
        self.assertEqual(changed.semantic_result["esg_metadata_keywords"], ["emisiones"])

        runs_before_invalid = AgentRun.objects.using("default").filter(capability=capability).count()
        missing_arguments = {
            **arguments,
            "inputs": [{**arguments["inputs"][0], "evidence_id": str(uuid4())}],
        }
        with self.assertRaises(Evidence.DoesNotExist):
            service.invoke_source(**missing_arguments)
        other_organization = Organization.objects.using("default").create(
            tenant_id=self.other_tenant_id, display_name="Context isolation fixture",
        )
        foreign_evidence = evidence_service.create_evidence(
            identity=self.other_identity, organization_id=other_organization.id,
            source_type="metadata", source_uri="fixture://cloud",
            content_hash="f" * 64, captured_at=self.now,
            actor_id=self.other_actor_id, trace_id=uuid4(),
        )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="worker"):
            self.assertFalse(Evidence.objects.using("worker").filter(id=foreign_evidence.entity_id).exists())
        foreign_arguments = {
            **arguments,
            "inputs": [{**arguments["inputs"][0], "evidence_id": str(foreign_evidence.entity_id)}],
        }
        with self.assertRaises(Evidence.DoesNotExist):
            service.invoke_source(**foreign_arguments)
        self.assertEqual(
            AgentRun.objects.using("default").filter(capability=capability).count(),
            runs_before_invalid,
        )

        with patch(
            "ai_modules.sca.services.internal_context_metadata.analyze_internal_factors",
            side_effect=RuntimeError("controlled analyzer failure"),
        ), self.assertRaisesRegex(RuntimeError, "controlled analyzer failure"):
            service.invoke_source(**arguments)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            failed_run = AgentRun.objects.using("app").filter(
                capability=capability, status=AgentRun.Status.FAILED,
            ).latest("started_at")
            failed_event = DomainEvent.objects.using("app").get(
                aggregate_type="agent_run", aggregate_id=failed_run.id,
                event_type="agent_run.failed",
            )
            self.assertEqual(failed_event.payload["failure"]["code"], "source_adapter_failed")
            self.assertFalse(DomainEvent.objects.using("app").filter(
                aggregate_type="agent_run", aggregate_id=failed_run.id,
                event_type="agent_run.completed",
            ).exists())
            self.assertFalse(AgentRunRecommendation.objects.using("app").filter(
                agent_run_id=failed_run.id,
            ).exists())
            self.assertTrue(TransactionalOutbox.objects.using("app").filter(
                domain_event_id=failed_event.event_id,
            ).exists())
            self.assertTrue(ImmutableAuditLog.objects.using("app").filter(
                stream_id=failed_run.id, action="agent_run.failed",
            ).exists())

        self.assertEqual(
            {model: model.objects.using("default").count() for model in tracked_models},
            before,
        )

    def test_scope_assurance_adapter_counts_only_tenant_scoped_process_links(self):
        from foundation.agent_execution_contract import ExecutionStatus
        from foundation.models import (
            AgentRun, AgentRunRecommendation, DomainEvent, ImmutableAuditLog,
            QmsScope, TransactionalOutbox,
        )
        from foundation.qms_context import QmsContextCommandService

        capability = "source.scope_assurance_agent"
        catalog = AgentCatalogCommandService()
        policy_id = catalog.create_model_policy(
            policy_key=f"scope-assurance-{self.tenant_id}", version="1",
            approved_models=["deterministic"], data_classes=["qms_scope_metadata"],
            guardrails={"allowed_capabilities": [capability], "autonomy_max": 4},
            human_gate_rules={}, actor_id="curator", trace_id=uuid4(),
        )
        catalog.publish_model_policy(model_policy_id=policy_id, actor_id="curator", trace_id=uuid4())
        SourceCapabilityCatalogService().register(
            model_policy_id=policy_id, actor_id="curator", trace_id=uuid4(),
        )
        service = CapabilityInvocationService()
        service.registry.activate(
            identity=self.identity, capability=capability,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        qms = QmsContextCommandService(using="app")
        first_process = qms.create_process(
            identity=self.identity, organization_id=self.organization_id,
            name="Assembly", actor_id=self.actor_id, trace_id=uuid4(),
        )
        second_process = qms.create_process(
            identity=self.identity, organization_id=self.organization_id,
            name="Quality review", actor_id=self.actor_id, trace_id=uuid4(),
        )
        scope = qms.create_scope(
            identity=self.identity, organization_id=self.organization_id,
            boundaries="Uninterpreted boundary fixture", applicability="Uninterpreted applicability fixture",
            products_services="Unparsed product service fixture", process_ids=(first_process.entity_id, second_process.entity_id),
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        evidence = DocumentEvidenceCommandService(using="app").create_evidence(
            identity=self.identity, organization_id=self.organization_id,
            source_type="scope_fixture", source_uri="fixture://scope-evidence",
            content_hash="d" * 64, captured_at=self.now,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        arguments = {
            "identity": self.identity, "organization_id": self.organization_id,
            "capability": capability, "model_policy_id": policy_id,
            "requested_autonomy": 2, "model_provider": "repository",
            "model_identifier": "deterministic", "model_version": "1",
            "prompt_version": "none", "rule_bundle_version": "scope-v1",
            "inputs": [{
                "standard_edition_id": str(self.edition.id),
                "requirement_control_id": str(self.scope_requirement.id),
                "knowledge_layer_rule_id": str(self.rule_id),
                "evidence_id": str(evidence.entity_id),
                "qms_scope_id": str(scope.entity_id),
            }],
            "actor_id": self.actor_id, "trace_id": uuid4(),
        }
        first = service.invoke_source(**arguments)
        second = service.invoke_source(**{**arguments, "trace_id": uuid4()})
        self.assertEqual(first.status, ExecutionStatus.COMPLETED)
        self.assertEqual(first.result_scope, "structural_scope_process_count_only")
        self.assertTrue(first.not_normative_assessment)
        self.assertEqual(first.semantic_result, {"linked_process_count": 2})
        self.assertEqual(first.semantic_result, second.semantic_result)
        self.assertEqual(first.provenance["scope_snapshot"], second.provenance["scope_snapshot"])
        self.assertEqual(first.provenance["input_snapshot_hash"], second.provenance["input_snapshot_hash"])
        snapshot = json.loads(first.provenance["scope_snapshot"])["value"]
        self.assertEqual(set(snapshot), {
            "schema", "tenant_id", "organization_id", "scope_id", "lineage_id", "revision", "process_ids",
        })
        self.assertNotIn("Uninterpreted boundary fixture", first.provenance["scope_snapshot"])
        event = DomainEvent.objects.using("default").get(event_id=first.emitted_events[0])
        self.assertEqual(event.payload["execution_result"]["semantic_result"]["linked_process_count"], 2)
        self.assertTrue(TransactionalOutbox.objects.using("default").filter(domain_event_id=event.event_id).exists())
        self.assertTrue(ImmutableAuditLog.objects.using("default").filter(
            stream_id=first.run_id, action="agent_run.completed",
        ).exists())
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertEqual(AgentRun.objects.using("app").get(id=first.run_id).status, AgentRun.Status.COMPLETED)
            self.assertFalse(AgentRunRecommendation.objects.using("app").filter(agent_run_id=first.run_id).exists())
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(QmsScope.objects.using("app").filter(id=scope.entity_id).exists())
            self.assertFalse(AgentRun.objects.using("app").filter(id=first.run_id).exists())

        other_organization = Organization.objects.using("default").create(
            tenant_id=self.other_tenant_id, display_name="Foreign scope fixture",
        )
        foreign_scope = qms.create_scope(
            identity=self.other_identity, organization_id=other_organization.id,
            boundaries="Foreign boundary", applicability="Foreign applicability",
            products_services="Foreign products", actor_id=self.other_actor_id,
            trace_id=uuid4(),
        )
        foreign_arguments = {
            **arguments,
            "inputs": [{**arguments["inputs"][0], "qms_scope_id": str(foreign_scope.entity_id)}],
        }
        with self.assertRaises(QmsScope.DoesNotExist):
            service.invoke_source(**foreign_arguments)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            failed_run = AgentRun.objects.using("app").filter(
                capability=capability, status=AgentRun.Status.FAILED,
            ).latest("started_at")
            self.assertTrue(DomainEvent.objects.using("app").filter(
                aggregate_type="agent_run", aggregate_id=failed_run.id,
                event_type="agent_run.failed",
            ).exists())

    def test_process_graph_adapter_projects_only_canonical_tenant_relationships(self):
        from foundation.agent_execution_contract import ExecutionStatus
        from foundation.change_performance import ChangePerformanceCommandService
        from foundation.models import AgentRun, AgentRunRecommendation, DomainEvent, Process
        from foundation.qms_context import QmsContextCommandService

        capability = "source.process_graph_agent"
        catalog = AgentCatalogCommandService()
        policy_id = catalog.create_model_policy(
            policy_key=f"process-graph-{self.tenant_id}", version="1",
            approved_models=["deterministic"], data_classes=["qms_process_metadata"],
            guardrails={"allowed_capabilities": [capability], "autonomy_max": 4},
            human_gate_rules={}, actor_id="curator", trace_id=uuid4(),
        )
        catalog.publish_model_policy(model_policy_id=policy_id, actor_id="curator", trace_id=uuid4())
        SourceCapabilityCatalogService().register(
            model_policy_id=policy_id, actor_id="curator", trace_id=uuid4(),
        )
        service = CapabilityInvocationService()
        service.registry.activate(
            identity=self.identity, capability=capability,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        qms = QmsContextCommandService(using="app")
        process_a = qms.create_process(
            identity=self.identity, organization_id=self.organization_id,
            name="Assembly", actor_id=self.actor_id, trace_id=uuid4(),
            owner_id=self.user_projection_id,
        )
        process_b = qms.create_process(
            identity=self.identity, organization_id=self.organization_id,
            name="Inspection", actor_id=self.actor_id, trace_id=uuid4(),
        )
        metric = ChangePerformanceCommandService(using="app").define_measurement(
            identity=self.identity, organization_id=self.organization_id,
            process_id=process_a.entity_id, what_is_measured="First pass yield",
            method="count accepted units / total units", measurement_timing="monthly",
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        scope = qms.create_scope(
            identity=self.identity, organization_id=self.organization_id,
            boundaries="Uninterpreted process boundary", applicability="Uninterpreted scope text",
            products_services="Unparsed service text", process_ids=(process_a.entity_id, process_b.entity_id),
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        evidence = DocumentEvidenceCommandService(using="app").create_evidence(
            identity=self.identity, organization_id=self.organization_id,
            source_type="process_graph_fixture", source_uri="fixture://process-evidence",
            content_hash="d" * 64, captured_at=self.now,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        arguments = {
            "identity": self.identity, "organization_id": self.organization_id,
            "capability": capability, "model_policy_id": policy_id,
            "requested_autonomy": 2, "model_provider": "repository",
            "model_identifier": "deterministic", "model_version": "1",
            "prompt_version": "none", "rule_bundle_version": "process-graph-v1",
            "inputs": [{
                "standard_edition_id": str(self.edition.id),
                "requirement_control_id": str(self.process_graph_requirement.id),
                "knowledge_layer_rule_id": str(self.rule_id),
                "evidence_id": str(evidence.entity_id),
            }],
            "actor_id": self.actor_id, "trace_id": uuid4(),
        }
        first = service.invoke_source(**arguments)
        second = service.invoke_source(**{**arguments, "trace_id": uuid4()})
        self.assertEqual(first.status, ExecutionStatus.COMPLETED)
        self.assertEqual(first.result_scope, "canonical_process_relationship_graph_only")
        self.assertTrue(first.not_normative_assessment)
        self.assertEqual(first.semantic_result, second.semantic_result)
        self.assertEqual(
            first.provenance["canonical_graph_snapshot"],
            second.provenance["canonical_graph_snapshot"],
        )
        self.assertEqual(first.provenance["input_snapshot_hash"], second.provenance["input_snapshot_hash"])
        graph = json.loads(first.provenance["canonical_graph_snapshot"])["value"]
        self.assertEqual(len(graph["nodes"]), 4)
        self.assertEqual(len(graph["edges"]), 3)
        self.assertIn("measurement_definition", [node["kind"] for node in graph["nodes"]])
        self.assertIn("process", [node["kind"] for node in graph["nodes"]])
        self.assertNotIn("Uninterpreted process boundary", first.provenance["canonical_graph_snapshot"])
        self.assertEqual(json.loads(first.provenance["unlinked_evidence_ids"])["value"], [str(evidence.entity_id)])
        event = DomainEvent.objects.using("default").get(event_id=first.emitted_events[0])
        self.assertEqual(event.payload["execution_result"]["result_scope"], "canonical_process_relationship_graph_only")
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertEqual(AgentRun.objects.using("app").get(id=first.run_id).status, AgentRun.Status.COMPLETED)
            self.assertFalse(AgentRunRecommendation.objects.using("app").filter(agent_run_id=first.run_id).exists())
            self.assertEqual(Process.objects.using("app").filter(
                tenant_id=self.tenant_id, organization_id=self.organization_id,
            ).count(), 2)
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(AgentRun.objects.using("app").filter(id=first.run_id).exists())

    def test_onboarding_replay_cannot_change_user_status_or_provenance(self):
        service = OnboardingWorkflowService()
        arguments = dict(identity=self.identity, user_id=self.user_projection_id,
                         step_key="plan_selection", to_status="complete", event_id=uuid4(),
                         event_type="test.plan.selected", source_reference="fixture://selected-plan",
                         actor_id=self.actor_id, trace_id=uuid4())
        _, original, duplicate = service.transition(**arguments)
        self.assertFalse(duplicate)
        self.assertTrue(service.transition(**arguments)[2])
        for changes in ({"to_status": "blocked"}, {"event_type": "different"},
                        {"source_reference": "fixture://different"}, {"state": {"plan": "different"}},
                        {"state": {"status": "blocked"}}):
            with self.subTest(changes=changes), self.assertRaises(OnboardingWorkflowError):
                service.transition(**{**arguments, **changes})
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertEqual(OnboardingTransition.objects.using("app").get(id=original.id).to_status, "complete")

    def test_organizational_profile_is_validated_persisted_and_replay_safe(self):
        service = OrganizationProfileCommandService(using="app")
        profile = {
            "role": "quality_manager", "expertise_level": "intermediate",
            "size_range": "51-200", "employees_count": 120, "sites_count": 2,
            "countries": ["Costa Rica"], "sector": "manufacturing",
            "certification_status": "in_progress",
        }
        with self.assertRaisesRegex(OnboardingWorkflowError, "missing"):
            service.save_profile(
                identity=self.identity, organization_id=self.organization_id,
                user_id=self.user_projection_id, profile={"role": "quality_manager"},
                event_id=uuid4(), actor_id=self.actor_id, trace_id=uuid4(),
            )
        with self.assertRaisesRegex(OnboardingWorkflowError, "unsupported fields"):
            service.validate_profile({**profile, "invented_threshold": "high"})
        with self.assertRaises(OnboardingWorkflowError):
            service.validate_profile({**profile, "sites_count": True})

        workflow_service = OnboardingWorkflowService(using="app")
        for step in ONBOARDING_STEPS[:9]:
            workflow_service.transition(
                identity=self.identity, user_id=self.user_projection_id,
                step_key=step.key, to_status="complete", event_id=uuid4(),
                event_type="test.onboarding.prerequisite",
                source_reference=f"fixture:{step.key}", actor_id=self.actor_id, trace_id=uuid4(),
            )
        event_id = uuid4()
        workflow, transition, duplicate = service.save_profile(
            identity=self.identity, organization_id=self.organization_id,
            user_id=self.user_projection_id, profile=profile, event_id=event_id,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        self.assertFalse(duplicate)
        self.assertEqual(workflow.state["organizational_profile"]["status"], "complete")
        self.assertEqual(workflow.state["organizational_profile"]["profile"], profile)
        self.assertEqual(
            workflow.state["organizational_profile"]["profile_hash"],
            transition.source_reference.split(":", 1)[1],
        )
        _, replayed_transition, duplicate = service.save_profile(
            identity=self.identity, organization_id=self.organization_id,
            user_id=self.user_projection_id, profile=profile, event_id=event_id,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        self.assertTrue(duplicate)
        self.assertEqual(replayed_transition.id, transition.id)
        with self.assertRaises(OnboardingWorkflowError):
            service.save_profile(
                identity=self.identity, organization_id=self.organization_id,
                user_id=self.user_projection_id,
                profile={**profile, "sector": "services"}, event_id=event_id,
                actor_id=self.actor_id, trace_id=uuid4(),
            )
        with self.assertRaises(Organization.DoesNotExist):
            service.save_profile(
                identity=self.identity, organization_id=uuid4(),
                user_id=self.user_projection_id, profile=profile,
                event_id=uuid4(), actor_id=self.actor_id, trace_id=uuid4(),
            )
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(OnboardingWorkflow.objects.using("app").filter(
                tenant_id=self.tenant_id, user_id=self.user_projection_id,
            ).exists())

    def test_onboarding_evidence_ingestion_is_metadata_only_atomic_and_replay_safe(self):
        from foundation.models import Evidence, ImmutableAuditLog

        service = OnboardingEvidenceIngestionService(using="app")
        workflow_service = OnboardingWorkflowService(using="app")
        items = [
            {
                "event_id": uuid4(), "source_type": "strategy",
                "source_uri": "adminapps://documents/strategy-1",
                "content_hash": "a" * 64, "captured_at": self.now,
            },
            {
                "event_id": uuid4(), "source_type": "kpi",
                "source_uri": "adminapps://measurements/kpi-1",
                "content_hash": "b" * 64, "captured_at": self.now,
            },
        ]
        transition_event_id = uuid4()
        with self.assertRaisesRegex(OnboardingWorkflowError, "prerequisites"):
            service.ingest_batch(
                identity=self.identity, organization_id=self.organization_id,
                user_id=self.user_projection_id, items=items,
                transition_event_id=transition_event_id, actor_id=self.actor_id, trace_id=uuid4(),
            )
        self.assertFalse(DomainEvent.objects.using("default").filter(
            event_id__in=[item["event_id"] for item in items],
        ).exists())

        for step in ONBOARDING_STEPS[:11]:
            workflow_service.transition(
                identity=self.identity, user_id=self.user_projection_id,
                step_key=step.key, to_status="complete", event_id=uuid4(),
                event_type="test.onboarding.prerequisite",
                source_reference=f"fixture:{step.key}", actor_id=self.actor_id, trace_id=uuid4(),
            )
        workflow, transition, duplicate = service.ingest_batch(
            identity=self.identity, organization_id=self.organization_id,
            user_id=self.user_projection_id, items=items,
            transition_event_id=transition_event_id, actor_id=self.actor_id, trace_id=uuid4(),
        )
        self.assertFalse(duplicate)
        step_state = workflow.state["document_data_ingestion"]
        self.assertEqual(step_state["status"], "complete")
        self.assertEqual(step_state["source_types"], ["kpi", "strategy"])
        self.assertFalse(step_state["content_bytes_read"])
        self.assertEqual(len(step_state["evidence_ids"]), 2)
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            evidence_rows = list(Evidence.objects.using("app").filter(id__in=step_state["evidence_ids"]))
            self.assertEqual(len(evidence_rows), 2)
            self.assertTrue(all(row.document_version_id is None for row in evidence_rows))
            self.assertTrue(all(row.content_hash in {"a" * 64, "b" * 64} for row in evidence_rows))
            evidence_events = DomainEvent.objects.using("app").filter(
                event_id__in=[item["event_id"] for item in items],
                event_type="evidence.created",
            )
            self.assertEqual(evidence_events.count(), 2)
            self.assertEqual(TransactionalOutbox.objects.using("app").filter(
                domain_event_id__in=evidence_events.values("event_id"),
            ).count(), 2)
            self.assertEqual(ImmutableAuditLog.objects.using("app").filter(
                entity_id__in=step_state["evidence_ids"], action="evidence.created",
            ).count(), 2)
            self.assertTrue(OnboardingTransition.objects.using("app").filter(
                id=transition.id, event_type="onboarding.document_data_ingestion.completed",
            ).exists())

        before = Evidence.objects.using("default").filter(organization_id=self.organization_id).count()
        replay = service.ingest_batch(
            identity=self.identity, organization_id=self.organization_id,
            user_id=self.user_projection_id, items=items,
            transition_event_id=transition_event_id, actor_id=self.actor_id, trace_id=uuid4(),
        )
        self.assertTrue(replay[2])
        self.assertEqual(Evidence.objects.using("default").filter(
            organization_id=self.organization_id,
        ).count(), before)
        with self.assertRaises(OnboardingWorkflowError):
            service.ingest_batch(
                identity=self.identity, organization_id=self.organization_id,
                user_id=self.user_projection_id, items=items,
                transition_event_id=uuid4(), actor_id=self.actor_id, trace_id=uuid4(),
            )
        with self.assertRaises(OnboardingWorkflowError):
            service.ingest_batch(
                identity=self.identity, organization_id=self.organization_id,
                user_id=self.user_projection_id,
                items=[{**items[0], "source_uri": "adminapps://changed"}, items[1]],
                transition_event_id=transition_event_id, actor_id=self.actor_id, trace_id=uuid4(),
            )
        with self.assertRaises(OnboardingWorkflowError):
            service.ingest_batch(
                identity=self.identity, organization_id=self.organization_id,
                user_id=self.user_projection_id,
                items=[{**items[0], "source_type": "unsupported"}],
                transition_event_id=uuid4(), actor_id=self.actor_id, trace_id=uuid4(),
            )
        other_org = Organization.objects.using("default").create(
            tenant_id=self.other_tenant_id, display_name="Foreign ingestion org",
        )
        with self.assertRaises(Organization.DoesNotExist):
            service.ingest_batch(
                identity=self.identity, organization_id=other_org.id,
                user_id=self.user_projection_id, items=items,
                transition_event_id=uuid4(), actor_id=self.actor_id, trace_id=uuid4(),
            )

    def test_document_updated_is_emitted_from_real_metadata_and_version_lifecycles(self):
        import hashlib
        from foundation.document_evidence import DocumentEvidenceCommandService
        from foundation.models import Document, DocumentVersion, TransactionalOutbox, ImmutableAuditLog

        service = DocumentEvidenceCommandService(using="app")
        content_bytes = b"synthetic integration fixture"
        effective_at = self.now
        document = service.create_document(
            identity=self.identity, organization_id=self.organization_id,
            document_type="procedure", owner_id=self.user_projection_id,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        metadata_result = service.revise_document_metadata(
            identity=self.identity, document_id=document.entity_id,
            document_type="policy", owner_id=self.user_projection_id,
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        version_result = service.create_document_version(
            identity=self.identity, document_id=document.entity_id, version="1",
            content_reference="storage://tenant/document/version-1",
            content_bytes=content_bytes, actor_id=self.actor_id,
            trace_id=uuid4(), approved_by=self.user_projection_id, effective_at=effective_at,
        )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            updates = list(DomainEvent.objects.using("app").filter(
                event_type="document.updated", aggregate_id=document.entity_id,
            ).order_by("aggregate_version"))
            self.assertEqual(len(updates), 2)
            metadata_update, version_update = updates
            self.assertEqual(metadata_update.payload["changes"]["document_type"]["after"], "policy")
            self.assertNotIn("content", metadata_update.payload)
            self.assertEqual(version_update.payload["document_version_id"], str(version_result.entity_id))
            document_row = Document.objects.using("app").get(id=document.entity_id)
            version_row = DocumentVersion.objects.using("app").get(id=version_result.entity_id)
            self.assertEqual((document_row.document_type, document_row.owner_id,
                              document_row.current_version_id),
                             ("policy", self.user_projection_id, version_result.entity_id))
            self.assertEqual((version_row.tenant_id, version_row.document_id, version_row.version,
                              version_row.content_reference, version_row.content_hash,
                              version_row.approved_by_id, version_row.effective_at),
                             (self.tenant_id, document.entity_id, "1",
                              "storage://tenant/document/version-1", hashlib.sha256(content_bytes).hexdigest(),
                              self.user_projection_id, effective_at))
            self.assertEqual(version_update.payload["content_hash"], version_row.content_hash)
            self.assertEqual(metadata_update.trace_id, metadata_result.trace_id)
            self.assertTrue(TransactionalOutbox.objects.using("app").filter(
                domain_event_id__in=[event.event_id for event in updates],
            ).count() == 2)
            self.assertEqual(ImmutableAuditLog.objects.using("app").filter(
                stream_id=document.entity_id, action="document.updated",
            ).count(), 2)
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(Document.objects.using("app").filter(id=document.entity_id).exists())
            self.assertFalse(DocumentVersion.objects.using("app").filter(id=version_result.entity_id).exists())

    def test_evidence_source_fields_are_persisted_without_interpreting_trust_score(self):
        from decimal import Decimal
        from foundation.document_evidence import DocumentEvidenceCommandService
        from foundation.models import Evidence

        result = DocumentEvidenceCommandService(using="app").create_evidence(
            identity=self.identity, organization_id=self.organization_id,
            source_type="synthetic_fixture", source_uri="fixture://evidence/1",
            content_hash="a" * 64, captured_at=self.now, trust_score="0.7500",
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            evidence = Evidence.objects.using("app").get(id=result.entity_id)
            self.assertEqual((evidence.tenant_id, evidence.source_type, evidence.source_uri,
                              evidence.content_hash, evidence.captured_at, evidence.trust_score),
                             (self.tenant_id, "synthetic_fixture", "fixture://evidence/1",
                              "a" * 64, self.now, Decimal("0.7500")))
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(Evidence.objects.using("app").filter(id=result.entity_id).exists())

    def test_evidence_coverage_source_fields_and_exact_requirement_link_are_persisted(self):
        from decimal import Decimal
        from foundation.document_evidence import DocumentEvidenceCommandService
        from foundation.models import EvidenceCoverage
        from foundation.normative_coverage import EvidenceCoverageCommandService

        evidence = DocumentEvidenceCommandService(using="app").create_evidence(
            identity=self.identity, organization_id=self.organization_id,
            source_type="synthetic_fixture", source_uri="fixture://coverage/1",
            content_hash="b" * 64, captured_at=self.now, actor_id=self.actor_id,
            trace_id=uuid4(),
        )
        result = EvidenceCoverageCommandService(using="app").record_evidence_coverage(
            identity=self.identity, organization_id=self.organization_id,
            evidence_id=evidence.entity_id, standard_edition_id=self.edition.id,
            requirement_control_id=self.requirement.id, confidence="0.6250",
            validation_status="synthetic_reviewed", validated_by=self.user_projection_id,
            validated_at=self.now, actor_id=self.actor_id, trace_id=uuid4(),
        )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            coverage = EvidenceCoverage.objects.using("app").get(id=result.entity_id)
            self.assertEqual((coverage.tenant_id, coverage.evidence_id, coverage.standard_edition_id,
                              coverage.requirement_control_id, coverage.confidence,
                              coverage.validation_status, coverage.validated_by_id, coverage.validated_at),
                             (self.tenant_id, evidence.entity_id, self.edition.id, self.requirement.id,
                              Decimal("0.6250"), "synthetic_reviewed", self.user_projection_id, self.now))
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(EvidenceCoverage.objects.using("app").filter(id=result.entity_id).exists())

    def test_stakeholder_requirement_changed_is_emitted_from_real_revision_lifecycle(self):
        from foundation.models import ImmutableAuditLog, Stakeholder, StakeholderRequirement
        from foundation.qms_context import QmsContextCommandService

        service = QmsContextCommandService(using="app")
        stakeholder = service.create_stakeholder(
            identity=self.identity, organization_id=self.organization_id,
            stakeholder_type="customer", name="Customer A", actor_id=self.actor_id,
            trace_id=uuid4(),
        )
        requirement = service.create_stakeholder_requirement(
            identity=self.identity, stakeholder_id=stakeholder.entity_id,
            requirement_text="Delivery reliability", actor_id=self.actor_id,
            trace_id=uuid4(), qms_addressed=False,
        )
        revised = service.supersede_stakeholder_requirement(
            identity=self.identity, requirement_id=requirement.entity_id,
            requirement_text="Delivery reliability and complaint response",
            actor_id=self.actor_id, trace_id=uuid4(), qms_addressed=True,
            change_reason="Updated source requirement fixture",
        )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            changed = DomainEvent.objects.using("app").get(
                aggregate_type="stakeholder_requirement", aggregate_id=requirement.aggregate_id,
                event_type="stakeholder.requirement.changed",
            )
            self.assertEqual(changed.payload["stakeholder_requirement_id"], str(revised.entity_id))
            self.assertEqual(changed.payload["previous_revision_id"], str(requirement.entity_id))
            self.assertEqual(changed.payload["changed_fields"]["requirement_text"]["after"],
                             "Delivery reliability and complaint response")
            self.assertTrue(TransactionalOutbox.objects.using("app").filter(
                domain_event_id=changed.event_id,
            ).exists())
            self.assertTrue(ImmutableAuditLog.objects.using("app").filter(
                stream_id=requirement.aggregate_id, action="stakeholder.requirement.changed",
            ).exists())
            self.assertEqual(StakeholderRequirement.objects.using("app").get(
                id=revised.entity_id,
            ).tenant_id, self.tenant_id)
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(Stakeholder.objects.using("app").filter(id=stakeholder.entity_id).exists())
            self.assertFalse(DomainEvent.objects.using("app").filter(event_id=changed.event_id).exists())

    def test_change_requested_is_emitted_from_real_change_creation(self):
        from foundation.change_performance import ChangePerformanceCommandService
        from foundation.models import Change, ChangeProcess, ImmutableAuditLog

        process = __import__("foundation.qms_context", fromlist=["QmsContextCommandService"]).QmsContextCommandService(
            using="app",
        ).create_process(
            identity=self.identity, organization_id=self.organization_id,
            name="Packaging", actor_id=self.actor_id, trace_id=uuid4(),
        )
        approval_id = uuid4()
        result = ChangePerformanceCommandService(using="app").create_change(
            identity=self.identity, organization_id=self.organization_id,
            change_type="process_change", purpose="Update packaging workflow",
            impact="Affects inspection order", status="requested", process_ids=(process.entity_id,),
            approval_id=approval_id, actor_id=self.actor_id, trace_id=uuid4(),
        )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            change = Change.objects.using("app").get(id=result.entity_id)
            event = DomainEvent.objects.using("app").get(
                aggregate_type="change", aggregate_id=change.id,
                event_type="change.requested",
            )
            self.assertEqual((change.tenant_id, change.change_type, change.purpose,
                              change.impact, change.status, change.approval_id),
                             (self.tenant_id, "process_change", "Update packaging workflow",
                              "Affects inspection order", "requested", approval_id))
            self.assertTrue(ChangeProcess.objects.using("app").filter(
                change_revision_id=change.id, process_id=process.entity_id,
                tenant_id=self.tenant_id,
            ).exists())
            self.assertEqual(event.payload["change_id"], str(change.id))
            self.assertEqual(event.payload["purpose"], change.purpose)
            self.assertEqual(event.payload["affected_process_ids"], [str(process.entity_id)])
            self.assertTrue(TransactionalOutbox.objects.using("app").filter(
                domain_event_id=event.event_id,
            ).exists())
            self.assertTrue(ImmutableAuditLog.objects.using("app").filter(
                stream_id=change.id, action="change.requested",
            ).exists())
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(Change.objects.using("app").filter(id=result.entity_id).exists())

    def test_context_signal_detected_is_emitted_from_real_context_item_lifecycle(self):
        from foundation.models import ContextItem, ImmutableAuditLog
        from foundation.qms_context import QmsContextCommandService

        service = QmsContextCommandService(using="app")
        created = service.create_context_item(
            identity=self.identity, organization_id=self.organization_id,
            issue_type=ContextItem.IssueType.EXTERNAL,
            description="Supplier regulation changed", actor_id=self.actor_id,
            trace_id=uuid4(),
        )
        revised = service.supersede_context_item(
            identity=self.identity, context_item_id=created.entity_id,
            issue_type=ContextItem.IssueType.EXTERNAL,
            description="Supplier regulation changed and updated expectations",
            actor_id=self.actor_id, trace_id=uuid4(),
            change_reason="New source information",
        )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            events = list(DomainEvent.objects.using("app").filter(
                aggregate_type="context_item", aggregate_id=created.aggregate_id,
                event_type="context.signal.detected",
            ).order_by("aggregate_version"))
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0].payload["context_item_id"], str(created.entity_id))
            self.assertEqual(events[1].payload["context_item_id"], str(revised.entity_id))
            self.assertEqual(events[1].payload["previous_revision_id"], str(created.entity_id))
            self.assertEqual(TransactionalOutbox.objects.using("app").filter(
                domain_event_id__in=[event.event_id for event in events],
            ).count(), 2)
            self.assertEqual(ImmutableAuditLog.objects.using("app").filter(
                stream_id=created.aggregate_id, action="context.signal.detected",
            ).count(), 2)
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(ContextItem.objects.using("app").filter(id=created.entity_id).exists())
            self.assertFalse(DomainEvent.objects.using("app").filter(event_id=events[0].event_id).exists())

    def test_source_backed_onboarding_and_agent_contracts_have_no_duplicates(self):
        self.assertEqual(len(ONBOARDING_STEPS), 17)
        step_keys = [step.key for step in ONBOARDING_STEPS]
        self.assertEqual(len(step_keys), len(set(step_keys)))
        for step in ONBOARDING_STEPS:
            self.assertTrue(set(step.prerequisite_keys).issubset(step_keys))
        agents = source_capability_catalog()
        self.assertEqual(len(agents), 33)
        capabilities = [agent["capability"] for agent in agents]
        self.assertEqual(len(capabilities), len(set(capabilities)))

    def test_wp2_foundation_migrations_reverse_and_reapply(self):
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connections["default"])
        self.assertEqual(
            executor.loader.graph.leaf_nodes("foundation")[-1],
            ("foundation", "0037_qms_audit_capa_foundation"),
        )
        executor.migrate([("foundation", "0028_capability_activation")])
        try:
            reversed_executor = MigrationExecutor(connections["default"])
            self.assertNotIn(("foundation", "0029_context_twin_result_completion"),
                             reversed_executor.loader.applied_migrations)
            self.assertNotIn(("foundation", "0030_qms_site"),
                             reversed_executor.loader.applied_migrations)
            self.assertNotIn(("foundation", "0031_tenant_standard_pack"),
                             reversed_executor.loader.applied_migrations)
            self.assertNotIn(("foundation", "0032_global_industry_profile"),
                             reversed_executor.loader.applied_migrations)
            self.assertNotIn(("foundation", "0033_tenant_projection_profile_fields"),
                             reversed_executor.loader.applied_migrations)
            self.assertNotIn(("foundation", "0034_organization_source_profile_fields"),
                             reversed_executor.loader.applied_migrations)
            self.assertNotIn(("foundation", "0035_user_projection_profile_fields"),
                             reversed_executor.loader.applied_migrations)
            self.assertNotIn(("foundation", "0036_action_execution_rollback_lineage"),
                             reversed_executor.loader.applied_migrations)
            self.assertNotIn(("foundation", "0037_qms_audit_capa_foundation"),
                             reversed_executor.loader.applied_migrations)
        finally:
            forward_executor = MigrationExecutor(connections["default"])
            forward_executor.migrate([("foundation", "0037_qms_audit_capa_foundation")])
        restored = MigrationExecutor(connections["default"])
        self.assertIn(("foundation", "0029_context_twin_result_completion"),
                      restored.loader.applied_migrations)
        self.assertIn(("foundation", "0030_qms_site"), restored.loader.applied_migrations)
        self.assertIn(("foundation", "0031_tenant_standard_pack"), restored.loader.applied_migrations)
        self.assertIn(("foundation", "0032_global_industry_profile"), restored.loader.applied_migrations)
        self.assertIn(("foundation", "0033_tenant_projection_profile_fields"), restored.loader.applied_migrations)
        self.assertIn(("foundation", "0034_organization_source_profile_fields"), restored.loader.applied_migrations)
        self.assertIn(("foundation", "0035_user_projection_profile_fields"), restored.loader.applied_migrations)
        self.assertIn(("foundation", "0036_action_execution_rollback_lineage"), restored.loader.applied_migrations)
        self.assertIn(("foundation", "0037_qms_audit_capa_foundation"), restored.loader.applied_migrations)

    def test_adminapps_tenant_projection_persists_optional_source_fields(self):
        from foundation.models import IndustryProfile, TenantProjection
        from foundation.normative_coverage import NormativeCatalogCommandService
        from foundation.projection_contract import validate_projection_event
        from foundation.projection_writer import ProjectionWriterService

        profile_id = NormativeCatalogCommandService(using="normative_curator").create_industry_profile(
            code=f"tenant-test-{self.tenant_id}", name="Test Profile",
            manufacturing_service_route="manufacturing/service",
            terminology_pack="test-terms-v1", actor_id="tenant-projection-curator",
            trace_id=uuid4(),
        )

        def projection_event(*, version, payload):
            return validate_projection_event({
                "event_id": str(uuid4()), "event_type": "tenant.updated",
                "schema_version": 1, "source": "adminapps", "source_version": version,
                "occurred_at": timezone.now().isoformat(), "trace_id": str(uuid4()),
                "aggregate_type": "tenant", "aggregate_id": str(self.external_tenant_id),
                "adminapps_tenant_id": str(self.external_tenant_id), "payload": payload,
            })

        writer = ProjectionWriterService(using="projector")
        writer.apply(projection_event(version=2, payload={
            "display_name": "Updated projection tenant", "lifecycle_status": "active",
            "plan": "standard", "locale": "en-CA", "industry_profile_id": str(profile_id),
        }))
        writer.apply(projection_event(version=3, payload={
            "display_name": "Updated projection tenant v3", "lifecycle_status": "active",
        }))
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            projection = TenantProjection.objects.using("app").get(id=self.tenant_id)
            self.assertEqual(projection.plan, "standard")
            self.assertEqual(projection.locale, "en-CA")
            self.assertEqual(projection.industry_profile_id, profile_id)
            self.assertEqual(projection.display_name_snapshot, "Updated projection tenant v3")
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(TenantProjection.objects.using("app").filter(id=self.tenant_id).exists())
        invalid = {
            "event_id": str(uuid4()), "event_type": "tenant.updated", "schema_version": 1,
            "source": "adminapps", "source_version": 4,
            "occurred_at": timezone.now().isoformat(), "trace_id": str(uuid4()),
            "aggregate_type": "tenant", "aggregate_id": str(self.external_tenant_id),
            "adminapps_tenant_id": str(self.external_tenant_id),
            "payload": {"display_name": "x", "plan": "", "industry_profile_id": str(profile_id)},
        }
        from foundation.projection_contract import ContractValidationError
        with self.assertRaises(ContractValidationError):
            validate_projection_event(invalid)

    def test_adminapps_user_projection_persists_email_role_and_mfa_status(self):
        from foundation.projection_contract import ContractValidationError, validate_projection_event
        from foundation.projection_writer import ProjectionWriterService

        def user_event(*, version, payload):
            return validate_projection_event({
                "event_id": str(uuid4()), "event_type": "user.updated",
                "schema_version": 1, "source": "adminapps", "source_version": version,
                "occurred_at": timezone.now().isoformat(), "trace_id": str(uuid4()),
                "aggregate_type": "user", "aggregate_id": str(self.actor_id),
                "adminapps_tenant_id": str(self.external_tenant_id), "payload": payload,
            })

        writer = ProjectionWriterService(using="projector")
        writer.apply(user_event(version=2, payload={
            "lifecycle_status": "active", "email": "user@tenant.invalid",
            "role": "quality_manager", "mfa_status": "verified",
        }))
        writer.apply(user_event(version=3, payload={"lifecycle_status": "active"}))
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            projection = UserProjection.objects.using("app").get(id=self.user_projection_id)
            self.assertEqual(projection.email, "user@tenant.invalid")
            self.assertEqual(projection.role, "quality_manager")
            self.assertEqual(projection.mfa_status, "verified")
            self.assertEqual(projection.source_version, 3)
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(UserProjection.objects.using("app").filter(
                id=self.user_projection_id,
            ).exists())
        invalid = {
            "event_id": str(uuid4()), "event_type": "user.updated", "schema_version": 1,
            "source": "adminapps", "source_version": 4,
            "occurred_at": timezone.now().isoformat(), "trace_id": str(uuid4()),
            "aggregate_type": "user", "aggregate_id": str(self.actor_id),
            "adminapps_tenant_id": str(self.external_tenant_id),
            "payload": {"lifecycle_status": "active", "role": ""},
        }
        with self.assertRaises(ContractValidationError):
            validate_projection_event(invalid)

    def test_site_entity_matches_source_fields_and_is_tenant_rls_bound(self):
        from foundation.models import ImmutableAuditLog, Site
        from foundation.qms_context import QmsContextCommandService

        service = QmsContextCommandService(using="app")
        site = service.create_site(
            identity=self.identity, organization_id=self.organization_id,
            country="CR", timezone="America/Costa_Rica", criticality="high",
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        with self.assertRaises(ValueError):
            service.create_site(
                identity=self.identity, organization_id=self.organization_id,
                country="", timezone="America/Costa_Rica", criticality="high",
                actor_id=self.actor_id, trace_id=uuid4(),
            )
        with self.assertRaises(RuntimeError):
            service.create_site(
                identity=self.identity, organization_id=self.organization_id,
                country="CR", timezone="America/Costa_Rica", criticality="high",
                actor_id=self.actor_id, trace_id=uuid4(), fail_before_commit=True,
            )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            row = Site.objects.using("app").get(id=site.entity_id)
            self.assertEqual((row.country, row.timezone, row.criticality),
                             ("CR", "America/Costa_Rica", "high"))
            self.assertEqual(Site.objects.using("app").filter(
                organization_id=self.organization_id,
            ).count(), 1)
            self.assertTrue(DomainEvent.objects.using("app").filter(
                aggregate_type="site", aggregate_id=site.entity_id, event_type="site.created",
            ).exists())
            self.assertTrue(TransactionalOutbox.objects.using("app").filter(
                domain_event__aggregate_type="site", domain_event__aggregate_id=site.entity_id,
            ).exists())
            self.assertTrue(ImmutableAuditLog.objects.using("app").filter(
                stream_type="site", stream_id=site.entity_id, action="site.created",
            ).exists())
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(Site.objects.using("app").filter(id=site.entity_id).exists())
            self.assertFalse(DomainEvent.objects.using("app").filter(
                aggregate_id=site.entity_id, event_type="site.created",
            ).exists())

    def test_standard_pack_is_a_tenant_binding_to_an_exact_edition(self):
        from foundation.models import ImmutableAuditLog, StandardPack
        from foundation.normative_coverage import StandardPackCommandService

        service = StandardPackCommandService(using="app")
        result = service.create_standard_pack(
            identity=self.identity, standard_edition_id=self.edition.id,
            status="enabled", actor_id=self.actor_id, trace_id=uuid4(),
        )
        with self.assertRaises(ValueError):
            service.create_standard_pack(
                identity=self.identity, standard_edition_id=self.edition.id,
                status="", actor_id=self.actor_id, trace_id=uuid4(),
            )
        with self.assertRaises(RuntimeError):
            service.create_standard_pack(
                identity=self.identity, standard_edition_id=self.edition.id,
                status="enabled", actor_id=self.actor_id, trace_id=uuid4(), fail_before_commit=True,
            )
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            pack = StandardPack.objects.using("app").get(id=result.entity_id)
            self.assertEqual(pack.tenant_id, self.tenant_id)
            self.assertEqual(pack.standard_edition_id, self.edition.id)
            self.assertEqual(pack.status, "enabled")
            event = DomainEvent.objects.using("app").get(
                aggregate_type="standard_pack", aggregate_id=pack.id,
                event_type="standard_pack.created",
            )
            self.assertEqual(event.payload["standard_edition_id"], str(self.edition.id))
            self.assertTrue(TransactionalOutbox.objects.using("app").filter(
                domain_event_id=event.event_id,
            ).exists())
            self.assertTrue(ImmutableAuditLog.objects.using("app").filter(
                stream_id=pack.id, action="standard_pack.created",
            ).exists())
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(StandardPack.objects.using("app").filter(id=result.entity_id).exists())

    def test_industry_profile_global_identity_uses_only_source_fields(self):
        from foundation.models import IndustryProfile
        from foundation.normative_coverage import NormativeCatalogCommandService

        service = NormativeCatalogCommandService(using="normative_curator")
        profile_id = service.create_industry_profile(
            code="manufacturing", name="Manufacturing",
            manufacturing_service_route="manufacturing",
            terminology_pack="manufacturing-terminology-v1",
            actor_id="wp2-industry-curator", trace_id=uuid4(),
        )
        with self.assertRaises(ValueError):
            service.create_industry_profile(
                code="", name="Manufacturing", manufacturing_service_route="manufacturing",
                terminology_pack="manufacturing-terminology-v1",
                actor_id="wp2-industry-curator", trace_id=uuid4(),
            )
        row = IndustryProfile.objects.using("app").get(id=profile_id)
        self.assertEqual(row.code, "manufacturing")
        self.assertEqual(row.manufacturing_service_route, "manufacturing")
        self.assertEqual(row.terminology_pack, "manufacturing-terminology-v1")
        self.assertEqual(
            {field.name for field in IndustryProfile._meta.fields},
            {"id", "code", "name", "manufacturing_service_route", "terminology_pack"},
        )

    def test_standard_identity_matches_source_fields_and_curator_command(self):
        from foundation.models import (
            Clause, KnowledgeLayer, KnowledgeLayerBinding, KnowledgeLayerRule,
            NormativeCurationAudit, RequirementControl, StandardEdition,
        )
        from foundation.knowledge_layer import KnowledgeLayerCommandService
        from foundation.normative_coverage import NormativeCatalogCommandService

        service = NormativeCatalogCommandService(using="normative_curator")
        with self.assertRaises(ValueError):
            service.create_standard(
                code="", title="Invalid", publisher="ISO",
                actor_id="wp2-standard-curator", trace_id=uuid4(),
            )
        standard_id = service.create_standard(
            code=f"WP2-STD-{self.tenant_id}", title="Synthetic standard identity",
            publisher="TEST", actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        standard = Standard.objects.using("app").get(id=standard_id)
        self.assertEqual((standard.code, standard.title, standard.publisher),
                         (f"WP2-STD-{self.tenant_id}", "Synthetic standard identity", "TEST"))
        self.assertTrue(NormativeCurationAudit.objects.using("normative_curator").filter(
            entity_id=standard_id, action="standard.created",
        ).exists())
        edition_id = service.create_standard_edition(
            standard_id=standard_id, edition="synthetic-edition-v1",
            effective_from=self.now.date(), source_hash="a" * 64,
            actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        edition = StandardEdition.objects.using("app").get(id=edition_id)
        self.assertEqual(edition.standard_id, standard_id)
        self.assertEqual(edition.edition, "synthetic-edition-v1")
        self.assertEqual(edition.status, StandardEdition.Status.DRAFT)
        self.assertEqual(edition.effective_from, self.now.date())
        self.assertEqual(edition.source_hash, "a" * 64)
        clause_id = service.add_clause(
            standard_edition_id=edition_id, code="4.1", title="Synthetic context clause",
            actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        clause = Clause.objects.using("app").get(id=clause_id)
        self.assertEqual((clause.standard_edition_id, clause.code, clause.title),
                         (edition_id, "4.1", "Synthetic context clause"))
        requirement_id = service.add_requirement_control(
            standard_edition_id=edition_id, clause_id=clause_id,
            paraphrase="Synthetic non-normative control fixture",
            actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        requirement = RequirementControl.objects.using("app").get(id=requirement_id)
        self.assertEqual(requirement.standard_edition_id, edition_id)
        self.assertEqual(requirement.clause_id, clause_id)
        self.assertEqual(requirement.paraphrase, "Synthetic non-normative control fixture")
        service.publish_standard_edition(
            standard_edition_id=edition_id, actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        edition.refresh_from_db(using="app")
        self.assertEqual(edition.status, StandardEdition.Status.PUBLISHED)
        knowledge_service = KnowledgeLayerCommandService(using="normative_curator")
        layer_id = knowledge_service.create_knowledge_layer(
            standard_edition_id=edition_id, layer_type="synthetic guidance fixture",
            actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        rule_id = knowledge_service.create_knowledge_layer_rule(
            knowledge_layer_id=layer_id, rule_key="fixture.context.guidance", version="1",
            logic_json={"source_fixture": True}, evidence_expectation={"kind": "synthetic"},
            actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        knowledge_service.publish_knowledge_layer_rule(
            rule_id=rule_id, actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        binding_id = knowledge_service.create_knowledge_layer_binding(
            knowledge_layer_rule_id=rule_id, standard_edition_id=edition_id,
            requirement_control_id=requirement_id, priority="normal",
            rationale="Synthetic guidance fixture only",
            actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        knowledge_service.publish_knowledge_layer_binding(
            binding_id=binding_id, actor_id="wp2-standard-curator", trace_id=uuid4(),
        )
        layer = KnowledgeLayer.objects.using("app").get(id=layer_id)
        rule = KnowledgeLayerRule.objects.using("app").get(id=rule_id)
        binding = KnowledgeLayerBinding.objects.using("app").get(id=binding_id)
        self.assertEqual(layer.standard_edition_id, edition_id)
        self.assertEqual(layer.layer_type, "synthetic guidance fixture")
        self.assertEqual(rule.rule_key, "fixture.context.guidance")
        self.assertEqual(rule.version, "1")
        self.assertEqual(rule.logic_json, {"source_fixture": True})
        self.assertEqual(rule.evidence_expectation, {"kind": "synthetic"})
        self.assertEqual(binding.requirement_control_id, requirement_id)
        self.assertEqual(binding.knowledge_layer_rule_id, rule_id)
        self.assertEqual(binding.priority, "normal")
        self.assertEqual(binding.rationale, "Synthetic guidance fixture only")

    def test_model_policy_source_fields_are_persisted_and_published(self):
        """Acceptance for REQ-ENTITY-MODEL-POLICY's explicit field contract."""
        from foundation.models import AgentCatalogCurationAudit, ModelPolicy

        policy_id = AgentCatalogCommandService(using="agent_catalog_curator").create_model_policy(
            policy_key="wp2-source-model-policy", version="1",
            approved_models=["deterministic-fixture"], data_classes=["synthetic_quality"],
            guardrails={"autonomy_max": 2},
            human_gate_rules={"required_autonomy_levels": ["A2"]},
            actor_id="wp2-model-policy-curator", trace_id=uuid4(),
        )
        AgentCatalogCommandService(using="agent_catalog_curator").publish_model_policy(
            model_policy_id=policy_id, actor_id="wp2-model-policy-curator", trace_id=uuid4(),
        )
        row = ModelPolicy.objects.using("app").get(id=policy_id)
        self.assertEqual(
            (row.id, row.approved_models, row.data_classes, row.guardrails, row.human_gate_rules,
             row.status),
            (policy_id, ["deterministic-fixture"], ["synthetic_quality"], {"autonomy_max": 2},
             {"required_autonomy_levels": ["A2"]}, ModelPolicy.Status.PUBLISHED),
        )
        self.assertTrue(AgentCatalogCurationAudit.objects.using("agent_catalog_curator").filter(
            entity_id=policy_id, action="model_policy.published",
        ).exists())

    def test_immutable_audit_log_source_fields_are_persisted_and_append_only(self):
        """Acceptance for REQ-ENTITY-IMMUTABLE-AUDIT-LOG's explicit field contract."""
        from foundation.models import ImmutableAuditLog
        from foundation.qms_context import QmsContextCommandService

        result = QmsContextCommandService(using="app").create_process(
            identity=self.identity, organization_id=self.organization_id,
            name="WP2 immutable audit source fixture", actor_id=self.actor_id, trace_id=uuid4(),
        )
        with trusted_tenant_context(
            self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app",
        ):
            row = ImmutableAuditLog.objects.using("app").get(entity_id=result.entity_id)
            self.assertEqual(
                (row.tenant_id, row.actor_type, row.actor_id, row.action, row.entity_type,
                 row.entity_id, row.before_hash),
                (self.tenant_id, "user", str(self.actor_id), "process.created", "process",
                 result.entity_id, None),
            )
            self.assertIsNotNone(row.occurred_at)
            self.assertTrue(row.after_hash)
            with self.assertRaises(DatabaseError):
                ImmutableAuditLog.objects.using("app").filter(id=row.id).update(action="mutated")
        with trusted_tenant_context(
            self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app",
        ):
            self.assertFalse(ImmutableAuditLog.objects.using("app").filter(id=row.id).exists())

    def test_source_defined_qms_process_stakeholder_risk_opportunity_objective_fields(self):
        from decimal import Decimal
        from foundation.change_performance import ChangePerformanceCommandService
        from foundation.models import (
            Objective, Opportunity, Process, Risk, Stakeholder, StakeholderRequirement,
        )
        from foundation.qms_context import QmsContextCommandService
        from foundation.risk_objective import RiskOpportunityObjectiveCommandService

        context = QmsContextCommandService(using="app")
        process_result = context.create_process(
            identity=self.identity, organization_id=self.organization_id,
            name="Assembly", owner_id=self.user_projection_id, process_type="operational",
            status="active", actor_id=self.actor_id, trace_id=uuid4(),
        )
        stakeholder_result = context.create_stakeholder(
            identity=self.identity, organization_id=self.organization_id,
            stakeholder_type="customer", name="Customer A", relevance_score=Decimal("0.7500"),
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        stakeholder_requirement_result = context.create_stakeholder_requirement(
            identity=self.identity, stakeholder_id=stakeholder_result.entity_id,
            requirement_text="On-time delivery", qms_addressed=True,
            owner_process_id=process_result.entity_id, actor_id=self.actor_id, trace_id=uuid4(),
        )
        measurement_result = ChangePerformanceCommandService(using="app").define_measurement(
            identity=self.identity, organization_id=self.organization_id,
            process_id=process_result.entity_id, what_is_measured="First pass yield",
            method="accepted / total", measurement_timing="monthly",
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        business = RiskOpportunityObjectiveCommandService(using="app")
        risk_result = business.create_risk(
            identity=self.identity, process_id=process_result.entity_id,
            cause="Synthetic cause", event="Synthetic event", consequence="Synthetic consequence",
            likelihood="medium", impact="low", residual="review",
            actor_id=self.actor_id, trace_id=uuid4(),
        )
        opportunity_result = business.create_opportunity(
            identity=self.identity, process_id=process_result.entity_id,
            hypothesis="Synthetic hypothesis", benefit="Synthetic benefit",
            feasibility="review", status="proposed", actor_id=self.actor_id, trace_id=uuid4(),
        )
        objective_result = business.create_objective(
            identity=self.identity, organization_id=self.organization_id,
            owner_id=self.user_projection_id, metric_id=measurement_result.entity_id,
            target="Synthetic target", due_date=self.now.date(), status="draft",
            actor_id=self.actor_id, trace_id=uuid4(),
        )

        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            process = Process.objects.using("app").get(id=process_result.entity_id)
            stakeholder = Stakeholder.objects.using("app").get(id=stakeholder_result.entity_id)
            stakeholder_requirement = StakeholderRequirement.objects.using("app").get(
                id=stakeholder_requirement_result.entity_id,
            )
            risk = Risk.objects.using("app").get(id=risk_result.entity_id)
            opportunity = Opportunity.objects.using("app").get(id=opportunity_result.entity_id)
            objective = Objective.objects.using("app").get(id=objective_result.entity_id)
            self.assertEqual((process.name, process.owner_id, process.process_type, process.status),
                             ("Assembly", self.user_projection_id, "operational", "active"))
            self.assertEqual((stakeholder.name, stakeholder.stakeholder_type, stakeholder.relevance_score),
                             ("Customer A", "customer", Decimal("0.7500")))
            self.assertEqual((stakeholder_requirement.requirement_text, stakeholder_requirement.qms_addressed,
                              stakeholder_requirement.owner_process_id),
                             ("On-time delivery", True, process_result.entity_id))
            self.assertEqual((risk.process_id, risk.cause, risk.event, risk.consequence,
                              risk.likelihood, risk.impact, risk.residual),
                             (process_result.entity_id, "Synthetic cause", "Synthetic event",
                              "Synthetic consequence", "medium", "low", "review"))
            self.assertEqual((opportunity.process_id, opportunity.hypothesis, opportunity.benefit,
                              opportunity.feasibility, opportunity.status),
                             (process_result.entity_id, "Synthetic hypothesis", "Synthetic benefit",
                              "review", "proposed"))
            self.assertEqual((objective.owner_id, objective.metric_id, objective.target,
                              objective.due_date, objective.status),
                             (self.user_projection_id, measurement_result.entity_id,
                              "Synthetic target", self.now.date(), "draft"))
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(Process.objects.using("app").filter(id=process_result.entity_id).exists())
            self.assertFalse(Stakeholder.objects.using("app").filter(id=stakeholder_result.entity_id).exists())
            self.assertFalse(Risk.objects.using("app").filter(id=risk_result.entity_id).exists())
            self.assertFalse(Opportunity.objects.using("app").filter(id=opportunity_result.entity_id).exists())
            self.assertFalse(Objective.objects.using("app").filter(id=objective_result.entity_id).exists())

    @override_settings(ISO_SMART_PRODUCT_CODE="iso-smart-test")
    def test_organization_source_profile_fields_are_authorized_and_replay_bound(self):
        from types import SimpleNamespace
        from foundation.qms_organization import QmsOrganizationCommandService, OrganizationRequestConflict

        class Authority:
            def validate_product_access(self, external_id, product_code, **kwargs):
                return {"allowed": True, "source": "adminapps", "fallback": False}

            def get_user(self, actor_id, *, organization_id):
                return {
                    "id": actor_id, "is_active": True,
                    "organizations": [{"id": organization_id, "role": "org_admin"}],
                }

        service = QmsOrganizationCommandService(using="app", authority=Authority())
        request_key = uuid4()
        result = service.create_organization(
            identity=self.identity, display_name="Manufacturing organization",
            legal_name="Manufacturing Ltd", sector="manufacturing",
            size="medium", maturity="established", actor_id=self.actor_id,
            trace_id=uuid4(), request_key=request_key,
        )
        from foundation.models import ImmutableAuditLog
        with trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            row = Organization.objects.using("app").get(id=result.organization_id)
            self.assertEqual((row.sector, row.size, row.maturity),
                             ("manufacturing", "medium", "established"))
            event = DomainEvent.objects.using("app").get(event_id=result.event_id)
            self.assertEqual(event.payload["sector"], "manufacturing")
            self.assertEqual(event.payload["size"], "medium")
            self.assertEqual(event.payload["maturity"], "established")
            self.assertTrue(ImmutableAuditLog.objects.using("app").filter(
                stream_id=row.id, action="organization.created",
            ).exists())
        with self.assertRaises(OrganizationRequestConflict):
            service.create_organization(
                identity=self.identity, display_name="Manufacturing organization",
                legal_name="Manufacturing Ltd", sector="services",
                size="medium", maturity="established", actor_id=self.actor_id,
                trace_id=uuid4(), request_key=request_key,
            )
        with trusted_tenant_context(self.other_identity, actor_id=self.other_actor_id, trace_id=uuid4(), using="app"):
            self.assertFalse(Organization.objects.using("app").filter(id=result.organization_id).exists())

    def test_signed_payment_boundary_is_replay_safe_and_transitions_step_five(self):
        workflow_service = OnboardingWorkflowService(using="app")
        for step in ONBOARDING_STEPS[:4]:
            workflow_service.transition(
                identity=self.identity, user_id=self.user_projection_id,
                step_key=step.key, to_status="complete", event_id=uuid4(),
                event_type="test.onboarding.completed", source_reference=f"fixture:{step.key}",
                actor_id=self.actor_id, trace_id=self.trace_id,
            )
        payload = {"status": "confirmed", "payment_reference": "pay_fixture_001"}
        timestamp = int(self.now.timestamp())
        signer = HmacPaymentSigner(b"wp2-test-payment-secret")
        service = PaymentVerificationService(
            using="worker", verifier=HmacPaymentVerifier(b"wp2-test-payment-secret"),
        )
        event_id = uuid4()
        first = service.verify(
            identity=self.identity, user_id=self.user_projection_id,
            event_id=event_id, payload=payload,
            signature=signer.sign(payload=json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(), timestamp=timestamp),
            timestamp=timestamp, actor_id=self.actor_id, trace_id=self.trace_id,
        )
        duplicate = service.verify(
            identity=self.identity, user_id=self.user_projection_id,
            event_id=event_id, payload=payload,
            signature=signer.sign(payload=json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(), timestamp=timestamp),
            timestamp=timestamp, actor_id=self.actor_id, trace_id=self.trace_id,
        )
        self.assertEqual(first.kind.value, "processed")
        self.assertEqual(duplicate.kind.value, "idempotent_duplicate")
        with self.assertRaises(PaymentBoundaryError):
            service.verify(
                identity=self.identity, user_id=self.user_projection_id,
                event_id=uuid4(), payload=payload, signature="v1=invalid",
                timestamp=timestamp, actor_id=self.actor_id, trace_id=self.trace_id,
            )
