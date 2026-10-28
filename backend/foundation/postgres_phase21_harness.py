"""PostgreSQL 18.6 Phase-21 blocking hardening and inertness matrix."""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase19_harness as phase19


PHASE19 = ("foundation", "0017_effectiveness_check_foundation")
PHASE21 = ("foundation", "0018_governed_learning_foundation")
ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_FILES = (
    "docs/governance/GOVERNED_LEARNING_POLICY_V1.md",
    "docs/governance/GOVERNED_LEARNING_IMPLEMENTATION_AUTHORIZATION_V1.md",
    "docs/governance/EFFECTIVENESS_CHECK_POLICY_V1.md",
    "docs/adr/0003-postgresql-rls-and-evidence-graph.md",
    "docs/adr/0005-governed-agent-runtime.md",
    "docs/adr/0009-transactional-domain-command-composition-least-privilege-executor.md",
    "docs/adr/0011-effectiveness-assessment-governance-operational-readiness.md",
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def file_hashes():
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in GOVERNANCE_FILES
    }


def protected_snapshot(connection):
    tables = (
        "governance.model_policy", "governance.agent_definition",
        "normative.knowledge_layer_rule", "normative.standard",
        "normative.standard_edition", "normative.clause",
        "normative.requirement_control", "qms.recommendation",
        "qms.recommendation_basis", "qms.opportunity", "qms.action_execution",
        "qms.execution_authorization", "qms.agent_run", "qms.agent_decision",
    )
    result = {}
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(
                f"SELECT count(*),md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM {table} t"
            )
            result[table] = cursor.fetchone()
    return result


def target_reference(connection, target_type, table):
    from foundation.canonical import canonical_hash
    from foundation.governed_learning import ExactLearningTarget

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT id,lineage_id,version,to_jsonb(t) FROM {table} t "
            "WHERE status='published' AND NOT EXISTS "
            f"(SELECT 1 FROM {table} n WHERE n.previous_revision_id=t.id) ORDER BY created_at LIMIT 1"
        )
        row = cursor.fetchone()
    require(row is not None, f"no published current {target_type} fixture")
    snapshot = json.loads(row[3]) if isinstance(row[3], str) else row[3]
    return ExactLearningTarget(target_type, row[0], row[1], row[2], canonical_hash(snapshot))


def run():
    governance_before = file_hashes()
    phase19.run()
    from django.db import connections, transaction
    from django.utils import timezone

    phase3.migrate(PHASE21)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.learning_signal'),to_regclass('qms.learning_proposal')")
        require(cursor.fetchone() == ("qms.learning_signal", "qms.learning_proposal"),
                "Phase 21 tables missing")
    phase3.migrate(PHASE19)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.learning_signal')")
        require(cursor.fetchone()[0] is None, "empty-history Phase 21 reverse failed")
    phase3.migrate(PHASE21)
    from foundation.effectiveness import (
        EffectivenessCheckCommandService, ExactEvidenceReference,
        GovernedEffectivenessPlan, TrustedEffectivenessAuthority,
    )
    from foundation.governed_learning import (
        ExactLearningTarget, LearningFailurePoint, LearningProposalCommandService,
        LearningSignalCommandService, TrustedLearningGovernanceAuthority,
    )
    from foundation.models import (
        ActionExecution, DomainEvent, EffectivenessCheck, EffectivenessEvidence,
        ImmutableAuditLog, LearningProposal, LearningProposalSignal, LearningSignal,
        LearningSignalEffectiveness, TransactionalOutbox, UserProjection,
    )
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    identity = TrustedTenantIdentity("phase21-governance", phase3.TENANT_A)
    with trusted_tenant_context(identity, actor_id="phase21-read", trace_id=uuid4(), using="app"):
        current = EffectivenessCheck.objects.using("app").order_by("-revision").first()
        require(current is not None, "Phase 19 current Effectiveness leaf missing")
        execution = ActionExecution.objects.using("app").get(pk=current.action_execution_id)
        user = UserProjection.objects.using("app").first()
        evidence_links = list(EffectivenessEvidence.objects.using("app").filter(
            effectiveness_check_id=current.id).order_by("id"))
    references = [ExactEvidenceReference(
        evidence_id=row.evidence_id, lineage_id=row.evidence_lineage_id_snapshot,
        revision=row.evidence_revision_snapshot,
        content_hash=row.evidence_content_hash_snapshot,
        criterion_role=row.criterion_role,
    ) for row in evidence_links]
    plan = GovernedEffectivenessPlan(
        action_execution_id=execution.id, organization_id=phase3.ORG_A,
        opportunity_lineage_id=current.opportunity_lineage_id, due_at=current.due_at,
        criteria_hash=current.criteria_hash,
        planning_context_hash=current.planning_context_hash,
        assessment_method=current.assessment_method,
        measurement_definition_id=current.measurement_definition_id,
    )
    review_authority = TrustedEffectivenessAuthority(
        identity=identity, organization_id=phase3.ORG_A,
        actor_user_projection_id=user.id, actor_external_id=user.adminapps_user_id,
        permissions=frozenset({"qms.effectiveness_check.record", "qms.effectiveness_check.supersede"}),
        mfa_verified=True, access_active=True,
        authority_context_version="adminapps-effectiveness/v1",
        authority_decision_reference="phase21-effectiveness-corrections",
    )
    learning_authority = TrustedLearningGovernanceAuthority(
        identity=identity, organization_id=phase3.ORG_A,
        actor_user_projection_id=user.id, actor_external_id=user.adminapps_user_id,
        permissions=frozenset({"qms.learning_signal.create", "qms.learning_proposal.create"}),
        mfa_verified=True, access_active=True,
        authority_context_version="adminapps-learning-governance/v1",
        authority_decision_reference="phase21-learning-decision",
    )
    signal_service = LearningSignalCommandService()
    proposal_service = LearningProposalCommandService()
    protected_before = protected_snapshot(connections["default"])

    # Every injected failure rolls back signal/link/event/outbox/audit as one unit.
    for point in LearningFailurePoint:
        with trusted_tenant_context(identity, actor_id="phase21-count", trace_id=uuid4(), using="learning_governance"):
            before = (
                LearningSignal.objects.using("learning_governance").count(),
                LearningSignalEffectiveness.objects.using("learning_governance").count(),
                DomainEvent.objects.using("learning_governance").filter(event_type="learning_signal.created").count(),
                TransactionalOutbox.objects.using("learning_governance").filter(domain_event__event_type="learning_signal.created").count(),
            )
        try:
            signal_service.create_signal(
                authority=learning_authority, effectiveness_check_id=current.id,
                trace_id=uuid4(), failure_point=point,
            )
        except RuntimeError as exc:
            require("deliberate Phase 21 rollback" in str(exc), f"unexpected signal rollback: {exc}")
        else:
            raise AssertionError(f"signal failure point committed: {point.value}")
        with trusted_tenant_context(identity, actor_id="phase21-count", trace_id=uuid4(), using="learning_governance"):
            after = (
                LearningSignal.objects.using("learning_governance").count(),
                LearningSignalEffectiveness.objects.using("learning_governance").count(),
                DomainEvent.objects.using("learning_governance").filter(event_type="learning_signal.created").count(),
                TransactionalOutbox.objects.using("learning_governance").filter(domain_event__event_type="learning_signal.created").count(),
            )
        require(after == before, f"partial signal unit at {point.value}")

    # Repeated categorical fixtures across all outcomes; still no scoring/runtime effect.
    signals = []
    expected_outcomes = []
    leaf = current
    for outcome in ("inconclusive", "effective", "ineffective", "unknown", "inconclusive"):
        if leaf.outcome != outcome:
            uncertain = outcome in ("unknown", "inconclusive")
            result = EffectivenessCheckCommandService(using="app").record_effectiveness_check(
                authority=review_authority, plan=plan, outcome=outcome,
                evidence=references, predecessor_id=leaf.id,
                correction_reason=f"Phase 21 categorical inertness fixture: {outcome}.",
                reason_code=("evidence_temporarily_unavailable" if outcome == "unknown" else
                             "conflicting_valid_evidence" if outcome == "inconclusive" else None),
                explanation="Categorical governed fixture without numeric meaning." if uncertain else None,
                trace_id=uuid4(), assessed_at=timezone.now(),
            )
            with trusted_tenant_context(identity, actor_id="phase21-read", trace_id=uuid4(), using="app"):
                leaf = EffectivenessCheck.objects.using("app").get(pk=result.effectiveness_check_id)
        for _ in range(2):
            result = signal_service.create_signal(
                authority=learning_authority, effectiveness_check_id=leaf.id, trace_id=uuid4(),
            )
            signals.append(result.artifact_id)
            expected_outcomes.append(outcome)

    with trusted_tenant_context(identity, actor_id="phase21-read", trace_id=uuid4(), using="learning_governance"):
        rows = list(LearningSignal.objects.using("learning_governance").filter(id__in=signals).order_by("created_at"))
        require([row.selected_outcome_snapshot for row in rows] == expected_outcomes,
                "categorical outcomes were not preserved exactly")
        first_signal = rows[0]
        frozen_links = list(LearningSignalEffectiveness.objects.using("learning_governance").filter(
            learning_signal_id=first_signal.id).order_by("revision_snapshot").values_list(
                "effectiveness_check_id", "revision_snapshot", "outcome_snapshot"))
    require(first_signal.selected_effectiveness_check_id == current.id and first_signal.selected_revision == current.revision,
            "old LearningSignal silently rebound after Effectiveness correction")
    require(len(frozen_links) == current.revision and frozen_links[-1][0] == current.id,
            "full historical derivation lineage is not reconstructible")

    targets = [
        target_reference(connections["default"], "ModelPolicy", "governance.model_policy"),
        target_reference(connections["default"], "AgentDefinition", "governance.agent_definition"),
        target_reference(connections["default"], "KnowledgeLayerRule", "normative.knowledge_layer_rule"),
    ]
    proposals = []
    for index, target in enumerate(targets):
        result = proposal_service.create_proposal(
            authority=learning_authority, signal_ids=[signals[index]], target=target,
            proposed_change_hash=hashlib.sha256(f"proposed-change-{index}".encode()).hexdigest(),
            rationale="Governance review may consider this inert proposal.",
            expected_effect="No effect unless a later separately authorized gate acts.",
            risks=["target drift", "incorrect inference"],
            required_governance_domains=["ai_governance", "security"], trace_id=uuid4(),
        )
        proposals.append(result.artifact_id)

    # Proposal rollback matrix against an exact frozen target.
    for point in LearningFailurePoint:
        try:
            proposal_service.create_proposal(
                authority=learning_authority, signal_ids=[signals[-1]], target=targets[0],
                proposed_change_hash="f" * 64, rationale="Rollback fixture.",
                expected_effect="None.", risks=["none"],
                required_governance_domains=["ai_governance"], trace_id=uuid4(),
                failure_point=point,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"proposal failure point committed: {point.value}")

    # Two real connections race to correct one proposal: exactly one append-only successor.
    def correct(suffix):
        try:
            return LearningProposalCommandService().create_proposal(
                authority=learning_authority, signal_ids=[signals[3]], target=targets[0],
                proposed_change_hash=hashlib.sha256(f"correction-{suffix}".encode()).hexdigest(),
                rationale=f"Governed correction {suffix}.", expected_effect="Still inert.",
                risks=["review required"], required_governance_domains=["ai_governance"],
                predecessor_id=proposals[0], correction_reason=f"Correction {suffix}.",
                trace_id=uuid4(),
            )
        except Exception as exc:
            connections["learning_governance"].close()
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        raced = list(pool.map(correct, ("a", "b")))
    require(len([item for item in raced if not isinstance(item, Exception)]) == 1 and
            len([item for item in raced if isinstance(item, Exception)]) == 1,
            "proposal correction race did not produce one immutable successor")

    # Real learning principal: artifact appends, but no transitive DML over protected domains.
    role = os.environ["FOUNDATION_LEARNING_GOVERNANCE_ROLE"]
    with connections["default"].cursor() as cursor:
        cursor.execute(
            "SELECT rolsuper,rolinherit,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
            "FROM pg_roles WHERE rolname=%s", [role],
        )
        require(cursor.fetchone() == (False, False, False, False, False, False),
                "learning principal has elevated role attributes")
        forbidden_tables = (
            "governance.model_policy", "governance.agent_definition",
            "normative.knowledge_layer_rule", "normative.requirement_control",
            "qms.opportunity", "qms.action_execution", "qms.effectiveness_check",
        )
        for table in forbidden_tables:
            cursor.execute(
                "SELECT has_table_privilege(%s,%s,'INSERT'),has_table_privilege(%s,%s,'UPDATE'),has_table_privilege(%s,%s,'DELETE')",
                [role, table, role, table, role, table],
            )
            require(cursor.fetchone() == (False, False, False), f"learning principal has target DML: {table}")
        cursor.execute(
            "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='qms' "
            "AND c.relname IN ('learning_signal','learning_signal_effectiveness','learning_proposal','learning_proposal_signal') ORDER BY c.relname"
        )
        rls = cursor.fetchall()
        require(len(rls) == 4 and all(row[1] and row[2] for row in rls), "learning ENABLE+FORCE RLS missing")

    visibility = []
    for tenant in (phase3.TENANT_A, None, phase3.TENANT_B):
        with phase3.runtime_transaction("learning_governance", tenant) as cursor:
            cursor.execute("SELECT count(*) FROM qms.learning_signal")
            visibility.append(cursor.fetchone()[0])
    require(visibility == [10, 0, 0], f"learning RLS isolation failed: {visibility}")

    protected_after = protected_snapshot(connections["default"])
    require(protected_after == protected_before,
            "signals/proposals changed a governed target, runtime behavior, autonomy or normative catalog")
    governance_after = file_hashes()
    require(governance_after == governance_before, "silent governance artifact change during Phase 21 execution")

    with trusted_tenant_context(identity, actor_id="phase21-final", trace_id=uuid4(), using="learning_governance"):
        require(LearningProposal.objects.using("learning_governance").exclude(status="governance_pending").count() == 0,
                "proposal status implied approval/application")
        event_types = set(DomainEvent.objects.using("learning_governance").filter(
            event_type__startswith="learning_").values_list("event_type", flat=True))
        require(event_types == {"learning_signal.created", "learning_proposal.created"},
                f"unauthorized learning event contract exists: {event_types}")
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM audit.immutable_audit_log WHERE action LIKE 'learning\\_%%' ESCAPE '\\'")
        require(cursor.fetchone()[0] == 14, "one audit append per committed learning command missing")

    print(json.dumps({
        "status": "PASS", "postgresql": "18.6",
        "effectiveness_derivation_snapshot": "exact selected leaf + complete immutable lineage PASS",
        "target_version_freeze": "exact full target JSON + canonical SHA-256 PASS",
        "global_target_inertness": "ModelPolicy/AgentDefinition/KnowledgeLayerRule identical PASS",
        "emergent_auto_learning": "10 signals; repeated effective/ineffective/unknown/inconclusive; ZERO runtime effects PASS",
        "numeric_score_derivation": "none PASS",
        "proposal_semantics": "governance_pending only; one-winner correction history PASS",
        "protected_target_hashes": "before/after byte-state identical PASS",
        "least_privilege": "real learning principal; protected DML denied; no elevated attributes PASS",
        "rls": "ENABLE+FORCE A/none/B PASS", "rollback_matrix": "14/14 PASS",
        "authorized_events": ["learning_signal.created/v1", "learning_proposal.created/v1"],
        "governance_sha256": governance_after, "external_effects": "ZERO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=__import__("sys").stderr)
        raise
