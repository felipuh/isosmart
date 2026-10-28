"""PostgreSQL 18.6 Phase 16 controlled Opportunity promotion matrix."""

import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase14_harness as phase14


PHASE14 = ("foundation", "0014_action_execution_synthetic_foundation")
PHASE15 = ("foundation", "0015_first_controlled_qms_mutation_poc")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def build_controlled_authorization(identity, ids, trace, opportunity, suffix, action_type,
                                   source, destination):
    from foundation.action_authorization import (
        ActionPreparationService,
        ExecutionAuthorizationService,
        ExecutionAuthorizerContext,
    )
    from foundation.controlled_opportunity import opportunity_substantive_fingerprint

    prep = ActionPreparationService(using="worker")
    parameters = {
        "expected_revision_id": str(opportunity.id),
        "expected_revision": opportunity.revision,
        "expected_current_state": source,
        "desired_state": destination,
        "expected_state_hash": opportunity_substantive_fingerprint(opportunity),
        "policy_id": "controlled-qms-action-policy/v1",
        "compensation_action_type": "opportunity.resume_evaluation",
    }
    preconditions = [
        {"identity": "exact_opportunity_leaf", "type": "state_fingerprint",
         "expected": parameters["expected_state_hash"], "required": True}
    ]
    plan = prep.prepare_action_plan(
        identity=identity, agent_decision_id=ids["decision"], action_type=action_type,
        target_type="Opportunity", target_id=str(opportunity.lineage_id),
        parameters=parameters, impact="standard", reversibility="reversible",
        preconditions=preconditions, dry_run_supported=True, required_autonomy=3,
        idempotency_key=f"phase16-plan-{suffix}", actor_id="phase16-worker",
        trace_id=trace,
    )
    dry = prep.run_action_plan_dry_run(
        identity=identity, action_plan_id=plan.action_plan_id,
        expected_affected_objects=[{
            "type": "Opportunity", "lineage_id": str(opportunity.lineage_id),
            "revision_id": str(opportunity.id),
        }],
        intended_state_delta={"status": {"before": source, "after": destination}},
        validation_status="passed",
        precondition_results=[{"identity": "exact_opportunity_leaf", "status": "satisfied"}],
        impact_summary={"impact": "standard", "business_state_changed": False},
        actor_id="phase16-worker", trace_id=trace,
    )
    auth = ExecutionAuthorizationService(using="execution_authorizer").evaluate_execution_authorization(
        authority=ExecutionAuthorizerContext(identity), action_plan_id=plan.action_plan_id,
        dry_run_id=dry.dry_run_id, idempotency_key=f"phase16-auth-{suffix}", trace_id=trace,
    )
    require(auth.outcome == "authorized", "controlled authorization was denied")
    return plan, auth


def run():
    # Complete promoted baseline first, then install only migration 0015.
    phase14.run()
    from django.db import connections, transaction

    phase3.migrate(PHASE15)

    # Schema reversibility is proven before any Phase 16 business history exists;
    # a real rollback after use would require an explicit data-retention policy.
    phase3.migrate(PHASE14)
    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT to_regprocedure('qms.defer_opportunity_evaluation(uuid,text)'),to_regprocedure('qms.resume_opportunity_evaluation(uuid,text)')")
        require(cursor.fetchone() == (None, None), "Phase 16 capability survived reverse")
        cursor.execute("SELECT has_table_privilege(%s,'qms.opportunity','SELECT'),has_schema_privilege(%s,'qms','USAGE'),pg_get_functiondef('qms.foundation_0014_validate_execution_start()'::regprocedure) NOT LIKE '%%controlled_opportunity%%'", [os.environ["FOUNDATION_QMS_ACTION_OWNER_ROLE"]] * 2)
        require(cursor.fetchone() == (False, False, True),
                "Phase 16 grants/trigger semantics survived reverse")
    from foundation.qms_context import QmsContextCommandService
    from foundation.risk_objective import RiskOpportunityObjectiveCommandService
    from foundation.tenant_context import TrustedTenantIdentity
    reverse_identity = TrustedTenantIdentity("phase16-reverse", phase3.TENANT_A)
    reverse_trace = uuid4()
    reverse_process = QmsContextCommandService(using="app").create_process(
        identity=reverse_identity, organization_id=phase3.ORG_A,
        name="Phase 16 reverse compatibility", actor_id="phase16-reverse",
        trace_id=reverse_trace,
    )
    reverse_opportunity = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
        identity=reverse_identity, process_id=reverse_process.entity_id,
        hypothesis="Reverse compatible", benefit="Preserved public command",
        feasibility="Ephemeral", status="under_evaluation",
        actor_id="phase16-reverse", trace_id=reverse_trace,
    )
    reverse_transition = RiskOpportunityObjectiveCommandService(using="app").change_opportunity_status(
        identity=reverse_identity, opportunity_id=reverse_opportunity.entity_id,
        status="deferred", actor_id="phase16-reverse", trace_id=reverse_trace,
    )
    require(reverse_transition.entity_id != reverse_opportunity.entity_id,
            "public Opportunity command failed after Phase 16 reverse")
    phase3.migrate(PHASE15)

    from foundation.controlled_opportunity import ControlledOpportunityActionService
    from foundation.models import (
        ActionExecution, ActionExecutionReceipt, DomainEvent, ImmutableAuditLog, Opportunity,
    )
    from foundation.tenant_context import trusted_tenant_context

    connection = connections["default"]
    identity = TrustedTenantIdentity("phase16-a", phase3.TENANT_A)
    ids, trace = phase14.seed_chain(connection, phase3.TENANT_A, phase3.ORG_A, "P16", 3)
    process = QmsContextCommandService(using="app").create_process(
        identity=identity, organization_id=phase3.ORG_A, name="Phase 16 evaluation",
        actor_id="phase16-human", trace_id=trace,
    )
    opportunity_result = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
        identity=identity, process_id=process.entity_id, hypothesis="Controlled hypothesis",
        benefit="Controlled benefit", feasibility="Controlled feasibility",
        status="under_evaluation", actor_id="phase16-human", trace_id=trace,
    )
    try:
        RiskOpportunityObjectiveCommandService(using="app")._apply_opportunity_status_transition_in_transaction(
            identity=identity, opportunity_id=opportunity_result.entity_id,
            status="deferred", actor_id="phase16-human", trace_id=trace,
        )
        raise AssertionError("Opportunity primitive accepted autocommit")
    except RuntimeError as exc:
        require("active transaction" in str(exc), "wrong autocommit rejection")
    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace, using="app"):
        opportunity = Opportunity.objects.using("app").get(id=opportunity_result.entity_id)

    # Golden public-command scenario with equivalent substantive transition.
    public_opp_result = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
        identity=identity, process_id=process.entity_id, hypothesis="Controlled hypothesis",
        benefit="Controlled benefit", feasibility="Controlled feasibility",
        status="under_evaluation", actor_id="phase16-human", trace_id=trace,
    )
    public_transition = RiskOpportunityObjectiveCommandService(using="app").change_opportunity_status(
        identity=identity, opportunity_id=public_opp_result.entity_id, status="deferred",
        actor_id="phase16-human", trace_id=trace, change_reason="public golden defer",
    )

    plan, authorization = build_controlled_authorization(
        identity, ids, trace, opportunity, "defer", "opportunity.defer_evaluation",
        "under_evaluation", "deferred",
    )
    before = {}
    with trusted_tenant_context(identity, actor_id="phase16-count", trace_id=trace, using="app"):
        before = {
            "opportunity": Opportunity.objects.using("app").count(),
            "opportunity_events": DomainEvent.objects.using("app").filter(
                event_type="opportunity.status_changed"
            ).count(),
        }
    service = ControlledOpportunityActionService(using="executor")
    forward = service.defer_evaluation(
        identity=identity, authorization_id=authorization.authorization_id,
        idempotency_key="phase16-execute-defer",
    )
    require(not forward.replayed and forward.receipt["after_status"] == "deferred",
            "authorized forward defer failed")
    replay = service.defer_evaluation(
        identity=identity, authorization_id=authorization.authorization_id,
        idempotency_key="phase16-execute-defer",
    )
    require(replay.replayed and replay.execution_id == forward.execution_id,
            "lost-response replay was not reconciled")

    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace, using="app"):
        deferred = Opportunity.objects.using("app").get(id=forward.after_revision_id)
        require(deferred.status == "deferred" and deferred.revision == opportunity.revision + 1,
                "forward revision semantics failed")
        require(Opportunity.objects.using("app").count() == before["opportunity"] + 1,
                "forward created more than one revision")
        require(DomainEvent.objects.using("app").filter(
            event_type="opportunity.status_changed"
        ).count() == before["opportunity_events"] + 1, "forward event duplicated")
        execution = ActionExecution.objects.using("app").get(id=forward.execution_id)
        receipt = ActionExecutionReceipt.objects.using("app").get(action_execution_id=execution.id)
        require(execution.status == "succeeded" and receipt.result["effectiveness_claimed"] is False,
                "execution/receipt contract failed")
        public_leaf = Opportunity.objects.using("app").get(id=public_transition.entity_id)
        public_event = DomainEvent.objects.using("app").get(event_id=public_transition.event_id)
        controlled_event = DomainEvent.objects.using("app").get(event_id=forward.domain_event_id)
        public_audit = ImmutableAuditLog.objects.using("app").get(id=public_transition.audit_id)
        controlled_audit = ImmutableAuditLog.objects.using("app").filter(
            stream_type="opportunity", stream_id=deferred.lineage_id,
            action="opportunity.status_changed",
        ).get()
        require(
            (public_leaf.revision, public_leaf.status, public_leaf.process_id,
             public_leaf.hypothesis, public_leaf.benefit, public_leaf.feasibility) ==
            (deferred.revision, deferred.status, deferred.process_id,
             deferred.hypothesis, deferred.benefit, deferred.feasibility),
            "public/controlled Opportunity semantics diverged",
        )
        require(
            public_event.event_type == controlled_event.event_type == "opportunity.status_changed"
            and public_event.schema_version == controlled_event.schema_version == 1
            and public_event.payload["changes"] == controlled_event.payload["changes"]
            and public_event.payload["revision"] == controlled_event.payload["revision"],
            "public/controlled event golden parity failed",
        )
        require(
            public_audit.before_hash == controlled_audit.before_hash
            and public_audit.after_hash == controlled_audit.after_hash,
            "public/controlled audit hash-input parity failed",
        )

    # Every practical failure point proves the one-transaction rollback invariant.
    ids_fail, trace_fail = phase14.seed_chain(connection, phase3.TENANT_A, phase3.ORG_A, "P16F", 3)
    failure_points = (
        "after_target_lock", "before_revision_insert", "after_revision_insert",
        "after_opportunity_event", "after_opportunity_outbox", "after_opportunity_audit",
        "before_execution_completion", "after_execution_completion", "after_receipt",
        "after_execution_event", "after_execution_outbox", "after_execution_audit",
        "before_commit",
    )
    for index, failure_point in enumerate(failure_points, start=1):
        fail_opp_result = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
            identity=identity, process_id=process.entity_id,
            hypothesis=f"Rollback hypothesis {index}", benefit="Rollback benefit",
            feasibility="Rollback feasibility", status="under_evaluation",
            actor_id="phase16-human", trace_id=trace_fail,
        )
        with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_fail, using="app"):
            fail_opp = Opportunity.objects.using("app").get(id=fail_opp_result.entity_id)
        _, fail_auth = build_controlled_authorization(
            identity, ids_fail, trace_fail, fail_opp, f"forced-{index}",
            "opportunity.defer_evaluation", "under_evaluation", "deferred",
        )
        key = f"phase16-forced-{index}"
        rejected = False
        try:
            with transaction.atomic(using="executor"):
                with connections["executor"].cursor() as cursor:
                    cursor.execute(
                        "SELECT set_config('foundation.phase16_fail_at',%s,true)",
                        [failure_point],
                    )
                service.defer_evaluation(
                    identity=identity, authorization_id=fail_auth.authorization_id,
                    idempotency_key=key,
                )
        except Exception:
            rejected = True
        require(rejected, f"failure injection did not fire: {failure_point}")
        with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_fail, using="app"):
            require(not Opportunity.objects.using("app").filter(
                previous_revision_id=fail_opp.id
            ).exists(), f"{failure_point} left a business revision")
            require(not ActionExecution.objects.using("app").filter(
                idempotency_key=key
            ).exists(), f"{failure_point} left execution completion")

    # Two authorized attempts against one expected leaf serialize at the target;
    # exactly one commits and the loser reports stale/conflict.
    concurrent_opp_result = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
        identity=identity, process_id=process.entity_id, hypothesis="Concurrent hypothesis",
        benefit="Concurrent benefit", feasibility="Concurrent feasibility",
        status="under_evaluation", actor_id="phase16-human", trace_id=trace_fail,
    )
    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_fail, using="app"):
        concurrent_opp = Opportunity.objects.using("app").get(id=concurrent_opp_result.entity_id)
    _, concurrent_auth_1 = build_controlled_authorization(
        identity, ids_fail, trace_fail, concurrent_opp, "concurrent-1",
        "opportunity.defer_evaluation", "under_evaluation", "deferred",
    )
    _, concurrent_auth_2 = build_controlled_authorization(
        identity, ids_fail, trace_fail, concurrent_opp, "concurrent-2",
        "opportunity.defer_evaluation", "under_evaluation", "deferred",
    )
    barrier = threading.Barrier(2)

    def concurrent_call(auth_id, key):
        import psycopg2
        db = psycopg2.connect(
            dbname=os.environ["FOUNDATION_DB_NAME"],
            user=os.environ["FOUNDATION_EXECUTOR_ROLE"],
            password=os.environ["FOUNDATION_EXECUTOR_PASSWORD"],
            host=os.environ["FOUNDATION_DB_HOST"], port=os.environ["FOUNDATION_DB_PORT"],
        )
        try:
            with db:
                with db.cursor() as cursor:
                    cursor.execute("SELECT set_config('app.tenant_id',%s,true)", [str(phase3.TENANT_A)])
                    barrier.wait(timeout=10)
                    cursor.execute("SELECT qms.defer_opportunity_evaluation(%s,%s)",
                                   [str(auth_id), key])
                    return "success"
        except Exception:
            return "stale_or_conflict"
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(
            lambda args: concurrent_call(*args),
            ((concurrent_auth_1.authorization_id, "phase16-concurrent-1"),
             (concurrent_auth_2.authorization_id, "phase16-concurrent-2")),
        ))
    require(sorted(outcomes) == ["stale_or_conflict", "success"],
            f"concurrent outcomes invalid: {outcomes}")
    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_fail, using="app"):
        require(Opportunity.objects.using("app").filter(
            previous_revision_id=concurrent_opp.id
        ).count() == 1, "concurrency created duplicate revisions")
    conflict = False
    try:
        service.defer_evaluation(
            identity=identity, authorization_id=concurrent_auth_1.authorization_id,
            idempotency_key="phase16-execute-defer",
        )
    except Exception:
        conflict = True
    require(conflict, "same idempotency key accepted different authorization/plan")

    unrelated_result = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
        identity=identity, process_id=process.entity_id, hypothesis="Unrelated provenance",
        benefit="Unrelated benefit", feasibility="Unrelated feasibility",
        status="under_evaluation", actor_id="phase16-human", trace_id=trace_fail,
    )
    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_fail, using="app"):
        unrelated_source = Opportunity.objects.using("app").get(id=unrelated_result.entity_id)
    _, unrelated_auth = build_controlled_authorization(
        identity, ids_fail, trace_fail, unrelated_source, "unrelated-deferred",
        "opportunity.defer_evaluation", "under_evaluation", "deferred",
    )
    RiskOpportunityObjectiveCommandService(using="app").change_opportunity_status(
        identity=identity, opportunity_id=unrelated_source.id, status="deferred",
        actor_id="phase16-human", trace_id=trace_fail,
    )
    denied = False
    try:
        service.defer_evaluation(
            identity=identity, authorization_id=unrelated_auth.authorization_id,
            idempotency_key="phase16-unrelated-deferred",
        )
    except Exception:
        denied = True
    require(denied, "unrelated already-deferred leaf was treated as replay")

    # Separate plan/approval/authorization and fixed wrapper for compensation.
    ids_resume, trace_resume = phase14.seed_chain(connection, phase3.TENANT_A, phase3.ORG_A, "P16R", 3)
    resume_plan, resume_auth = build_controlled_authorization(
        identity, ids_resume, trace_resume, deferred, "resume",
        "opportunity.resume_evaluation", "deferred", "under_evaluation",
    )
    for wrong_method, wrong_auth, wrong_key in (
        (service.defer_evaluation, resume_auth.authorization_id, "phase16-forward-cannot-resume"),
        (service.resume_evaluation, authorization.authorization_id, "phase16-resume-cannot-forward"),
    ):
        separated = False
        try:
            wrong_method(identity=identity, authorization_id=wrong_auth,
                         idempotency_key=wrong_key)
        except Exception:
            separated = True
        require(separated, "forward/compensation capability separation failed")
    resumed = service.resume_evaluation(
        identity=identity, authorization_id=resume_auth.authorization_id,
        idempotency_key="phase16-execute-resume",
    )
    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_resume, using="app"):
        resume_leaf = Opportunity.objects.using("app").get(id=resumed.after_revision_id)
        require(resume_leaf.status == "under_evaluation" and resume_leaf.revision == 3,
                "compensation history failed")

    stale_opp_result = RiskOpportunityObjectiveCommandService(using="app").create_opportunity(
        identity=identity, process_id=process.entity_id, hypothesis="Stale compensation",
        benefit="Stale benefit", feasibility="Stale feasibility", status="under_evaluation",
        actor_id="phase16-human", trace_id=trace_resume,
    )
    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_resume, using="app"):
        stale_source = Opportunity.objects.using("app").get(id=stale_opp_result.entity_id)
    _, stale_forward_auth = build_controlled_authorization(
        identity, ids_fail, trace_fail, stale_source, "stale-forward",
        "opportunity.defer_evaluation", "under_evaluation", "deferred",
    )
    stale_forward = service.defer_evaluation(
        identity=identity, authorization_id=stale_forward_auth.authorization_id,
        idempotency_key="phase16-stale-forward",
    )
    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_resume, using="app"):
        stale_deferred = Opportunity.objects.using("app").get(id=stale_forward.after_revision_id)
    _, stale_resume_auth = build_controlled_authorization(
        identity, ids_resume, trace_resume, stale_deferred, "stale-resume",
        "opportunity.resume_evaluation", "deferred", "under_evaluation",
    )
    intervening = RiskOpportunityObjectiveCommandService(using="app").change_opportunity_status(
        identity=identity, opportunity_id=stale_deferred.id, status="deferred_reviewed",
        actor_id="phase16-human", trace_id=trace_resume,
    )
    denied = False
    try:
        service.resume_evaluation(
            identity=identity, authorization_id=stale_resume_auth.authorization_id,
            idempotency_key="phase16-stale-resume",
        )
    except Exception:
        denied = True
    require(denied, "stale compensation was accepted")
    with trusted_tenant_context(identity, actor_id="phase16-read", trace_id=trace_resume, using="app"):
        require(not Opportunity.objects.using("app").filter(
            previous_revision_id=intervening.entity_id
        ).exists(), "stale compensation rewrote or extended history")

    # Cross-tenant and no-context invocations fail closed without disclosure.
    tenant_b = TrustedTenantIdentity("phase16-b", phase3.TENANT_B)
    denied = False
    try:
        service.defer_evaluation(
            identity=tenant_b, authorization_id=authorization.authorization_id,
            idempotency_key="phase16-cross-tenant",
        )
    except Exception:
        denied = True
    require(denied, "cross-tenant controlled invocation succeeded")
    denied = False
    try:
        with transaction.atomic(using="executor"):
            with connections["executor"].cursor() as cursor:
                cursor.execute("SELECT qms.defer_opportunity_evaluation(%s,%s)",
                               [str(authorization.authorization_id), "phase16-no-context"])
    except Exception:
        denied = True
    require(denied, "no-tenant controlled invocation succeeded")

    owner = os.environ["FOUNDATION_QMS_ACTION_OWNER_ROLE"]
    executor = os.environ["FOUNDATION_EXECUTOR_ROLE"]
    with connection.cursor() as cursor:
        cursor.execute("SELECT rolcanlogin,rolsuper,rolbypassrls,rolinherit FROM pg_roles WHERE rolname=%s", [owner])
        require(cursor.fetchone() == (False, False, False, False), "function owner attributes unsafe")
        cursor.execute("SELECT r.rolname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='qms' AND c.relname='opportunity'")
        require(cursor.fetchone()[0] != owner, "function owner owns Opportunity table")
        cursor.execute("SELECT has_table_privilege(%s,'qms.opportunity','INSERT'),has_table_privilege(%s,'qms.opportunity','UPDATE'),has_table_privilege(%s,'qms.opportunity','DELETE'),has_function_privilege('public','qms.defer_opportunity_evaluation(uuid,text)','EXECUTE'),has_function_privilege(%s,'qms.foundation_0015_apply_opportunity_status_transition(uuid,uuid,text,text,uuid,text,text)','EXECUTE')", [executor, executor, executor, executor])
        require(cursor.fetchone() == (False, False, False, False, False),
                "executor or PUBLIC escaped the narrow capability")
        denied_roles = [os.environ[name] for name in (
            "FOUNDATION_APP_ROLE", "FOUNDATION_WORKER_ROLE", "FOUNDATION_PROJECTOR_ROLE",
            "FOUNDATION_AUDIT_WRITER_ROLE", "FOUNDATION_NORMATIVE_CURATOR_ROLE",
            "FOUNDATION_AGENT_CATALOG_CURATOR_ROLE", "FOUNDATION_HUMAN_APPROVER_ROLE",
            "FOUNDATION_EXECUTION_AUTHORIZER_ROLE",
        )]
        cursor.execute("SELECT bool_or(has_function_privilege(role_name,'qms.defer_opportunity_evaluation(uuid,text)','EXECUTE')) FROM unnest(%s::text[]) role_name", [denied_roles])
        require(cursor.fetchone()[0] is False, "non-executor principal can defer")
        cursor.execute("SELECT has_function_privilege(%s,'qms.defer_opportunity_evaluation(uuid,text)','EXECUTE'),has_schema_privilege(%s,'qms','CREATE')", [executor, owner])
        require(cursor.fetchone() == (True, False), "capability grant or owner schema privilege unsafe")

    # Hostile caller search_path cannot shadow fully qualified trusted objects.
    with transaction.atomic(using="executor"):
        from foundation.tenant_context import bind_trusted_tenant_context_in_transaction
        bind_trusted_tenant_context_in_transaction(
            identity, actor_id="hostile", trace_id=uuid4(), using="executor"
        )
        with connections["executor"].cursor() as cursor:
            cursor.execute("CREATE TEMP TABLE opportunity(id uuid)")
            cursor.execute("SET LOCAL search_path=pg_temp,public")
            cursor.execute("SELECT count(*) FROM qms.action_execution WHERE id=%s", [str(forward.execution_id)])
            require(cursor.fetchone()[0] == 1, "hostile search_path affected trusted execution")

    # Executor direct target DML is denied for every generic operation.
    for statement in (
        "INSERT INTO qms.opportunity(id) VALUES(uuidv7())",
        "UPDATE qms.opportunity SET status='accepted' WHERE id='" + str(resume_leaf.id) + "'",
        "DELETE FROM qms.opportunity WHERE id='" + str(resume_leaf.id) + "'",
    ):
        denied = False
        try:
            with transaction.atomic(using="executor"):
                from foundation.tenant_context import bind_trusted_tenant_context_in_transaction
                bind_trusted_tenant_context_in_transaction(
                    identity, actor_id="bypass", trace_id=uuid4(), using="executor"
                )
                with connections["executor"].cursor() as cursor:
                    cursor.execute(statement)
        except Exception:
            denied = True
        require(denied, "executor generic Opportunity DML was accepted")

    print(json.dumps({
        "status": "PASS", "postgresql": "18.6",
        "forward": "under_evaluation -> deferred PASS",
        "public_shared_primitive": "installed/autocommit guarded PASS",
        "idempotency_lost_response": "PASS", "atomic_forced_rollback": "13/13 PASS",
        "golden_public_parity": "PASS", "concurrency": "one winner PASS",
        "tenant_context": "A/cross-tenant/none PASS",
        "compensation": "separate success + stale denial PASS",
        "least_privilege": "owner/executor/ACL/direct DML PASS",
        "hostile_search_path": "PASS", "forward_reverse_forward": "PASS",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise
