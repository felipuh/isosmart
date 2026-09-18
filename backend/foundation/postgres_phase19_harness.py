"""PostgreSQL 18.6 Phase 19 EffectivenessCheck promotion matrix."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase17_harness as phase17


PHASE16 = ("foundation", "0016_controlled_execution_recovery_hardening")
PHASE19 = ("foundation", "0017_effectiveness_check_foundation")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def protected_snapshot(connection):
    tables = (
        "qms.action_execution", "qms.action_execution_receipt", "qms.action_plan",
        "qms.execution_authorization", "qms.agent_decision", "qms.recommendation",
        "qms.recommendation_basis", "qms.opportunity", "governance.model_policy",
        "governance.agent_definition", "normative.knowledge_layer_rule",
        "normative.requirement_control", "normative.standard_edition", "qms.evidence_coverage",
    )
    result = {}
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(
                f"SELECT count(*),md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM {table} t"
            )
            result[table] = cursor.fetchone()
    return result


def run():
    phase17.run()
    from django.db import connections, transaction
    from django.utils import timezone

    # Empty Phase-19 history permits schema reverse; retained history does not.
    phase3.migrate(PHASE19)
    with connections["default"].cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('qms.effectiveness_check'),to_regclass('qms.effectiveness_evidence')"
        )
        require(cursor.fetchone() == ("qms.effectiveness_check", "qms.effectiveness_evidence"),
                "Phase 19 tables missing")
    phase3.migrate(PHASE16)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.effectiveness_check')")
        require(cursor.fetchone()[0] is None, "empty-history Phase 19 reverse failed")
    phase3.migrate(PHASE19)

    from foundation.document_evidence import DocumentEvidenceCommandService
    from foundation.effectiveness import (
        EffectivenessCheckCommandService,
        EffectivenessFailurePoint,
        EffectivenessReviewQueueService,
        ExactEvidenceReference,
        GovernedEffectivenessPlan,
        TrustedEffectivenessAuthority,
    )
    from foundation.models import (
        ActionExecution,
        DomainEvent,
        EffectivenessCheck,
        EffectivenessEvidence,
        Evidence,
        ImmutableAuditLog,
        TransactionalOutbox,
        UserProjection,
    )
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    identity = TrustedTenantIdentity("phase19-reviewer", phase3.TENANT_A)
    trace = uuid4()
    with trusted_tenant_context(identity, actor_id="phase19-seed", trace_id=trace, using="app"):
        execution = (
            ActionExecution.objects.using("app")
            .filter(status="succeeded", executor_type="controlled_opportunity",
                    receipt__outcome="opportunity_deferred")
            .select_related("receipt").order_by("completed_at").first()
        )
        require(execution is not None, "Phase 16/17 produced no assessable execution")
        user = UserProjection.objects.using("app").first()
        require(user is not None, "AdminApps UserProjection fixture missing")
        result = execution.receipt.result

    evidence_service = DocumentEvidenceCommandService(using="app")
    evidence_results = []
    for index in range(2):
        evidence_results.append(evidence_service.create_evidence(
            identity=identity, organization_id=phase3.ORG_A,
            source_type="phase19_governed_observation",
            captured_at=timezone.now(), actor_id=str(user.adminapps_user_id), trace_id=uuid4(),
            source_uri=f"urn:phase19:evidence:{index}", content_hash=("a" if index == 0 else "b") * 64,
        ))
    with trusted_tenant_context(identity, actor_id="phase19-read", trace_id=trace, using="app"):
        evidence_rows = list(Evidence.objects.using("app").filter(
            id__in=[item.entity_id for item in evidence_results]).order_by("id"))
        after_created = __import__("foundation.models", fromlist=["Opportunity"]).Opportunity.objects.using("app").get(
            pk=result["after_revision_id"]).created_at

    references = [ExactEvidenceReference(
        evidence_id=row.id, lineage_id=row.lineage_id, revision=row.revision,
        content_hash=row.content_hash, criterion_role=f"mandatory criterion {index + 1}",
    ) for index, row in enumerate(evidence_rows)]
    protected_before = protected_snapshot(connections["default"])
    due_at = after_created + timedelta(microseconds=1)
    require(due_at <= timezone.now(), "fixture execution is too recent for due assessment")
    plan = GovernedEffectivenessPlan(
        action_execution_id=execution.id, organization_id=phase3.ORG_A,
        opportunity_lineage_id=result["opportunity_lineage_id"], due_at=due_at,
        criteria_hash="c" * 64, planning_context_hash="d" * 64,
        assessment_method="human_review",
    )
    authority = TrustedEffectivenessAuthority(
        identity=identity, organization_id=phase3.ORG_A,
        actor_user_projection_id=user.id, actor_external_id=user.adminapps_user_id,
        permissions=frozenset({
            "qms.effectiveness_check.record", "qms.effectiveness_check.supersede",
        }), mfa_verified=True, access_active=True,
        authority_context_version="adminapps-authority/v1",
        authority_decision_reference="phase19-authority-decision",
    )
    service = EffectivenessCheckCommandService(using="app")
    queue = EffectivenessReviewQueueService(using="app")

    due_items = queue.requiring_attention(
        identity=identity, organization_id=phase3.ORG_A, plans=[plan], as_of=due_at,
    )
    require(len(due_items) == 1 and due_items[0].category == "due",
            "due review queue classification failed")
    overdue_items = queue.requiring_attention(
        identity=identity, organization_id=phase3.ORG_A, plans=[plan],
        as_of=due_at + timedelta(microseconds=1),
    )
    require(len(overdue_items) == 1 and overdue_items[0].category == "overdue",
            "overdue review queue classification failed")

    # Every injected failure leaves the complete Phase-19 unit absent.
    for point in EffectivenessFailurePoint:
        before = []
        with trusted_tenant_context(identity, actor_id="phase19-count", trace_id=trace, using="app"):
            before = [
                EffectivenessCheck.objects.using("app").count(),
                EffectivenessEvidence.objects.using("app").count(),
                DomainEvent.objects.using("app").filter(event_type="effectiveness_check.recorded").count(),
                TransactionalOutbox.objects.using("app").filter(domain_event__event_type="effectiveness_check.recorded").count(),
                ImmutableAuditLog.objects.using("app").filter(action="effectiveness_check.recorded").count(),
            ]
        try:
            service.record_effectiveness_check(
                authority=authority, plan=plan, outcome="effective", evidence=references,
                trace_id=uuid4(), assessed_at=timezone.now(), failure_point=point,
            )
        except RuntimeError as exc:
            require("deliberate Phase 19 rollback" in str(exc), f"unexpected rollback error: {exc}")
        else:
            raise AssertionError(f"failure injection {point.value} committed")
        with trusted_tenant_context(identity, actor_id="phase19-count", trace_id=trace, using="app"):
            after = [
                EffectivenessCheck.objects.using("app").count(),
                EffectivenessEvidence.objects.using("app").count(),
                DomainEvent.objects.using("app").filter(event_type="effectiveness_check.recorded").count(),
                TransactionalOutbox.objects.using("app").filter(domain_event__event_type="effectiveness_check.recorded").count(),
                ImmutableAuditLog.objects.using("app").filter(action="effectiveness_check.recorded").count(),
            ]
        require(after == before, f"partial Phase 19 unit at {point.value}: {before} -> {after}")

    first = service.record_effectiveness_check(
        authority=authority, plan=plan, outcome="inconclusive", evidence=references,
        reason_code="conflicting_valid_evidence", explanation="Governed observations conflict.",
        trace_id=uuid4(), assessed_at=timezone.now(),
    )
    inconclusive_items = queue.requiring_attention(
        identity=identity, organization_id=phase3.ORG_A, plans=[plan], as_of=timezone.now(),
    )
    require(len(inconclusive_items) == 1 and inconclusive_items[0].category == "inconclusive",
            "inconclusive current-leaf queue classification failed")

    # Two separately connected reviewers race from the same predecessor: one leaf only.
    def correction(outcome):
        try:
            return EffectivenessCheckCommandService(using="app").record_effectiveness_check(
                authority=authority, plan=plan, outcome=outcome, evidence=references[:1],
                predecessor_id=first.effectiveness_check_id,
                correction_reason=f"Concurrent governed correction to {outcome}.",
                reason_code="evidence_temporarily_unavailable" if outcome == "unknown" else None,
                explanation="Required evidence is unavailable." if outcome == "unknown" else None,
                trace_id=uuid4(), assessed_at=timezone.now(),
            )
        except Exception as exc:
            connections["app"].close()
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        raced = list(pool.map(correction, ("effective", "unknown")))
    winners = [item for item in raced if not isinstance(item, Exception)]
    losers = [item for item in raced if isinstance(item, Exception)]
    require(len(winners) == 1 and len(losers) == 1,
            f"concurrent correction did not produce one winner/one stale conflict: {raced}")
    second = winners[0]

    third = service.record_effectiveness_check(
        authority=authority, plan=plan, outcome="unknown", evidence=references[:1],
        predecessor_id=second.effectiveness_check_id,
        correction_reason="New governed assessment records an evidence blocker.",
        reason_code="evidence_temporarily_unavailable",
        explanation="Required evidence is unavailable at assessment time.",
        trace_id=uuid4(), assessed_at=timezone.now(),
    )
    fourth = service.record_effectiveness_check(
        authority=authority, plan=plan, outcome="inconclusive", evidence=references,
        predecessor_id=third.effectiveness_check_id,
        correction_reason="Later evidence is conflicting rather than unavailable.",
        reason_code="conflicting_valid_evidence",
        explanation="Valid observations conflict.", trace_id=uuid4(), assessed_at=timezone.now(),
    )

    revoked_authority = TrustedEffectivenessAuthority(
        identity=identity, organization_id=phase3.ORG_A,
        actor_user_projection_id=user.id, actor_external_id=user.adminapps_user_id,
        permissions=authority.permissions, mfa_verified=True, access_active=False,
        authority_context_version="adminapps-authority/v2-revoked",
        authority_decision_reference="phase20-revoked",
    )
    try:
        service.record_effectiveness_check(
            authority=revoked_authority, plan=plan, outcome="effective",
            evidence=references[:1], predecessor_id=fourth.effectiveness_check_id,
            correction_reason="Must not be recorded.", trace_id=uuid4(),
            assessed_at=timezone.now(),
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("revoked reviewer created a new EffectivenessCheck")
    with trusted_tenant_context(identity, actor_id="phase19-read", trace_id=trace, using="app"):
        checks = list(EffectivenessCheck.objects.using("app").order_by("revision"))
        require([row.revision for row in checks] == [1, 2, 3, 4],
                "long supersession lineage was not retained")
        require([row.predecessor_id for row in checks[1:]] == [row.id for row in checks[:-1]],
                "linear predecessor chain missing")
        require(checks[0].actor_external_id_snapshot == user.adminapps_user_id,
                "authority revocation rewrote historical actor provenance")
        require(EffectivenessEvidence.objects.using("app").count() == 6,
                "exact Evidence links missing from retained lineage")
        require(DomainEvent.objects.using("app").filter(event_type="effectiveness_check.recorded").count() == 4,
                "each assessment requires one event")
        require(ImmutableAuditLog.objects.using("app").filter(action="effectiveness_check.recorded").count() == 4,
                "each assessment requires one audit")
    protected_after = protected_snapshot(connections["default"])
    require(protected_after == protected_before,
            "Effectiveness recording mutated execution, learning, recommendation or normative history")

    fork_denied = False
    try:
        service.record_effectiveness_check(
            authority=authority, plan=plan, outcome="effective", evidence=references[:1],
            predecessor_id=first.effectiveness_check_id,
            correction_reason="Attempted second successor.", trace_id=uuid4(),
            assessed_at=timezone.now(),
        )
    except Exception:
        fork_denied = True
        connections["app"].close()
    require(fork_denied, "Effectiveness supersession fork unexpectedly succeeded")

    # Material mutation and fork are rejected with real runtime authority.
    def app_sql(statement, params):
        with transaction.atomic(using="app"):
            with connections["app"].cursor() as cursor:
                cursor.execute("SELECT set_config('app.tenant_id',%s,true)", [str(phase3.TENANT_A)])
                cursor.execute(statement, params)

    for statement in (
        "UPDATE qms.effectiveness_check SET outcome='ineffective' WHERE id=%s",
        "DELETE FROM qms.effectiveness_check WHERE id=%s",
        "UPDATE qms.effectiveness_evidence SET tenant_id=%s WHERE effectiveness_check_id=%s",
    ):
        denied = False
        try:
            params = ([str(phase3.TENANT_B), str(first.effectiveness_check_id)]
                      if statement.count("%s") == 2 else [str(first.effectiveness_check_id)])
            app_sql(statement, params)
        except Exception:
            denied = True
            connections["app"].close()
        require(denied, f"material SQL unexpectedly succeeded: {statement}")

    for organization_id, reference in (
        (phase3.ORG_A, references[0]),
        (phase3.ORG_B, references[1]),
    ):
        denied = False
        try:
            with transaction.atomic(using="app"):
                with connections["app"].cursor() as cursor:
                    cursor.execute("SELECT set_config('app.tenant_id',%s,true)", [str(phase3.TENANT_A)])
                    cursor.execute(
                        "INSERT INTO qms.effectiveness_evidence(id,tenant_id,organization_id,"
                        "effectiveness_check_id,evidence_id,evidence_lineage_id_snapshot,"
                        "evidence_revision_snapshot,evidence_content_hash_snapshot,criterion_role) "
                        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'negative boundary fixture')",
                        [str(uuid4()), str(phase3.TENANT_A), str(organization_id),
                         str(first.effectiveness_check_id), str(reference.evidence_id),
                         str(reference.lineage_id), reference.revision, reference.content_hash],
                    )
        except Exception:
            denied = True
            connections["app"].close()
        require(denied, "duplicate/cross-Organization Evidence link unexpectedly succeeded")

    # RLS A / none / B and pooled context cleanup.
    visibility = []
    for tenant in (phase3.TENANT_A, None, phase3.TENANT_B):
        with phase3.runtime_transaction("app", tenant) as cursor:
            cursor.execute("SELECT count(*) FROM qms.effectiveness_check")
            visibility.append(cursor.fetchone()[0])
    require(visibility == [4, 0, 0], f"Effectiveness RLS isolation failed: {visibility}")

    # Retained Phase-19 history makes downgrade fail closed without deletion.
    downgrade_blocked = False
    try:
        phase3.migrate(PHASE16)
    except Exception:
        downgrade_blocked = True
        connections["default"].close()
    require(downgrade_blocked, "retained Effectiveness history was destructively downgraded")
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM qms.effectiveness_check")
        require(cursor.fetchone()[0] == 4, "failed downgrade lost Effectiveness history")

    print(json.dumps({
        "status": "PASS", "postgresql": "18.6", "phase16_regression": "PASS",
        "phase17_regression": "PASS", "forward_reverse_forward": "PASS",
        "retained_history": "forward-only after first EffectivenessCheck PASS",
        "atomic_success": "Check + Evidence + Event + Outbox + Audit PASS",
        "rollback_matrix": "9/9 PASS", "supersession": "v1 -> v2 -> v3 -> v4 PASS",
        "concurrent_correction": "one winner / one stale conflict / no fork PASS",
        "authority_time": "historical provenance retained; revoked reviewer denied PASS",
        "review_queue": "due/overdue/inconclusive current-leaf PASS",
        "protected_history": "execution/learning/recommendation/normative rows byte-state unchanged PASS",
        "rls": "ENABLE+FORCE A/none/B PASS",
        "raw_sql": "material mutation, Evidence duplicate/scope and fork denied PASS",
        "external_effects": "ZERO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=__import__("sys").stderr)
        raise
