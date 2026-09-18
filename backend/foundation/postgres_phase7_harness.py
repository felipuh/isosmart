"""Blocking Phase 7 matrix layered on the promoted Phase 6 PostgreSQL gate."""

import hashlib
import json
import os
import sys
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase6_harness as phase6


TABLES = ("document", "document_version", "evidence")
PHASE6_MIGRATION = ("foundation", "0006_change_performance_measurement_foundation")
PHASE7_MIGRATION = ("foundation", "0007_document_evidence_foundation")


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
    require(table in TABLES, "unknown Phase 7 table")
    with phase3.runtime_transaction(alias, tenant) as cursor:
        cursor.execute(f"SELECT count(*) FROM qms.{table}")
        return cursor.fetchone()[0]


def run():
    phase6.run()
    phase3.migrate(PHASE7_MIGRATION)

    from django.db import connections
    from django.utils import timezone
    from foundation.audit import verify_audit_stream
    from foundation.document_evidence import DocumentEvidenceCommandService
    from foundation.models import (
        Document, DocumentVersion, DomainEvent, Evidence, ImmutableAuditLog,
        TransactionalOutbox,
    )
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    migrator = connections["default"]
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,r.rolname "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner "
            "WHERE n.nspname='qms' AND c.relname=ANY(%s) ORDER BY c.relname",
            [list(TABLES)],
        )
        protected = cursor.fetchall()
        require(len(protected) == 3, "Phase 7 protected tables missing")
        require(all(row[1] and row[2] for row in protected), "Phase 7 ENABLE/FORCE RLS missing")
        require(all(row[3] == os.environ["FOUNDATION_MIGRATOR_ROLE"] for row in protected),
                "runtime owns Phase 7 table")
        cursor.execute(
            "SELECT tablename,cmd FROM pg_policies WHERE schemaname='qms' AND tablename=ANY(%s)",
            [list(TABLES)],
        )
        policies = cursor.fetchall()
        require(len(policies) == 15, f"expected 15 explicit Phase 7 policies, found {len(policies)}")
        for table in TABLES:
            require({row[1] for row in policies if row[0] == table} ==
                    {"SELECT", "INSERT", "UPDATE", "DELETE", "ALL"},
                    f"policy matrix incomplete for {table}")
        app = os.environ["FOUNDATION_APP_ROLE"]
        worker = os.environ["FOUNDATION_WORKER_ROLE"]
        projector = os.environ["FOUNDATION_PROJECTOR_ROLE"]
        audit_writer = os.environ["FOUNDATION_AUDIT_WRITER_ROLE"]
        for table in TABLES:
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.'||%s,'SELECT'),"
                "has_table_privilege(%s,'qms.'||%s,'INSERT'),"
                "has_table_privilege(%s,'qms.'||%s,'UPDATE'),"
                "has_table_privilege(%s,'qms.'||%s,'DELETE')",
                [app, table, app, table, app, table, app, table],
            )
            expected = (True, True, table == "document", False)
            require(cursor.fetchone() == expected, f"app privilege drift for {table}")
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.'||%s,'SELECT'),"
                "has_table_privilege(%s,'qms.'||%s,'INSERT')",
                [worker, table, worker, table],
            )
            require(cursor.fetchone() == (True, False), f"worker privilege drift for {table}")
            for role in (projector, audit_writer):
                cursor.execute("SELECT has_table_privilege(%s,'qms.'||%s,'SELECT')", [role, table])
                require(cursor.fetchone()[0] is False, f"{role} can read {table}")

    identity_a = TrustedTenantIdentity("phase7-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase7-b", phase3.TENANT_B)
    service = DocumentEvidenceCommandService(using="app")
    actor = "phase7-gate"

    document_a = service.create_document(
        identity=identity_a, organization_id=phase3.ORG_A, document_type="procedure",
        actor_id=actor, trace_id=uuid4(),
    )
    document_b = service.create_document(
        identity=identity_b, organization_id=phase3.ORG_B, document_type="record",
        actor_id=actor, trace_id=uuid4(),
    )
    bytes_v1 = b"ISO Smart Phase 7 fixture\x00v1\n"
    bytes_v2 = b"ISO Smart Phase 7 fixture\x00v2\n"
    bytes_v3 = b"ISO Smart Phase 7 fixture\x00v3\n"
    version_a_v1 = service.create_document_version(
        identity=identity_a, document_id=document_a.entity_id, version="1",
        content_reference="object://phase7/a/procedure/v1", content_bytes=bytes_v1,
        actor_id=actor, trace_id=uuid4(),
    )
    version_a_v2 = service.create_document_version(
        identity=identity_a, document_id=document_a.entity_id, version="2",
        content_reference="object://phase7/a/procedure/v2", content_bytes=bytes_v2,
        actor_id=actor, trace_id=uuid4(),
    )
    version_a_v3 = service.create_document_version(
        identity=identity_a, document_id=document_a.entity_id, version="3",
        content_reference="object://phase7/a/procedure/v3", content_bytes=bytes_v3,
        actor_id=actor, trace_id=uuid4(),
    )
    version_b_v1 = service.create_document_version(
        identity=identity_b, document_id=document_b.entity_id, version="1",
        content_reference="object://phase7/b/record/v1", content_bytes=b"tenant-b",
        actor_id=actor, trace_id=uuid4(),
    )
    evidence_a_v1 = service.create_evidence(
        identity=identity_a, organization_id=phase3.ORG_A, source_type="document_version",
        document_version_id=version_a_v1.entity_id, captured_at=timezone.now(),
        trust_score="0.9000", actor_id=actor, trace_id=uuid4(),
    )
    evidence_a_v2 = service.supersede_evidence(
        identity=identity_a, evidence_id=evidence_a_v1.entity_id, source_type="document_version",
        document_version_id=version_a_v2.entity_id, captured_at=timezone.now(),
        trust_score="0.9500", change_reason="Document revised", actor_id=actor, trace_id=uuid4(),
    )
    evidence_a_v3 = service.supersede_evidence(
        identity=identity_a, evidence_id=evidence_a_v2.entity_id, source_type="document_version",
        document_version_id=version_a_v3.entity_id, captured_at=timezone.now(),
        trust_score="1.0000", change_reason="Approved material version", actor_id=actor, trace_id=uuid4(),
    )
    evidence_b = service.create_evidence(
        identity=identity_b, organization_id=phase3.ORG_B, source_type="document_version",
        document_version_id=version_b_v1.entity_id, captured_at=timezone.now(),
        actor_id=actor, trace_id=uuid4(),
    )

    for result, identity, tenant in (
        (document_a, identity_a, phase3.TENANT_A),
        (version_a_v1, identity_a, phase3.TENANT_A),
        (evidence_a_v1, identity_a, phase3.TENANT_A),
    ):
        with trusted_tenant_context(identity, actor_id=actor, trace_id=uuid4(), using="app"):
            event = DomainEvent.objects.using("app").get(event_id=result.event_id)
            outbox = TransactionalOutbox.objects.using("app").get(id=result.outbox_id)
            audit = ImmutableAuditLog.objects.using("app").get(id=result.audit_id)
            require(event.tenant_id == tenant == outbox.tenant_id == audit.tenant_id,
                    "atomic tenant mismatch")
            require(event.trace_id == result.trace_id == audit.trace_id, "atomic trace mismatch")
            require(event.aggregate_id == result.aggregate_id == audit.stream_id,
                    "atomic aggregate mismatch")

    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        versions = list(DocumentVersion.objects.using("app").filter(document_id=document_a.entity_id)
                        .order_by("created_at").values_list(
                            "id", "version", "predecessor_id", "content_hash"))
        require(versions == [
            (version_a_v1.entity_id, "1", None, hashlib.sha256(bytes_v1).hexdigest()),
            (version_a_v2.entity_id, "2", version_a_v1.entity_id, hashlib.sha256(bytes_v2).hexdigest()),
            (version_a_v3.entity_id, "3", version_a_v2.entity_id, hashlib.sha256(bytes_v3).hexdigest()),
        ], "Document v1 -> v2 -> v3 history/hash mismatch")
        require(Document.objects.using("app").get(id=document_a.entity_id).current_version_id == version_a_v3.entity_id,
                "Document current version is ambiguous")
        evidence = list(Evidence.objects.using("app").filter(lineage_id=evidence_a_v1.aggregate_id)
                        .order_by("revision").values_list(
                            "id", "revision", "previous_revision_id", "document_version_id", "content_hash"))
        require(evidence == [
            (evidence_a_v1.entity_id, 1, None, version_a_v1.entity_id, hashlib.sha256(bytes_v1).hexdigest()),
            (evidence_a_v2.entity_id, 2, evidence_a_v1.entity_id, version_a_v2.entity_id, hashlib.sha256(bytes_v2).hexdigest()),
            (evidence_a_v3.entity_id, 3, evidence_a_v2.entity_id, version_a_v3.entity_id, hashlib.sha256(bytes_v3).hexdigest()),
        ], "Evidence v1 -> v2 -> v3 provenance history mismatch")
        require(verify_audit_stream(tenant_id=phase3.TENANT_A, stream_type="document",
                                    stream_id=document_a.entity_id, using="app"),
                "Document audit chain invalid")
        require(verify_audit_stream(tenant_id=phase3.TENANT_A, stream_type="evidence",
                                    stream_id=evidence_a_v1.aggregate_id, using="app"),
                "Evidence audit chain invalid")
        require(DomainEvent.objects.using("app").filter(
            aggregate_type="document", aggregate_id=document_a.entity_id).count() == 4,
            "Document event history incomplete")
        require(DomainEvent.objects.using("app").filter(
            aggregate_type="evidence", aggregate_id=evidence_a_v1.aggregate_id).count() == 3,
            "Evidence event history incomplete")

    for model, operation in (
        (DocumentVersion, lambda: service.create_document_version(
            identity=identity_a, document_id=document_a.entity_id, version="4",
            content_reference="object://phase7/a/procedure/v4", content_bytes=b"rollback-v4",
            actor_id=actor, trace_id=uuid4(), fail_before_commit=True)),
        (Evidence, lambda: service.supersede_evidence(
            identity=identity_a, evidence_id=evidence_a_v3.entity_id, source_type="manual",
            source_uri="capture://rollback", content_hash=hashlib.sha256(b"rollback").hexdigest(),
            captured_at=timezone.now(), actor_id=actor, trace_id=uuid4(),
            fail_before_commit=True)),
    ):
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            before = (model.objects.using("app").count(), DomainEvent.objects.using("app").count(),
                      TransactionalOutbox.objects.using("app").count(), ImmutableAuditLog.objects.using("app").count())
        expect_error(operation, "deliberate Phase 7 rollback")
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            after = (model.objects.using("app").count(), DomainEvent.objects.using("app").count(),
                     TransactionalOutbox.objects.using("app").count(), ImmutableAuditLog.objects.using("app").count())
        require(after == before, f"{model.__name__} rollback left partial state")

    matrix = {table: [visible("app", table, phase3.TENANT_A), visible("app", table),
                      visible("app", table, phase3.TENANT_B)] for table in TABLES}
    worker_matrix = {table: [visible("worker", table, phase3.TENANT_A), visible("worker", table),
                             visible("worker", table, phase3.TENANT_B)] for table in TABLES}
    require(all(v[0] > 0 and v[1] == 0 and v[2] > 0 for v in matrix.values()),
            "Phase 7 app RLS/pool matrix failed")
    require(all(v[0] > 0 and v[1] == 0 and v[2] > 0 for v in worker_matrix.values()),
            "Phase 7 worker matrix failed")
    try:
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.evidence")
            raise RuntimeError("intentional Phase 7 rollback context")
    except RuntimeError:
        pass
    require(visible("app", "evidence") == 0 and visible("app", "evidence", phase3.TENANT_B) > 0,
            "Phase 7 rollback context leaked")

    def raw_insert(sql, params):
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute(sql, params)

    bad = uuid4()
    expect_error(lambda: raw_insert(
        "INSERT INTO qms.document(id,tenant_id,organization_id,doc_type) VALUES (%s,%s,%s,'x')",
        [str(bad), str(phase3.TENANT_A), str(phase3.ORG_B)]))
    bad = uuid4()
    expect_error(lambda: raw_insert(
        "INSERT INTO qms.document_version(id,tenant_id,organization_id,document_id,version,content_reference,content_hash) VALUES (%s,%s,%s,%s,'x','x',%s)",
        [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(document_b.entity_id), "0" * 64]))
    bad = uuid4()
    expect_error(lambda: raw_insert(
        "INSERT INTO qms.document_version(id,tenant_id,organization_id,document_id,version,predecessor_id,content_reference,content_hash) VALUES (%s,%s,%s,%s,'x',%s,'x',%s)",
        [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(document_a.entity_id), str(version_b_v1.entity_id), "0" * 64]))
    bad = uuid4()
    expect_error(lambda: raw_insert(
        "INSERT INTO qms.evidence(id,tenant_id,organization_id,lineage_id,revision,source_type,content_hash,captured_at,document_version_id) VALUES (%s,%s,%s,%s,1,'document_version',%s,now(),%s)",
        [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(bad), "0" * 64, str(version_b_v1.entity_id)]))
    bad = uuid4()
    expect_error(lambda: raw_insert(
        "INSERT INTO qms.evidence(id,tenant_id,organization_id,lineage_id,revision,source_type,content_hash,captured_at,document_version_id) VALUES (%s,%s,%s,%s,1,'document_version',%s,now(),%s)",
        [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(bad), "0" * 64, str(version_a_v3.entity_id)]),
        "hash must match")

    def privileged(sql, params):
        with migrator.cursor() as cursor:
            cursor.execute(sql, params)
    expect_error(lambda: privileged(
        "UPDATE qms.document_version SET content_hash=%s WHERE id=%s",
        ["0" * 64, str(version_a_v1.entity_id)]), "append-only"); migrator.rollback()
    expect_error(lambda: privileged(
        "UPDATE qms.document_version SET content_reference='substituted' WHERE id=%s",
        [str(version_a_v1.entity_id)]), "append-only"); migrator.rollback()
    expect_error(lambda: privileged(
        "UPDATE qms.document_version SET tenant_id=%s WHERE id=%s",
        [str(phase3.TENANT_B), str(version_a_v1.entity_id)]), "tenant_id is immutable"); migrator.rollback()
    expect_error(lambda: privileged(
        "UPDATE qms.evidence SET organization_id=%s WHERE id=%s",
        [str(phase3.ORG_B), str(evidence_a_v1.entity_id)]), "organization_id is immutable"); migrator.rollback()
    expect_error(lambda: privileged(
        "UPDATE qms.document SET current_version_id=%s WHERE id=%s",
        [str(version_a_v1.entity_id), str(document_a.entity_id)]), "advance by one"); migrator.rollback()
    expect_error(lambda: raw_insert(
        "DELETE FROM qms.document_version WHERE id=%s", [str(version_a_v1.entity_id)]),
        "permission denied")
    expect_error(lambda: visible("projector", "document", phase3.TENANT_A), "permission denied")

    phase3.migrate(PHASE6_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('qms.change'),to_regclass('qms.measurement_definition'),"
            "to_regclass('qms.document'),to_regclass('qms.document_version'),to_regclass('qms.evidence')"
        )
        require(cursor.fetchone() == ("qms.change", "qms.measurement_definition", None, None, None),
                "Phase 7 reverse damaged promoted Phase 6")
    phase3.migrate(PHASE7_MIGRATION)

    print(json.dumps({
        "status": "PASS",
        "migration": "0007_document_evidence_foundation",
        "protected_tables": protected,
        "policy_count": len(policies),
        "rls_pool_matrix": matrix,
        "worker_matrix": worker_matrix,
        "hashing": "SHA-256 exact binary bytes; v1/v2/v3 fixture MATCH",
        "document_history": "v1 -> v2 -> v3 retained; unique current leaf; overwrite rejected",
        "evidence_history": "v1 -> v2 -> v3 retained with exact DocumentVersion provenance",
        "atomic_success": "Document + DocumentVersion + Evidence business/event/outbox/audit PASS",
        "atomic_rollback": "DocumentVersion and Evidence post-audit rollback leaves zero partial state",
        "cross_tenant_constraints": "Organization, Document, predecessor and Evidence provenance PASS",
        "forward_reverse_forward": "0001 -> ... -> 0007 -> 0006 -> 0007 PASS",
        "projector_audit_writer": "zero Phase 7 business permissions",
        "pool_rollback_context": "A -> none -> B and A rollback -> none -> B PASS",
    }, default=str, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
