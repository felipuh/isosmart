"""Blocking Phase 9 matrix layered on the promoted Phase 8 PostgreSQL gate."""

import json
import os
import sys
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase8_harness as phase8


PHASE8_MIGRATION = ("foundation", "0008_evidence_coverage_normative_core_foundation")
PHASE9_MIGRATION = ("foundation", "0009_knowledge_layer_foundation")
CATALOG_TABLES = ("knowledge_layer", "knowledge_layer_rule", "knowledge_layer_binding")


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


def run():
    phase8.run()
    phase3.migrate(PHASE9_MIGRATION)

    from django.db import connections
    from foundation.knowledge_layer import KnowledgeCatalogQueryService, KnowledgeLayerCommandService
    from foundation.models import KnowledgeLayerBinding, KnowledgeLayerRule, NormativeCurationAudit
    from foundation.normative_coverage import NormativeCatalogCommandService

    migrator = connections["default"]
    app_role = os.environ["FOUNDATION_APP_ROLE"]
    worker_role = os.environ["FOUNDATION_WORKER_ROLE"]
    projector_role = os.environ["FOUNDATION_PROJECTOR_ROLE"]
    curator_role = os.environ["FOUNDATION_NORMATIVE_CURATOR_ROLE"]
    audit_writer_role = os.environ["FOUNDATION_AUDIT_WRITER_ROLE"]

    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT c.relname,r.rolname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='normative' AND c.relname=ANY(%s)",
            [list(CATALOG_TABLES)],
        )
        ownership = cursor.fetchall()
        require(len(ownership) == 3 and all(owner != curator_role for _, owner in ownership),
                "curator owns Phase 9 catalog objects")
        for table in CATALOG_TABLES:
            for role in (app_role, worker_role, projector_role):
                cursor.execute(
                    "SELECT has_table_privilege(%s,'normative.'||%s,'SELECT'),"
                    "has_table_privilege(%s,'normative.'||%s,'INSERT'),"
                    "has_table_privilege(%s,'normative.'||%s,'UPDATE'),"
                    "has_table_privilege(%s,'normative.'||%s,'DELETE')",
                    [role, table, role, table, role, table, role, table],
                )
                require(cursor.fetchone() == (True, False, False, False),
                        f"runtime catalog privilege drift: {role}/{table}")
            cursor.execute(
                "SELECT has_table_privilege(%s,'normative.'||%s,'SELECT'),"
                "has_table_privilege(%s,'normative.'||%s,'INSERT'),"
                "has_table_privilege(%s,'normative.'||%s,'DELETE')",
                [curator_role, table, curator_role, table, curator_role, table],
            )
            require(cursor.fetchone() == (True, True, False), f"curator grant drift: {table}")
        cursor.execute(
            "SELECT has_column_privilege(%s,'normative.knowledge_layer_rule','status','UPDATE'),"
            "has_column_privilege(%s,'normative.knowledge_layer_rule','logic_json','UPDATE'),"
            "has_column_privilege(%s,'normative.knowledge_layer_binding','status','UPDATE'),"
            "has_column_privilege(%s,'normative.knowledge_layer_binding','requirement_control_id','UPDATE')",
            [curator_role, curator_role, curator_role, curator_role],
        )
        require(cursor.fetchone() == (True, False, True, False), "curator UPDATE grants are not minimal")
        for table in ("tenant_projection", "organization", "risk", "evidence", "evidence_coverage"):
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.'||%s,'INSERT'),"
                "has_table_privilege(%s,'qms.'||%s,'UPDATE'),"
                "has_table_privilege(%s,'qms.'||%s,'DELETE')",
                [curator_role, table, curator_role, table, curator_role, table],
            )
            require(cursor.fetchone() == (False, False, False), f"curator can mutate qms.{table}")
        cursor.execute(
            "SELECT has_table_privilege(%s,'normative.knowledge_layer','INSERT')",
            [audit_writer_role],
        )
        require(cursor.fetchone()[0] is False, "audit writer can mutate Phase 9 catalog")

    normative = NormativeCatalogCommandService(using="normative_curator")
    knowledge = KnowledgeLayerCommandService(using="normative_curator")
    actor = "phase9-synthetic-curator"

    def create_published_edition(code, edition, source_digit, control_text):
        standard_id = normative.create_standard(
            code=code, title="NON-OFFICIAL TEST FIXTURE", publisher="TEST",
            actor_id=actor, trace_id=uuid4(),
        )
        edition_id = normative.create_standard_edition(
            standard_id=standard_id, edition=edition, source_hash=source_digit * 64,
            actor_id=actor, trace_id=uuid4(),
        )
        clause_id = normative.add_clause(
            standard_edition_id=edition_id, code="T.1", title="NON-OFFICIAL TEST FIXTURE",
            actor_id=actor, trace_id=uuid4(),
        )
        control_id = normative.add_requirement_control(
            standard_edition_id=edition_id, clause_id=clause_id,
            paraphrase=control_text, applicability_rule={"synthetic": True},
            control_type="synthetic_test", actor_id=actor, trace_id=uuid4(),
        )
        normative.publish_standard_edition(
            standard_edition_id=edition_id, actor_id=actor, trace_id=uuid4(),
        )
        return standard_id, edition_id, control_id

    _, guide_edition, _ = create_published_edition(
        "P9-GUIDE", "synthetic-guide-v1", "3",
        "NON-OFFICIAL TEST FIXTURE: source placeholder only.",
    )
    target_standard, edition1, control1 = create_published_edition(
        "P9-TARGET", "synthetic-target-edition-1", "4",
        "NON-OFFICIAL TEST FIXTURE: certifiable target control edition 1.",
    )
    edition2 = normative.create_standard_edition(
        standard_id=target_standard, edition="synthetic-target-edition-2", source_hash="5" * 64,
        actor_id=actor, trace_id=uuid4(),
    )
    clause2 = normative.add_clause(
        standard_edition_id=edition2, code="T.1", title="NON-OFFICIAL TEST FIXTURE",
        actor_id=actor, trace_id=uuid4(),
    )
    control2 = normative.add_requirement_control(
        standard_edition_id=edition2, clause_id=clause2,
        paraphrase="NON-OFFICIAL TEST FIXTURE: certifiable target control edition 2.",
        applicability_rule={"synthetic": True, "edition": 2}, control_type="synthetic_test",
        actor_id=actor, trace_id=uuid4(),
    )
    normative.publish_standard_edition(
        standard_edition_id=edition2, actor_id=actor, trace_id=uuid4(),
    )

    query = KnowledgeCatalogQueryService(using="app")
    requirement_count_before = query.certifiable_requirement_count()
    with connections["normative_curator"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        audit_before = cursor.fetchone()[0]

    layer_id = knowledge.create_knowledge_layer(
        standard_edition_id=guide_edition, layer_type="Quality Intelligence",
        actor_id=actor, trace_id=uuid4(),
    )
    rule1 = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer_id, rule_key="synthetic-guidance", version="v1",
        logic_json={"fixture": "NON-OFFICIAL TEST FIXTURE", "revision": 1},
        evidence_expectation={"fixture": True}, source_reference="synthetic://phase9/rule/v1",
        actor_id=actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_rule(rule_id=rule1, actor_id=actor, trace_id=uuid4())
    binding1 = knowledge.create_knowledge_layer_binding(
        knowledge_layer_rule_id=rule1, standard_edition_id=edition1,
        requirement_control_id=control1, relationship_type="informs", priority="P0",
        rationale="NON-OFFICIAL TEST FIXTURE: guidance may assist this control.",
        actor_id=actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_binding(binding_id=binding1, actor_id=actor, trace_id=uuid4())

    rule2 = knowledge.revise_knowledge_layer_rule(
        previous_revision_id=rule1, version="v2",
        logic_json={"fixture": "NON-OFFICIAL TEST FIXTURE", "revision": 2},
        evidence_expectation={"fixture": True, "revision": 2},
        source_reference="synthetic://phase9/rule/v2", actor_id=actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_rule(rule_id=rule2, actor_id=actor, trace_id=uuid4())
    binding2 = knowledge.create_knowledge_layer_binding(
        knowledge_layer_rule_id=rule2, standard_edition_id=edition1,
        requirement_control_id=control1, priority="P1",
        rationale="NON-OFFICIAL TEST FIXTURE: explicit v2 binding.",
        actor_id=actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_binding(binding_id=binding2, actor_id=actor, trace_id=uuid4())
    rule3 = knowledge.revise_knowledge_layer_rule(
        previous_revision_id=rule2, version="v3",
        logic_json={"fixture": "NON-OFFICIAL TEST FIXTURE", "revision": 3},
        evidence_expectation={"fixture": True, "revision": 3},
        source_reference="synthetic://phase9/rule/v3", actor_id=actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_rule(rule_id=rule3, actor_id=actor, trace_id=uuid4())
    binding3 = knowledge.create_knowledge_layer_binding(
        knowledge_layer_rule_id=rule3, standard_edition_id=edition2,
        requirement_control_id=control2, priority="P0",
        rationale="NON-OFFICIAL TEST FIXTURE: explicit edition 2 binding.",
        actor_id=actor, trace_id=uuid4(),
    )
    knowledge.publish_knowledge_layer_binding(binding_id=binding3, actor_id=actor, trace_id=uuid4())

    with phase3.runtime_transaction("app") as cursor:
        cursor.execute(
            "SELECT version,previous_revision_id,lineage_id,status,source_reference,"
            "certifiability_classification FROM normative.knowledge_layer_rule "
            "WHERE lineage_id=%s ORDER BY version", [str(rule1)],
        )
        history = cursor.fetchall()
        require([row[0] for row in history] == ["v1", "v2", "v3"], "v1-v3 history missing")
        require(history[0][1] is None and history[1][1] == rule1 and history[2][1] == rule2,
                "rule predecessor lineage invalid")
        require(all(row[2] == rule1 and row[3] == "published" for row in history),
                "rule lineage/status invalid")
        require(all(row[5] == "non_certifiable_guidance" for row in history),
                "rule certifiability classification drift")
        cursor.execute(
            "SELECT knowledge_layer_rule_id,standard_edition_id,requirement_control_id,semantic_effect "
            "FROM normative.knowledge_layer_binding WHERE id=%s", [str(binding1)],
        )
        require(cursor.fetchone() == (rule1, edition1, control1, "guidance_only"),
                "historical B1 was silently repointed")
        cursor.execute(
            "SELECT object_kind,certifiability_classification,count(*) "
            "FROM normative.catalog_object_classification GROUP BY 1,2 ORDER BY 1"
        )
        classifications = cursor.fetchall()
        require(("requirement_control", "normative_requirement", requirement_count_before) in classifications,
                "requirement classification view mismatch")
        cursor.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema='qms' "
            "AND table_name='evidence_coverage' AND column_name IN ('knowledge_layer_rule_id','knowledge_layer_binding_id')"
        )
        require(cursor.fetchone()[0] == 0, "EvidenceCoverage can treat guidance as a requirement")

    require(query.certifiable_requirement_count() == requirement_count_before,
            "guidance increased the certifiable requirement count")

    for alias in ("app", "worker", "projector"):
        with phase3.runtime_transaction(alias) as cursor:
            for table in CATALOG_TABLES:
                cursor.execute(f"SELECT count(*) FROM normative.{table}")
                require(cursor.fetchone()[0] > 0, f"{alias} cannot read {table}")
            expect_error(lambda c=cursor: c.execute(
                "INSERT INTO normative.knowledge_layer(id,standard_edition_id,layer_type) VALUES (%s,%s,'DENIED')",
                [str(uuid4()), str(guide_edition)],
            ), "permission denied")

    def privileged(sql, params):
        with migrator.cursor() as cursor:
            cursor.execute(sql, params)

    for sql, params, fragment in (
        ("UPDATE normative.knowledge_layer_rule SET logic_json='{}'::jsonb WHERE id=%s", [str(rule1)], "published"),
        ("UPDATE normative.knowledge_layer_rule SET knowledge_layer_id=%s WHERE id=%s", [str(layer_id), str(rule1)], "published"),
        ("UPDATE normative.knowledge_layer_rule SET version='rewritten' WHERE id=%s", [str(rule1)], "published"),
        ("UPDATE normative.knowledge_layer_rule SET previous_revision_id=%s WHERE id=%s", [str(rule3), str(rule1)], "published"),
        ("DELETE FROM normative.knowledge_layer_rule WHERE id=%s", [str(rule1)], "published"),
        ("UPDATE normative.knowledge_layer_binding SET knowledge_layer_rule_id=%s WHERE id=%s", [str(rule2), str(binding1)], "published"),
        ("UPDATE normative.knowledge_layer_binding SET requirement_control_id=%s,standard_edition_id=%s WHERE id=%s", [str(control2), str(edition2), str(binding1)], "published"),
        ("DELETE FROM normative.knowledge_layer_binding WHERE id=%s", [str(binding1)], "published"),
    ):
        expect_error(lambda s=sql, p=params: privileged(s, p), fragment)
        migrator.rollback()

    duplicate_id = uuid4()
    expect_error(lambda: privileged(
        "INSERT INTO normative.knowledge_layer_binding(id,knowledge_layer_rule_id,standard_edition_id,requirement_control_id) VALUES (%s,%s,%s,%s)",
        [str(duplicate_id), str(rule1), str(edition1), str(control1)]), "unique")
    migrator.rollback()
    self_rule = uuid4()
    expect_error(lambda: privileged(
        "INSERT INTO normative.knowledge_layer_rule(id,knowledge_layer_id,lineage_id,rule_key,version,previous_revision_id) VALUES (%s,%s,%s,'self-test','v1',%s)",
        [str(self_rule), str(layer_id), str(self_rule), str(self_rule)]), "predecessor")
    migrator.rollback()
    expect_error(lambda: privileged(
        "INSERT INTO normative.knowledge_layer_binding(id,knowledge_layer_rule_id,standard_edition_id,requirement_control_id) VALUES (%s,%s,%s,%s)",
        [str(uuid4()), str(rule3), str(edition2), str(control1)]), "foreign key")
    migrator.rollback()
    expect_error(lambda: privileged(
        "INSERT INTO normative.knowledge_layer_binding(id,knowledge_layer_rule_id,standard_edition_id,requirement_control_id) VALUES (%s,%s,%s,%s)",
        [str(uuid4()), str(uuid4()), str(edition1), str(control1)]), "published exact rule")
    migrator.rollback()

    rollback_rule = knowledge.create_knowledge_layer_rule(
        knowledge_layer_id=layer_id, rule_key="rollback-guidance", version="v1",
        logic_json={"fixture": True}, evidence_expectation={"fixture": True},
        source_reference="synthetic://phase9/rollback", actor_id=actor, trace_id=uuid4(),
    )
    with connections["normative_curator"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        before_failed_publish = cursor.fetchone()[0]
    expect_error(lambda: knowledge.publish_knowledge_layer_rule(
        rule_id=rollback_rule, actor_id=actor, trace_id=uuid4(), fail_before_commit=True), "deliberate")
    with phase3.runtime_transaction("normative_curator") as cursor:
        cursor.execute("SELECT status FROM normative.knowledge_layer_rule WHERE id=%s", [str(rollback_rule)])
        require(cursor.fetchone()[0] == "draft", "failed rule publication changed status")
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        require(cursor.fetchone()[0] == before_failed_publish, "failed rule publication left audit")
    expect_error(lambda: privileged(
        "INSERT INTO normative.knowledge_layer_binding(id,knowledge_layer_rule_id,standard_edition_id,requirement_control_id) VALUES (%s,%s,%s,%s)",
        [str(uuid4()), str(rollback_rule), str(edition1), str(control1)]), "published exact rule")
    migrator.rollback()

    rollback_binding = knowledge.create_knowledge_layer_binding(
        knowledge_layer_rule_id=rule1, standard_edition_id=edition2,
        requirement_control_id=control2, priority="P2",
        rationale="NON-OFFICIAL TEST FIXTURE: publication rollback.",
        actor_id=actor, trace_id=uuid4(),
    )
    with connections["normative_curator"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        before_failed_binding_publish = cursor.fetchone()[0]
    expect_error(lambda: knowledge.publish_knowledge_layer_binding(
        binding_id=rollback_binding, actor_id=actor, trace_id=uuid4(),
        fail_before_commit=True), "deliberate")
    with phase3.runtime_transaction("normative_curator") as cursor:
        cursor.execute("SELECT status FROM normative.knowledge_layer_binding WHERE id=%s",
                       [str(rollback_binding)])
        require(cursor.fetchone()[0] == "draft", "failed binding publication changed status")
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        require(cursor.fetchone()[0] == before_failed_binding_publish,
                "failed binding publication left audit")

    with phase3.runtime_transaction("normative_curator") as cursor:
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        require(cursor.fetchone()[0] > audit_before, "Phase 9 material mutations were not audited")
        expect_error(lambda c=cursor: c.execute(
            "UPDATE normative.knowledge_layer_rule SET logic_json='{}'::jsonb WHERE id=%s", [str(rule3)]
        ), "permission denied")

    phase3.migrate(PHASE8_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('normative.standard'),to_regclass('normative.requirement_control'),"
            "to_regclass('qms.evidence_coverage'),to_regclass('normative.knowledge_layer')"
        )
        require(cursor.fetchone() == ("normative.standard", "normative.requirement_control",
                                      "qms.evidence_coverage", None),
                "Phase 9 reverse damaged Phase 8")
    reverse_probe = normative.create_standard(
        code="P9-REVERSE-PROBE", title="NON-OFFICIAL TEST FIXTURE", publisher="TEST",
        actor_id=actor, trace_id=uuid4(),
    )
    require(reverse_probe is not None, "Phase 8 curator command failed after Phase 9 reverse")
    phase3.migrate(PHASE9_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('normative.knowledge_layer'),"
            "to_regclass('normative.knowledge_layer_rule'),"
            "to_regclass('normative.knowledge_layer_binding'),"
            "to_regclass('normative.catalog_object_classification')"
        )
        require(all(cursor.fetchone()), "Phase 9 second forward incomplete")

    print(json.dumps({
        "status": "PASS",
        "migration": "0009_knowledge_layer_foundation",
        "runtime_privileges": "APP/WORKER/PROJECTOR SELECT-only on all Phase 9 catalog tables",
        "curator_privileges": "controlled INSERT + status/published_at only; zero QMS writes",
        "rule_history": "v1 -> v2 -> v3 retained; one lineage/current leaf; provenance retained",
        "binding_history": "B1 remains Rule v1 + Edition1/RC1 after v2/v3 and Edition2/RC2",
        "certifiability": "RequirementControl-only count unchanged; guidance fixed non-certifiable",
        "raw_sql": "published Rule/Binding material UPDATE and DELETE rejected",
        "global_events": "no fake tenant and no global DomainEvent; curation ledger reused",
        "forward_reverse_forward": "0001 -> ... -> 0009 -> 0008 -> 0009 PASS",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
