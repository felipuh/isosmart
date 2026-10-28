"""Blocking Phase 6 matrix layered on the promoted Phase 5 PostgreSQL gate."""

import json
import sys
from datetime import date
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase4_harness as phase4


TABLES = ("change", "change_process", "measurement_definition")
PHASE5_MIGRATION = ("foundation", "0005_risk_opportunity_objective_foundation")
PHASE6_MIGRATION = ("foundation", "0006_change_performance_measurement_foundation")


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
    require(table in TABLES, "unknown Phase 6 table")
    with phase3.runtime_transaction(alias, tenant) as cursor:
        cursor.execute(f"SELECT count(*) FROM qms.{table}")
        return cursor.fetchone()[0]


def run():
    phase4.run()
    phase3.migrate(PHASE5_MIGRATION)
    phase3.migrate(PHASE6_MIGRATION)

    from django.db import connections
    from foundation.audit import verify_audit_stream
    from foundation.change_performance import ChangePerformanceCommandService
    from foundation.models import (
        Change, ChangeProcess, DomainEvent, ImmutableAuditLog, MeasurementDefinition,
        Objective, TransactionalOutbox,
    )
    from foundation.qms_context import QmsContextCommandService
    from foundation.risk_objective import RiskOpportunityObjectiveCommandService
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
        require(len(protected) == 3, "Phase 6 protected tables missing")
        require(all(row[1] and row[2] for row in protected), "Phase 6 ENABLE/FORCE RLS missing")
        require(all(row[3] == __import__("os").environ["FOUNDATION_MIGRATOR_ROLE"] for row in protected),
                "runtime owns Phase 6 table")
        cursor.execute("SELECT tablename,cmd FROM pg_policies WHERE schemaname='qms' AND tablename=ANY(%s)", [list(TABLES)])
        policies = cursor.fetchall()
        require(len(policies) == 15, f"expected 15 explicit Phase 6 policies, found {len(policies)}")
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

    identity_a = TrustedTenantIdentity("phase6-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase6-b", phase3.TENANT_B)
    context_service = QmsContextCommandService(using="app")
    service = ChangePerformanceCommandService(using="app")
    objective_service = RiskOpportunityObjectiveCommandService(using="app")
    actor = "phase6-gate"

    process_a = context_service.create_process(
        identity=identity_a, organization_id=phase3.ORG_A, name="Phase 6 A process",
        process_type="operational", status="active", actor_id=actor, trace_id=uuid4(),
    )
    process_b = context_service.create_process(
        identity=identity_b, organization_id=phase3.ORG_B, name="Phase 6 B process",
        process_type="operational", status="active", actor_id=actor, trace_id=uuid4(),
    )
    metric_a_v1 = service.define_measurement(
        identity=identity_a, organization_id=phase3.ORG_A, process_id=process_a.entity_id,
        what_is_measured="On-time delivery", method="Delivered on time divided by delivered orders",
        measurement_timing="Monthly", actor_id=actor, trace_id=uuid4(),
    )
    metric_b = service.define_measurement(
        identity=identity_b, organization_id=phase3.ORG_B, process_id=process_b.entity_id,
        what_is_measured="Supplier review completion", method="Completed reviews divided by planned reviews",
        measurement_timing="Quarterly", actor_id=actor, trace_id=uuid4(),
    )
    change_a_v1 = service.create_change(
        identity=identity_a, organization_id=phase3.ORG_A, change_type="process",
        purpose="Improve delivery reliability", impact="Updates dispatch sequencing",
        status="requested", process_ids=[process_a.entity_id], actor_id=actor, trace_id=uuid4(),
    )
    change_b = service.create_change(
        identity=identity_b, organization_id=phase3.ORG_B, change_type="process",
        purpose="Improve supplier review", impact="Updates review cadence",
        status="requested", process_ids=[process_b.entity_id], actor_id=actor, trace_id=uuid4(),
    )
    objective_a = objective_service.create_objective(
        identity=identity_a, organization_id=phase3.ORG_A, metric_id=metric_a_v1.entity_id,
        target="At least 95 percent on time", due_date=date(2027, 12, 31), status="active",
        actor_id=actor, trace_id=uuid4(),
    )

    for result in (metric_a_v1, change_a_v1, objective_a):
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            event = DomainEvent.objects.using("app").get(event_id=result.event_id)
            outbox = TransactionalOutbox.objects.using("app").get(id=result.outbox_id)
            audit = ImmutableAuditLog.objects.using("app").get(id=result.audit_id)
            require(event.tenant_id == phase3.TENANT_A == outbox.tenant_id == audit.tenant_id, "atomic tenant mismatch")
            require(event.trace_id == result.trace_id == audit.trace_id, "atomic trace mismatch")
            require(event.aggregate_id == result.aggregate_id == audit.stream_id, "atomic aggregate mismatch")

    change_a_v2 = service.revise_change(
        identity=identity_a, change_id=change_a_v1.entity_id, change_type="process",
        purpose="Improve delivery reliability", impact="Updates dispatch and carrier handoff",
        status="planned", process_ids=[process_a.entity_id], change_reason="Impact clarified",
        actor_id=actor, trace_id=uuid4(),
    )
    change_a_v3 = service.change_change_status(
        identity=identity_a, change_id=change_a_v2.entity_id, status="implemented",
        change_reason="Implementation recorded", actor_id=actor, trace_id=uuid4(),
    )
    metric_a_v2 = service.revise_measurement_definition(
        identity=identity_a, measurement_definition_id=metric_a_v1.entity_id,
        process_id=process_a.entity_id, what_is_measured="On-time delivery",
        method="Orders delivered by promised date divided by delivered orders",
        measurement_timing="Monthly at period close", change_reason="Method clarified",
        actor_id=actor, trace_id=uuid4(),
    )

    with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
        rows = list(Change.objects.using("app").filter(lineage_id=change_a_v1.aggregate_id)
                    .order_by("revision").values_list("id", "revision", "previous_revision_id", "status"))
        require(rows == [
            (change_a_v1.entity_id, 1, None, "requested"),
            (change_a_v2.entity_id, 2, change_a_v1.entity_id, "planned"),
            (change_a_v3.entity_id, 3, change_a_v2.entity_id, "implemented"),
        ], "Change v1 -> v2 -> v3 history is incomplete")
        require(ChangeProcess.objects.using("app").filter(
            change_revision_id__in=[change_a_v1.entity_id, change_a_v2.entity_id, change_a_v3.entity_id],
            process_id=process_a.entity_id).count() == 3, "Change Process snapshots were not retained")
        require(verify_audit_stream(tenant_id=phase3.TENANT_A, stream_type="change",
            stream_id=change_a_v1.aggregate_id, using="app"), "Change audit chain invalid")
        require(DomainEvent.objects.using("app").filter(
            aggregate_type="change", aggregate_id=change_a_v1.aggregate_id).count() == 3,
            "Change event history invalid")
        metrics = list(MeasurementDefinition.objects.using("app").filter(
            lineage_id=metric_a_v1.aggregate_id).order_by("revision")
            .values_list("id", "revision", "previous_revision_id"))
        require(metrics == [(metric_a_v1.entity_id, 1, None),
                            (metric_a_v2.entity_id, 2, metric_a_v1.entity_id)],
                "MeasurementDefinition history incomplete")
        require(Objective.objects.using("app").get(id=objective_a.entity_id).metric_id == metric_a_v1.entity_id,
                "Objective.metric_id did not retain its frozen definition revision")
        require(verify_audit_stream(tenant_id=phase3.TENANT_A, stream_type="measurement_definition",
            stream_id=metric_a_v1.aggregate_id, using="app"), "MeasurementDefinition audit chain invalid")

    for model, operation in (
        (Change, lambda: service.revise_change(
            identity=identity_a, change_id=change_a_v3.entity_id, change_type="process",
            purpose="rollback", impact="rollback", status="rollback", actor_id=actor,
            trace_id=uuid4(), process_ids=[process_a.entity_id], fail_before_commit=True)),
        (MeasurementDefinition, lambda: service.revise_measurement_definition(
            identity=identity_a, measurement_definition_id=metric_a_v2.entity_id,
            process_id=process_a.entity_id, what_is_measured="rollback", method="rollback",
            measurement_timing="rollback", actor_id=actor, trace_id=uuid4(),
            fail_before_commit=True)),
    ):
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            before = (model.objects.using("app").count(), DomainEvent.objects.using("app").count(),
                      TransactionalOutbox.objects.using("app").count(), ImmutableAuditLog.objects.using("app").count())
        expect_error(operation, "deliberate Phase 6 rollback")
        with trusted_tenant_context(identity_a, actor_id=actor, trace_id=uuid4(), using="app"):
            after = (model.objects.using("app").count(), DomainEvent.objects.using("app").count(),
                     TransactionalOutbox.objects.using("app").count(), ImmutableAuditLog.objects.using("app").count())
        require(after == before, f"{model.__name__} rollback left partial state")

    matrix = {table: [visible("app", table, phase3.TENANT_A), visible("app", table),
                      visible("app", table, phase3.TENANT_B)] for table in TABLES}
    worker_matrix = {table: [visible("worker", table, phase3.TENANT_A), visible("worker", table),
                             visible("worker", table, phase3.TENANT_B)] for table in TABLES}
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0 for values in matrix.values()),
            "Phase 6 app RLS/pool matrix failed")
    require(all(values[0] > 0 and values[1] == 0 and values[2] > 0 for values in worker_matrix.values()),
            "Phase 6 worker matrix failed")
    try:
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.change")
            raise RuntimeError("intentional Phase 6 rollback context")
    except RuntimeError:
        pass
    require(visible("app", "change") == 0 and visible("app", "change", phase3.TENANT_B) > 0,
            "Phase 6 rollback context leaked")

    def cross_tenant_change_process():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute(
                "INSERT INTO qms.change_process(id,tenant_id,organization_id,change_revision_id,process_id) VALUES (%s,%s,%s,%s,%s)",
                [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A),
                 str(change_a_v3.entity_id), str(process_b.entity_id)],
            )
    expect_error(cross_tenant_change_process)

    def cross_tenant_measurement_process():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            bad = uuid4()
            cursor.execute(
                "INSERT INTO qms.measurement_definition(id,tenant_id,organization_id,lineage_id,revision,process_id,what_is_measured,method,measurement_timing) VALUES (%s,%s,%s,%s,1,%s,'x','x','x')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(bad), str(process_b.entity_id)],
            )
    expect_error(cross_tenant_measurement_process)

    def cross_tenant_objective_metric():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            bad = uuid4()
            cursor.execute(
                "INSERT INTO qms.objective(id,tenant_id,organization_id,lineage_id,revision,metric_id,target,status) VALUES (%s,%s,%s,%s,1,%s,'x','x')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(bad), str(metric_b.entity_id)],
            )
    expect_error(cross_tenant_objective_metric)

    def cross_tenant_predecessor():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute(
                "INSERT INTO qms.change(id,tenant_id,organization_id,lineage_id,revision,previous_revision_id,type,purpose,impact,status) VALUES (%s,%s,%s,%s,2,%s,'x','x','x','x')",
                [str(uuid4()), str(phase3.TENANT_A), str(phase3.ORG_A),
                 str(change_a_v1.aggregate_id), str(change_b.entity_id)],
            )
    expect_error(cross_tenant_predecessor)

    def blank_status():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            bad = uuid4()
            cursor.execute(
                "INSERT INTO qms.change(id,tenant_id,organization_id,lineage_id,revision,type,purpose,impact,status) VALUES (%s,%s,%s,%s,1,'x','x','x',' ')",
                [str(bad), str(phase3.TENANT_A), str(phase3.ORG_A), str(bad)],
            )
    expect_error(blank_status)

    def tenant_reassignment():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.change SET tenant_id=%s WHERE id=%s", [str(phase3.TENANT_B), str(change_a_v1.entity_id)])
    expect_error(tenant_reassignment, "tenant_id is immutable"); migrator.rollback()

    def organization_reassignment():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.measurement_definition SET organization_id=%s WHERE id=%s",
                           [str(phase3.ORG_B), str(metric_a_v1.entity_id)])
    expect_error(organization_reassignment, "organization_id is immutable"); migrator.rollback()

    def destructive_update():
        with migrator.cursor() as cursor:
            cursor.execute("UPDATE qms.change SET purpose='overwrite' WHERE id=%s", [str(change_a_v1.entity_id)])
    expect_error(destructive_update, "append-only"); migrator.rollback()

    def runtime_delete():
        with phase3.runtime_transaction("app", phase3.TENANT_A) as cursor:
            cursor.execute("DELETE FROM qms.measurement_definition WHERE id=%s", [str(metric_a_v1.entity_id)])
    expect_error(runtime_delete, "permission denied")
    expect_error(lambda: visible("projector", "change", phase3.TENANT_A), "permission denied")

    phase3.migrate(PHASE5_MIGRATION)
    with migrator.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('qms.risk'),to_regclass('qms.objective'),to_regclass('qms.change'),"
            "to_regclass('qms.measurement_definition'),"
            "EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='qms' AND table_name='objective' AND column_name='metric_id')"
        )
        require(cursor.fetchone() == ("qms.risk", "qms.objective", None, None, False),
                "Phase 6 reverse damaged promoted Phase 5")
    phase3.migrate(PHASE6_MIGRATION)

    print(json.dumps({
        "status": "PASS",
        "migration": "0006_change_performance_measurement_foundation",
        "measurement_gate": "B: MeasurementDefinition only; no KPI or MeasurementRecord",
        "protected_tables": protected,
        "policy_count": len(policies),
        "rls_pool_matrix": matrix,
        "worker_matrix": worker_matrix,
        "history": "Change v1 -> v2 -> v3 and MeasurementDefinition v1 -> v2 retained",
        "objective_metric": "metric_id -> frozen MeasurementDefinition revision PASS",
        "atomic_success": "business + DomainEvent + Outbox + Audit PASS",
        "atomic_rollback": "Change and MeasurementDefinition post-audit rollback leaves zero partial state",
        "cross_tenant_constraints": "ChangeProcess, MeasurementDefinition Process, Objective metric and predecessor PASS",
        "forward_reverse_forward": "0001 -> ... -> 0006 -> 0005 -> 0006 PASS",
        "projector_audit_writer": "zero Phase 6 business permissions",
        "pool_rollback_context": "A -> none -> B and A rollback -> none -> B PASS",
    }, default=str, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
