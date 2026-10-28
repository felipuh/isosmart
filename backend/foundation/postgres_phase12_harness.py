"""Blocking PostgreSQL 18.6 matrix for AgentDecision and Human Decision Gate."""

import json
import os
import sys
from uuid import UUID, uuid4

import postgres_foundation_harness as phase3
import postgres_phase11_harness as phase11


PHASE11_MIGRATION = ("foundation", "0011_agent_definition_run_provenance_foundation")
PHASE12_MIGRATION = ("foundation", "0012_agent_decision_human_decision_gate_foundation")
TENANT_TABLES = ("agent_decision", "approval")
ADMINAPPS_USER_A = UUID("50000000-0000-4000-8000-000000000001")
ADMINAPPS_USER_B = UUID("60000000-0000-4000-8000-000000000001")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_error(operation, fragment=None):
    try:
        operation()
    except Exception as exc:
        if fragment:
            require(fragment.lower() in str(exc).lower(), f"unexpected error: {exc}")
        return
    raise AssertionError("operation unexpectedly succeeded")


def visible(alias, table, tenant=None):
    with phase3.runtime_transaction(alias, tenant) as cursor:
        cursor.execute(f"SELECT count(*) FROM qms.{table}")
        return cursor.fetchone()[0]


def run():
    phase11.run()
    phase3.migrate(PHASE12_MIGRATION)

    from django.db import connections
    from foundation.agent_runtime import AgentCatalogCommandService, AgentRunCommandService
    from foundation.audit import verify_audit_stream
    from foundation.canonical import canonical_hash
    from foundation.human_decision import (
        AgentDecisionCommandService,
        AuthorizedHumanContext,
        HumanDecisionGateService,
    )
    from foundation.models import (
        AgentDecision, AgentDefinition, AgentRun, AgentRunInput, Approval,
        DomainEvent, Evidence, ImmutableAuditLog, KnowledgeLayerRule, ModelPolicy,
        Recommendation, RecommendationBasis, RequirementControl, TransactionalOutbox,
        UserProjection,
    )
    from foundation.projection_contract import validate_projection_event
    from foundation.projection_writer import ProjectionWriterService
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    migrator = connections["default"]
    app_role = os.environ["FOUNDATION_APP_ROLE"]
    worker_role = os.environ["FOUNDATION_WORKER_ROLE"]
    projector_role = os.environ["FOUNDATION_PROJECTOR_ROLE"]
    audit_role = os.environ["FOUNDATION_AUDIT_WRITER_ROLE"]
    normative_role = os.environ["FOUNDATION_NORMATIVE_CURATOR_ROLE"]
    agent_curator_role = os.environ["FOUNDATION_AGENT_CATALOG_CURATOR_ROLE"]
    human_role = os.environ["FOUNDATION_HUMAN_APPROVER_ROLE"]
    unauthorized_roles = (worker_role, projector_role, audit_role, normative_role, agent_curator_role)

    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,r.rolname "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='qms' AND c.relname=ANY(%s)",
            [list(TENANT_TABLES)],
        )
        rows = cursor.fetchall()
        require(len(rows) == 2 and all(row[1] and row[2] for row in rows),
                "Phase 12 ENABLE/FORCE RLS missing")
        require(all(row[3] not in (app_role, worker_role, projector_role, audit_role,
                                   normative_role, agent_curator_role, human_role) for row in rows),
                "runtime principal owns Phase 12 table")
        for table in TENANT_TABLES:
            cursor.execute("SELECT cmd FROM pg_policies WHERE schemaname='qms' AND tablename=%s", [table])
            require({row[0] for row in cursor.fetchall()} == {"SELECT", "INSERT", "UPDATE", "DELETE", "ALL"},
                    f"Phase 12 policy matrix incomplete: {table}")
        cursor.execute("SELECT rolcanlogin,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s", [human_role])
        require(cursor.fetchone() == (True, False, False), "human approver principal is privileged")
        cursor.execute(
            "SELECT has_table_privilege(%s,'qms.approval','INSERT'),"
            "has_function_privilege(%s,'qms.foundation_0012_record_human_approval(uuid,uuid,uuid,uuid,uuid,text,text,uuid,uuid,text,timestamptz,uuid)','EXECUTE'),"
            "has_table_privilege(%s,'qms.agent_decision','INSERT'),"
            "has_table_privilege(%s,'qms.recommendation','UPDATE'),"
            "has_table_privilege(%s,'qms.risk','UPDATE')",
            [human_role, human_role, human_role, human_role, human_role],
        )
        require(cursor.fetchone() == (False, True, False, False, False),
                "human approver escaped the controlled least-privilege boundary")
        for role in unauthorized_roles:
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.approval','INSERT'),"
                "has_function_privilege(%s,'qms.foundation_0012_record_human_approval(uuid,uuid,uuid,uuid,uuid,text,text,uuid,uuid,text,timestamptz,uuid)','EXECUTE')",
                [role, role],
            )
            require(cursor.fetchone() == (False, False), f"unauthorized Approval path: {role}")

    identity_a = TrustedTenantIdentity("phase12-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase12-b", phase3.TENANT_B)
    worker_actor = "phase12-synthetic-worker"
    curator_actor = "phase12-synthetic-agent-curator"

    catalog = AgentCatalogCommandService(using="agent_catalog_curator")
    policy3_id = catalog.create_model_policy(
        policy_key="phase12-human-gate-policy", version="v1",
        approved_models=["synthetic-model-v2"], data_classes=["NON-OFFICIAL TEST FIXTURE"],
        guardrails={"allowed_capabilities": ["synthetic-analysis"], "autonomy_max": 2},
        human_gate_rules={"required_autonomy_levels": ["A2"],
                          "required_role": "quality_approver"},
        actor_id=curator_actor, trace_id=uuid4(),
    )
    catalog.publish_model_policy(model_policy_id=policy3_id, actor_id=curator_actor, trace_id=uuid4())
    definition3_id = catalog.create_agent_definition(
        agent_key="phase12-human-gate-agent", name="NON-OFFICIAL Phase 12 Gate Agent",
        version="v1", purpose="Synthetic Phase 12 gate fixture",
        capability="synthetic-analysis", autonomy_max=2, model_policy_id=policy3_id,
        actor_id=curator_actor, trace_id=uuid4(),
    )
    catalog.publish_agent_definition(agent_definition_id=definition3_id,
                                     actor_id=curator_actor, trace_id=uuid4())

    rule2 = KnowledgeLayerRule.objects.using("default").get(
        rule_key="phase11-guidance", version="v2",
    )
    control2 = RequirementControl.objects.using("default").filter(
        standard_edition__standard__code="P11-TARGET", standard_edition__edition="edition-2",
    ).get()

    def latest_evidence(identity):
        with trusted_tenant_context(identity, actor_id=worker_actor, trace_id=uuid4(), using="worker"):
            return Evidence.objects.using("worker").order_by("-revision").first()

    evidence_a = latest_evidence(identity_a)
    evidence_b = latest_evidence(identity_b)
    run_service = AgentRunCommandService(using="worker")
    common_run = dict(
        agent_definition_id=definition3_id, model_policy_id=policy3_id,
        capability="synthetic-analysis", requested_autonomy=2, model_provider="synthetic",
        model_identifier="synthetic-model-v2", model_version="model-v2",
        prompt_version="prompt-v2", rule_bundle_version="bundle-v2",
        actor_id=worker_actor,
    )

    def completed_run(identity, organization_id, evidence):
        frozen_input = {
            "standard_edition_id": control2.standard_edition_id,
            "requirement_control_id": control2.id,
            "knowledge_layer_rule_id": rule2.id,
            "evidence_id": evidence.id,
        }
        started = run_service.start_agent_run(
            identity=identity, organization_id=organization_id, inputs=[frozen_input],
            trace_id=uuid4(), **common_run,
        )
        completed = run_service.complete_agent_run_with_recommendation(
            identity=identity, agent_run_id=started.agent_run_id,
            title="NON-OFFICIAL PHASE 12 recommendation",
            body="SYNTHETIC MODEL OUTPUT. Advisory only; no action executed.",
            confidence="0.8000", assumptions=["Synthetic fixture"],
            basis=[dict(frozen_input, rationale="NON-OFFICIAL exact Phase 12 basis")],
            actor_id=worker_actor, impact="synthetic",
        )
        return started, completed

    started_a, completed_a = completed_run(identity_a, phase3.ORG_A, evidence_a)
    started_b, completed_b = completed_run(identity_b, phase3.ORG_B, evidence_b)
    decision_service = AgentDecisionCommandService(using="worker")

    before_ceiling = visible("worker", "agent_decision", phase3.TENANT_A)
    expect_error(lambda: decision_service.record_agent_decision(
        identity=identity_a, agent_run_id=started_a.agent_run_id,
        decision_type="proposed_material_decision", payload={"proposal": "synthetic"},
        confidence="0.8000", explainability={"basis": "exact frozen provenance"},
        decision_autonomy=3, actor_id=worker_actor,
    ), "ceiling")
    require(visible("worker", "agent_decision", phase3.TENANT_A) == before_ceiling,
            "policy ceiling rejection persisted partial AgentDecision")

    decision_a = decision_service.record_agent_decision(
        identity=identity_a, agent_run_id=started_a.agent_run_id,
        decision_type="proposed_material_decision", payload={"proposal": "synthetic"},
        confidence="0.8000", explainability={"basis": "exact frozen provenance"},
        decision_autonomy=2, actor_id=worker_actor,
    )
    decision_b = decision_service.record_agent_decision(
        identity=identity_b, agent_run_id=started_b.agent_run_id,
        decision_type="proposed_material_decision", payload={"proposal": "synthetic-b"},
        confidence="0.7000", explainability={"basis": "exact frozen provenance"},
        decision_autonomy=2, actor_id=worker_actor,
    )
    require(decision_a.recommendation_id == completed_a.recommendation_id and
            decision_b.recommendation_id == completed_b.recommendation_id and
            decision_a.human_gate_required, "exact run/recommendation or policy gate failed")

    def resolved_authority(identity, adminapps_user_id):
        with trusted_tenant_context(identity, actor_id=adminapps_user_id,
                                    trace_id=uuid4(), using="human_approver"):
            user = UserProjection.objects.using("human_approver").get(
                adminapps_user_id=adminapps_user_id,
            )
        return AuthorizedHumanContext(
            identity=identity, user_projection_id=user.id,
            adminapps_user_id=adminapps_user_id,
            authorized_roles=("quality_approver",),
            authority_source="controlled_test_fixture",
        )

    ProjectionWriterService(using="projector").apply(validate_projection_event({
        "event_id": "12121212-1212-4212-8212-121212121212",
        "event_type": "user.updated", "schema_version": 1, "source": "adminapps",
        "source_version": 3, "occurred_at": "2026-08-17T22:00:00Z",
        "trace_id": "12121212-aaaa-4aaa-8aaa-121212121212",
        "aggregate_type": "user", "aggregate_id": str(ADMINAPPS_USER_A),
        "adminapps_tenant_id": "10000000-0000-4000-8000-000000000001",
        "payload": {"lifecycle_status": "active"},
    }))
    authority_a = resolved_authority(identity_a, ADMINAPPS_USER_A)
    authority_b = resolved_authority(identity_b, ADMINAPPS_USER_B)
    human_gate = HumanDecisionGateService(using="human_approver")

    before_sources = None
    with trusted_tenant_context(identity_a, actor_id=worker_actor, trace_id=uuid4(), using="worker"):
        before_sources = canonical_hash({
            "recommendation": list(Recommendation.objects.using("worker").filter(id=completed_a.recommendation_id).values())[0],
            "basis": list(RecommendationBasis.objects.using("worker").filter(recommendation_id=completed_a.recommendation_id).values()),
            "inputs": list(AgentRunInput.objects.using("worker").filter(agent_run_id=started_a.agent_run_id).values()),
        })
    approval_a = human_gate.record_human_approval(
        authority=authority_a, agent_decision_id=decision_a.decision_id,
        comments="NON-OFFICIAL TEST FIXTURE: approved for governance only.", trace_id=uuid4(),
    )
    approval_b = human_gate.record_human_rejection(
        authority=authority_b, agent_decision_id=decision_b.decision_id,
        comments="NON-OFFICIAL TEST FIXTURE rejection.", trace_id=uuid4(),
    )

    with trusted_tenant_context(identity_a, actor_id=ADMINAPPS_USER_A,
                                trace_id=uuid4(), using="human_approver"):
        recorded = Approval.objects.using("human_approver").get(id=approval_a.approval_id)
        exact_decision = AgentDecision.objects.using("human_approver").get(id=recorded.agent_decision_id)
        require(recorded.actor_type == "human" and recorded.decision == "approve" and
                recorded.required_role == "quality_approver" and
                recorded.adminapps_user_id_snapshot == ADMINAPPS_USER_A,
                "human actor provenance failed")
        require(recorded.recommendation_id == exact_decision.recommendation_id == completed_a.recommendation_id,
                "Approval/Decision/Recommendation consistency failed")
    with trusted_tenant_context(identity_a, actor_id=worker_actor,
                                trace_id=uuid4(), using="worker"):
        require(verify_audit_stream(tenant_id=phase3.TENANT_A, stream_type="approval",
                                    stream_id=recorded.id, using="worker"),
                "Approval audit chain failed")

    with trusted_tenant_context(identity_a, actor_id=worker_actor, trace_id=uuid4(), using="worker"):
        after_sources = canonical_hash({
            "recommendation": list(Recommendation.objects.using("worker").filter(id=completed_a.recommendation_id).values())[0],
            "basis": list(RecommendationBasis.objects.using("worker").filter(recommendation_id=completed_a.recommendation_id).values()),
            "inputs": list(AgentRunInput.objects.using("worker").filter(agent_run_id=started_a.agent_run_id).values()),
        })
    require(before_sources == after_sources, "Approval mutated Recommendation/Basis/AgentRunInput")

    def approval_counts():
        with trusted_tenant_context(identity_a, actor_id=ADMINAPPS_USER_A,
                                    trace_id=uuid4(), using="human_approver"):
            governed_counts = (
                Approval.objects.using("human_approver").count(),
                DomainEvent.objects.using("human_approver").filter(event_type="approval.recorded").count(),
                TransactionalOutbox.objects.using("human_approver").filter(
                    domain_event__event_type="approval.recorded").count(),
            )
        with trusted_tenant_context(identity_a, actor_id=worker_actor,
                                    trace_id=uuid4(), using="worker"):
            audit_count = ImmutableAuditLog.objects.using("worker").filter(
                action="approval.recorded").count()
        return governed_counts + (audit_count,)

    rollback_before = approval_counts()
    expect_error(lambda: human_gate.request_human_changes(
        authority=authority_a, agent_decision_id=decision_a.decision_id,
        comments="rollback fixture", trace_id=uuid4(), fail_before_commit=True,
    ), "rollback after audit")
    require(approval_counts() == rollback_before, "Approval rollback left partial state")

    worker_human_gate = HumanDecisionGateService(using="worker")
    expect_error(lambda: worker_human_gate.record_human_approval(
        authority=authority_a, agent_decision_id=decision_a.decision_id,
        comments="worker forgery", trace_id=uuid4(),
    ), "permission denied")

    with migrator.cursor() as cursor:
        for sql, params, fragment in (
            ("UPDATE qms.approval SET decision='reject' WHERE id=%s", [str(approval_a.approval_id)], "append-only"),
            ("UPDATE qms.approval SET decided_by_id=(SELECT id FROM qms.user_projection WHERE tenant_id=%s LIMIT 1) WHERE id=%s", [str(phase3.TENANT_B),str(approval_a.approval_id)], "append-only"),
            ("UPDATE qms.approval SET comments='rewrite' WHERE id=%s", [str(approval_a.approval_id)], "append-only"),
            ("UPDATE qms.approval SET agent_decision_id=%s WHERE id=%s", [str(decision_b.decision_id),str(approval_a.approval_id)], "append-only"),
            ("UPDATE qms.approval SET tenant_id=%s WHERE id=%s", [str(phase3.TENANT_B),str(approval_a.approval_id)], "append-only"),
            ("DELETE FROM qms.approval WHERE id=%s", [str(approval_a.approval_id)], "append-only"),
            ("UPDATE qms.agent_decision SET recommendation_id=%s WHERE id=%s", [str(completed_b.recommendation_id),str(decision_a.decision_id)], "append-only"),
        ):
            expect_error(lambda s=sql,p=params: cursor.execute(s,p), fragment)
            migrator.rollback()

    # A4 remains metadata only, even when a decision is recorded.
    a4_policy_id = catalog.create_model_policy(
        policy_key="phase12-a4-policy", version="v1",
        approved_models=["synthetic-model-v2"], data_classes=["NON-OFFICIAL TEST FIXTURE"],
        guardrails={"allowed_capabilities": ["synthetic-analysis"], "autonomy_max": 4},
        human_gate_rules={"required_autonomy_levels": [], "required_role": "quality_approver"},
        actor_id=curator_actor, trace_id=uuid4(),
    )
    catalog.publish_model_policy(model_policy_id=a4_policy_id, actor_id=curator_actor, trace_id=uuid4())
    a4_definition_id = catalog.create_agent_definition(
        agent_key="phase12-a4-agent", name="NON-OFFICIAL Phase 12 A4 Agent", version="v1",
        purpose="Synthetic A4 no-execution fixture", capability="synthetic-analysis",
        autonomy_max=4, model_policy_id=a4_policy_id, actor_id=curator_actor, trace_id=uuid4(),
    )
    catalog.publish_agent_definition(agent_definition_id=a4_definition_id,
                                     actor_id=curator_actor, trace_id=uuid4())
    a4_input = {"standard_edition_id": control2.standard_edition_id,
                "requirement_control_id": control2.id,
                "knowledge_layer_rule_id": rule2.id, "evidence_id": evidence_a.id}
    a4_started = run_service.start_agent_run(
        identity=identity_a, organization_id=phase3.ORG_A,
        agent_definition_id=a4_definition_id, model_policy_id=a4_policy_id,
        capability="synthetic-analysis", requested_autonomy=4, model_provider="synthetic",
        model_identifier="synthetic-model-v2", model_version="model-v2",
        prompt_version="prompt-v2", rule_bundle_version="bundle-v2", inputs=[a4_input],
        actor_id=worker_actor, trace_id=uuid4(),
    )
    run_service.complete_agent_run_with_recommendation(
        identity=identity_a, agent_run_id=a4_started.agent_run_id,
        title="NON-OFFICIAL A4 recommendation", body="SYNTHETIC MODEL OUTPUT. No execution.",
        confidence="0.5000", assumptions=[],
        basis=[dict(a4_input, rationale="NON-OFFICIAL A4 exact basis")], actor_id=worker_actor,
    )
    a4_decision = decision_service.record_agent_decision(
        identity=identity_a, agent_run_id=a4_started.agent_run_id, decision_type="a4_governance_metadata",
        payload={"execution": False}, confidence="0.5000",
        explainability={"phase": 12}, decision_autonomy=4, actor_id=worker_actor,
    )
    require(not a4_decision.human_gate_required, "A4 policy was reinterpreted as an automatic gate")
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.action_execution')")
        require(cursor.fetchone()[0] is None, "A4 created ActionExecution")

    # Publish later catalog versions; historical approval stays on v3/run/Recommendation.
    policy4_id = catalog.revise_model_policy(
        previous_revision_id=policy3_id, version="v2", approved_models=["synthetic-model-v4"],
        data_classes=["NON-OFFICIAL TEST FIXTURE"],
        guardrails={"allowed_capabilities": ["synthetic-analysis"], "autonomy_max": 1},
        human_gate_rules={"required_autonomy_levels": ["A1"], "required_role": "future_role"},
        actor_id=curator_actor, trace_id=uuid4(),
    )
    catalog.publish_model_policy(model_policy_id=policy4_id, actor_id=curator_actor, trace_id=uuid4())
    definition4_id = catalog.revise_agent_definition(
        previous_revision_id=definition3_id, version="v2", purpose="future synthetic fixture",
        capability="synthetic-analysis", autonomy_max=1, model_policy_id=policy4_id,
        actor_id=curator_actor, trace_id=uuid4(),
    )
    catalog.publish_agent_definition(agent_definition_id=definition4_id,
                                     actor_id=curator_actor, trace_id=uuid4())
    with trusted_tenant_context(identity_a, actor_id=ADMINAPPS_USER_A,
                                trace_id=uuid4(), using="human_approver"):
        frozen_decision = AgentDecision.objects.using("human_approver").get(id=decision_a.decision_id)
        frozen_run = AgentRun.objects.using("human_approver").get(id=frozen_decision.agent_run_id)
        frozen_approval = Approval.objects.using("human_approver").get(id=approval_a.approval_id)
        require((frozen_run.agent_definition_id, frozen_run.model_policy_id,
                 frozen_decision.recommendation_id, frozen_approval.required_role) ==
                (definition3_id, policy3_id, completed_a.recommendation_id, "quality_approver"),
                "future versions reinterpreted frozen approval provenance")

    app_matrix = {table: [visible("app",table,phase3.TENANT_A), visible("app",table),
                          visible("app",table,phase3.TENANT_B)] for table in TENANT_TABLES}
    human_matrix = {table: [visible("human_approver",table,phase3.TENANT_A),
                            visible("human_approver",table),
                            visible("human_approver",table,phase3.TENANT_B)] for table in TENANT_TABLES}
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0
                for values in app_matrix.values()), "app A/none/B isolation failed")
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0
                for values in human_matrix.values()), "human A/none/B isolation failed")
    try:
        with phase3.runtime_transaction("human_approver", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.approval")
            raise RuntimeError("intentional Phase 12 rollback context")
    except RuntimeError:
        pass
    require(visible("human_approver", "approval") == 0 and
            visible("human_approver", "approval", phase3.TENANT_B) == 1,
            "rollback/pool human tenant context leaked")

    phase3.migrate(PHASE11_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.agent_run'),to_regclass('qms.agent_decision'),to_regclass('qms.approval')")
        require(cursor.fetchone() == ("qms.agent_run", None, None), "Phase 12 reverse damaged Phase 11")
    phase3.migrate(PHASE12_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.agent_decision'),to_regclass('qms.approval'),to_regclass('qms.action_execution')")
        require(cursor.fetchone() == ("qms.agent_decision", "qms.approval", None),
                "Phase 12 second forward or no-execution invariant failed")

    print(json.dumps({
        "status": "PASS",
        "migration": "0012_agent_decision_human_decision_gate_foundation",
        "source_semantics": "append-only AgentDecision and Approval; approve/reject/request_changes only",
        "exact_linkage": "Approval -> Decision -> Run -> Definition/Policy + Recommendation/Basis/Input",
        "human_principal": "LOGIN non-superuser NOBYPASSRLS non-owner; controlled function only",
        "authorization": "trusted context + policy-required role; worker/system self-approval denied",
        "atomic_success": "Decision/Approval + Event + Outbox + Audit PASS",
        "atomic_rollback": "post-audit failure left zero Approval/Event/Outbox/Audit delta",
        "immutability": "raw UPDATE/DELETE/re-point/tenant reassignment denied",
        "policy_ceiling": "A2 run rejected A3 decision with zero partial state",
        "a4": "metadata only; no ActionExecution or business mutation",
        "rls": {"app": app_matrix, "human_approver": human_matrix},
        "pool": "A -> none -> B and rollback -> none -> B PASS",
        "forward_reverse_forward": "0001 -> ... -> 0012 -> 0011 -> 0012 PASS",
    }, default=str, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
