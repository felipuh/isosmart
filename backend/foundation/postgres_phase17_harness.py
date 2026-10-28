"""PostgreSQL 18.6 Phase 17 controlled-execution hardening gate."""

import json
import os
import select
import socket
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase14_harness as phase14
import postgres_phase16_harness as phase16


PHASE14 = ("foundation", "0014_action_execution_synthetic_foundation")
PHASE15 = ("foundation", "0015_first_controlled_qms_mutation_poc")
PHASE16 = ("foundation", "0016_controlled_execution_recovery_hardening")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class CommitAckLossProxy:
    """One-shot PostgreSQL protocol proxy that drops ReadyForQuery after COMMIT.

    The COMMIT query is forwarded intact.  The backend response is parsed and
    the client connection is closed only when the server's ReadyForQuery packet
    proves transaction completion.  This models a committed transaction whose
    acknowledgement is unavailable to libpq.
    """

    def __init__(self, upstream_host, upstream_port):
        self.upstream = (upstream_host, int(upstream_port))
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.commit_forwarded = threading.Event()
        self.ack_dropped = threading.Event()
        self.error = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        return self

    @staticmethod
    def _frontend_packets(buffer, startup_complete):
        packets = []
        while True:
            header = 5 if startup_complete else 4
            if len(buffer) < header:
                break
            if startup_complete:
                length = int.from_bytes(buffer[1:5], "big")
                total = 1 + length
            else:
                length = int.from_bytes(buffer[:4], "big")
                total = length
            if len(buffer) < total:
                break
            packets.append(buffer[:total])
            buffer = buffer[total:]
            if not startup_complete:
                startup_complete = True
        return packets, buffer, startup_complete

    @staticmethod
    def _backend_packets(buffer):
        packets = []
        while len(buffer) >= 5:
            length = int.from_bytes(buffer[1:5], "big")
            total = 1 + length
            if len(buffer) < total:
                break
            packets.append(buffer[:total])
            buffer = buffer[total:]
        return packets, buffer

    def _run(self):
        client = upstream = None
        try:
            client, _ = self.listener.accept()
            upstream = socket.create_connection(self.upstream, timeout=10)
            client.setblocking(False)
            upstream.setblocking(False)
            front_buffer = b""
            back_buffer = b""
            startup_complete = False
            commit_seen = False
            while True:
                readable, _, _ = select.select([client, upstream], [], [], 10)
                if not readable:
                    raise TimeoutError("commit acknowledgement proxy timed out")
                if client in readable:
                    chunk = client.recv(65536)
                    if not chunk:
                        return
                    front_buffer += chunk
                    packets, front_buffer, startup_complete = self._frontend_packets(
                        front_buffer, startup_complete
                    )
                    for packet in packets:
                        if startup_complete and packet[:1] == b"Q" and b"COMMIT\x00" in packet.upper():
                            commit_seen = True
                            self.commit_forwarded.set()
                        upstream.sendall(packet)
                if upstream in readable:
                    chunk = upstream.recv(65536)
                    if not chunk:
                        return
                    back_buffer += chunk
                    packets, back_buffer = self._backend_packets(back_buffer)
                    for packet in packets:
                        if commit_seen and packet[:1] == b"Z":
                            self.ack_dropped.set()
                            client.close()
                            client = None
                            return
                        client.sendall(packet)
        except Exception as exc:
            self.error = exc
        finally:
            for connection in (client, upstream, self.listener):
                if connection is not None:
                    try:
                        connection.close()
                    except Exception:
                        pass

    def finish(self):
        self.thread.join(timeout=15)
        require(not self.thread.is_alive(), "commit acknowledgement proxy did not stop")
        require(self.error is None, f"commit acknowledgement proxy failed: {self.error}")
        require(self.commit_forwarded.is_set(), "proxy did not forward COMMIT")
        require(self.ack_dropped.is_set(), "proxy did not drop the commit acknowledgement")


def raw_executor_connection(port=None):
    import psycopg2

    return psycopg2.connect(
        dbname=os.environ["FOUNDATION_DB_NAME"],
        user=os.environ["FOUNDATION_EXECUTOR_ROLE"],
        password=os.environ["FOUNDATION_EXECUTOR_PASSWORD"],
        host=os.environ["FOUNDATION_DB_HOST"],
        port=port or os.environ["FOUNDATION_DB_PORT"],
        sslmode="disable",
    )


def invoke_uncommitted(authorization_id, key, port=None):
    connection = raw_executor_connection(port)
    cursor = connection.cursor()
    cursor.execute("SELECT set_config('app.tenant_id',%s,true)", [str(phase3.TENANT_A)])
    cursor.execute("SELECT qms.defer_opportunity_evaluation_recoverable(%s,%s)", [str(authorization_id), key])
    result = cursor.fetchone()[0]
    return connection, cursor, result


def new_authorization(identity, process, suffix):
    from foundation.models import Opportunity
    from foundation.risk_objective import RiskOpportunityObjectiveCommandService
    from foundation.tenant_context import trusted_tenant_context

    from django.db import connections

    ids, trace = phase14.seed_chain(
        connections["default"], phase3.TENANT_A, phase3.ORG_A, f"P17{suffix}", 3
    )
    result = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
        identity=identity,
        process_id=process.entity_id,
        hypothesis=f"Phase 17 hypothesis {suffix}",
        benefit="Controlled recovery proof",
        feasibility="Ephemeral PostgreSQL 18.6",
        status="under_evaluation",
        actor_id="phase17-human",
        trace_id=trace,
    )
    with trusted_tenant_context(identity, actor_id="phase17-read", trace_id=trace, using="app"):
        opportunity = Opportunity.objects.using("app").get(id=result.entity_id)
    plan, authorization = phase16.build_controlled_authorization(
        identity,
        ids,
        trace,
        opportunity,
        suffix,
        "opportunity.defer_evaluation",
        "under_evaluation",
        "deferred",
    )
    return trace, opportunity, plan, authorization


def run():
    phase16.run()
    from django.db import connections, transaction

    phase3.migrate(PHASE16)

    from foundation.controlled_opportunity import (
        ControlledExecutionInconsistent,
        ControlledOpportunityActionService,
        ReconciliationOutcome,
    )
    from foundation.models import ActionExecution, ActionExecutionReceipt, DomainEvent, ImmutableAuditLog, Opportunity
    from foundation.qms_context import QmsContextCommandService
    from foundation.risk_objective import RiskOpportunityObjectiveCommandService
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    identity = TrustedTenantIdentity("phase17-a", phase3.TENANT_A)
    seed_trace = uuid4()
    process = QmsContextCommandService(using="app").create_process(
        identity=identity,
        organization_id=phase3.ORG_A,
        name="Phase 17 recovery",
        actor_id="phase17-human",
        trace_id=seed_trace,
    )
    service = ControlledOpportunityActionService(using="executor")

    # A: the client connection disappears before COMMIT is sent. PostgreSQL
    # rolls back the open transaction and exact durable reconciliation permits
    # one controlled retry.
    _, before_opp, _, before_auth = new_authorization(identity, process, "before-commit")
    before_key = "phase17-before-commit"
    connection, cursor, _ = invoke_uncommitted(before_auth.authorization_id, before_key)
    cursor.close()
    connection.close()
    before_reconciliation = service.reconcile_defer_evaluation(
        identity=identity,
        authorization_id=before_auth.authorization_id,
        idempotency_key=before_key,
    )
    require(before_reconciliation.outcome is ReconciliationOutcome.NOT_COMMITTED,
            f"pre-COMMIT disconnect classified {before_reconciliation.outcome}")
    retried = service.recover_defer_after_ambiguous_commit(
        identity=identity,
        authorization_id=before_auth.authorization_id,
        idempotency_key=before_key,
    )
    require(not retried.replayed, "NOT_COMMITTED path did not perform one fresh execution")

    # B: a protocol-aware local proxy forwards COMMIT, observes the backend's
    # ReadyForQuery, withholds it, and closes the client socket.  libpq reports
    # an unknown outcome although PostgreSQL committed.
    _, ack_opp, _, ack_auth = new_authorization(identity, process, "ack-lost")
    ack_key = "phase17-ack-lost"
    proxy = CommitAckLossProxy(
        os.environ["FOUNDATION_DB_HOST"], os.environ["FOUNDATION_DB_PORT"]
    ).start()
    ambiguous = False
    proxied_connection = proxied_cursor = None
    try:
        proxied_connection, proxied_cursor, _ = invoke_uncommitted(
            ack_auth.authorization_id, ack_key, proxy.port
        )
        proxied_connection.commit()
    except Exception:
        ambiguous = True
    finally:
        if proxied_cursor is not None:
            try:
                proxied_cursor.close()
            except Exception:
                pass
        if proxied_connection is not None:
            try:
                proxied_connection.close()
            except Exception:
                pass
    proxy.finish()
    require(ambiguous, "libpq received a known successful commit through the fault proxy")
    committed = service.reconcile_defer_evaluation(
        identity=identity,
        authorization_id=ack_auth.authorization_id,
        idempotency_key=ack_key,
    )
    require(committed.outcome is ReconciliationOutcome.COMMITTED,
            f"acknowledgement-loss classified {committed.outcome}: {committed.reason}")
    recovered = service.recover_defer_after_ambiguous_commit(
        identity=identity,
        authorization_id=ack_auth.authorization_id,
        idempotency_key=ack_key,
    )
    require(recovered.replayed and recovered.execution_id == committed.execution_id,
            "COMMITTED reconciliation replayed the mutation instead of the receipt")
    require(all(value == 1 for value in committed.observed.values()),
            f"committed proof has missing/duplicate artifacts: {committed.observed}")

    # Same exact claim is serialized before row lookup: one creator, one waiter
    # returning the same durable result.
    _, race_opp, _, race_auth = new_authorization(identity, process, "same-claim-race")
    race_key = "phase17-same-claim-race"
    barrier = threading.Barrier(2)

    def same_claim_call():
        db = raw_executor_connection()
        try:
            with db:
                with db.cursor() as raw_cursor:
                    raw_cursor.execute("SELECT set_config('app.tenant_id',%s,true)", [str(phase3.TENANT_A)])
                    barrier.wait(timeout=10)
                    raw_cursor.execute("SELECT qms.defer_opportunity_evaluation_recoverable(%s,%s)",
                                       [str(race_auth.authorization_id), race_key])
                    return raw_cursor.fetchone()[0]
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        race_results = list(pool.map(lambda _: same_claim_call(), range(2)))
    require(sorted(result["replayed"] for result in race_results) == [False, True],
            f"same claim ownership results invalid: {race_results}")
    require(len({result["execution_id"] for result in race_results}) == 1,
            "same claim created multiple ActionExecutions")

    # Same idempotency identity with different provenance cannot be reassigned.
    _, _, _, provenance_auth_a = new_authorization(identity, process, "provenance-a")
    _, _, _, provenance_auth_b = new_authorization(identity, process, "provenance-b")
    provenance_key = "phase17-provenance-conflict"
    barrier = threading.Barrier(2)

    def provenance_call(auth_id):
        db = raw_executor_connection()
        try:
            with db:
                with db.cursor() as raw_cursor:
                    raw_cursor.execute("SELECT set_config('app.tenant_id',%s,true)", [str(phase3.TENANT_A)])
                    barrier.wait(timeout=10)
                    raw_cursor.execute("SELECT qms.defer_opportunity_evaluation_recoverable(%s,%s)",
                                       [str(auth_id), provenance_key])
                    raw_cursor.fetchone()
                    return "owner"
        except Exception:
            return "conflict"
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        provenance_results = list(pool.map(
            provenance_call,
            [provenance_auth_a.authorization_id, provenance_auth_b.authorization_id],
        ))
    require(sorted(provenance_results) == ["conflict", "owner"],
            f"changed provenance claim results invalid: {provenance_results}")

    # A running claim cannot arise from the one-transaction controlled path,
    # because disconnect/crash rolls it back.  A deliberately retained legacy/
    # corrupt running fixture is nevertheless never stolen.
    abandoned_trace, _, abandoned_plan, abandoned_auth = new_authorization(identity, process, "abandoned")
    abandoned_id = uuid4()
    abandoned_key = "phase17-abandoned"
    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "INSERT INTO qms.action_execution(id,tenant_id,organization_id,execution_authorization_id,"
                "action_plan_id,action_plan_hash,executor_type,status,attempt_number,precondition_results,"
                "idempotency_key,trace_id,started_at) VALUES(%s,%s,%s,%s,%s,%s,'controlled_opportunity',"
                "'running',1,%s,%s,%s,statement_timestamp())",
                [str(abandoned_id), str(phase3.TENANT_A), str(phase3.ORG_A),
                 str(abandoned_auth.authorization_id), str(abandoned_plan.action_plan_id),
                 abandoned_plan.action_plan_hash, json.dumps({"exact_opportunity_leaf": "satisfied"}),
                 abandoned_key, str(abandoned_trace)],
            )
    abandoned = service.reconcile_defer_evaluation(
        identity=identity, authorization_id=abandoned_auth.authorization_id,
        idempotency_key=abandoned_key,
    )
    require(abandoned.outcome is ReconciliationOutcome.INCONSISTENT and
            abandoned.reason == "nonterminal_or_abandoned_claim",
            f"abandoned claim was not failed closed: {abandoned}")
    blocked = False
    try:
        service.recover_defer_after_ambiguous_commit(
            identity=identity, authorization_id=abandoned_auth.authorization_id,
            idempotency_key=abandoned_key,
        )
    except ControlledExecutionInconsistent:
        blocked = True
    require(blocked, "abandoned claim was silently stolen")

    # Artificial terminal execution without a Receipt is contradictory durable
    # evidence and must not manufacture success.
    inconsistent_trace, _, inconsistent_plan, inconsistent_auth = new_authorization(identity, process, "inconsistent")
    inconsistent_id = uuid4()
    inconsistent_key = "phase17-inconsistent"
    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "INSERT INTO qms.action_execution(id,tenant_id,organization_id,execution_authorization_id,"
                "action_plan_id,action_plan_hash,executor_type,status,attempt_number,precondition_results,"
                "idempotency_key,trace_id,started_at) VALUES(%s,%s,%s,%s,%s,%s,'controlled_opportunity',"
                "'running',1,%s,%s,%s,statement_timestamp())",
                [str(inconsistent_id), str(phase3.TENANT_A), str(phase3.ORG_A),
                 str(inconsistent_auth.authorization_id), str(inconsistent_plan.action_plan_id),
                 inconsistent_plan.action_plan_hash, json.dumps({"exact_opportunity_leaf": "satisfied"}),
                 inconsistent_key, str(inconsistent_trace)],
            )
            cursor.execute("SELECT set_config('foundation.execution_completion',%s,true)",
                           [str(inconsistent_id)])
            cursor.execute("UPDATE qms.action_execution SET status='succeeded',completed_at=statement_timestamp() WHERE id=%s",
                           [str(inconsistent_id)])
    inconsistent = service.reconcile_defer_evaluation(
        identity=identity, authorization_id=inconsistent_auth.authorization_id,
        idempotency_key=inconsistent_key,
    )
    require(inconsistent.outcome is ReconciliationOutcome.INCONSISTENT and
            inconsistent.reason == "terminal_execution_without_exactly_one_receipt",
            f"inconsistent fixture was not failed closed: {inconsistent}")

    # Exact owner catalog inventory and privilege minimization.
    owner = os.environ["FOUNDATION_QMS_ACTION_OWNER_ROLE"]
    executor = os.environ["FOUNDATION_EXECUTOR_ROLE"]
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT rolcanlogin,rolsuper,rolinherit,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=%s", [owner])
        require(cursor.fetchone() == (False, False, False, False, False, False, False),
                "function owner role attributes are not minimal")
        cursor.execute("SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname=%s", [owner])
        require(cursor.fetchone()[0] == 0, "function owner is a member of another role")
        cursor.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles r ON r.oid=c.relowner WHERE r.rolname=%s AND c.relkind IN ('r','p','S')", [owner])
        require(cursor.fetchone()[0] == 0, "function owner owns a table or sequence")
        cursor.execute("SELECT has_schema_privilege(%s,'qms','CREATE'),has_table_privilege(%s,'qms.organization','SELECT'),has_table_privilege(%s,'qms.user_projection','SELECT'),has_table_privilege(%s,'qms.recommendation','SELECT'),has_table_privilege(%s,'audit.immutable_audit_log','SELECT')", [owner] * 5)
        require(cursor.fetchone() == (False, False, False, False, True),
                "function owner before/after ACL minimization mismatch")
        cursor.execute("SELECT has_sequence_privilege(%s,c.oid,'USAGE') OR has_sequence_privilege(%s,c.oid,'UPDATE') FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='S' AND n.nspname IN ('qms','eventing','audit','governance')", [owner, owner])
        require(not any(row[0] for row in cursor.fetchall()), "function owner has sequence privileges")
        cursor.execute("SELECT has_function_privilege('public','qms.reconcile_defer_opportunity_evaluation(uuid,text)','EXECUTE'),has_function_privilege(%s,'qms.reconcile_defer_opportunity_evaluation(uuid,text)','EXECUTE'),has_function_privilege(%s,'qms.foundation_0016_reconcile_controlled_opportunity_execution(uuid,text,text)','EXECUTE')", [executor, executor])
        require(cursor.fetchone() == (False, True, False), "reconciliation function ACL escaped")

    # Capability disablement is a grant change, never business rollback.  Past
    # execution/effectiveness-independent history stays readable and the public
    # Opportunity command remains available.
    with trusted_tenant_context(identity, actor_id="phase17-count", trace_id=seed_trace, using="app"):
        history_before = (
            Opportunity.objects.using("app").count(),
            ActionExecution.objects.using("app").filter(executor_type="controlled_opportunity").count(),
            ActionExecutionReceipt.objects.using("app").filter(executor_type="controlled_opportunity").count(),
            DomainEvent.objects.using("app").count(),
            ImmutableAuditLog.objects.using("app").count(),
        )
    connections["executor"].close()
    from psycopg2 import sql
    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cursor:
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(owner)))
            cursor.execute(sql.SQL(
                "REVOKE EXECUTE ON FUNCTION qms.defer_opportunity_evaluation_recoverable(uuid,text) FROM {}"
            ).format(sql.Identifier(executor)))
    _, disabled_opp, _, disabled_auth = new_authorization(identity, process, "disabled")
    denied = False
    try:
        service.defer_evaluation(identity=identity, authorization_id=disabled_auth.authorization_id,
                                 idempotency_key="phase17-disabled")
    except Exception:
        denied = True
    require(denied, "revoked controlled capability still executed")
    public_result = RiskOpportunityObjectiveCommandService(using="app").change_opportunity_status(
        identity=identity, opportunity_id=disabled_opp.id, status="deferred",
        actor_id="phase17-human", trace_id=seed_trace,
    )
    require(public_result.entity_id != disabled_opp.id,
            "public Opportunity command was coupled to controlled capability")
    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cursor:
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(owner)))
            cursor.execute(sql.SQL(
                "GRANT EXECUTE ON FUNCTION qms.defer_opportunity_evaluation_recoverable(uuid,text) TO {}"
            ).format(sql.Identifier(executor)))
    connections["executor"].close()
    with trusted_tenant_context(identity, actor_id="phase17-count", trace_id=seed_trace, using="app"):
        require(ActionExecution.objects.using("app").filter(executor_type="controlled_opportunity").count() == history_before[1],
                "capability disablement deleted or manufactured controlled executions")
        require(ActionExecutionReceipt.objects.using("app").filter(executor_type="controlled_opportunity").count() == history_before[2],
                "capability disablement deleted controlled receipts")

    # 0016 -> 0015 is non-destructive with retained history.  0015 -> 0014 is
    # intentionally blocked once controlled rows exist; failed DDL rollback must
    # preserve every governed row rather than deleting it to satisfy constraints.
    phase3.migrate(PHASE15)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM qms.action_execution WHERE executor_type='controlled_opportunity'")
        retained_count = cursor.fetchone()[0]
    require(retained_count >= history_before[1], "0016 reverse lost controlled history")
    downgrade_blocked = False
    try:
        phase3.migrate(PHASE14)
    except Exception:
        downgrade_blocked = True
        connections["default"].close()
    require(downgrade_blocked, "0015 destructive retained-history downgrade unexpectedly succeeded")
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT count(*) FROM qms.action_execution WHERE executor_type='controlled_opportunity'")
        require(cursor.fetchone()[0] == retained_count, "failed downgrade deleted business history")
        cursor.execute("SELECT to_regprocedure('qms.defer_opportunity_evaluation(uuid,text)') IS NOT NULL")
        require(cursor.fetchone()[0], "failed downgrade left capability schema partially removed")
    phase3.migrate(PHASE16)

    print(json.dumps({
        "status": "PASS",
        "postgresql": "18.6",
        "phase16_regression": "PASS",
        "commit_before_server": "NOT_COMMITTED then one safe retry PASS",
        "commit_ack_lost": "COMMITTED exact durable replay PASS",
        "inconsistent": "fail closed PASS",
        "claim_serialization": "one creator + deterministic waiter PASS",
        "claim_provenance_conflict": "PASS",
        "abandoned_claim": "explicit reconciliation/no stealing PASS",
        "owner_acl": "exact attributes/ownership/membership/table/sequence/function PASS",
        "privilege_minimization": "unused Organization/UserProjection/Recommendation reads removed",
        "capability_disable": "new executions denied; public command/history preserved PASS",
        "retained_history": "0016 reverse safe; 0015 reverse intentionally blocked PASS",
        "effectiveness_schema": "ABSENT",
        "external_effects": "ZERO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
