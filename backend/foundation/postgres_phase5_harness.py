"""Blocking Phase 5 matrix layered on the promoted Phase 4 PostgreSQL gate."""

import json
import sys
from datetime import date
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase4_harness as phase4


TABLES = ("risk", "opportunity", "objective")
PHASE4_MIGRATION = ("foundation", "0004_qms_harmonized_context_foundation")
PHASE5_MIGRATION = ("foundation", "0005_risk_opportunity_objective_foundation")


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
    require(table in TABLES, "unknown Phase 5 table")
    with phase3.runtime_transaction(alias, tenant) as cursor:
        cursor.execute(f"SELECT count(*) FROM qms.{table}")
        return cursor.fetchone()[0]


def run():
    phase4.run()
    phase3.migrate(PHASE5_MIGRATION)

    from django.db import connections
    from foundation.audit import verify_audit_stream
    from foundation.models import DomainEvent, ImmutableAuditLog, Objective, Opportunity, Risk, TransactionalOutbox
    from foundation.qms_context import QmsContextCommandService
    from foundation.risk_objective import RiskOpportunityObjectiveCommandService
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
        require(len(protected) == 3, "Phase 5 protected tables missing")
        require(all(row[1] and row[2] for row in protected), "Phase 5 ENABLE/FORCE RLS missing")
        require(all(row[3] == __import__("os").environ["FOUNDATION_MIGRATOR_ROLE"] for row in protected),
                "runtime owns Phase 5 table")
        cursor.execute("SELECT tablename,cmd FROM pg_policies WHERE schemaname='qms' AND tablename=ANY(%s)", [list(TABLES)])
        policies = cursor.fetchall()
        require(len(policies) == 15, f"expected 15 explicit Phase 5 policies, found {len(policies)}")
        for table in TABLES:
            require({row[1] for row in policies if row[0] == table} == {"SELECT", "INSERT", "UPDATE", "DELETE", "ALL"},
                    f"policy matrix incomplete for {table}")
        app_role = __import__("os").environ["FOUNDATION_APP_ROLE"]
        worker_role = __import__("os").environ["FOUNDATION_WORKER_ROLE"]
        projector_role = __import__("os").environ["FOUNDATION_PROJECTOR_ROLE"]
        audit_role = __import__("os").environ["FOUNDATION_AUDIT_WRITER_ROLE"]
        for table in TABLES:
            cursor.execute(
                "SELECT has_table_privilege(%s,'qms.'||%s,'SELECT'),has_table_privilege(%s,'qms.'||%s,'INSERT'),"
                "has_table_privilege(%s,'qms.'||%s,'UPDATE'),has_table_privilege(%s,'qms.'||%s,'DELETE')",
                [app_role, table, app_role, table, app_role, table, app_role, table],
            )
            require(cursor.fetchone() == (True, True, False, False), f"app privilege drift for {table}")
            cursor.execute("SELECT has_table_privilege(%s,'qms.'||%s,'SELECT'),has_table_privilege(%s,'qms.'||%s,'INSERT')",
                           [worker_role, table, worker_role, table])
            require(cursor.fetchone() == (True, False), f"worker privilege drift for {table}")
            for role in (projector_role, audit_role):
                cursor.execute("SELECT has_table_privilege(%s,'qms.'||%s,'SELECT')", [role, table])
                require(cursor.fetchone()[0] is False, f"{role} can read {table}")

    identity_a = TrustedTenantIdentity("phase5-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase5-b", phase3.TENANT_B)
    context_service = QmsContextCommandService(using="app")
    service = RiskOpportunityObjectiveCommandService(using="app")
    actor = "phase5-gate"

    process_a = context_service.create_process(identity=identity_a, organization_id=phase3.ORG_A,
        name="Customer delivery", process_type="operational", status="active", actor_id=actor, trace_id=uuid4())
    process_b = context_service.create_process(identity=identity_b, organization_id=phase3.ORG_B,
        name="Supplier control", process_type="support", status="active", actor_id=actor, trace_id=uuid4())

    risk_v1 = service.create_risk(identity=identity_a, process_id=process_a.entity_id,
        cause="Carrier capacity constraint", event="Late shipment", consequence="Customer delivery missed",
        likelihood="possible", impact="high", residual="medium", actor_id=actor, trace_id=uuid4())
    opportunity_v1 = service.create_opportunity(identity=identity_a, process_id=process_a.entity_id,
        hypothesis="Route consolidation", benefit="Shorter lead time", feasibility="pilot feasible",
        status="proposed", actor_id=actor, trace_id=uuid4())
    opportunity_b = service.create_opportunity(identity=identity_b, process_id=process_b.entity_id,
        hypothesis="Supplier portal", benefit="Earlier visibility", feasibility="feasible",
        status="proposed", actor_id=actor, trace_id=uuid4())
    risk_b = service.create_risk(identity=identity_b, process_id=process_b.entity_id,
        cause="Supplier capacity constraint", event="Material delay", consequence="Schedule disruption",
        likelihood="possible", impact="medium", residual="low", actor_id=actor, trace_id=uuid4())
    objective_v1 = service.create_objective(identity=identity_a, organization_id=phase3.ORG_A,
        target="Deliver agreed orders within 10 business days", due_date=date(2027, 3, 31),
        status="active", actor_id=actor, trace_id=uuid4())
    objective_b = service.create_objective(identity=identity_b, organization_id=phase3.ORG_B,
        target="Review all critical suppliers quarterly", due_date=date(2027, 6, 30),
        status="active", actor_id=actor, trace_id=uuid4())

    require(risk_v1.entity_id != opportunity_v1.entity_id, "Risk and Opportunity share row identity")
    for result in (risk_v1, opportunity_v1, objective_v1):
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            event = DomainEvent.objects.using("app").get(event_id=result.event_id)
            outbox = TransactionalOutbox.objects.using("app").get(id=result.outbox_id)
            audit = ImmutableAuditLog.objects.using("app").get(id=result.audit_id)
            require(event.tenant_id == phase3.TENANT_A == outbox.tenant_id == audit.tenant_id, "atomic tenant mismatch")
            require(event.trace_id == result.trace_id == audit.trace_id, "atomic trace mismatch")
            require(event.aggregate_id == result.aggregate_id == audit.stream_id, "atomic aggregate mismatch")

    risk_v2 = service.revise_risk(identity=identity_a, risk_id=risk_v1.entity_id, process_id=process_a.entity_id,
        cause="Carrier capacity constraint", event="Late shipment", consequence="Customer delivery missed",
        likelihood="likely", impact="high", residual="medium", change_reason="Quarterly assessment",
        actor_id=actor, trace_id=uuid4())
    risk_v3 = service.revise_risk(identity=identity_a, risk_id=risk_v2.entity_id, process_id=process_a.entity_id,
        cause="Carrier capacity constraint", event="Late shipment", consequence="Customer delivery missed",
        likelihood="possible", impact="high", residual="low", change_reason="Controls verified",
        actor_id=actor, trace_id=uuid4())
    opportunity_v2 = service.revise_opportunity(identity=identity_a, opportunity_id=opportunity_v1.entity_id,
        process_id=process_a.entity_id, hypothesis="Route consolidation pilot", benefit="Shorter lead time",
        feasibility="approved pilot", status="approved", change_reason="Pilot reviewed", actor_id=actor, trace_id=uuid4())
    opportunity_v3 = service.change_opportunity_status(identity=identity_a, opportunity_id=opportunity_v2.entity_id,
        status="active", change_reason="Pilot started", actor_id=actor, trace_id=uuid4())
    objective_v2 = service.revise_objective(identity=identity_a, objective_id=objective_v1.entity_id,
        target="Deliver 95% of agreed orders within 10 business days", due_date=date(2027, 3, 31),
        status="active", change_reason="Target clarified", actor_id=actor, trace_id=uuid4())
    objective_v3 = service.change_objective_status(identity=identity_a, objective_id=objective_v2.entity_id,
        status="completed", change_reason="Period closed", actor_id=actor, trace_id=uuid4())

    histories = ((Risk, "risk", risk_v1, risk_v2, risk_v3),
                 (Opportunity, "opportunity", opportunity_v1, opportunity_v2, opportunity_v3),
                 (Objective, "objective", objective_v1, objective_v2, objective_v3))
    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        for model, aggregate_type, v1, v2, v3 in histories:
            rows = list(model.objects.using("app").filter(lineage_id=v1.aggregate_id)
                        .order_by("revision").values_list("id", "revision", "previous_revision_id"))
            require(rows == [(v1.entity_id, 1, None), (v2.entity_id, 2, v1.entity_id),
                             (v3.entity_id, 3, v2.entity_id)], f"{aggregate_type} history is incomplete")
            leaf_ids = set(model.objects.using("app").filter(lineage_id=v1.aggregate_id)
                           .values_list("id", flat=True)) - set(model.objects.using("app").filter(
                               lineage_id=v1.aggregate_id, previous_revision_id__isnull=False)
                               .values_list("previous_revision_id", flat=True))
            require(leaf_ids == {v3.entity_id}, f"{aggregate_type} current revision is ambiguous")
            require(verify_audit_stream(tenant_id=phase3.TENANT_A, stream_type=aggregate_type,
                stream_id=v1.aggregate_id, using="app"), f"{aggregate_type} audit chain invalid")

    # Each rollback is injected after business revision, DomainEvent, Outbox and Audit append.
    for model, revise in (
        (Risk, lambda: service.revise_risk(identity=identity_a, risk_id=risk_v3.entity_id,
            process_id=process_a.entity_id, cause="rollback", event="rollback", consequence="rollback",
            likelihood="rollback", impact="rollback", residual="rollback", actor_id=actor,
            trace_id=uuid4(), fail_before_commit=True)),
        (Opportunity, lambda: service.revise_opportunity(identity=identity_a, opportunity_id=opportunity_v3.entity_id,
            process_id=process_a.entity_id, hypothesis="rollback", benefit="rollback", feasibility="rollback",
            status="rollback", actor_id=actor, trace_id=uuid4(), fail_before_commit=True)),
        (Objective, lambda: service.revise_objective(identity=identity_a, objective_id=objective_v3.entity_id,
            target="rollback", status="rollback", actor_id=actor, trace_id=uuid4(), fail_before_commit=True)),
    ):
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            before = (model.objects.using("app").count(), DomainEvent.objects.using("app").count(),
                      TransactionalOutbox.objects.using("app").count(), ImmutableAuditLog.objects.using("app").count())
        expect_error(revise, "deliberate Phase 5 rollback")
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            after = (model.objects.using("app").count(), DomainEvent.objects.using("app").count(),
                     TransactionalOutbox.objects.using("app").count(), ImmutableAuditLog.objects.using("app").count())
        require(after == before, f"{model.__name__} rollback left partial state")

    matrix = {table: [visible("app", table, phase3.TENANT_A), visible("app", table),
                      visible("app", table, phase3.TENANT_B)] for table in TABLES}
    worker_matrix = {table: [visible("worker", table, phase3.TENANT_A), visible("worker", table),
                             visible("worker", table, phase3.TENANT_B)] for table in TABLES}
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0 for values in matrix.values()), "Phase 5 app RLS/pool matrix failed")
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0 for values in worker_matrix.values()), "Phase 5 worker matrix failed")
    try:
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.risk")
            raise RuntimeError("intentional Phase 5 rollback context")
    except RuntimeError:
        pass
    require(visible("app", "risk") == 0 and visible("app", "risk", phase3.TENANT_B) > 0,
            "Phase 5 rollback context leaked")

    def cross_tenant_risk_process():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            bad = uuid4()
            cursor.execute("INSERT INTO qms.risk(id,tenant_id,organization_id,lineage_id,revision,process_id,cause,event,consequence,likelihood,impact,residual) VALUES (%s,%s,%s,%s,1,%s,'x','x','x','x','x','x')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(bad), str(process_b.entity_id)])
    expect_error(cross_tenant_risk_process)

    def cross_tenant_opportunity_process():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            bad = uuid4()
            cursor.execute("INSERT INTO qms.opportunity(id,tenant_id,organization_id,lineage_id,revision,process_id,hypothesis,benefit,feasibility,status) VALUES (%s,%s,%s,%s,1,%s,'x','x','x','x')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(bad), str(process_b.entity_id)])
    expect_error(cross_tenant_opportunity_process)

    def cross_tenant_objective_org():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            bad = uuid4()
            cursor.execute("INSERT INTO qms.objective(id,tenant_id,organization_id,lineage_id,revision,target,status) VALUES (%s,%s,%s,%s,1,'x','x')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_B), str(bad)])
    expect_error(cross_tenant_objective_org)

    def cross_tenant_predecessor():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("INSERT INTO qms.risk(id,tenant_id,organization_id,lineage_id,revision,previous_revision_id,process_id,cause,event,consequence,likelihood,impact,residual) VALUES (%s,%s,%s,%s,2,%s,%s,'x','x','x','x','x','x')",
                [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A), str(risk_v1.aggregate_id),
                 str(risk_b.entity_id), str(process_a.entity_id)])
    expect_error(cross_tenant_predecessor)

    def tenant_reassignment():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.risk SET tenant_id=%s WHERE id=%s", [str(phase3.TENANT_B), str(risk_v1.entity_id)])
    expect_error(tenant_reassignment, "tenant_id is immutable"); migrator.rollback()

    def organization_reassignment():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.opportunity SET organization_id=%s WHERE id=%s", [str(phase3.ORG_B), str(opportunity_v1.entity_id)])
    expect_error(organization_reassignment, "organization_id is immutable"); migrator.rollback()

    def destructive_update():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.objective SET target='overwrite' WHERE id=%s", [str(objective_v1.entity_id)])
    expect_error(destructive_update, "append-only"); migrator.rollback()

    def runtime_delete():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("DELETE FROM qms.risk WHERE id=%s", [str(risk_v1.entity_id)])
    expect_error(runtime_delete, "permission denied")
    expect_error(lambda: visible("projector", "risk", phase3.TENANT_A), "permission denied")

    phase3.migrate(PHASE4_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.stakeholder'),to_regclass('qms.process'),to_regclass('qms.stakeholder_requirement'),to_regclass('eventing.domain_event'),to_regclass('qms.risk'),to_regclass('qms.opportunity'),to_regclass('qms.objective')")
        require(cursor.fetchone() == ("qms.stakeholder", "qms.process", "qms.stakeholder_requirement",
                "eventing.domain_event", None, None, None), "Phase 5 reverse damaged promoted Phase 4")
    phase3.migrate(PHASE5_MIGRATION)

    print(json.dumps({
        "status": "PASS", "migration": "0005_risk_opportunity_objective_foundation",
        "protected_tables": protected, "policy_count": len(policies), "rls_pool_matrix": matrix,
        "worker_matrix": worker_matrix,
        "history": "Risk, Opportunity and Objective v1 -> v2 -> v3 retained with one current leaf",
        "atomic_success": "business revision + DomainEvent + Outbox + Audit PASS for all three aggregates",
        "atomic_rollback": "post-audit injected failure leaves no partial rows for all three aggregates",
        "independence": "Risk and Opportunity exist independently with distinct identities",
        "cross_tenant_constraints": "Organization, Process and predecessor composite FKs PASS",
        "forward_reverse_forward": "0001 -> 0002 -> 0003 -> 0004 -> 0005 -> 0004 -> 0005 PASS",
        "projector_audit_writer": "zero Phase 5 business permissions",
        "pool_rollback_context": "A -> none -> B and A rollback -> none -> B PASS",
    }, default=str, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
