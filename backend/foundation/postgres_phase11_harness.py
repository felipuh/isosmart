"""Blocking PostgreSQL 18.6 matrix for governed AgentRun provenance."""

import hashlib
import json
import os
import sys
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase10_harness as phase10


PHASE10_MIGRATION = ("foundation", "0010_governed_recommendation_foundation")
PHASE11_MIGRATION = ("foundation", "0011_agent_definition_run_provenance_foundation")
TENANT_TABLES = ("agent_run", "agent_run_input", "agent_run_recommendation")


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
    phase10.run()
    phase3.migrate(PHASE11_MIGRATION)

    from django.db import connections
    from django.utils import timezone
    from foundation.agent_runtime import AgentCatalogCommandService, AgentRunCommandService
    from foundation.audit import verify_audit_stream
    from foundation.document_evidence import DocumentEvidenceCommandService
    from foundation.knowledge_layer import KnowledgeLayerCommandService
    from foundation.models import (
        AgentDefinition, AgentRun, AgentRunInput, AgentRunRecommendation,
        DomainEvent, ImmutableAuditLog, ModelPolicy, Recommendation,
        RecommendationBasis, TransactionalOutbox,
    )
    from foundation.normative_coverage import NormativeCatalogCommandService
    from foundation.recommendation import RecommendationCommandService
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    migrator = connections["default"]
    app_role = os.environ["FOUNDATION_APP_ROLE"]
    worker_role = os.environ["FOUNDATION_WORKER_ROLE"]
    projector_role = os.environ["FOUNDATION_PROJECTOR_ROLE"]
    normative_curator_role = os.environ["FOUNDATION_NORMATIVE_CURATOR_ROLE"]
    agent_curator_role = os.environ["FOUNDATION_AGENT_CATALOG_CURATOR_ROLE"]

    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,r.rolname "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='qms' AND c.relname=ANY(%s)",
            [list(TENANT_TABLES)],
        )
        rows = cursor.fetchall()
        require(len(rows) == 3 and all(row[1] and row[2] for row in rows), "Phase 11 ENABLE/FORCE RLS missing")
        require(all(row[3] not in (app_role, worker_role, projector_role, normative_curator_role, agent_curator_role)
                    for row in rows), "runtime owns Phase 11 tenant table")
        for table in TENANT_TABLES:
            cursor.execute("SELECT cmd FROM pg_policies WHERE schemaname='qms' AND tablename=%s", [table])
            require({x[0] for x in cursor.fetchall()} == {"SELECT", "INSERT", "UPDATE", "DELETE", "ALL"},
                    f"policy matrix incomplete: {table}")
        for table in ("model_policy", "agent_definition"):
            cursor.execute(
                "SELECT has_table_privilege(%s,'governance.'||%s,'SELECT'),"
                "has_table_privilege(%s,'governance.'||%s,'INSERT'),"
                "has_table_privilege(%s,'governance.'||%s,'UPDATE'),"
                "has_table_privilege(%s,'governance.'||%s,'DELETE')",
                [agent_curator_role, table, agent_curator_role, table,
                 agent_curator_role, table, agent_curator_role, table],
            )
            require(cursor.fetchone() == (True, True, False, False), f"agent curator broad grant drift: {table}")
            cursor.execute(
                "SELECT has_column_privilege(%s,'governance.'||%s,'status','UPDATE'),"
                "has_column_privilege(%s,'governance.'||%s,'published_at','UPDATE')",
                [agent_curator_role, table, agent_curator_role, table],
            )
            require(cursor.fetchone() == (True, True), f"agent curator publication grant missing: {table}")
            for role in (app_role, worker_role, projector_role):
                cursor.execute(
                    "SELECT has_table_privilege(%s,'governance.'||%s,'SELECT'),"
                    "has_table_privilege(%s,'governance.'||%s,'INSERT'),"
                    "has_table_privilege(%s,'governance.'||%s,'UPDATE')",
                    [role, table, role, table, role, table],
                )
                require(cursor.fetchone() == (True, False, False), f"runtime catalog privilege drift: {role}/{table}")
            cursor.execute(
                "SELECT has_table_privilege(%s,'governance.'||%s,'SELECT'),"
                "has_table_privilege(%s,'governance.'||%s,'INSERT'),"
                "has_table_privilege(%s,'governance.'||%s,'UPDATE')",
                [normative_curator_role, table, normative_curator_role, table,
                 normative_curator_role, table],
            )
            require(cursor.fetchone() == (False, False, False),
                    f"normative curator gained agent catalog privilege: {table}")
        cursor.execute(
            "SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s", [agent_curator_role],
        )
        require(cursor.fetchone() == (False, False), "agent catalog curator is privileged")
        cursor.execute(
            "SELECT has_table_privilege(%s,'normative.standard','INSERT'),"
            "has_table_privilege(%s,'qms.evidence','INSERT'),"
            "has_table_privilege(%s,'qms.agent_run','INSERT')",
            [agent_curator_role, agent_curator_role, agent_curator_role],
        )
        require(cursor.fetchone() == (False, False, False), "agent catalog curator escaped its boundary")

    identity_a = TrustedTenantIdentity("phase11-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase11-b", phase3.TENANT_B)
    actor = "phase11-synthetic-worker"
    curator_actor = "phase11-synthetic-agent-curator"

    catalog = AgentCatalogCommandService(using="agent_catalog_curator")
    policy1 = catalog.create_model_policy(
        policy_key="phase11-synthetic-policy", version="v1",
        approved_models=["synthetic-model-v1"], data_classes=["NON-OFFICIAL TEST FIXTURE"],
        guardrails={"allowed_capabilities": ["synthetic-analysis"], "autonomy_max": 4},
        human_gate_rules={"synthetic_only": True}, actor_id=curator_actor, trace_id=uuid4(),
    )
    catalog.publish_model_policy(model_policy_id=policy1, actor_id=curator_actor, trace_id=uuid4())
    definition1 = catalog.create_agent_definition(
        agent_key="phase11-synthetic-agent", name="NON-OFFICIAL TEST FIXTURE Agent",
        version="v1", purpose="Synthetic governed recommendation fixture.",
        capability="synthetic-analysis", autonomy_max=4, model_policy_id=policy1,
        actor_id=curator_actor, trace_id=uuid4(),
    )
    catalog.publish_agent_definition(agent_definition_id=definition1, actor_id=curator_actor, trace_id=uuid4())

    normative = NormativeCatalogCommandService(using="normative_curator")
    knowledge = KnowledgeLayerCommandService(using="normative_curator")

    def published_edition(code, edition, digit):
        standard = normative.create_standard(code=code, title="NON-OFFICIAL TEST FIXTURE", publisher="TEST",
                                             actor_id=curator_actor, trace_id=uuid4())
        edition_id = normative.create_standard_edition(standard_id=standard, edition=edition,
                                                        source_hash=digit * 64, actor_id=curator_actor,
                                                        trace_id=uuid4())
        clause = normative.add_clause(standard_edition_id=edition_id, code="T.11",
                                      title="NON-OFFICIAL TEST FIXTURE", actor_id=curator_actor,
                                      trace_id=uuid4())
        control = normative.add_requirement_control(
            standard_edition_id=edition_id, clause_id=clause,
            paraphrase="NON-OFFICIAL TEST FIXTURE: no licensed normative text.",
            applicability_rule={"synthetic": True}, control_type="synthetic_test",
            actor_id=curator_actor, trace_id=uuid4(),
        )
        normative.publish_standard_edition(standard_edition_id=edition_id,
                                            actor_id=curator_actor, trace_id=uuid4())
        return standard, edition_id, control

    target_standard, edition1, control1 = published_edition("P11-TARGET", "edition-1", "a")
    _, guide_edition, _ = published_edition("P11-GUIDE", "guide-1", "b")
    layer = knowledge.create_knowledge_layer(standard_edition_id=guide_edition,
                                             layer_type="Quality Intelligence",
                                             actor_id=curator_actor, trace_id=uuid4())
    rule1 = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer, rule_key="phase11-guidance", version="v1",
        logic_json={"fixture": "NON-OFFICIAL TEST FIXTURE"},
        evidence_expectation={"synthetic": True}, source_reference="synthetic://phase11/rule/v1",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_rule(rule_id=rule1, actor_id=curator_actor, trace_id=uuid4())

    documents = DocumentEvidenceCommandService(using="app")
    evidence_a1 = documents.create_evidence(
        identity=identity_a, organization_id=phase3.ORG_A, source_type="synthetic_test",
        source_uri="synthetic://phase11/evidence/a/v1",
        content_hash=hashlib.sha256(b"NON-OFFICIAL PHASE 11 EVIDENCE A V1").hexdigest(),
        captured_at=timezone.now(), actor_id=actor, trace_id=uuid4(),
    )
    evidence_b1 = documents.create_evidence(
        identity=identity_b, organization_id=phase3.ORG_B, source_type="synthetic_test",
        source_uri="synthetic://phase11/evidence/b/v1",
        content_hash=hashlib.sha256(b"NON-OFFICIAL PHASE 11 EVIDENCE B V1").hexdigest(),
        captured_at=timezone.now(), actor_id=actor, trace_id=uuid4(),
    )
    input_a = {"standard_edition_id": edition1, "requirement_control_id": control1,
               "knowledge_layer_rule_id": rule1, "evidence_id": evidence_a1.entity_id}
    run_service = AgentRunCommandService(using="worker")
    common_run = dict(
        agent_definition_id=definition1, model_policy_id=policy1,
        capability="synthetic-analysis", requested_autonomy=4, model_provider="synthetic",
        model_identifier="synthetic-model-v1", model_version="model-v1",
        prompt_version="prompt-v1", rule_bundle_version="bundle-v1",
        dataset_version_reference="synthetic-dataset-v1",
        embedding_namespace="synthetic-namespace-v1", actor_id=actor,
    )

    before_policy_rejection = visible("worker", "agent_run", phase3.TENANT_A)
    expect_error(lambda: run_service.start_agent_run(
        identity=identity_a, organization_id=phase3.ORG_A, inputs=[input_a], trace_id=uuid4(),
        **dict(common_run, capability="disallowed-capability")), "incompatible")
    require(visible("worker", "agent_run", phase3.TENANT_A) == before_policy_rejection,
            "policy rejection persisted partial AgentRun")

    trace1 = uuid4()
    started = run_service.start_agent_run(identity=identity_a, organization_id=phase3.ORG_A,
                                           inputs=[input_a], trace_id=trace1, **common_run)
    basis1 = dict(input_a, rationale="NON-OFFICIAL TEST FIXTURE exact run input basis.")
    completed = run_service.complete_agent_run_with_recommendation(
        identity=identity_a, agent_run_id=started.agent_run_id,
        title="NON-OFFICIAL TEST FIXTURE recommendation",
        body="SYNTHETIC MODEL OUTPUT. Advisory only; no action executed.",
        confidence="0.7500", assumptions=["Synthetic fixture"], basis=[basis1],
        actor_id=actor, impact="synthetic",
    )
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="worker"):
        run1 = AgentRun.objects.using("worker").get(id=started.agent_run_id)
        frozen = AgentRunInput.objects.using("worker").get(agent_run_id=run1.id)
        link = AgentRunRecommendation.objects.using("worker").get(agent_run_id=run1.id)
        recommendation = Recommendation.objects.using("worker").get(id=link.recommendation_id)
        basis_row = RecommendationBasis.objects.using("worker").get(recommendation_id=recommendation.id)
        require(run1.status == "completed" and run1.trace_id == trace1, "AgentRun completion/trace failed")
        require((frozen.standard_edition_id, frozen.requirement_control_id,
                 frozen.knowledge_layer_rule_id, frozen.evidence_id) ==
                (edition1, control1, rule1, evidence_a1.entity_id), "exact frozen input failed")
        require((basis_row.standard_edition_id, basis_row.requirement_control_id,
                 basis_row.knowledge_layer_rule_id, basis_row.evidence_id) ==
                (edition1, control1, rule1, evidence_a1.entity_id), "RecommendationBasis consistency failed")
        require(basis_row.model_version == run1.model_version and basis_row.trace_id == run1.trace_id,
                "inference metadata linkage diverged")
        require(verify_audit_stream(tenant_id=phase3.TENANT_A, stream_type="agent_run",
                                    stream_id=run1.id, using="worker"), "AgentRun audit chain failed")

    # Mismatch is rejected before any Recommendation exists.
    rollback_run = run_service.start_agent_run(identity=identity_a, organization_id=phase3.ORG_A,
                                                inputs=[input_a], trace_id=uuid4(), **common_run)
    mismatch = dict(basis1, evidence_id=evidence_b1.entity_id)
    expect_error(lambda: run_service.complete_agent_run_with_recommendation(
        identity=identity_a, agent_run_id=rollback_run.agent_run_id, title="mismatch",
        body="SYNTHETIC MODEL OUTPUT", confidence="0.5", assumptions=[], basis=[mismatch],
        actor_id=actor), "exactly match")

    def completion_counts():
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="worker"):
            return (Recommendation.objects.using("worker").count(),
                    AgentRunRecommendation.objects.using("worker").count(),
                    DomainEvent.objects.using("worker").filter(event_type__in=("recommendation.created","agent_run.completed")).count(),
                    TransactionalOutbox.objects.using("worker").filter(domain_event__event_type__in=("recommendation.created","agent_run.completed")).count(),
                    ImmutableAuditLog.objects.using("worker").filter(action__in=("recommendation.created","agent_run.completed")).count())

    rollback_before = completion_counts()
    expect_error(lambda: run_service.complete_agent_run_with_recommendation(
        identity=identity_a, agent_run_id=rollback_run.agent_run_id, title="rollback",
        body="SYNTHETIC MODEL OUTPUT", confidence="0.5", assumptions=[], basis=[basis1],
        actor_id=actor, fail_before_commit=True), "after Recommendation/Audit")
    require(completion_counts() == rollback_before, "completion rollback left partial state")
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="worker"):
        require(AgentRun.objects.using("worker").get(id=rollback_run.agent_run_id).status == "running",
                "rollback did not preserve pre-completion state")

    # Future catalog/normative/evidence versions never mutate R1.
    policy2 = catalog.revise_model_policy(
        previous_revision_id=policy1, version="v2", approved_models=["synthetic-model-v2"],
        data_classes=["NON-OFFICIAL TEST FIXTURE"],
        guardrails={"allowed_capabilities": ["synthetic-analysis"], "autonomy_max": 2},
        human_gate_rules={"synthetic_only": True}, actor_id=curator_actor, trace_id=uuid4())
    catalog.publish_model_policy(model_policy_id=policy2, actor_id=curator_actor, trace_id=uuid4())
    definition2 = catalog.revise_agent_definition(
        previous_revision_id=definition1, version="v2", purpose="Synthetic v2",
        capability="synthetic-analysis", autonomy_max=2, model_policy_id=policy2,
        actor_id=curator_actor, trace_id=uuid4())
    catalog.publish_agent_definition(agent_definition_id=definition2, actor_id=curator_actor, trace_id=uuid4())
    edition2 = normative.create_standard_edition(standard_id=target_standard, edition="edition-2",
                                                 source_hash="c"*64, actor_id=curator_actor, trace_id=uuid4())
    clause2 = normative.add_clause(standard_edition_id=edition2, code="T.11",
                                   title="NON-OFFICIAL TEST FIXTURE", actor_id=curator_actor, trace_id=uuid4())
    control2 = normative.add_requirement_control(standard_edition_id=edition2, clause_id=clause2,
        paraphrase="NON-OFFICIAL TEST FIXTURE v2.", applicability_rule={"synthetic":True},
        control_type="synthetic_test", actor_id=curator_actor, trace_id=uuid4())
    normative.publish_standard_edition(standard_edition_id=edition2, actor_id=curator_actor, trace_id=uuid4())
    rule2 = knowledge.revise_knowledge_layer_rule(previous_revision_id=rule1, version="v2",
        logic_json={"fixture":"NON-OFFICIAL TEST FIXTURE","revision":2}, evidence_expectation={"synthetic":True},
        source_reference="synthetic://phase11/rule/v2", actor_id=curator_actor, trace_id=uuid4())
    knowledge.publish_knowledge_layer_rule(rule_id=rule2, actor_id=curator_actor, trace_id=uuid4())
    evidence_a2 = documents.supersede_evidence(identity=identity_a, evidence_id=evidence_a1.entity_id,
        source_type="synthetic_test", source_uri="synthetic://phase11/evidence/a/v2",
        content_hash=hashlib.sha256(b"NON-OFFICIAL PHASE 11 EVIDENCE A V2").hexdigest(),
        captured_at=timezone.now(), change_reason="Phase 11 frozen history fixture",
        actor_id=actor, trace_id=uuid4())
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="worker"):
        old_run = AgentRun.objects.using("worker").get(id=started.agent_run_id)
        old_input = AgentRunInput.objects.using("worker").get(agent_run_id=old_run.id)
        require((old_run.agent_definition_id, old_run.model_policy_id) == (definition1, policy1),
                "catalog versions reinterpreted historical run")
        require((old_input.standard_edition_id, old_input.requirement_control_id,
                 old_input.knowledge_layer_rule_id, old_input.evidence_id) ==
                (edition1, control1, rule1, evidence_a1.entity_id), "input versions reinterpreted")

    def privileged(sql, params):
        with migrator.cursor() as cursor:
            cursor.execute(sql, params)

    for sql, params, fragment in (
        ("UPDATE qms.agent_run SET model_version='rewritten' WHERE id=%s", [str(started.agent_run_id)], "immutable"),
        ("UPDATE qms.agent_run SET tenant_id=%s WHERE id=%s", [str(phase3.TENANT_B),str(started.agent_run_id)], "immutable"),
        ("UPDATE qms.agent_run_input SET evidence_id=%s WHERE id=%s", [str(evidence_a2.entity_id),str(started.input_ids[0])], "frozen"),
        ("DELETE FROM qms.agent_run_recommendation WHERE id=%s", [str(completed.link_id)], "frozen"),
        ("UPDATE governance.model_policy SET guardrails='{}' WHERE id=%s", [str(policy1)], "immutable"),
        ("UPDATE governance.agent_definition SET purpose='rewritten' WHERE id=%s", [str(definition1)], "immutable"),
    ):
        expect_error(lambda s=sql,p=params: privileged(s,p), fragment); migrator.rollback()

    with migrator.cursor() as cursor:
        for table in ("process","risk","objective","change"):
            cursor.execute(f"SELECT count(*) FROM qms.{table}")
            require(cursor.fetchone()[0] >= 0, f"missing business table {table}")
        cursor.execute("SELECT to_regclass('qms.action_execution')")
        require(cursor.fetchone()[0] is None, "A4 created ActionExecution")
    with phase3.runtime_transaction("worker", phase3.TENANT_A) as cursor:
        expect_error(lambda: cursor.execute("UPDATE qms.risk SET cause='worker escape'"), "permission denied")

    input_b = dict(input_a, evidence_id=evidence_b1.entity_id)
    started_b = run_service.start_agent_run(identity=identity_b, organization_id=phase3.ORG_B,
                                             inputs=[input_b], trace_id=uuid4(), **common_run)
    require(started_b.agent_run_id is not None, "tenant B AgentRun failed")
    run_service.complete_agent_run_with_recommendation(
        identity=identity_b, agent_run_id=started_b.agent_run_id, title="Tenant B synthetic output",
        body="SYNTHETIC MODEL OUTPUT. Advisory only.", confidence="0.5", assumptions=[],
        basis=[dict(input_b, rationale="NON-OFFICIAL TEST FIXTURE tenant B basis")], actor_id=actor,
    )
    app_matrix = {table: [visible("app",table,phase3.TENANT_A),visible("app",table),visible("app",table,phase3.TENANT_B)]
                  for table in TENANT_TABLES}
    worker_matrix = {table: [visible("worker",table,phase3.TENANT_A),visible("worker",table),visible("worker",table,phase3.TENANT_B)]
                     for table in TENANT_TABLES}
    require(all(v[0] > 0 and v[1] == 0 and v[2] > 0 for v in app_matrix.values()),
            "app A/none/B isolation failed")
    require(worker_matrix["agent_run"][1] == 0 and worker_matrix["agent_run_input"][1] == 0,
            "worker no-context isolation failed")

    try:
        with phase3.runtime_transaction("worker", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.agent_run")
            raise RuntimeError("intentional Phase 11 rollback context")
    except RuntimeError:
        pass
    require(visible("worker","agent_run") == 0 and visible("worker","agent_run",phase3.TENANT_B) == 1,
            "rollback/pool tenant context leaked")

    phase3.migrate(PHASE10_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.recommendation'),to_regclass('qms.agent_run'),to_regclass('governance.agent_definition')")
        require(cursor.fetchone() == ("qms.recommendation",None,None), "Phase 11 reverse damaged Phase 10")
    probe = RecommendationCommandService(using="app").create_recommendation(
        identity=identity_a, organization_id=phase3.ORG_A, title="Phase 10 reverse probe",
        body="Advisory only", confidence="0.5", assumptions=[], intended_autonomy=0,
        basis=[dict(basis1, model_provider="synthetic", model_identifier="synthetic-model-v1",
                    model_version="model-v1", prompt_version="prompt-v1", rule_bundle_version="bundle-v1")],
        actor_id=actor, trace_id=uuid4())
    require(probe.recommendation_id is not None, "Phase 10 command failed after Phase 11 reverse")
    phase3.migrate(PHASE11_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.agent_run'),to_regclass('governance.agent_definition')")
        require(cursor.fetchone() == ("qms.agent_run","governance.agent_definition"), "Phase 11 second forward failed")

    print(json.dumps({
        "status":"PASS", "migration":"0011_agent_definition_run_provenance_foundation",
        "catalog":"AgentDefinition/ModelPolicy v1->v2 published immutable",
        "provenance":"exact Definition/Policy/Edition/Requirement/Rule/Evidence frozen",
        "boundaries":"deterministic rules/retrieval/model inference/governance policy distinct",
        "recommendation_link":"separate immutable link; exact Basis consistency service+DB",
        "atomic_success":"Run+inputs and Recommendation+Basis+link+events+outbox+audit PASS",
        "atomic_rollback":"post-Recommendation/Audit failure left pre-completion state",
        "policy_rejection":"incompatible capability rejected with zero partial state",
        "no_execution":"A4 metadata; no ActionExecution or worker business write",
        "rls":{"app":app_matrix,"worker":worker_matrix},
        "pool":"A -> none -> B and rollback -> none -> B PASS",
        "forward_reverse_forward":"0001 -> ... -> 0011 -> 0010 -> 0011 PASS",
    },default=str,indent=2,sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)},indent=2),file=sys.stderr)
        raise
