"""Blocking Phase 8 matrix layered on the promoted Phase 7 PostgreSQL gate."""

import hashlib
import json
import os
import sys
from uuid import UUID, uuid4

import postgres_foundation_harness as phase3
import postgres_phase7_harness as phase7


PHASE7_MIGRATION = ("foundation", "0007_document_evidence_foundation")
PHASE8_MIGRATION = ("foundation", "0008_evidence_coverage_normative_core_foundation")
CATALOG_TABLES = ("standard", "standard_edition", "clause", "requirement_control")
ADMINAPPS_USER_A = UUID("50000000-0000-4000-8000-000000000001")


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


def coverage_visible(alias, tenant=None):
    with phase3.runtime_transaction(alias, tenant) as cursor:
        cursor.execute("SELECT count(*) FROM qms.evidence_coverage")
        return cursor.fetchone()[0]


def run():
    phase7.run()
    phase3.migrate(PHASE8_MIGRATION)

    from django.db import connections
    from django.utils import timezone
    from foundation.audit import verify_audit_stream
    from foundation.document_evidence import DocumentEvidenceCommandService
    from foundation.models import (
        Clause, DomainEvent, EvidenceCoverage, ImmutableAuditLog,
        NormativeCurationAudit, RequirementControl, StandardEdition,
        TransactionalOutbox,
    )
    from foundation.normative_coverage import (
        EvidenceCoverageCommandService, NormativeCatalogCommandService,
    )
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    migrator = connections["default"]
    app_role = os.environ["FOUNDATION_APP_ROLE"]
    worker_role = os.environ["FOUNDATION_WORKER_ROLE"]
    projector_role = os.environ["FOUNDATION_PROJECTOR_ROLE"]
    audit_writer_role = os.environ["FOUNDATION_AUDIT_WRITER_ROLE"]
    curator_role = os.environ["FOUNDATION_NORMATIVE_CURATOR_ROLE"]

    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT rolname,rolcanlogin,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s",
            [curator_role],
        )
        curator = cursor.fetchone()
        require(curator == (curator_role, True, False, False), "normative curator role flags invalid")
        cursor.execute(
            "SELECT c.relname,r.rolname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname IN ('normative','qms') "
            "AND c.relname=ANY(%s)",
            [list(CATALOG_TABLES) + ["curation_audit", "evidence_coverage"]],
        )
        ownership = cursor.fetchall()
        require(len(ownership) == 6 and all(owner != curator_role for _, owner in ownership),
                "normative curator owns Phase 8 objects")
        cursor.execute(
            "SELECT relrowsecurity,relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='qms' AND c.relname='evidence_coverage'"
        )
        require(cursor.fetchone() == (True, True), "Coverage ENABLE/FORCE RLS missing")
        cursor.execute(
            "SELECT cmd FROM pg_policies WHERE schemaname='qms' AND tablename='evidence_coverage'"
        )
        policy_commands = {row[0] for row in cursor.fetchall()}
        require(policy_commands == {"SELECT", "INSERT", "UPDATE", "DELETE", "ALL"},
                "Coverage explicit policy matrix incomplete")

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
            require(cursor.fetchone() == (True, True, False), f"curator grant drift for {table}")
        cursor.execute(
            "SELECT has_column_privilege(%s,'normative.standard_edition','status','UPDATE'),"
            "has_column_privilege(%s,'normative.standard_edition','edition','UPDATE')",
            [curator_role, curator_role],
        )
        require(cursor.fetchone() == (True, False), "curator edition UPDATE is not column-minimal")
        for table in ("tenant_projection", "organization", "evidence", "evidence_coverage"):
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.'||%s,'INSERT'),"
                "has_table_privilege(%s,'qms.'||%s,'UPDATE'),"
                "has_table_privilege(%s,'qms.'||%s,'DELETE')",
                [curator_role, table, curator_role, table, curator_role, table],
            )
            require(cursor.fetchone() == (False, False, False), f"curator can mutate qms.{table}")
        cursor.execute(
            "SELECT has_table_privilege(%s,'normative.standard','INSERT')",
            [audit_writer_role],
        )
        require(cursor.fetchone()[0] is False, "audit writer can mutate normative catalog")

    curator_service = NormativeCatalogCommandService(using="normative_curator")
    curator_actor = "phase8-synthetic-curator"
    standard_id = curator_service.create_standard(
        code="TEST-STD", title="Synthetic test standard; not official ISO content",
        publisher="TEST", actor_id=curator_actor, trace_id=uuid4(),
    )
    edition1 = curator_service.create_standard_edition(
        standard_id=standard_id, edition="test-edition-1", source_hash="1" * 64,
        actor_id=curator_actor, trace_id=uuid4(),
    )
    clause1_root = curator_service.add_clause(
        standard_edition_id=edition1, code="4", title="Synthetic root",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    clause1 = curator_service.add_clause(
        standard_edition_id=edition1, code="4.1", title="Synthetic child",
        parent_id=clause1_root, actor_id=curator_actor, trace_id=uuid4(),
    )
    control1 = curator_service.add_requirement_control(
        standard_edition_id=edition1, clause_id=clause1,
        paraphrase="Synthetic test control; not official ISO normative text.",
        applicability_rule={"synthetic": True}, control_type="test",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    curator_service.publish_standard_edition(
        standard_edition_id=edition1, actor_id=curator_actor, trace_id=uuid4(),
    )

    edition2 = curator_service.create_standard_edition(
        standard_id=standard_id, edition="test-edition-2", source_hash="2" * 64,
        actor_id=curator_actor, trace_id=uuid4(),
    )
    clause2 = curator_service.add_clause(
        standard_edition_id=edition2, code="4.1", title="Synthetic edition 2 clause",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    control2 = curator_service.add_requirement_control(
        standard_edition_id=edition2, clause_id=clause2,
        paraphrase="Synthetic test control edition 2; not official ISO normative text.",
        applicability_rule={"synthetic": True, "edition": 2}, control_type="test",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    curator_service.publish_standard_edition(
        standard_edition_id=edition2, actor_id=curator_actor, trace_id=uuid4(),
    )

    with phase3.runtime_transaction("normative_curator") as cursor:
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        require(cursor.fetchone()[0] == 10, "normative material commands are not fully audited")
        cursor.execute("SELECT status FROM normative.standard_edition ORDER BY edition")
        require(cursor.fetchall() == [("published",), ("published",)], "edition publication failed")

    for alias in ("app", "worker", "projector"):
        with phase3.runtime_transaction(alias) as cursor:
            cursor.execute("SELECT count(*) FROM normative.standard")
            require(cursor.fetchone()[0] == 1, f"{alias} cannot read Standard")
            expect_error(lambda c=cursor: c.execute(
                "INSERT INTO normative.standard(id,code,publisher) VALUES (%s,'DENIED','TEST')",
                [str(uuid4())],
            ), "permission denied")

    def curator_sql(sql, params):
        with phase3.runtime_transaction("normative_curator") as cursor:
            cursor.execute(sql, params)

    def privileged(sql, params):
        with migrator.cursor() as cursor:
            cursor.execute(sql, params)

    expect_error(lambda: curator_sql(
        "UPDATE normative.standard_edition SET edition='rewritten' WHERE id=%s",
        [str(edition1)]), "permission denied")
    expect_error(lambda: curator_sql(
        "INSERT INTO normative.clause(id,standard_edition_id,code,title) VALUES (%s,%s,'late','late')",
        [str(uuid4()), str(edition1)]), "published normative material")
    expect_error(lambda: privileged(
        "UPDATE normative.standard_edition SET effective_from=current_date WHERE id=%s",
        [str(edition1)]), "published standard edition")
    migrator.rollback()
    expect_error(lambda: privileged(
        "UPDATE normative.clause SET title='rewritten' WHERE id=%s", [str(clause1)]),
        "published normative material")
    migrator.rollback()
    expect_error(lambda: privileged(
        "UPDATE normative.requirement_control SET paraphrase='rewritten' WHERE id=%s",
        [str(control1)]), "published normative material")
    migrator.rollback()
    expect_error(lambda: privileged(
        "DELETE FROM normative.standard_edition WHERE id=%s", [str(edition1)]),
        "published standard edition")
    migrator.rollback()

    draft3 = curator_service.create_standard_edition(
        standard_id=standard_id, edition="cycle-test", actor_id=curator_actor, trace_id=uuid4(),
    )
    cycle_a = curator_service.add_clause(
        standard_edition_id=draft3, code="A", actor_id=curator_actor, trace_id=uuid4(),
    )
    cycle_b = curator_service.add_clause(
        standard_edition_id=draft3, code="B", parent_id=cycle_a,
        actor_id=curator_actor, trace_id=uuid4(),
    )
    expect_error(lambda: privileged(
        "UPDATE normative.clause SET parent_id=%s WHERE id=%s",
        [str(cycle_b), str(cycle_a)]), "cycle")
    migrator.rollback()
    expect_error(lambda: curator_sql(
        "INSERT INTO normative.clause(id,standard_edition_id,code,parent_id) VALUES (%s,%s,'cross',%s)",
        [str(uuid4()), str(draft3), str(clause1)]))
    curator_service.add_requirement_control(
        standard_edition_id=draft3, clause_id=cycle_a,
        paraphrase="Synthetic rollback-only control; not official normative text.",
        actor_id=curator_actor, trace_id=uuid4(),
    )
    with phase3.runtime_transaction("normative_curator") as cursor:
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        publish_before_audit = cursor.fetchone()[0]
    expect_error(lambda: curator_service.publish_standard_edition(
        standard_edition_id=draft3, actor_id=curator_actor, trace_id=uuid4(),
        fail_before_commit=True), "deliberate Phase 8 publication rollback")
    with phase3.runtime_transaction("normative_curator") as cursor:
        cursor.execute("SELECT status FROM normative.standard_edition WHERE id=%s", [str(draft3)])
        require(cursor.fetchone()[0] == "draft", "failed publication left edition published")
        cursor.execute("SELECT count(*) FROM normative.curation_audit")
        require(cursor.fetchone()[0] == publish_before_audit,
                "failed publication left a partial curation audit record")

    identity_a = TrustedTenantIdentity("phase8-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase8-b", phase3.TENANT_B)
    document_service = DocumentEvidenceCommandService(using="app")
    actor = "phase8-gate"
    document_a = document_service.create_document(
        identity=identity_a, organization_id=phase3.ORG_A, document_type="record",
        actor_id=actor, trace_id=uuid4(),
    )
    version_a1 = document_service.create_document_version(
        identity=identity_a, document_id=document_a.entity_id, version="1",
        content_reference="object://phase8/a/v1", content_bytes=b"phase8-a-v1",
        actor_id=actor, trace_id=uuid4(),
    )
    version_a2 = document_service.create_document_version(
        identity=identity_a, document_id=document_a.entity_id, version="2",
        content_reference="object://phase8/a/v2", content_bytes=b"phase8-a-v2",
        actor_id=actor, trace_id=uuid4(),
    )
    evidence_a1 = document_service.create_evidence(
        identity=identity_a, organization_id=phase3.ORG_A, source_type="document_version",
        document_version_id=version_a1.entity_id, captured_at=timezone.now(),
        actor_id=actor, trace_id=uuid4(),
    )
    evidence_a2 = document_service.supersede_evidence(
        identity=identity_a, evidence_id=evidence_a1.entity_id,
        source_type="document_version", document_version_id=version_a2.entity_id,
        captured_at=timezone.now(), change_reason="synthetic revision",
        actor_id=actor, trace_id=uuid4(),
    )
    document_b = document_service.create_document(
        identity=identity_b, organization_id=phase3.ORG_B, document_type="record",
        actor_id=actor, trace_id=uuid4(),
    )
    version_b = document_service.create_document_version(
        identity=identity_b, document_id=document_b.entity_id, version="1",
        content_reference="object://phase8/b/v1", content_bytes=b"phase8-b-v1",
        actor_id=actor, trace_id=uuid4(),
    )
    evidence_b = document_service.create_evidence(
        identity=identity_b, organization_id=phase3.ORG_B, source_type="document_version",
        document_version_id=version_b.entity_id, captured_at=timezone.now(),
        actor_id=actor, trace_id=uuid4(),
    )

    coverage_service = EvidenceCoverageCommandService(using="app")
    with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
        cursor.execute(
            "SELECT id FROM qms.user_projection WHERE adminapps_user_id=%s",
            [str(ADMINAPPS_USER_A)],
        )
        user_a_id = cursor.fetchone()[0]
    coverage1 = coverage_service.record_evidence_coverage(
        identity=identity_a, organization_id=phase3.ORG_A,
        evidence_id=evidence_a1.entity_id, standard_edition_id=edition1,
        requirement_control_id=control1, confidence="0.9000",
        validation_status="validated", validated_by=user_a_id, validated_at=timezone.now(),
        actor_id=actor, trace_id=uuid4(),
    )
    coverage2 = coverage_service.record_evidence_coverage(
        identity=identity_a, organization_id=phase3.ORG_A,
        evidence_id=evidence_a2.entity_id, standard_edition_id=edition2,
        requirement_control_id=control2, confidence="0.9500",
        validation_status="proposed", actor_id=actor, trace_id=uuid4(),
    )
    coverage_b = coverage_service.record_evidence_coverage(
        identity=identity_b, organization_id=phase3.ORG_B,
        evidence_id=evidence_b.entity_id, standard_edition_id=edition1,
        requirement_control_id=control1, validation_status="proposed",
        actor_id=actor, trace_id=uuid4(),
    )

    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        row = EvidenceCoverage.objects.using("app").get(id=coverage1.entity_id)
        require((row.evidence_id, row.standard_edition_id, row.requirement_control_id) ==
                (evidence_a1.entity_id, edition1, control1), "coverage exact references changed")
        require(EvidenceCoverage.objects.using("app").get(id=coverage2.entity_id).evidence_id == evidence_a2.entity_id,
                "new coverage did not use exact Evidence revision 2")
        event = DomainEvent.objects.using("app").get(event_id=coverage1.event_id)
        outbox = TransactionalOutbox.objects.using("app").get(id=coverage1.outbox_id)
        audit = ImmutableAuditLog.objects.using("app").get(id=coverage1.audit_id)
        require(event.tenant_id == outbox.tenant_id == audit.tenant_id == phase3.TENANT_A,
                "coverage atomic tenant mismatch")
        require(event.trace_id == audit.trace_id == coverage1.trace_id, "coverage atomic trace mismatch")
        require(event.event_type == "evidence_coverage.recorded" and event.schema_version == 1,
                "coverage event contract mismatch")
        require(event.payload["evidence_revision"] == 1, "event omitted exact Evidence revision")
        require(verify_audit_stream(tenant_id=phase3.TENANT_A,
                                    stream_type="evidence_coverage", stream_id=coverage1.entity_id,
                                    using="app"), "Coverage audit chain invalid")

    expect_error(lambda: coverage_service.record_evidence_coverage(
        identity=identity_a, organization_id=phase3.ORG_A,
        evidence_id=evidence_a1.entity_id, standard_edition_id=edition1,
        requirement_control_id=control1, actor_id=actor, trace_id=uuid4()), "unique")

    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        before = (EvidenceCoverage.objects.using("app").count(),
                  DomainEvent.objects.using("app").count(),
                  TransactionalOutbox.objects.using("app").count(),
                  ImmutableAuditLog.objects.using("app").count())
    expect_error(lambda: coverage_service.record_evidence_coverage(
        identity=identity_a, organization_id=phase3.ORG_A,
        evidence_id=evidence_a2.entity_id, standard_edition_id=edition1,
        requirement_control_id=control1, actor_id=actor, trace_id=uuid4(),
        fail_before_commit=True), "deliberate Phase 8 coverage rollback")
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        after = (EvidenceCoverage.objects.using("app").count(),
                 DomainEvent.objects.using("app").count(),
                 TransactionalOutbox.objects.using("app").count(),
                 ImmutableAuditLog.objects.using("app").count())
    require(after == before, "coverage rollback left partial business/event/outbox/audit state")

    require([coverage_visible("app", phase3.TENANT_A), coverage_visible("app"),
             coverage_visible("app", phase3.TENANT_B)] == [2, 0, 1],
            "Coverage app A/none/B matrix failed")
    require([coverage_visible("worker", phase3.TENANT_A), coverage_visible("worker"),
             coverage_visible("worker", phase3.TENANT_B)] == [2, 0, 1],
            "Coverage worker A/none/B matrix failed")
    try:
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.evidence_coverage")
            raise RuntimeError("intentional Phase 8 rollback context")
    except RuntimeError:
        pass
    require(coverage_visible("app") == 0 and coverage_visible("app", phase3.TENANT_B) == 1,
            "Coverage rollback context leaked")

    def raw_coverage(sql, params):
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute(sql, params)

    expect_error(lambda: raw_coverage(
        "INSERT INTO qms.evidence_coverage(id,tenant_id,organization_id,evidence_id,standard_edition_id,requirement_control_id) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(evidence_b.entity_id),
         str(edition1), str(control1)]))
    expect_error(lambda: raw_coverage(
        "INSERT INTO qms.evidence_coverage(id,tenant_id,organization_id,evidence_id,standard_edition_id,requirement_control_id) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(evidence_a2.entity_id),
         str(edition2), str(control1)]))
    expect_error(lambda: raw_coverage(
        "UPDATE qms.evidence_coverage SET confidence=0.1 WHERE id=%s", [str(coverage1.entity_id)]),
        "permission denied")
    expect_error(lambda: privileged(
        "UPDATE qms.evidence_coverage SET confidence=0.1 WHERE id=%s", [str(coverage1.entity_id)]),
        "append-only")
    migrator.rollback()
    expect_error(lambda: curator_sql(
        "INSERT INTO qms.evidence_coverage(id,tenant_id,organization_id,evidence_id,standard_edition_id,requirement_control_id) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(evidence_a2.entity_id),
         str(edition2), str(control2)]), "permission denied")

    phase3.migrate(PHASE7_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('qms.document'),to_regclass('qms.evidence'),"
            "to_regclass('qms.evidence_coverage'),to_regclass('normative.standard')"
        )
        require(cursor.fetchone() == ("qms.document", "qms.evidence", None, None),
                "Phase 8 reverse damaged promoted Phase 7")
    reverse_probe = document_service.create_evidence(
        identity=identity_a, organization_id=phase3.ORG_A, source_type="manual",
        source_uri="synthetic://phase8/reverse-probe",
        content_hash=hashlib.sha256(b"reverse-probe").hexdigest(),
        captured_at=timezone.now(), actor_id=actor, trace_id=uuid4(),
    )
    require(reverse_probe.entity_id is not None, "Phase 7 command failed after Phase 8 reverse")
    phase3.migrate(PHASE8_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('normative.standard'),to_regclass('qms.evidence_coverage')"
        )
        require(cursor.fetchone() == ("normative.standard", "qms.evidence_coverage"),
                "Phase 8 second forward failed")

    print(json.dumps({
        "status": "PASS",
        "migration": "0008_evidence_coverage_normative_core_foundation",
        "catalog": "global Standard/Edition/Clause/RequirementControl; runtime SELECT only",
        "curator": "LOGIN non-superuser/NOBYPASSRLS/non-owner; controlled INSERT + edition status UPDATE only",
        "curation_audit": "all material command operations recorded; append-only table",
        "publication": "draft -> published atomic; published edition/clause/control UPDATE/DELETE rejected",
        "clause_hierarchy": "edition-safe parent, cross-edition/self/cycle defense",
        "coverage": "append-only exact Evidence revision + exact Edition/Control",
        "duplicate_key": "tenant + organization + exact evidence revision + requirement control",
        "rls": "ENABLE+FORCE; app/worker A=2, none=0, B=1",
        "eventing": "evidence_coverage.recorded v1 + outbox + immutable audit atomic",
        "global_event_decision": "no fake tenant and no global DomainEvent; isolated curation audit",
        "rollback": "post-audit failure leaves zero partial state",
        "history": "Coverage 1 remains Edition 1/Control 1/Evidence revision 1 after Edition 2/Evidence revision 2",
        "forward_reverse_forward": "0001 -> ... -> 0008 -> 0007 -> 0008 PASS",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
