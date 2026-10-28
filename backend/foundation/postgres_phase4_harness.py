"""Blocking Phase 4 matrix layered on the promoted Phase 3 PostgreSQL gate."""

import json
import sys
from uuid import uuid4

import postgres_foundation_harness as phase3


TABLES = (
    "stakeholder", "process", "stakeholder_requirement",
    "context_item", "qms_scope", "qms_scope_process",
)
PHASE4_MIGRATION = ("foundation", "0004_qms_harmonized_context_foundation")
PHASE3_MIGRATION = ("foundation", "0003_eventing_immutable_audit_foundation")


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
    require(table in TABLES, "unknown Phase 4 table")
    with phase3.runtime_transaction(alias, tenant) as cursor:
        cursor.execute(f"SELECT count(*) FROM qms.{table}")
        return cursor.fetchone()[0]


def run():
    # Re-run every promoted Phase 1-3 catalog, principal, RLS, raw SQL, pool,
    # rollback, event/outbox/inbox and audit assertion first.
    phase3.run()
    phase3.migrate(PHASE4_MIGRATION)

    from django.db import connections
    from foundation.audit import verify_audit_stream
    from foundation.models import ContextItem, DomainEvent, ImmutableAuditLog, Process, QmsScope, StakeholderRequirement, TransactionalOutbox
    from foundation.qms_context import QmsContextCommandService
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    migrator = connections["default"]
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,r.rolname "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='qms' AND c.relname=ANY(%s) ORDER BY c.relname",
            [list(TABLES)],
        )
        protected = cursor.fetchall()
        require(len(protected) == 6, "Phase 4 protected tables missing")
        require(all(row[1] and row[2] for row in protected), "Phase 4 ENABLE/FORCE RLS missing")
        require(all(row[3] == __import__("os").environ["FOUNDATION_MIGRATOR_ROLE"] for row in protected), "runtime owns Phase 4 table")
        cursor.execute("SELECT tablename,cmd FROM pg_policies WHERE schemaname='qms' AND tablename=ANY(%s)", [list(TABLES)])
        policies = cursor.fetchall()
        require(len(policies) == 30, f"expected 30 explicit Phase 4 policies, found {len(policies)}")
        for table in TABLES:
            require({row[1] for row in policies if row[0] == table} == {"SELECT", "INSERT", "UPDATE", "DELETE", "ALL"}, f"policy matrix incomplete for {table}")

    identity_a = TrustedTenantIdentity("phase4-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase4-b", phase3.TENANT_B)
    service = QmsContextCommandService(using="app")
    actor = "phase4-gate"

    # Atomic success for each aggregate foundation.
    stakeholder_a = service.create_stakeholder(identity=identity_a, organization_id=phase3.ORG_A,
        stakeholder_type="customer", name="Customer A", relevance_score=0.9000, actor_id=actor, trace_id=uuid4())
    stakeholder_b = service.create_stakeholder(identity=identity_b, organization_id=phase3.ORG_B,
        stakeholder_type="supplier", name="Supplier B", relevance_score=0.8000, actor_id=actor, trace_id=uuid4())
    process_a = service.create_process(identity=identity_a, organization_id=phase3.ORG_A,
        name="Order fulfilment", process_type="operational", status="active", actor_id=actor, trace_id=uuid4())
    process_b = service.create_process(identity=identity_b, organization_id=phase3.ORG_B,
        name="Supplier management", process_type="support", status="active", actor_id=actor, trace_id=uuid4())
    requirement_v1 = service.create_stakeholder_requirement(identity=identity_a,
        stakeholder_id=stakeholder_a.entity_id, requirement_text="Delivery within agreed lead time",
        qms_addressed=False, owner_process_id=process_a.entity_id, actor_id=actor, trace_id=uuid4())
    requirement_b = service.create_stakeholder_requirement(identity=identity_b,
        stakeholder_id=stakeholder_b.entity_id, requirement_text="Approved supplier status",
        qms_addressed=True, owner_process_id=process_b.entity_id, actor_id=actor, trace_id=uuid4())
    context_v1 = service.create_context_item(identity=identity_a, organization_id=phase3.ORG_A,
        issue_type="external", description="Supply lead times are increasing", actor_id=actor, trace_id=uuid4())
    context_b = service.create_context_item(identity=identity_b, organization_id=phase3.ORG_B,
        issue_type="internal", description="Training capacity is constrained", actor_id=actor, trace_id=uuid4())
    scope_v1 = service.create_scope(identity=identity_a, organization_id=phase3.ORG_A,
        boundaries="Costa Rica operations", applicability="All QMS activities",
        products_services="Distribution service", process_ids=(process_a.entity_id,), actor_id=actor, trace_id=uuid4())
    scope_b = service.create_scope(identity=identity_b, organization_id=phase3.ORG_B,
        boundaries="Plant B", applicability="Manufacturing operations", products_services="Components",
        process_ids=(process_b.entity_id,), actor_id=actor, trace_id=uuid4())

    success_results = (stakeholder_a, process_a, requirement_v1, context_v1, scope_v1)
    for result in success_results:
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            event = DomainEvent.objects.using("app").get(event_id=result.event_id)
            outbox = TransactionalOutbox.objects.using("app").get(id=result.outbox_id)
            audit = ImmutableAuditLog.objects.using("app").get(id=result.audit_id)
            require(event.tenant_id == phase3.TENANT_A == outbox.tenant_id == audit.tenant_id, "atomic tenant mismatch")
            require(event.trace_id == result.trace_id == audit.trace_id, "atomic trace mismatch")
            require(event.aggregate_id == result.aggregate_id == audit.stream_id, "atomic aggregate mismatch")

    # Requirement v1 -> v2 -> v3, with retained immutable lineage and valid audit chain.
    requirement_v2 = service.supersede_stakeholder_requirement(identity=identity_a,
        requirement_id=requirement_v1.entity_id, requirement_text="Delivery within 10 business days",
        qms_addressed=True, change_reason="Contract clarified", actor_id=actor, trace_id=uuid4())
    requirement_v3 = service.supersede_stakeholder_requirement(identity=identity_a,
        requirement_id=requirement_v2.entity_id, requirement_text="Delivery within 8 business days",
        qms_addressed=True, change_reason="Service level revised", actor_id=actor, trace_id=uuid4())
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        requirement_rows = list(StakeholderRequirement.objects.using("app").filter(
            lineage_id=requirement_v1.aggregate_id).order_by("revision").values_list("id", "revision", "previous_revision_id"))
        require(requirement_rows == [
            (requirement_v1.entity_id, 1, None),
            (requirement_v2.entity_id, 2, requirement_v1.entity_id),
            (requirement_v3.entity_id, 3, requirement_v2.entity_id),
        ], "requirement history is incomplete")
        require(verify_audit_stream(tenant_id=phase3.TENANT_A, stream_type="stakeholder_requirement",
            stream_id=requirement_v1.aggregate_id, using="app"), "requirement audit chain invalid")
        require(DomainEvent.objects.using("app").filter(aggregate_type="stakeholder_requirement",
            aggregate_id=requirement_v1.aggregate_id).count() == 3, "requirement events missing")

    # Context and scope historical reconstruction, including structural process scope.
    context_v2 = service.supersede_context_item(identity=identity_a, context_item_id=context_v1.entity_id,
        issue_type="external", description="Supply lead times stabilized but remain elevated",
        change_reason="Quarterly review", actor_id=actor, trace_id=uuid4())
    scope_v2 = service.revise_scope(identity=identity_a, scope_id=scope_v1.entity_id,
        boundaries="Costa Rica operations and remote service", applicability="All QMS activities",
        products_services="Distribution and support services", process_ids=(process_a.entity_id,),
        change_reason="Remote service added", actor_id=actor, trace_id=uuid4())
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        require(list(ContextItem.objects.using("app").filter(lineage_id=context_v1.aggregate_id)
            .order_by("revision").values_list("revision", flat=True)) == [1, 2], "context history missing")
        require(list(QmsScope.objects.using("app").filter(lineage_id=scope_v1.aggregate_id)
            .order_by("revision").values_list("revision", flat=True)) == [1, 2], "scope history missing")
        require(QmsScope.objects.using("app").get(pk=scope_v1.entity_id).boundaries == "Costa Rica operations", "scope v1 overwritten")

    # Atomic rollback after business/event/outbox/audit for the mandatory operations.
    before_counts = {}
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        for name, model in (("requirements", StakeholderRequirement), ("events", DomainEvent),
                            ("outbox", TransactionalOutbox), ("audit", ImmutableAuditLog)):
            before_counts[name] = model.objects.using("app").count()
    expect_error(lambda: service.supersede_stakeholder_requirement(identity=identity_a,
        requirement_id=requirement_v3.entity_id, requirement_text="Must rollback", actor_id=actor,
        trace_id=uuid4(), fail_before_commit=True), "deliberate Phase 4 rollback")
    old_process_name = "Order fulfilment"
    expect_error(lambda: service.update_process(identity=identity_a, process_id=process_a.entity_id,
        name="Must rollback", actor_id=actor, trace_id=uuid4(), fail_before_commit=True), "deliberate Phase 4 rollback")
    expect_error(lambda: service.supersede_context_item(identity=identity_a, context_item_id=context_v2.entity_id,
        issue_type="external", description="Must rollback", actor_id=actor, trace_id=uuid4(),
        fail_before_commit=True), "deliberate Phase 4 rollback")
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        after_counts = {
            "requirements": StakeholderRequirement.objects.using("app").count(),
            "events": DomainEvent.objects.using("app").count(),
            "outbox": TransactionalOutbox.objects.using("app").count(),
            "audit": ImmutableAuditLog.objects.using("app").count(),
        }
        require(after_counts == before_counts, "rollback left Phase 4 rows/events/outbox/audit")
        require(Process.objects.using("app").get(pk=process_a.entity_id).name == old_process_name, "process rollback failed")

    # Raw SQL RLS, worker and connection reuse A -> none -> B.
    matrix = {table: [visible("app", table, phase3.TENANT_A), visible("app", table), visible("app", table, phase3.TENANT_B)] for table in TABLES}
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0 for values in matrix.values()), "Phase 4 app RLS/pool matrix failed")
    worker_matrix = {table: [visible("worker", table, phase3.TENANT_A), visible("worker", table), visible("worker", table, phase3.TENANT_B)] for table in TABLES}
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0 for values in worker_matrix.values()), "Phase 4 worker matrix failed")
    try:
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.stakeholder")
            raise RuntimeError("intentional Phase 4 rollback context")
    except RuntimeError:
        pass
    require(visible("app", "stakeholder") == 0 and visible("app", "stakeholder", phase3.TENANT_B) > 0,
            "Phase 4 rollback context leaked")

    # DB-level graph rejection independent from application filtering.
    def cross_org_stakeholder():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("INSERT INTO qms.stakeholder(id,tenant_id,organization_id,stakeholder_type,name) VALUES (%s,%s,%s,'customer','invalid')",
                [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_B)])
    expect_error(cross_org_stakeholder)

    def cross_org_process():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("INSERT INTO qms.process(id,tenant_id,organization_id,name,status) VALUES (%s,%s,%s,'invalid','active')",
                [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_B)])
    expect_error(cross_org_process)

    def cross_tenant_requirement_stakeholder():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            bad = uuid4()
            cursor.execute("INSERT INTO qms.stakeholder_requirement(id,tenant_id,organization_id,stakeholder_id,lineage_id,revision,requirement_text) VALUES (%s,%s,%s,%s,%s,1,'invalid')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(stakeholder_b.entity_id), str(bad)])
    expect_error(cross_tenant_requirement_stakeholder)

    def cross_tenant_requirement_predecessor():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("INSERT INTO qms.stakeholder_requirement(id,tenant_id,organization_id,stakeholder_id,lineage_id,revision,previous_revision_id,requirement_text) VALUES (%s,%s,%s,%s,%s,2,%s,'invalid')",
                [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(stakeholder_a.entity_id),
                 str(requirement_v1.aggregate_id), str(requirement_b.entity_id)])
    expect_error(cross_tenant_requirement_predecessor)

    def cross_tenant_context_predecessor():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("INSERT INTO qms.context_item(id,tenant_id,organization_id,lineage_id,revision,previous_revision_id,issue_type,description) VALUES (%s,%s,%s,%s,3,%s,'external','invalid')",
                [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(context_v1.aggregate_id), str(context_b.entity_id)])
    expect_error(cross_tenant_context_predecessor)

    def cross_tenant_scope_organization():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            bad = uuid4()
            cursor.execute("INSERT INTO qms.qms_scope(id,tenant_id,organization_id,lineage_id,revision,boundaries,applicability,products_services) VALUES (%s,%s,%s,%s,1,'invalid','invalid','invalid')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_B), str(bad)])
    expect_error(cross_tenant_scope_organization)

    def cross_tenant_scope_process():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("INSERT INTO qms.qms_scope_process(id,tenant_id,organization_id,scope_revision_id,process_id) VALUES (%s,%s,%s,%s,%s)",
                [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(scope_v2.entity_id), str(process_b.entity_id)])
    expect_error(cross_tenant_scope_process)

    def tenant_reassignment():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.stakeholder SET tenant_id=%s WHERE id=%s", [str(phase3.TENANT_B), str(stakeholder_a.entity_id)])
    expect_error(tenant_reassignment, "tenant_id is immutable"); migrator.rollback()

    def organization_reassignment():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.process SET organization_id=%s WHERE id=%s", [str(phase3.ORG_B), str(process_a.entity_id)])
    expect_error(organization_reassignment, "organization_id is immutable"); migrator.rollback()

    def destructive_requirement_update():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.stakeholder_requirement SET requirement_text='overwrite' WHERE id=%s", [str(requirement_v1.entity_id)])
    expect_error(destructive_requirement_update, "append-only"); migrator.rollback()

    def runtime_delete_permanent_object():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("DELETE FROM qms.stakeholder WHERE id=%s", [str(stakeholder_a.entity_id)])
    expect_error(runtime_delete_permanent_object, "permission denied")

    def self_supersession():
        with migrator.cursor() as cursor:
            bad = uuid4()
            cursor.execute("INSERT INTO qms.context_item(id,tenant_id,organization_id,lineage_id,revision,previous_revision_id,issue_type,description) VALUES (%s,%s,%s,%s,2,%s,'internal','invalid')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(bad), str(bad)])
    expect_error(self_supersession); migrator.rollback()

    # Projector remains unable to read or mutate the business domain.
    expect_error(lambda: visible("projector", "stakeholder", phase3.TENANT_A), "permission denied")

    # Reverse removes only Phase 4; 0001-0003 remain, then forward succeeds again.
    phase3.migrate(PHASE3_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.tenant_projection'),to_regclass('qms.organization'),to_regclass('eventing.domain_event'),to_regclass('audit.immutable_audit_log'),to_regclass('qms.stakeholder')")
        require(cursor.fetchone() == ("qms.tenant_projection", "qms.organization", "eventing.domain_event", "audit.immutable_audit_log", None),
                "Phase 4 reverse damaged promoted foundation")
    phase3.migrate(PHASE4_MIGRATION)

    print(json.dumps({
        "status": "PASS", "migration": "0004_qms_harmonized_context_foundation",
        "protected_tables": protected, "policy_count": len(policies), "rls_pool_matrix": matrix,
        "worker_matrix": worker_matrix,
        "atomic_success": "Stakeholder, Requirement, Process, Context and Scope business/event/outbox/audit PASS",
        "atomic_rollback": "Requirement supersession, Process update and Context supersession leave no partial state",
        "requirement_history": "v1 -> v2 -> v3 retained; lineage/events/audit chain PASS",
        "context_history": "v1 -> v2 retained", "scope_history": "v1 -> v2 retained with Process links",
        "cross_tenant_constraints": "Organization, stakeholder, predecessor, process and scope graph composite FKs/guards PASS",
        "forward_reverse_forward": "0001 -> 0002 -> 0003 -> 0004 -> 0003 -> 0004 PASS",
        "projector": "zero Phase 4 business permissions", "rollback_context": "A rollback -> none -> B PASS",
    }, default=str, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
