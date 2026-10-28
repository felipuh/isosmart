"""PostgreSQL 18.6 Phase 14 synthetic execution promotion matrix."""

import json
import os
import sys
from uuid import uuid4

import postgres_foundation_harness as phase3
import postgres_phase13_harness as phase13


PHASE13 = ("foundation", "0013_action_execution_preparation_authorization_foundation")
PHASE14 = ("foundation", "0014_action_execution_synthetic_foundation")
TABLES = ("action_execution", "action_execution_receipt")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def seed_chain(connection, tenant_id, org_id, label, autonomy=3):
    ids = {name: uuid4() for name in (
        "tenant_external", "tenant_event", "user", "admin_user", "user_event", "standard",
        "edition", "clause", "control", "layer", "rule", "evidence", "policy", "definition",
        "run", "run_input", "recommendation", "basis", "run_recommendation", "decision", "approval",
    )}
    trace = uuid4()
    from django.db import transaction
    with transaction.atomic(using="default"):
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO qms.tenant_projection(id,adminapps_tenant_id,source_version,source_event_id,display_name_snapshot,lifecycle_status,provisioning_status,reconciliation_status,last_synced_at) VALUES(%s,%s,1,%s,%s,'active','complete','in_sync',statement_timestamp()) ON CONFLICT(id) DO NOTHING", [str(tenant_id),str(ids["tenant_external"]),str(ids["tenant_event"]),f"Phase14 {label}"])
            cursor.execute("INSERT INTO qms.organization(id,tenant_id,display_name) VALUES(%s,%s,%s) ON CONFLICT(id) DO NOTHING", [str(org_id),str(tenant_id),f"Phase14 Org {label}"])
            cursor.execute("INSERT INTO qms.user_projection(id,adminapps_user_id,tenant_id,source_version,source_event_id,lifecycle_status,last_synced_at) VALUES(%s,%s,%s,1,%s,'active',statement_timestamp())", [str(ids["user"]),str(ids["admin_user"]),str(tenant_id),str(ids["user_event"])])
            cursor.execute("INSERT INTO normative.standard(id,code,title,publisher) VALUES(%s,%s,'Synthetic','ISO')", [str(ids["standard"]),f"P14-{label}"])
            cursor.execute("INSERT INTO normative.standard_edition(id,standard_id,edition,status,effective_from,source_hash) VALUES(%s,%s,'v1','draft',current_date,%s)", [str(ids["edition"]),str(ids["standard"]),"1"*64])
            cursor.execute("INSERT INTO normative.clause(id,standard_edition_id,code,title) VALUES(%s,%s,'1','Synthetic')", [str(ids["clause"]),str(ids["edition"])])
            cursor.execute("INSERT INTO normative.requirement_control(id,standard_edition_id,clause_id,paraphrase,applicability_rule) VALUES(%s,%s,%s,'Synthetic control','{}')", [str(ids["control"]),str(ids["edition"]),str(ids["clause"])])
            cursor.execute("UPDATE normative.standard_edition SET status='published' WHERE id=%s", [str(ids["edition"])])
            cursor.execute("INSERT INTO normative.knowledge_layer(id,standard_edition_id,layer_type) VALUES(%s,%s,'synthetic')", [str(ids["layer"]),str(ids["edition"])])
            cursor.execute("INSERT INTO normative.knowledge_layer_rule(id,knowledge_layer_id,lineage_id,rule_key,version,status,logic_json,evidence_expectation) VALUES(%s,%s,%s,%s,'v1','draft','{}','{}')", [str(ids["rule"]),str(ids["layer"]),str(ids["rule"]),f"p14-{label}"])
            cursor.execute("UPDATE normative.knowledge_layer_rule SET status='published',published_at=statement_timestamp() WHERE id=%s", [str(ids["rule"])])
            cursor.execute("INSERT INTO qms.evidence(id,tenant_id,organization_id,lineage_id,revision,source_type,content_hash,captured_at,trust_score) VALUES(%s,%s,%s,%s,1,'synthetic',%s,statement_timestamp(),1)", [str(ids["evidence"]),str(tenant_id),str(org_id),str(ids["evidence"]),"2"*64])
            cursor.execute("INSERT INTO governance.model_policy(id,lineage_id,policy_key,version,approved_models,data_classes,guardrails,human_gate_rules,status,published_at) VALUES(%s,%s,%s,'v1','[\"synthetic\"]','[]',%s,%s,'published',statement_timestamp())", [str(ids["policy"]),str(ids["policy"]),f"p14-policy-{label}",json.dumps({"autonomy_max":autonomy}),json.dumps({"required_autonomy_levels":[f"A{autonomy}"],"required_role":"quality_approver"})])
            cursor.execute("INSERT INTO governance.agent_definition(id,lineage_id,agent_key,name,version,purpose,capability,autonomy_max,model_policy_id,status,published_at) VALUES(%s,%s,%s,%s,'v1','Synthetic Phase 14','synthetic',%s,%s,'published',statement_timestamp())", [str(ids["definition"]),str(ids["definition"]),f"p14-agent-{label}",f"P14 {label}",autonomy,str(ids["policy"])])
            cursor.execute("INSERT INTO qms.agent_run(id,tenant_id,organization_id,agent_definition_id,model_policy_id,capability,status,requested_autonomy,effective_autonomy_ceiling,model_provider,model_identifier,model_version,prompt_version,rule_bundle_version,trace_id,started_at) VALUES(%s,%s,%s,%s,%s,'synthetic','running',%s,%s,'synthetic','synthetic','v1','v1','v1',%s,statement_timestamp())", [str(ids["run"]),str(tenant_id),str(org_id),str(ids["definition"]),str(ids["policy"]),autonomy,autonomy,str(trace)])
            cursor.execute("INSERT INTO qms.agent_run_input(id,tenant_id,organization_id,agent_run_id,standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", [str(ids["run_input"]),str(tenant_id),str(org_id),str(ids["run"]),str(ids["edition"]),str(ids["control"]),str(ids["rule"]),str(ids["evidence"])])
            cursor.execute("INSERT INTO qms.recommendation(id,tenant_id,organization_id,title,body,confidence,assumptions,impact,status,intended_autonomy) VALUES(%s,%s,%s,'Synthetic','No production action',0.8,'[]','material','proposed',%s)", [str(ids["recommendation"]),str(tenant_id),str(org_id),autonomy])
            cursor.execute("INSERT INTO qms.recommendation_basis(id,tenant_id,organization_id,recommendation_id,standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id,rationale,model_identifier,model_version,prompt_version,rule_bundle_version,trace_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'Synthetic','synthetic','v1','v1','v1',%s)", [str(ids["basis"]),str(tenant_id),str(org_id),str(ids["recommendation"]),str(ids["edition"]),str(ids["control"]),str(ids["rule"]),str(ids["evidence"]),str(trace)])
            cursor.execute("INSERT INTO qms.agent_run_recommendation(id,tenant_id,organization_id,agent_run_id,recommendation_id) VALUES(%s,%s,%s,%s,%s)", [str(ids["run_recommendation"]),str(tenant_id),str(org_id),str(ids["run"]),str(ids["recommendation"])])
            cursor.execute("INSERT INTO qms.agent_decision(id,tenant_id,organization_id,agent_run_id,recommendation_id,decision_type,payload,confidence,explainability,decision_autonomy,human_gate_required,trace_id) VALUES(%s,%s,%s,%s,%s,'execute_synthetic','{}',0.8,'{}',%s,true,%s)", [str(ids["decision"]),str(tenant_id),str(org_id),str(ids["run"]),str(ids["recommendation"]),autonomy,str(trace)])
            cursor.execute("INSERT INTO qms.approval(id,tenant_id,organization_id,agent_decision_id,recommendation_id,required_role,decision,decided_by_id,adminapps_user_id_snapshot,actor_type,comments,decided_at,trace_id) VALUES(%s,%s,%s,%s,%s,'quality_approver','approve',%s,%s,'human','synthetic only',statement_timestamp(),%s)", [str(ids["approval"]),str(tenant_id),str(org_id),str(ids["decision"]),str(ids["recommendation"]),str(ids["user"]),str(ids["admin_user"]),str(trace)])
    return ids, trace


def build_authorization(identity, ids, trace, suffix, autonomy=3, impact="standard", reversibility="reversible"):
    from foundation.action_authorization import ActionPreparationService, ExecutionAuthorizationService, ExecutionAuthorizerContext
    prep = ActionPreparationService(using="worker")
    plan = prep.prepare_action_plan(
        identity=identity, agent_decision_id=ids["decision"], action_type="synthetic_noop",
        target_type="synthetic_fixture", target_id=f"target-{suffix}", parameters={"fixture":suffix},
        impact=impact, reversibility=reversibility,
        preconditions=[{"identity":"revision","type":"exact_value","expected":1,"required":True}],
        dry_run_supported=True, required_autonomy=autonomy, idempotency_key=f"plan-{suffix}",
        actor_id="phase14-worker", trace_id=trace,
    )
    dry = prep.run_action_plan_dry_run(
        identity=identity, action_plan_id=plan.action_plan_id, expected_affected_objects=[],
        intended_state_delta={}, validation_status="passed",
        precondition_results=[{"identity":"revision","status":"satisfied"}],
        impact_summary={"synthetic":True}, actor_id="phase14-worker", trace_id=trace,
    )
    auth = ExecutionAuthorizationService(using="execution_authorizer").evaluate_execution_authorization(
        authority=ExecutionAuthorizerContext(identity), action_plan_id=plan.action_plan_id,
        dry_run_id=dry.dry_run_id, idempotency_key=f"auth-{suffix}", trace_id=trace,
    )
    require(auth.outcome == "authorized", f"authorization {suffix} failed")
    return plan, auth


def run():
    # Re-run the complete promoted Phase 1-13 matrix first; it finishes at an empty Phase 13 schema.
    phase13.run()
    phase3.migrate(PHASE14)
    from django.db import connections, transaction
    connection = connections["default"]
    executor_role = os.environ["FOUNDATION_EXECUTOR_ROLE"]
    runtime_roles = {os.environ[key] for key in (
        "FOUNDATION_APP_ROLE", "FOUNDATION_WORKER_ROLE", "FOUNDATION_PROJECTOR_ROLE",
        "FOUNDATION_AUDIT_WRITER_ROLE", "FOUNDATION_NORMATIVE_CURATOR_ROLE",
        "FOUNDATION_AGENT_CATALOG_CURATOR_ROLE", "FOUNDATION_HUMAN_APPROVER_ROLE",
        "FOUNDATION_EXECUTION_AUTHORIZER_ROLE", "FOUNDATION_EXECUTOR_ROLE",
    )}
    with connection.cursor() as cursor:
        cursor.execute("SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,r.rolname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='qms' AND c.relname=ANY(%s) ORDER BY c.relname", [list(TABLES)])
        rows = cursor.fetchall()
        require(len(rows)==2 and all(row[1] and row[2] for row in rows), "Phase14 ENABLE/FORCE RLS missing")
        require(all(row[3] not in runtime_roles for row in rows), "runtime owns execution table")
        for table in TABLES:
            cursor.execute("SELECT cmd FROM pg_policies WHERE schemaname='qms' AND tablename=%s", [table])
            require({row[0] for row in cursor.fetchall()}=={"SELECT","INSERT","UPDATE","DELETE","ALL"}, f"policy matrix {table}")
        cursor.execute("SELECT rolcanlogin,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s", [executor_role])
        require(cursor.fetchone()==(True,False,False), "executor principal is privileged")
        cursor.execute("SELECT has_table_privilege(%s,'qms.action_execution','INSERT'),has_table_privilege(%s,'qms.action_execution','UPDATE'),has_function_privilege(%s,'qms.foundation_0014_start_action_execution(uuid,uuid,uuid,uuid,uuid,text,text,text,uuid,integer,jsonb,text,uuid,timestamptz,text)','EXECUTE'),has_table_privilege(%s,'qms.risk','UPDATE'),has_table_privilege(%s,'qms.approval','INSERT')", [executor_role]*5)
        require(cursor.fetchone()==(False,False,True,False,False), "executor escaped function-only least privilege")

    ids_a, trace_a = seed_chain(connection, phase3.TENANT_A, phase3.ORG_A, "A3", 3)
    ids_b, trace_b = seed_chain(connection, phase3.TENANT_B, phase3.ORG_B, "B3", 3)
    from foundation.action_execution import (
        ActionExecutionService, ExecutionPrincipalContext, ExecutorRegistry,
        ExecutionRejected, SyntheticPreconditionEvaluator,
    )
    from foundation.action_authorization import IdempotencyConflict
    from foundation.models import ActionExecution, ActionExecutionReceipt, DomainEvent, ImmutableAuditLog, TransactionalOutbox
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context
    identity_a = TrustedTenantIdentity("phase14-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase14-b", phase3.TENANT_B)
    principal_a = ExecutionPrincipalContext(identity_a, SyntheticPreconditionEvaluator({"revision":"satisfied"}))
    principal_b = ExecutionPrincipalContext(identity_b, SyntheticPreconditionEvaluator({"revision":"satisfied"}))
    plan_a, auth_a = build_authorization(identity_a, ids_a, trace_a, "a")
    plan_b, auth_b = build_authorization(identity_b, ids_b, trace_b, "b")
    service = ActionExecutionService(using="executor")
    with connection.cursor() as cursor:
        cursor.execute("SELECT (SELECT count(*) FROM qms.process),(SELECT count(*) FROM qms.risk),(SELECT count(*) FROM qms.opportunity),(SELECT count(*) FROM qms.objective),(SELECT count(*) FROM qms.change),(SELECT count(*) FROM qms.evidence)")
        business_before = cursor.fetchone()
    success = service.execute_authorized_action(principal=principal_a, authorization_id=auth_a.authorization_id, idempotency_key="execute-a", trace_id=trace_a)
    require(success.status=="succeeded" and success.receipt_id, "synthetic success failed")
    replay = service.execute_authorized_action(principal=principal_a, authorization_id=auth_a.authorization_id, idempotency_key="execute-a", trace_id=trace_a)
    require(replay.replayed and replay.execution_id==success.execution_id, "execution replay duplicated")
    with connection.cursor() as cursor:
        cursor.execute("SELECT (SELECT count(*) FROM qms.process),(SELECT count(*) FROM qms.risk),(SELECT count(*) FROM qms.opportunity),(SELECT count(*) FROM qms.objective),(SELECT count(*) FROM qms.change),(SELECT count(*) FROM qms.evidence)")
        require(cursor.fetchone()==business_before, "synthetic success changed QMS state")

    failed = ActionExecutionService(using="executor", registry=ExecutorRegistry.synthetic_only(force_failure=True)).execute_authorized_action(
        principal=principal_a, authorization_id=auth_a.authorization_id,
        idempotency_key="execute-failed", trace_id=trace_a)
    require(failed.status=="failed", "forced failure was not durable")
    retry = service.execute_authorized_action(principal=principal_a, authorization_id=auth_a.authorization_id,
        idempotency_key="execute-retry", retry_of_execution_id=failed.execution_id, trace_id=trace_a)
    require(retry.status=="succeeded", "retry did not create successful new attempt")
    with trusted_tenant_context(identity_a,actor_id="verify",trace_id=trace_a,using="executor"):
        old = ActionExecution.objects.using("executor").get(id=failed.execution_id)
        new = ActionExecution.objects.using("executor").get(id=retry.execution_id)
        require(old.status=="failed" and new.retry_of_id==old.id and new.attempt_number==2,
                "retry overwrote failed history")

    changed_plan, changed_auth = build_authorization(identity_a, ids_a, trace_a, "changed")
    try:
        service.execute_authorized_action(principal=principal_a, authorization_id=changed_auth.authorization_id,
            idempotency_key="execute-a", trace_id=trace_a)
        raise AssertionError("idempotency conflict accepted changed authorization")
    except IdempotencyConflict:
        pass
    unknown_principal = ExecutionPrincipalContext(identity_a, SyntheticPreconditionEvaluator({"revision":"unknown"}))
    try:
        service.execute_authorized_action(principal=unknown_principal, authorization_id=changed_auth.authorization_id,
            idempotency_key="execute-precondition-changed", trace_id=trace_a)
        raise AssertionError("changed precondition executed")
    except ExecutionRejected as exc:
        require(exc.reason_code=="required_precondition_not_satisfied", "wrong precondition denial")

    # Start rollback: aggregate/event/outbox/audit all remain absent for the idempotency identity.
    before_counts = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT (SELECT count(*) FROM qms.action_execution),(SELECT count(*) FROM eventing.domain_event),(SELECT count(*) FROM eventing.transactional_outbox),(SELECT count(*) FROM audit.immutable_audit_log)")
        before_counts = cursor.fetchone()
    try:
        service.execute_authorized_action(principal=principal_a, authorization_id=changed_auth.authorization_id,
            idempotency_key="execute-start-rollback", trace_id=trace_a, fail_start_before_commit=True)
        raise AssertionError("start rollback fixture committed")
    except RuntimeError:
        pass
    with connection.cursor() as cursor:
        cursor.execute("SELECT (SELECT count(*) FROM qms.action_execution),(SELECT count(*) FROM eventing.domain_event),(SELECT count(*) FROM eventing.transactional_outbox),(SELECT count(*) FROM audit.immutable_audit_log)")
        require(cursor.fetchone()==before_counts, "start rollback left partial state")

    # Completion rollback leaves the committed running intent and no partial receipt/terminal event.
    terminal_events_before = None
    with phase3.runtime_transaction("executor",phase3.TENANT_A) as cursor:
        cursor.execute("SELECT count(*) FROM eventing.domain_event WHERE event_type IN ('action_execution.succeeded','action_execution.failed')")
        terminal_events_before = cursor.fetchone()[0]
    try:
        service.execute_authorized_action(principal=principal_a, authorization_id=changed_auth.authorization_id,
            idempotency_key="execute-completion-rollback", trace_id=trace_a,
            fail_completion_before_commit=True)
        raise AssertionError("completion rollback fixture committed")
    except RuntimeError:
        pass
    with trusted_tenant_context(identity_a,actor_id="verify",trace_id=trace_a,using="executor"):
        running = ActionExecution.objects.using("executor").get(idempotency_key="execute-completion-rollback")
        require(running.status=="running" and not ActionExecutionReceipt.objects.using("executor").filter(action_execution_id=running.id).exists(), "partial completion persisted")
        require(DomainEvent.objects.using("executor").filter(event_type__in=["action_execution.succeeded","action_execution.failed"]).count()==terminal_events_before, "partial terminal event persisted")

    # DB-side executor allowlist and exact plan/hash consistency reject before any terminal state.
    with trusted_tenant_context(identity_a,actor_id="raw",trace_id=trace_a,using="executor"):
        for executor_type, plan_hash in (("shell",plan_a.action_plan_hash),("synthetic_noop","f"*64)):
            rejected = False
            try:
                with transaction.atomic(using="executor"):
                    with connections["executor"].cursor() as cursor:
                        cursor.execute("SELECT qms.foundation_0014_start_action_execution(%s,%s,%s,%s,%s,%s,%s,'running',NULL,1,%s::jsonb,%s,%s,statement_timestamp(),'raw')", [str(uuid4()),str(phase3.TENANT_A),str(phase3.ORG_A),str(auth_a.authorization_id),str(plan_a.action_plan_id),plan_hash,executor_type,json.dumps({"revision":"satisfied"}),f"raw-{executor_type}-{plan_hash[0]}",str(trace_a)])
            except Exception:
                rejected = True
            require(rejected, f"raw forged execution accepted: {executor_type}/{plan_hash[0]}")

    # A2 is denied even when a preparation authorization exists.
    plan_a2, auth_a2 = build_authorization(identity_a, ids_a, trace_a, "a2", autonomy=2)
    try:
        service.execute_authorized_action(principal=principal_a, authorization_id=auth_a2.authorization_id,
            idempotency_key="execute-a2", trace_id=trace_a)
        raise AssertionError("A2 executed")
    except ExecutionRejected as exc:
        require(exc.reason_code=="autonomy_ceiling_denied", "wrong A2 denial")

    # A4 may execute only the same synthetic no-op under reversible/standard guardrails.
    ids_a4, trace_a4 = seed_chain(connection, phase3.TENANT_A, phase3.ORG_A, "A4", 4)
    plan_a4, auth_a4 = build_authorization(identity_a, ids_a4, trace_a4, "a4", autonomy=4)
    a4 = service.execute_authorized_action(principal=principal_a, authorization_id=auth_a4.authorization_id,
        idempotency_key="execute-a4", trace_id=trace_a4)
    require(a4.status=="succeeded", "A4 synthetic no-op failed")

    b_result = service.execute_authorized_action(principal=principal_b, authorization_id=auth_b.authorization_id,
        idempotency_key="execute-b", trace_id=trace_b)
    require(b_result.status=="succeeded", "tenant B execution failed")
    for alias in ("app","executor"):
        with phase3.runtime_transaction(alias,phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.action_execution")
            require(cursor.fetchone()[0] >= 1, f"{alias} tenant A sees no execution")
        with phase3.runtime_transaction(alias,None) as cursor:
            cursor.execute("SELECT count(*) FROM qms.action_execution")
            require(cursor.fetchone()[0] == 0, f"{alias} none sees execution")
        with phase3.runtime_transaction(alias,phase3.TENANT_B) as cursor:
            cursor.execute("SELECT count(*) FROM qms.action_execution")
            require(cursor.fetchone()[0] == 1, f"{alias} tenant B isolation failed")

    try:
        with phase3.runtime_transaction("executor",phase3.TENANT_A) as cursor:
            cursor.execute("UPDATE qms.action_execution SET action_plan_hash=%s WHERE id=%s", ["e"*64,str(success.execution_id)])
        raise AssertionError("executor direct terminal mutation succeeded")
    except Exception as exc:
        require("permission denied" in str(exc).lower(), "unexpected direct mutation result")
    try:
        with phase3.runtime_transaction("executor",phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.action_execution")
            raise RuntimeError("intentional rollback")
    except RuntimeError:
        pass
    with phase3.runtime_transaction("executor",None) as cursor:
        cursor.execute("SELECT count(*) FROM qms.action_execution")
        require(cursor.fetchone()[0]==0, "executor tenant leaked after rollback")

    phase3.migrate(PHASE13)
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.execution_authorization'),to_regclass('qms.action_execution')")
        require(cursor.fetchone()==("qms.execution_authorization",None), "Phase14 reverse damaged Phase13")
    phase3.migrate(PHASE14)
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.action_execution'),to_regclass('qms.action_execution_receipt')")
        require(cursor.fetchone()==("qms.action_execution","qms.action_execution_receipt"), "Phase14 second forward failed")

    print(json.dumps({
        "status":"PASS", "migration":PHASE14[1], "postgresql":"18.6",
        "executor":"synthetic_noop ONLY; LOGIN non-superuser NOBYPASSRLS function-only",
        "success_failure_retry":"PASS", "idempotency":"replay/conflict PASS",
        "authorization_plan_hash_policy":"exact revalidation/A2 denied/A4 synthetic-only PASS",
        "precondition_dry_run":"execution-time fail-closed/exact hash PASS",
        "qms_side_effects":"zero PASS", "event_outbox_audit":"start/terminal atomic PASS",
        "rls":"ENABLE+FORCE A/none/B PASS", "pool_rollback":"PASS",
        "forward_reverse_forward":"PASS",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)},indent=2),file=sys.stderr)
        raise
