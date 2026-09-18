"""PostgreSQL 18.6 catalog, RLS, reversibility, and no-execution gate for Phase 13."""

import json
import os
import sys
from uuid import uuid4

import postgres_foundation_harness as phase3


PHASE12 = ("foundation", "0012_agent_decision_human_decision_gate_foundation")
PHASE13 = ("foundation", "0013_action_execution_preparation_authorization_foundation")
TABLES = ("action_plan", "action_plan_dry_run", "execution_authorization")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run():
    phase3.configure_django()
    from django.db import connections

    phase3.migrate(PHASE13)
    connection = connections["default"]
    app_role = os.environ["FOUNDATION_APP_ROLE"]
    worker_role = os.environ["FOUNDATION_WORKER_ROLE"]
    authorizer_role = os.environ["FOUNDATION_EXECUTION_AUTHORIZER_ROLE"]
    runtime_roles = {
        os.environ[key] for key in (
            "FOUNDATION_APP_ROLE", "FOUNDATION_WORKER_ROLE", "FOUNDATION_PROJECTOR_ROLE",
            "FOUNDATION_AUDIT_WRITER_ROLE", "FOUNDATION_NORMATIVE_CURATOR_ROLE",
            "FOUNDATION_AGENT_CATALOG_CURATOR_ROLE", "FOUNDATION_HUMAN_APPROVER_ROLE",
            "FOUNDATION_EXECUTION_AUTHORIZER_ROLE",
        )
    }
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,r.rolname "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner "
            "WHERE n.nspname='qms' AND c.relname=ANY(%s) ORDER BY c.relname",
            [list(TABLES)],
        )
        rows = cursor.fetchall()
        require(len(rows) == 3 and all(row[1] and row[2] for row in rows),
                "Phase 13 ENABLE/FORCE RLS missing")
        require(all(row[3] not in runtime_roles for row in rows),
                "runtime role owns a Phase 13 table")
        for table in TABLES:
            cursor.execute("SELECT cmd FROM pg_policies WHERE schemaname='qms' AND tablename=%s", [table])
            require({row[0] for row in cursor.fetchall()} == {"SELECT","INSERT","UPDATE","DELETE","ALL"},
                    f"incomplete RLS policy matrix for {table}")
        cursor.execute(
            "SELECT rolcanlogin,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s",
            [authorizer_role],
        )
        require(cursor.fetchone() == (True,False,False), "execution authorizer is privileged")
        cursor.execute(
            "SELECT has_table_privilege(%s,'qms.execution_authorization','INSERT'),"
            "has_function_privilege(%s,'qms.foundation_0013_grant_execution_authorization(uuid,uuid,uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,smallint,text,text,text,text,text,text,text,uuid)','EXECUTE'),"
            "has_table_privilege(%s,'qms.approval','INSERT'),"
            "has_table_privilege(%s,'qms.risk','UPDATE'),"
            "has_table_privilege(%s,'qms.action_plan','INSERT')",
            [authorizer_role]*5,
        )
        require(cursor.fetchone() == (False,True,False,False,False),
                "execution authorizer escaped narrow function-only boundary")
        cursor.execute(
            "SELECT has_table_privilege(%s,'qms.execution_authorization','INSERT'),"
            "has_function_privilege(%s,'qms.foundation_0013_grant_execution_authorization(uuid,uuid,uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,smallint,text,text,text,text,text,text,text,uuid)','EXECUTE')",
            [worker_role,worker_role],
        )
        require(cursor.fetchone() == (False,False), "worker can self-authorize")
        cursor.execute("SELECT to_regclass('qms.action_execution')")
        require(cursor.fetchone()[0] is None, "ActionExecution exists")

    from django.db import transaction
    from foundation.action_authorization import (
        ActionPreparationService, ExecutionAuthorizationService,
        ExecutionAuthorizerContext, IdempotencyConflict, resolve_effective_approval,
    )
    from foundation.models import ActionPlan, Approval, DomainEvent, ImmutableAuditLog, TransactionalOutbox
    from foundation.tenant_context import TrustedTenantIdentity, trusted_tenant_context

    def seed_chain(tenant_id, org_id, label):
        ids = {name: uuid4() for name in (
            "tenant_external","tenant_event","user","admin_user","user_event","standard",
            "edition","clause","control","layer","rule","evidence","policy","definition",
            "run","run_input","recommendation","basis","run_recommendation","decision",
            "approval_changes","approval_approve",
        )}
        trace = uuid4()
        with transaction.atomic(using="default"):
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO qms.tenant_projection(id,adminapps_tenant_id,source_version,source_event_id,display_name_snapshot,lifecycle_status,provisioning_status,reconciliation_status,last_synced_at) VALUES(%s,%s,1,%s,%s,'active','complete','in_sync',statement_timestamp())", [str(tenant_id),str(ids["tenant_external"]),str(ids["tenant_event"]),f"Phase13 {label}"])
                cursor.execute("INSERT INTO qms.organization(id,tenant_id,display_name) VALUES(%s,%s,%s)",[str(org_id),str(tenant_id),f"Phase13 Org {label}"])
                cursor.execute("INSERT INTO qms.user_projection(id,adminapps_user_id,tenant_id,source_version,source_event_id,lifecycle_status,last_synced_at) VALUES(%s,%s,%s,1,%s,'active',statement_timestamp())",[str(ids["user"]),str(ids["admin_user"]),str(tenant_id),str(ids["user_event"])])
                cursor.execute("INSERT INTO normative.standard(id,code,title,publisher) VALUES(%s,%s,'Synthetic','ISO')",[str(ids["standard"]),f"P13-{label}"])
                cursor.execute("INSERT INTO normative.standard_edition(id,standard_id,edition,status,effective_from,source_hash) VALUES(%s,%s,'v1','draft',current_date,%s)",[str(ids["edition"]),str(ids["standard"]),"1"*64])
                cursor.execute("INSERT INTO normative.clause(id,standard_edition_id,code,title) VALUES(%s,%s,'1','Synthetic')",[str(ids["clause"]),str(ids["edition"])])
                cursor.execute("INSERT INTO normative.requirement_control(id,standard_edition_id,clause_id,paraphrase,applicability_rule) VALUES(%s,%s,%s,'Synthetic control','{}')",[str(ids["control"]),str(ids["edition"]),str(ids["clause"])])
                cursor.execute("UPDATE normative.standard_edition SET status='published' WHERE id=%s",[str(ids["edition"])])
                cursor.execute("INSERT INTO normative.knowledge_layer(id,standard_edition_id,layer_type) VALUES(%s,%s,'synthetic')",[str(ids["layer"]),str(ids["edition"])])
                cursor.execute("INSERT INTO normative.knowledge_layer_rule(id,knowledge_layer_id,lineage_id,rule_key,version,status,logic_json,evidence_expectation) VALUES(%s,%s,%s,%s,'v1','draft','{}','{}')",[str(ids["rule"]),str(ids["layer"]),str(ids["rule"]),f"p13-{label}"])
                cursor.execute("UPDATE normative.knowledge_layer_rule SET status='published',published_at=statement_timestamp() WHERE id=%s",[str(ids["rule"])])
                cursor.execute("INSERT INTO qms.evidence(id,tenant_id,organization_id,lineage_id,revision,source_type,content_hash,captured_at,trust_score) VALUES(%s,%s,%s,%s,1,'synthetic',%s,statement_timestamp(),1)",[str(ids["evidence"]),str(tenant_id),str(org_id),str(ids["evidence"]),"2"*64])
                cursor.execute("INSERT INTO governance.model_policy(id,lineage_id,policy_key,version,approved_models,data_classes,guardrails,human_gate_rules,status,published_at) VALUES(%s,%s,%s,'v1','[\"synthetic\"]','[]','{\"autonomy_max\":3}',%s,'published',statement_timestamp())",[str(ids["policy"]),str(ids["policy"]),f"p13-policy-{label}",'{"required_autonomy_levels":["A3"],"required_role":"quality_approver"}'])
                cursor.execute("INSERT INTO governance.agent_definition(id,lineage_id,agent_key,name,version,purpose,capability,autonomy_max,model_policy_id,status,published_at) VALUES(%s,%s,%s,%s,'v1','Synthetic Phase 13','synthetic',3,%s,'published',statement_timestamp())",[str(ids["definition"]),str(ids["definition"]),f"p13-agent-{label}",f"P13 {label}",str(ids["policy"])])
                cursor.execute("INSERT INTO qms.agent_run(id,tenant_id,organization_id,agent_definition_id,model_policy_id,capability,status,requested_autonomy,effective_autonomy_ceiling,model_provider,model_identifier,model_version,prompt_version,rule_bundle_version,trace_id,started_at) VALUES(%s,%s,%s,%s,%s,'synthetic','running',3,3,'synthetic','synthetic','v1','v1','v1',%s,statement_timestamp())",[str(ids["run"]),str(tenant_id),str(org_id),str(ids["definition"]),str(ids["policy"]),str(trace)])
                cursor.execute("INSERT INTO qms.agent_run_input(id,tenant_id,organization_id,agent_run_id,standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",[str(ids["run_input"]),str(tenant_id),str(org_id),str(ids["run"]),str(ids["edition"]),str(ids["control"]),str(ids["rule"]),str(ids["evidence"])])
                cursor.execute("INSERT INTO qms.recommendation(id,tenant_id,organization_id,title,body,confidence,assumptions,impact,status,intended_autonomy) VALUES(%s,%s,%s,'Synthetic','No execution',0.8,'[]','high','proposed',3)",[str(ids["recommendation"]),str(tenant_id),str(org_id)])
                cursor.execute("INSERT INTO qms.recommendation_basis(id,tenant_id,organization_id,recommendation_id,standard_edition_id,requirement_control_id,knowledge_layer_rule_id,evidence_id,rationale,model_identifier,model_version,prompt_version,rule_bundle_version,trace_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'Synthetic','synthetic','v1','v1','v1',%s)",[str(ids["basis"]),str(tenant_id),str(org_id),str(ids["recommendation"]),str(ids["edition"]),str(ids["control"]),str(ids["rule"]),str(ids["evidence"]),str(trace)])
                cursor.execute("INSERT INTO qms.agent_run_recommendation(id,tenant_id,organization_id,agent_run_id,recommendation_id) VALUES(%s,%s,%s,%s,%s)",[str(ids["run_recommendation"]),str(tenant_id),str(org_id),str(ids["run"]),str(ids["recommendation"])])
                cursor.execute("INSERT INTO qms.agent_decision(id,tenant_id,organization_id,agent_run_id,recommendation_id,decision_type,payload,confidence,explainability,decision_autonomy,human_gate_required,trace_id) VALUES(%s,%s,%s,%s,%s,'prepare','{}',0.8,'{}',3,true,%s)",[str(ids["decision"]),str(tenant_id),str(org_id),str(ids["run"]),str(ids["recommendation"]),str(trace)])
                cursor.execute("INSERT INTO qms.approval(id,tenant_id,organization_id,agent_decision_id,recommendation_id,required_role,decision,decided_by_id,adminapps_user_id_snapshot,actor_type,comments,decided_at,trace_id) VALUES(%s,%s,%s,%s,%s,'quality_approver','request_changes',%s,%s,'human','first',statement_timestamp()-interval '1 minute',%s),(%s,%s,%s,%s,%s,'quality_approver','approve',%s,%s,'human','effective',statement_timestamp(),%s)",[str(ids["approval_changes"]),str(tenant_id),str(org_id),str(ids["decision"]),str(ids["recommendation"]),str(ids["user"]),str(ids["admin_user"]),str(trace),str(ids["approval_approve"]),str(tenant_id),str(org_id),str(ids["decision"]),str(ids["recommendation"]),str(ids["user"]),str(ids["admin_user"]),str(trace)])
        return ids, trace

    ids_a, trace_a = seed_chain(phase3.TENANT_A, phase3.ORG_A, "A")
    ids_b, trace_b = seed_chain(phase3.TENANT_B, phase3.ORG_B, "B")
    identity_a = TrustedTenantIdentity("phase13-a", phase3.TENANT_A)
    identity_b = TrustedTenantIdentity("phase13-b", phase3.TENANT_B)
    prep = ActionPreparationService(using="worker")
    common_plan = dict(action_type="prepare_change",target_type="change",target_id="synthetic-1",
                       parameters={"status":"proposed"},impact="high",reversibility="irreversible",
                       preconditions=[{"identity":"revision","type":"exact_value","expected":1,
                                      "required":True,"source_reference":"synthetic-1"}],
                       dry_run_supported=True,required_autonomy=3,actor_id="phase13-worker")
    before_business = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT (SELECT count(*) FROM qms.process),(SELECT count(*) FROM qms.risk),(SELECT count(*) FROM qms.opportunity),(SELECT count(*) FROM qms.objective),(SELECT count(*) FROM qms.change),(SELECT count(*) FROM qms.evidence)")
        before_business = cursor.fetchone()
    plan_a = prep.prepare_action_plan(identity=identity_a,agent_decision_id=ids_a["decision"],idempotency_key="prepare-a",trace_id=trace_a,**common_plan)
    replay = prep.prepare_action_plan(identity=identity_a,agent_decision_id=ids_a["decision"],idempotency_key="prepare-a",trace_id=trace_a,**common_plan)
    require(replay.replayed and replay.action_plan_id==plan_a.action_plan_id,"ActionPlan idempotent replay failed")
    try:
        prep.prepare_action_plan(identity=identity_a,agent_decision_id=ids_a["decision"],idempotency_key="prepare-a",trace_id=trace_a,**dict(common_plan,parameters={"status":"changed"}))
        raise AssertionError("changed plan reused idempotency key")
    except IdempotencyConflict:
        pass
    dry_a = prep.run_action_plan_dry_run(identity=identity_a,action_plan_id=plan_a.action_plan_id,
        expected_affected_objects=[{"type":"change","id":"synthetic-1"}],
        intended_state_delta={"status":{"from":"draft","to":"proposed"}},validation_status="passed",
        precondition_results=[{"identity":"revision","status":"satisfied"}],
        impact_summary={"impact":"high","reversibility":"irreversible"},actor_id="phase13-worker",trace_id=trace_a)
    with connection.cursor() as cursor:
        cursor.execute("SELECT (SELECT count(*) FROM qms.process),(SELECT count(*) FROM qms.risk),(SELECT count(*) FROM qms.opportunity),(SELECT count(*) FROM qms.objective),(SELECT count(*) FROM qms.change),(SELECT count(*) FROM qms.evidence)")
        require(cursor.fetchone()==before_business,"dry-run changed business state")
    authority = ExecutionAuthorizerContext(identity_a)
    auth_service = ExecutionAuthorizationService(using="execution_authorizer")
    granted = auth_service.evaluate_execution_authorization(authority=authority,action_plan_id=plan_a.action_plan_id,dry_run_id=dry_a.dry_run_id,idempotency_key="authorize-a",trace_id=trace_a)
    require(granted.outcome=="authorized" and granted.authorization_id,"authorized path failed")
    auth_replay = auth_service.evaluate_execution_authorization(authority=authority,action_plan_id=plan_a.action_plan_id,dry_run_id=dry_a.dry_run_id,idempotency_key="authorize-a",trace_id=trace_a)
    require(auth_replay.replayed and auth_replay.authorization_id==granted.authorization_id,"authorization replay duplicated")
    failing_plan = prep.prepare_action_plan(identity=identity_a,agent_decision_id=ids_a["decision"],
        idempotency_key="prepare-precondition-fail",trace_id=trace_a,
        **dict(common_plan,target_id="synthetic-precondition-fail"))
    failing_dry = prep.run_action_plan_dry_run(identity=identity_a,action_plan_id=failing_plan.action_plan_id,
        expected_affected_objects=[],intended_state_delta={},validation_status="passed",
        precondition_results=[{"identity":"revision","status":"unknown"}],impact_summary={"impact":"high"},
        actor_id="phase13-worker",trace_id=trace_a)
    denied_precondition = auth_service.evaluate_execution_authorization(authority=authority,
        action_plan_id=failing_plan.action_plan_id,dry_run_id=failing_dry.dry_run_id,
        idempotency_key="authorize-precondition-fail",trace_id=trace_a)
    require(denied_precondition.outcome=="denied" and denied_precondition.reason_code=="required_precondition_not_satisfied",
            "unknown required precondition did not fail closed")
    ceiling_plan = prep.prepare_action_plan(identity=identity_a,agent_decision_id=ids_a["decision"],
        idempotency_key="prepare-ceiling",trace_id=trace_a,
        **dict(common_plan,target_id="synthetic-ceiling",required_autonomy=4))
    ceiling_dry = prep.run_action_plan_dry_run(identity=identity_a,action_plan_id=ceiling_plan.action_plan_id,
        expected_affected_objects=[],intended_state_delta={},validation_status="passed",
        precondition_results=[{"identity":"revision","status":"satisfied"}],impact_summary={"impact":"high"},
        actor_id="phase13-worker",trace_id=trace_a)
    denied_ceiling = auth_service.evaluate_execution_authorization(authority=authority,
        action_plan_id=ceiling_plan.action_plan_id,dry_run_id=ceiling_dry.dry_run_id,
        idempotency_key="authorize-ceiling",trace_id=trace_a)
    require(denied_ceiling.reason_code=="policy_ceiling_exceeded","policy ceiling did not deny")
    dry_mismatch = auth_service.evaluate_execution_authorization(authority=authority,
        action_plan_id=failing_plan.action_plan_id,dry_run_id=dry_a.dry_run_id,
        idempotency_key="authorize-dry-mismatch",trace_id=trace_a)
    require(dry_mismatch.reason_code=="dry_run_plan_hash_mismatch","dry-run hash mismatch did not deny")
    try:
        auth_service.evaluate_execution_authorization(authority=authority,
            action_plan_id=failing_plan.action_plan_id,dry_run_id=failing_dry.dry_run_id,
            idempotency_key="authorize-a",trace_id=trace_a)
        raise AssertionError("authorization key reused for changed plan")
    except IdempotencyConflict:
        pass
    second_decision = uuid4()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO qms.agent_decision(id,tenant_id,organization_id,agent_run_id,recommendation_id,decision_type,payload,confidence,explainability,decision_autonomy,human_gate_required,trace_id) VALUES(%s,%s,%s,%s,%s,'prepare-without-approval','{}',0.8,'{}',3,true,%s)",[str(second_decision),str(phase3.TENANT_A),str(phase3.ORG_A),str(ids_a["run"]),str(ids_a["recommendation"]),str(trace_a)])
    no_approval_plan = prep.prepare_action_plan(identity=identity_a,agent_decision_id=second_decision,
        idempotency_key="prepare-no-approval",trace_id=trace_a,
        **dict(common_plan,target_id="synthetic-no-approval"))
    no_approval_dry = prep.run_action_plan_dry_run(identity=identity_a,action_plan_id=no_approval_plan.action_plan_id,
        expected_affected_objects=[],intended_state_delta={},validation_status="passed",
        precondition_results=[{"identity":"revision","status":"satisfied"}],impact_summary={"impact":"high"},
        actor_id="phase13-worker",trace_id=trace_a)
    denied_no_approval = auth_service.evaluate_execution_authorization(authority=authority,
        action_plan_id=no_approval_plan.action_plan_id,dry_run_id=no_approval_dry.dry_run_id,
        idempotency_key="authorize-no-approval",trace_id=trace_a)
    require(denied_no_approval.reason_code in {"approval_missing","human_gate_cannot_be_bypassed"},
            "high/irreversible action bypassed human gate")
    for outcome in ("reject","request_changes"):
        denied_decision, denied_approval = uuid4(), uuid4()
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO qms.agent_decision(id,tenant_id,organization_id,agent_run_id,recommendation_id,decision_type,payload,confidence,explainability,decision_autonomy,human_gate_required,trace_id) VALUES(%s,%s,%s,%s,%s,%s,'{}',0.8,'{}',3,true,%s)",[str(denied_decision),str(phase3.TENANT_A),str(phase3.ORG_A),str(ids_a["run"]),str(ids_a["recommendation"]),f"prepare-{outcome}",str(trace_a)])
            cursor.execute("INSERT INTO qms.approval(id,tenant_id,organization_id,agent_decision_id,recommendation_id,required_role,decision,decided_by_id,adminapps_user_id_snapshot,actor_type,comments,decided_at,trace_id) VALUES(%s,%s,%s,%s,%s,'quality_approver',%s,%s,%s,'human','denial fixture',statement_timestamp(),%s)",[str(denied_approval),str(phase3.TENANT_A),str(phase3.ORG_A),str(denied_decision),str(ids_a["recommendation"]),outcome,str(ids_a["user"]),str(ids_a["admin_user"]),str(trace_a)])
        denied_plan = prep.prepare_action_plan(identity=identity_a,agent_decision_id=denied_decision,
            idempotency_key=f"prepare-{outcome}",trace_id=trace_a,
            **dict(common_plan,target_id=f"synthetic-{outcome}"))
        denied_dry = prep.run_action_plan_dry_run(identity=identity_a,action_plan_id=denied_plan.action_plan_id,
            expected_affected_objects=[],intended_state_delta={},validation_status="passed",
            precondition_results=[{"identity":"revision","status":"satisfied"}],impact_summary={"impact":"high"},
            actor_id="phase13-worker",trace_id=trace_a)
        denied_result = auth_service.evaluate_execution_authorization(authority=authority,
            action_plan_id=denied_plan.action_plan_id,dry_run_id=denied_dry.dry_run_id,
            idempotency_key=f"authorize-{outcome}",trace_id=trace_a)
        require(denied_result.reason_code==f"effective_approval_{outcome}",f"{outcome} did not deny")
    ambiguous_decision, ambiguous_one, ambiguous_two = uuid4(), uuid4(), uuid4()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO qms.agent_decision(id,tenant_id,organization_id,agent_run_id,recommendation_id,decision_type,payload,confidence,explainability,decision_autonomy,human_gate_required,trace_id) VALUES(%s,%s,%s,%s,%s,'prepare-ambiguous','{}',0.8,'{}',3,true,%s)",[str(ambiguous_decision),str(phase3.TENANT_A),str(phase3.ORG_A),str(ids_a["run"]),str(ids_a["recommendation"]),str(trace_a)])
        cursor.execute("INSERT INTO qms.approval(id,tenant_id,organization_id,agent_decision_id,recommendation_id,required_role,decision,decided_by_id,adminapps_user_id_snapshot,actor_type,comments,decided_at,trace_id) VALUES(%s,%s,%s,%s,%s,'quality_approver','approve',%s,%s,'human','tie',statement_timestamp(),%s),(%s,%s,%s,%s,%s,'quality_approver','reject',%s,%s,'human','tie',statement_timestamp(),%s)",[str(ambiguous_one),str(phase3.TENANT_A),str(phase3.ORG_A),str(ambiguous_decision),str(ids_a["recommendation"]),str(ids_a["user"]),str(ids_a["admin_user"]),str(trace_a),str(ambiguous_two),str(phase3.TENANT_A),str(phase3.ORG_A),str(ambiguous_decision),str(ids_a["recommendation"]),str(ids_a["user"]),str(ids_a["admin_user"]),str(trace_a)])
    with trusted_tenant_context(identity_a,actor_id="phase13-worker",trace_id=trace_a,using="worker"):
        ambiguous_effective, ambiguous_reason = resolve_effective_approval(using="worker",agent_decision_id=ambiguous_decision)
    require(ambiguous_effective is None and ambiguous_reason=="approval_history_ambiguous",
            "ambiguous Approval history did not fail closed")
    try:
        auth_service.evaluate_execution_authorization(authority=authority,action_plan_id=plan_a.action_plan_id,
            dry_run_id=dry_a.dry_run_id,idempotency_key="authorize-rollback",trace_id=trace_a,
            fail_before_commit=True)
        raise AssertionError("authorization rollback fixture succeeded")
    except RuntimeError:
        pass
    with phase3.runtime_transaction("execution_authorizer",phase3.TENANT_A) as cursor:
        cursor.execute("SELECT count(*) FROM qms.execution_authorization")
        require(cursor.fetchone()[0]==1,"authorization rollback left partial state")
    plan_b = prep.prepare_action_plan(identity=identity_b,agent_decision_id=ids_b["decision"],idempotency_key="prepare-b",trace_id=trace_b,**common_plan)
    for alias, expected_a, expected_b in (("app",6,1),("worker",6,1),("execution_authorizer",1,0)):
        table = "execution_authorization" if alias=="execution_authorizer" else "action_plan"
        with phase3.runtime_transaction(alias,phase3.TENANT_A) as cursor:
            cursor.execute(f"SELECT count(*) FROM qms.{table}"); require(cursor.fetchone()[0]==expected_a,f"{alias} tenant A matrix")
        with phase3.runtime_transaction(alias,None) as cursor:
            cursor.execute(f"SELECT count(*) FROM qms.{table}"); require(cursor.fetchone()[0]==0,f"{alias} none matrix")
        with phase3.runtime_transaction(alias,phase3.TENANT_B) as cursor:
            cursor.execute(f"SELECT count(*) FROM qms.{table}"); require(cursor.fetchone()[0]==expected_b,f"{alias} tenant B matrix")
    with connection.cursor() as cursor:
        try:
            cursor.execute("UPDATE qms.action_plan SET target_id='forged' WHERE id=%s",[str(plan_a.action_plan_id)])
            raise AssertionError("authorized ActionPlan mutation succeeded")
        except Exception as exc:
            connection.rollback(); require("immutable" in str(exc).lower(),"unexpected ActionPlan mutation error")
    effective, reason = None, None
    with trusted_tenant_context(identity_a,actor_id="phase13-worker",trace_id=trace_a,using="worker"):
        effective, reason = resolve_effective_approval(using="worker",agent_decision_id=ids_a["decision"])
    require(reason is None and effective.id==ids_a["approval_approve"],"effective Approval resolution failed")

    try:
        with phase3.runtime_transaction("worker", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.execution_authorization")
        raise AssertionError("worker unexpectedly read execution authorization")
    except Exception as exc:
        require("permission denied" in str(exc).lower(), "unexpected worker authorization-read error")
    try:
        with phase3.runtime_transaction("execution_authorizer", phase3.TENANT_A) as cursor:
            cursor.execute("SELECT count(*) FROM qms.execution_authorization")
            raise RuntimeError("intentional Phase 13 rollback context")
    except RuntimeError:
        pass
    with phase3.runtime_transaction("execution_authorizer", None) as cursor:
        cursor.execute("SELECT count(*) FROM qms.execution_authorization")
        require(cursor.fetchone()[0] == 0, "tenant context leaked after rollback")

    phase3.migrate(PHASE12)
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.approval'),to_regclass('qms.action_plan'),to_regclass('qms.action_execution')")
        require(cursor.fetchone() == ("qms.approval",None,None), "Phase 13 reverse damaged Phase 12")
    phase3.migrate(PHASE13)
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('qms.action_plan'),to_regclass('qms.execution_authorization'),to_regclass('qms.action_execution')")
        require(cursor.fetchone() == ("qms.action_plan","qms.execution_authorization",None),
                "Phase 13 second forward/no-execution invariant failed")

    print(json.dumps({
        "status":"PASS", "migration":PHASE13[1], "postgresql":"18.6",
        "rls":"ENABLE+FORCE; populated A/none/B matrix",
        "principal":"execution authorizer LOGIN, non-superuser, NOBYPASSRLS, function-only write",
        "worker_self_authorization":"DENIED", "denied_paths":"reject/request_changes/ambiguous/precondition/policy/dry-run/no-approval PASS",
        "idempotency":"same replay; changed plan conflict PASS", "dry_run_no_side_effect":"PASS",
        "pool_rollback":"PASS",
        "forward_reverse_forward":"PASS", "action_execution":"ABSENT",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)},indent=2),file=sys.stderr)
        raise
