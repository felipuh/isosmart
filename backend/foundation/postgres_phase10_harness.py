"""Blocking PostgreSQL 18.6 matrix for governed Recommendation provenance."""

import hashlib
import json
import os
import sys
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase9_harness as phase9


PHASE9_MIGRATION = ("foundation", "0009_knowledge_layer_foundation")
PHASE10_MIGRATION = ("foundation", "0010_governed_recommendation_foundation")
TABLES = ("recommendation", "recommendation_basis")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_error(operation, fragment=None):
    try:
        operation()
    except Exception as exc:
        if fragment:
            require(fragment.lower() in str(exc).lower(), f"unexpected database error: {exc}")
        return
    raise AssertionError("database operation unexpectedly succeeded")


def visible(alias, table, tenant=None):
    require(table in TABLES, "unknown Phase 10 table")
    with phase3.runtime_transaction(alias, tenant) as cursor:
        cursor.execute(f"SELECT count(*) FROM qms.{table}")
        return cursor.fetchone()[0]


def run():
    phase9.run()
    phase3.migrate(PHASE10_MIGRATION)

    from django.db import connections
    from django.utils import timezone
    from foundation.audit import verify_audit_stream
    from foundation.document_evidence import DocumentEvidenceCommandService
    from foundation.knowledge_layer import KnowledgeLayerCommandService
    from foundation.models import (
        DomainEvent, ImmutableAuditLog, Recommendation, RecommendationBasis,
        TransactionalOutbox,
    )
    from foundation.normative_coverage import NormativeCatalogCommandService
    from foundation.recommendation import RecommendationCommandService
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    migrator = connections["default"]
    app_role = os.environ["FOUNDATION_APP_ROLE"]
    worker_role = os.environ["FOUNDATION_WORKER_ROLE"]
    projector_role = os.environ["FOUNDATION_PROJECTOR_ROLE"]
    audit_writer_role = os.environ["FOUNDATION_AUDIT_WRITER_ROLE"]
    curator_role = os.environ["FOUNDATION_NORMATIVE_CURATOR_ROLE"]

    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,r.rolname "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner "
            "WHERE n.nspname='qms' AND c.relname=ANY(%s) ORDER BY c.relname",
            [list(TABLES)],
        )
        protected = cursor.fetchall()
        require(len(protected) == 2, "Phase 10 tables missing")
        require(all(row[1] and row[2] for row in protected), "Phase 10 ENABLE/FORCE RLS missing")
        require(all(row[3] not in (app_role, worker_role, projector_role, audit_writer_role, curator_role)
                    for row in protected), "runtime principal owns Phase 10 table")
        for table in TABLES:
            cursor.execute(
                "SELECT cmd FROM pg_policies WHERE schemaname='qms' AND tablename=%s",
                [table],
            )
            require({row[0] for row in cursor.fetchall()} == {"SELECT", "INSERT", "UPDATE", "DELETE", "ALL"},
                    f"explicit policy matrix incomplete: {table}")
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.'||%s,'SELECT'),"
                "has_table_privilege(%s,'qms.'||%s,'INSERT'),"
                "has_table_privilege(%s,'qms.'||%s,'UPDATE'),"
                "has_table_privilege(%s,'qms.'||%s,'DELETE')",
                [app_role, table, app_role, table, app_role, table, app_role, table],
            )
            require(cursor.fetchone() == (True, True, False, False), f"app grant drift: {table}")
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.'||%s,'SELECT'),"
                "has_table_privilege(%s,'qms.'||%s,'INSERT'),"
                "has_table_privilege(%s,'qms.'||%s,'UPDATE'),"
                "has_table_privilege(%s,'qms.'||%s,'DELETE')",
                [worker_role, table, worker_role, table, worker_role, table, worker_role, table],
            )
            require(cursor.fetchone() == (True, False, False, False), f"worker is not read-only: {table}")
            for role in (projector_role, audit_writer_role, curator_role):
                cursor.execute(
                    "SELECT has_table_privilege(%s,'qms.'||%s,'SELECT'),"
                    "has_table_privilege(%s,'qms.'||%s,'INSERT'),"
                    "has_table_privilege(%s,'qms.'||%s,'UPDATE'),"
                    "has_table_privilege(%s,'qms.'||%s,'DELETE')",
                    [role, table, role, table, role, table, role, table],
                )
                require(cursor.fetchone() == (False, False, False, False),
                        f"isolated principal has Recommendation privilege: {role}/{table}")

    identity_a = TrustedTenantIdentity("phase10-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase10-b", phase3.TENANT_B)
    actor = "phase10-synthetic-actor"
    document_service = DocumentEvidenceCommandService(using="app")
    evidence_a1 = document_service.create_evidence(
        identity=identity_a, organization_id=phase3.ORG_A, source_type="synthetic_test",
        source_uri="synthetic://phase10/evidence/a/v1",
        content_hash=hashlib.sha256(b"NON-OFFICIAL PHASE 10 EVIDENCE A V1").hexdigest(),
        captured_at=timezone.now(), actor_id=actor, trace_id=uuid4(),
    )
    evidence_b1 = document_service.create_evidence(
        identity=identity_b, organization_id=phase3.ORG_B, source_type="synthetic_test",
        source_uri="synthetic://phase10/evidence/b/v1",
        content_hash=hashlib.sha256(b"NON-OFFICIAL PHASE 10 EVIDENCE B V1").hexdigest(),
        captured_at=timezone.now(), actor_id=actor, trace_id=uuid4(),
    )

    normative = NormativeCatalogCommandService(using="normative_curator")
    knowledge = KnowledgeLayerCommandService(using="normative_curator")
    curator_actor = "phase10-synthetic-curator"

    def published_edition(code, edition, digit):
        standard = normative.create_standard(
            code=code, title="NON-OFFICIAL TEST FIXTURE", publisher="TEST",
            actor_id=curator_actor, trace_id=uuid4(),
        )
        edition_id = normative.create_standard_edition(
            standard_id=standard, edition=edition, source_hash=digit * 64,
            actor_id=curator_actor, trace_id=uuid4(),
        )
        clause = normative.add_clause(
            standard_edition_id=edition_id, code="T.1", title="NON-OFFICIAL TEST FIXTURE",
            actor_id=curator_actor, trace_id=uuid4(),
        )
        control = normative.add_requirement_control(
            standard_edition_id=edition_id, clause_id=clause,
            paraphrase="NON-OFFICIAL TEST FIXTURE: no licensed normative text.",
            applicability_rule={"synthetic": True}, control_type="synthetic_test",
            actor_id=curator_actor, trace_id=uuid4(),
        )
        normative.publish_standard_edition(
            standard_edition_id=edition_id, actor_id=curator_actor, trace_id=uuid4(),
        )
        return standard, edition_id, control

    target_standard, edition1, control1 = published_edition("P10-TARGET", "edition-1", "6")
    _, guide_edition, _ = published_edition("P10-GUIDE", "guide-1", "7")
    layer = knowledge.create_knowledge_layer(
        standard_edition_id=guide_edition, layer_type="Quality Intelligence",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    rule1 = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer, rule_key="phase10-guidance", version="v1",
        logic_json={"fixture": "NON-OFFICIAL TEST FIXTURE", "revision": 1},
        evidence_expectation={"synthetic": True}, source_reference="synthetic://phase10/rule/v1",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_rule(rule_id=rule1, actor_id=curator_actor, trace_id=uuid4())
    binding1 = knowledge.create_knowledge_layer_binding(
        knowledge_layer_rule_id=rule1, standard_edition_id=edition1,
        requirement_control_id=control1, priority="P0",
        rationale="NON-OFFICIAL TEST FIXTURE: guidance informs the control.",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_binding(binding_id=binding1, actor_id=curator_actor, trace_id=uuid4())

    recommendation_service = RecommendationCommandService(using="app")
    common_basis = {
        "standard_edition_id": edition1,
        "requirement_control_id": control1,
        "knowledge_layer_rule_id": rule1,
        "evidence_id": evidence_a1.entity_id,
        "rationale": "NON-OFFICIAL TEST FIXTURE: exact sources support advisory analysis.",
        "model_provider": "synthetic",
        "model_identifier": "fixture-model",
        "model_version": "model-v1",
        "prompt_version": "prompt-v1",
        "rule_bundle_version": "bundle-v1",
        "dataset_version_reference": "synthetic-dataset-v1",
        "embedding_namespace": "synthetic-namespace-v1",
    }

    with migrator.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.requirement_control")
        certifiable_before = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule")
        rule_count_before = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM qms.evidence")
        evidence_count_before = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM qms.evidence_coverage")
        coverage_count_before = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM qms.process")
        process_before = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM qms.risk")
        risk_before = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM qms.objective")
        objective_before = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM qms.change")
        change_before = cursor.fetchone()[0]

    trace_a = uuid4()
    created_a = recommendation_service.create_recommendation(
        identity=identity_a, organization_id=phase3.ORG_A,
        title="NON-OFFICIAL TEST FIXTURE recommendation",
        body="Advisory proposal only; no action is executed.", confidence="0.8750",
        assumptions=["Fixture input remains current", "Human review remains required"],
        intended_autonomy=4, basis=[common_basis], impact="synthetic-medium",
        actor_id=actor, trace_id=trace_a,
    )

    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        recommendation = Recommendation.objects.using("app").get(id=created_a.recommendation_id)
        basis_a = RecommendationBasis.objects.using("app").get(id=created_a.basis_ids[0])
        event = DomainEvent.objects.using("app").get(event_id=created_a.event_id)
        outbox = TransactionalOutbox.objects.using("app").get(id=created_a.outbox_id)
        audit = ImmutableAuditLog.objects.using("app").get(id=created_a.audit_id)
        require(str(recommendation.confidence) == "0.8750", "confidence reconstruction failed")
        require(recommendation.assumptions == ["Fixture input remains current", "Human review remains required"],
                "assumptions reconstruction failed")
        require(recommendation.intended_autonomy == 4 and recommendation.status == "proposed",
                "A4 metadata/status reconstruction failed")
        require(basis_a.trace_id == trace_a and event.trace_id == trace_a and audit.trace_id == trace_a,
                "trace coherence failed")
        require(outbox.domain_event_id == event.event_id and event.event_type == "recommendation.created",
                "event/outbox contract failed")
        require(verify_audit_stream(
            tenant_id=phase3.TENANT_A, stream_type="recommendation",
            stream_id=recommendation.id, using="app",
        ), "recommendation audit chain failed")

    with migrator.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.requirement_control")
        require(cursor.fetchone()[0] == certifiable_before, "Recommendation changed certifiable count")
        cursor.execute("SELECT count(*) FROM normative.knowledge_layer_rule")
        require(cursor.fetchone()[0] == rule_count_before, "Recommendation changed guidance")
        cursor.execute("SELECT count(*) FROM qms.evidence")
        require(cursor.fetchone()[0] == evidence_count_before, "Recommendation changed Evidence")
        cursor.execute("SELECT count(*) FROM qms.evidence_coverage")
        require(cursor.fetchone()[0] == coverage_count_before, "Recommendation changed EvidenceCoverage")
        for table, expected in (("process", process_before), ("risk", risk_before),
                                ("objective", objective_before), ("change", change_before)):
            cursor.execute(f"SELECT count(*) FROM qms.{table}")
            require(cursor.fetchone()[0] == expected, f"A4 recommendation mutated {table}")
        cursor.execute("SELECT to_regclass('qms.action_execution')")
        require(cursor.fetchone()[0] is None, "ActionExecution was implemented or created")

    expect_error(lambda: recommendation_service.create_recommendation(
        identity=identity_a, organization_id=phase3.ORG_A, title="invalid", body="invalid",
        confidence="1.0001", assumptions=[], intended_autonomy=1, basis=[common_basis],
        actor_id=actor, trace_id=uuid4()), "confidence")

    def counts_a():
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            return (
                Recommendation.objects.using("app").count(),
                RecommendationBasis.objects.using("app").count(),
                DomainEvent.objects.using("app").filter(event_type="recommendation.created").count(),
                TransactionalOutbox.objects.using("app").filter(domain_event__event_type="recommendation.created").count(),
                ImmutableAuditLog.objects.using("app").filter(action="recommendation.created").count(),
            )

    rollback_before = counts_a()
    expect_error(lambda: recommendation_service.create_recommendation(
        identity=identity_a, organization_id=phase3.ORG_A, title="rollback", body="rollback",
        confidence="0.5000", assumptions=["synthetic rollback"], intended_autonomy=1,
        basis=[common_basis], actor_id=actor, trace_id=uuid4(), fail_before_commit=True,
    ), "deliberate Phase 10")
    require(counts_a() == rollback_before, "atomic rollback left Recommendation/Basis/Event/Outbox/Audit")

    edition2 = normative.create_standard_edition(
        standard_id=target_standard, edition="edition-2", source_hash="8" * 64,
        actor_id=curator_actor, trace_id=uuid4(),
    )
    clause2 = normative.add_clause(
        standard_edition_id=edition2, code="T.1", title="NON-OFFICIAL TEST FIXTURE",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    control2 = normative.add_requirement_control(
        standard_edition_id=edition2, clause_id=clause2,
        paraphrase="NON-OFFICIAL TEST FIXTURE edition 2.", applicability_rule={"synthetic": True},
        control_type="synthetic_test", actor_id=curator_actor, trace_id=uuid4(),
    )
    normative.publish_standard_edition(
        standard_edition_id=edition2, actor_id=curator_actor, trace_id=uuid4(),
    )
    rule2 = knowledge.revise_knowledge_layer_rule(
        previous_revision_id=rule1, version="v2",
        logic_json={"fixture": "NON-OFFICIAL TEST FIXTURE", "revision": 2},
        evidence_expectation={"synthetic": True, "revision": 2},
        source_reference="synthetic://phase10/rule/v2",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_rule(rule_id=rule2, actor_id=curator_actor, trace_id=uuid4())
    evidence_a2 = document_service.supersede_evidence(
        identity=identity_a, evidence_id=evidence_a1.entity_id, source_type="synthetic_test",
        source_uri="synthetic://phase10/evidence/a/v2",
        content_hash=hashlib.sha256(b"NON-OFFICIAL PHASE 10 EVIDENCE A V2").hexdigest(),
        captured_at=timezone.now(), actor_id=actor, trace_id=uuid4(),
        change_reason="synthetic Phase 10 history fixture",
    )
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        frozen = RecommendationBasis.objects.using("app").get(id=created_a.basis_ids[0])
        require((frozen.standard_edition_id, frozen.requirement_control_id,
                 frozen.knowledge_layer_rule_id, frozen.evidence_id) ==
                (edition1, control1, rule1, evidence_a1.entity_id),
                "frozen provenance changed after Edition2/Rule2/Evidence2")

    def privileged(sql, params):
        with migrator.cursor() as cursor:
            cursor.execute(sql, params)

    for sql, params, fragment in (
        ("UPDATE qms.recommendation_basis SET requirement_control_id=%s,standard_edition_id=%s WHERE id=%s",
         [str(control2), str(edition2), str(created_a.basis_ids[0])], "append-only"),
        ("UPDATE qms.recommendation_basis SET knowledge_layer_rule_id=%s WHERE id=%s",
         [str(rule2), str(created_a.basis_ids[0])], "append-only"),
        ("UPDATE qms.recommendation_basis SET evidence_id=%s WHERE id=%s",
         [str(evidence_a2.entity_id), str(created_a.basis_ids[0])], "append-only"),
        ("UPDATE qms.recommendation_basis SET tenant_id=%s WHERE id=%s",
         [str(phase3.TENANT_B), str(created_a.basis_ids[0])], "append-only"),
        ("DELETE FROM qms.recommendation_basis WHERE id=%s",
         [str(created_a.basis_ids[0])], "append-only"),
        ("UPDATE qms.recommendation SET body='rewritten' WHERE id=%s",
         [str(created_a.recommendation_id)], "immutable"),
    ):
        expect_error(lambda s=sql, p=params: privileged(s, p), fragment)
        migrator.rollback()

    expect_error(lambda: privileged(
        "INSERT INTO qms.recommendation(id,tenant_id,organization_id,title,body,confidence,assumptions,status,intended_autonomy) "
        "VALUES (%s,%s,%s,'bad confidence','bad',1.1,'[]','proposed',1)",
        [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A)]), "confidence")
    migrator.rollback()

    # Tenant B gets one independent governed row for the A/B/none matrix.
    basis_b = dict(common_basis, evidence_id=evidence_b1.entity_id)
    created_b = recommendation_service.create_recommendation(
        identity=identity_b, organization_id=phase3.ORG_B, title="Tenant B fixture",
        body="Independent advisory proposal.", confidence="0.5000", assumptions=[],
        intended_autonomy=0, basis=[basis_b], actor_id=actor, trace_id=uuid4(),
    )
    require(created_b.recommendation_id is not None, "Tenant B recommendation failed")
    app_matrix = {table: [visible("app", table, phase3.TENANT_A), visible("app", table),
                          visible("app", table, phase3.TENANT_B)] for table in TABLES}
    worker_matrix = {table: [visible("worker", table, phase3.TENANT_A), visible("worker", table),
                             visible("worker", table, phase3.TENANT_B)] for table in TABLES}
    require(all(values == [1, 0, 1] for values in app_matrix.values()), "app A/none/B matrix failed")
    require(all(values == [1, 0, 1] for values in worker_matrix.values()), "worker A/none/B matrix failed")
    with phase3.runtime_transaction("worker", phase3.TENANT_A) as cursor:
        expect_error(lambda: cursor.execute(
            "INSERT INTO qms.recommendation(id,tenant_id,organization_id,title,body,confidence,assumptions,status,intended_autonomy) "
            "VALUES (%s,%s,%s,'denied','denied',0.5,'[]','proposed',0)",
            [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A)]), "permission denied")

    def raw_app(sql, params):
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute(sql, params)

    expect_error(lambda: raw_app(
        "INSERT INTO qms.recommendation(id,tenant_id,organization_id,title,body,confidence,assumptions,status,intended_autonomy) "
        "VALUES (%s,%s,%s,'incomplete','incomplete',0.5,'[]','proposed',1)",
        [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A)]), "requires at least one basis")
    expect_error(lambda: raw_app(
        "INSERT INTO qms.recommendation_basis(id,tenant_id,organization_id,recommendation_id,standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id,rationale,model_identifier,model_version,prompt_version,rule_bundle_version,trace_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'cross tenant','m','v','p','r',%s)",
        [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(created_a.recommendation_id),
         str(edition1), str(control1), str(rule1), str(evidence_b1.entity_id), str(uuid4())]))
    expect_error(lambda: raw_app(
        "INSERT INTO qms.recommendation_basis(id,tenant_id,organization_id,recommendation_id,standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id,rationale,model_identifier,model_version,prompt_version,rule_bundle_version,trace_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'edition mismatch','m','v','p','r',%s)",
        [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(created_a.recommendation_id),
         str(edition2), str(control1), str(rule1), str(evidence_a2.entity_id), str(uuid4())]),
        "foreign key")
    draft_rule = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer, rule_key="phase10-draft-rejected", version="v1",
        logic_json={"synthetic": True}, evidence_expectation={"synthetic": True},
        source_reference="synthetic://phase10/draft-rejected",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    expect_error(lambda: raw_app(
        "INSERT INTO qms.recommendation_basis(id,tenant_id,organization_id,recommendation_id,standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id,rationale,model_identifier,model_version,prompt_version,rule_bundle_version,trace_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'draft rule','m','v','p','r',%s)",
        [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(created_a.recommendation_id),
         str(edition2), str(control2), str(draft_rule), str(evidence_a2.entity_id), str(uuid4())]),
        "published rule")

    try:
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.recommendation")
            raise RuntimeError("intentional Phase 10 rollback context")
    except RuntimeError:
        pass
    require(visible("app", "recommendation") == 0 and
            visible("app", "recommendation", phase3.TENANT_B) == 1,
            "rollback context leaked")

    phase3.migrate(PHASE9_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('normative.knowledge_layer_rule'),"
            "to_regclass('qms.evidence'),to_regclass('qms.recommendation'),"
            "to_regclass('qms.recommendation_basis')"
        )
        require(cursor.fetchone() == ("normative.knowledge_layer_rule", "qms.evidence", None, None),
                "Phase 10 reverse damaged Phase 9")
    reverse_probe = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer, rule_key="phase10-reverse-probe", version="v1",
        logic_json={"synthetic": True}, evidence_expectation={"synthetic": True},
        source_reference="synthetic://phase10/reverse-probe",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    require(reverse_probe is not None, "Phase 9 command failed after Phase 10 reverse")
    phase3.migrate(PHASE10_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.recommendation'),to_regclass('qms.recommendation_basis')")
        require(cursor.fetchone() == ("qms.recommendation", "qms.recommendation_basis"),
                "Phase 10 second forward failed")

    print(json.dumps({
        "status": "PASS",
        "migration": "0010_governed_recommendation_foundation",
        "history": "immutable Recommendation row; material changes require a new Recommendation",
        "basis": "append-only exact Edition/Requirement/Rule revision/Evidence revision",
        "evidence_coverage": "direct Evidence source contract; no duplicate Coverage FK",
        "confidence": "normalized [0,1] indicator; not represented as statistical probability",
        "assumptions": "structured JSON string list reconstructed exactly",
        "model_rule_metadata": "synthetic provider/model/prompt/rule bundle/dataset/embedding/trace snapshot",
        "semantic_invariants": "Requirement != Guidance != Evidence != Recommendation",
        "no_execution": "A4 metadata caused zero Process/Risk/Objective/Change mutation; no ActionExecution",
        "certifiability": "Recommendation left controls/rules/evidence/coverage unchanged",
        "atomic_success": "Recommendation + Basis + DomainEvent + Outbox + Audit PASS",
        "atomic_rollback": "post-audit failure left no partial Phase 10 state",
        "rls": {"app": app_matrix, "worker": worker_matrix},
        "principals": "worker read-only; projector/curator/audit writer zero Phase 10 privileges",
        "pool": "A -> none -> B and rollback -> none -> B PASS",
        "forward_reverse_forward": "0001 -> ... -> 0010 -> 0009 -> 0010 PASS",
    }, default=str, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
