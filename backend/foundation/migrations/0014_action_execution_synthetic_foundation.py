"""Phase 14 synthetic/no-external-effect ActionExecution foundation."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
  app_role text:=current_setting('foundation.app_role',true);
  worker_role text:=current_setting('foundation.worker_role',true);
  human_role text:=current_setting('foundation.human_approver_role',true);
  authorizer_role text:=current_setting('foundation.execution_authorizer_role',true);
  executor_role text:=current_setting('foundation.executor_role',true);
BEGIN
 IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' OR
    human_role IS NULL OR human_role='' OR authorizer_role IS NULL OR authorizer_role='' OR
    executor_role IS NULL OR executor_role='' THEN
   RAISE EXCEPTION 'Phase 14 runtime roles are required';
 END IF;

 CREATE TABLE qms.action_execution (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
  organization_id uuid NOT NULL,
  execution_authorization_id uuid NOT NULL,
  action_plan_id uuid NOT NULL,
  action_plan_hash char(64) NOT NULL,
  executor_type varchar(40) NOT NULL,
  status varchar(24) NOT NULL,
  attempt_number integer NOT NULL,
  retry_of_execution_id uuid NULL,
  precondition_results jsonb NOT NULL DEFAULT '{}'::jsonb,
  idempotency_key varchar(200) NOT NULL,
  trace_id uuid NOT NULL,
  started_at timestamptz NOT NULL,
  completed_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
  CONSTRAINT qms_action_execution_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
  CONSTRAINT qms_action_execution_tenant_idempotency_unique UNIQUE(tenant_id,idempotency_key),
  CONSTRAINT qms_action_execution_authorization_fk FOREIGN KEY(tenant_id,organization_id,execution_authorization_id)
    REFERENCES qms.execution_authorization(tenant_id,organization_id,id) ON DELETE RESTRICT,
  CONSTRAINT qms_action_execution_plan_fk FOREIGN KEY(tenant_id,organization_id,action_plan_id)
    REFERENCES qms.action_plan(tenant_id,organization_id,id) ON DELETE RESTRICT,
  CONSTRAINT qms_action_execution_retry_fk FOREIGN KEY(tenant_id,organization_id,retry_of_execution_id)
    REFERENCES qms.action_execution(tenant_id,organization_id,id) ON DELETE RESTRICT,
  CONSTRAINT qms_action_execution_org_fk FOREIGN KEY(tenant_id,organization_id)
    REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
  CONSTRAINT qms_action_execution_hash CHECK(action_plan_hash ~ '^[0-9a-f]{64}$'),
  CONSTRAINT qms_action_execution_executor CHECK(executor_type='synthetic_noop'),
  CONSTRAINT qms_action_execution_status CHECK(status IN ('running','succeeded','failed')),
  CONSTRAINT qms_action_execution_attempt CHECK(attempt_number>=1),
  CONSTRAINT qms_action_execution_preconditions_shape CHECK(jsonb_typeof(precondition_results)='object'),
  CONSTRAINT qms_action_execution_idempotency_nonblank CHECK(btrim(idempotency_key)<>''),
  CONSTRAINT qms_action_execution_terminal_time CHECK(
    (status='running' AND completed_at IS NULL) OR
    (status IN ('succeeded','failed') AND completed_at IS NOT NULL AND completed_at>=started_at))
 );

 CREATE TABLE qms.action_execution_receipt (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
  organization_id uuid NOT NULL,
  action_execution_id uuid NOT NULL,
  executor_type varchar(40) NOT NULL,
  outcome varchar(40) NOT NULL,
  result jsonb NOT NULL,
  result_hash char(64) NOT NULL,
  action_plan_hash char(64) NOT NULL,
  trace_id uuid NOT NULL,
  started_at timestamptz NOT NULL,
  completed_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
  CONSTRAINT qms_action_execution_receipt_execution_unique UNIQUE(action_execution_id),
  CONSTRAINT qms_action_execution_receipt_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
  CONSTRAINT qms_action_execution_receipt_execution_fk FOREIGN KEY(tenant_id,organization_id,action_execution_id)
    REFERENCES qms.action_execution(tenant_id,organization_id,id) ON DELETE RESTRICT,
  CONSTRAINT qms_action_execution_receipt_org_fk FOREIGN KEY(tenant_id,organization_id)
    REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
  CONSTRAINT qms_action_execution_receipt_executor CHECK(executor_type='synthetic_noop'),
  CONSTRAINT qms_action_execution_receipt_outcome CHECK(outcome IN ('synthetic_noop_succeeded','synthetic_noop_failed')),
  CONSTRAINT qms_action_execution_receipt_result_shape CHECK(jsonb_typeof(result)='object'),
  CONSTRAINT qms_action_execution_receipt_hashes CHECK(result_hash ~ '^[0-9a-f]{64}$' AND action_plan_hash ~ '^[0-9a-f]{64}$'),
  CONSTRAINT qms_action_execution_receipt_time CHECK(completed_at>=started_at),
  CONSTRAINT qms_action_execution_receipt_synthetic CHECK(
    result->>'classification'='NON-PRODUCTION' AND result->>'mode'='SYNTHETIC' AND
    result->>'effect'='NO-OP' AND result->>'business_state_changed'='false')
 );

 CREATE FUNCTION qms.foundation_0014_validate_execution_start() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
 DECLARE a qms.execution_authorization%ROWTYPE; p qms.action_plan%ROWTYPE;
         d qms.action_plan_dry_run%ROWTYPE; parent qms.action_execution%ROWTYPE;
         latest_time timestamptz; latest_outcomes integer;
 BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='ActionExecution delete is forbidden'; END IF;
  IF TG_OP='UPDATE' THEN
   IF OLD.status<>'running' OR NEW.status NOT IN ('succeeded','failed') OR
      NEW.completed_at IS NULL OR
      ROW(NEW.tenant_id,NEW.organization_id,NEW.execution_authorization_id,NEW.action_plan_id,
          NEW.action_plan_hash,NEW.executor_type,NEW.attempt_number,NEW.retry_of_execution_id,
          NEW.precondition_results,NEW.idempotency_key,NEW.trace_id,NEW.started_at,NEW.created_at)
      IS DISTINCT FROM
      ROW(OLD.tenant_id,OLD.organization_id,OLD.execution_authorization_id,OLD.action_plan_id,
          OLD.action_plan_hash,OLD.executor_type,OLD.attempt_number,OLD.retry_of_execution_id,
          OLD.precondition_results,OLD.idempotency_key,OLD.trace_id,OLD.started_at,OLD.created_at) OR
      current_setting('foundation.execution_completion',true) IS DISTINCT FROM OLD.id::text THEN
    RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='invalid or ungoverned ActionExecution transition';
   END IF;
   RETURN NEW;
  END IF;
  SELECT * INTO STRICT a FROM qms.execution_authorization WHERE id=NEW.execution_authorization_id;
  SELECT * INTO STRICT p FROM qms.action_plan WHERE id=NEW.action_plan_id;
  SELECT * INTO STRICT d FROM qms.action_plan_dry_run WHERE id=a.dry_run_id;
  IF NEW.status<>'running' OR NEW.completed_at IS NOT NULL OR NEW.executor_type<>'synthetic_noop' OR
     a.outcome<>'authorized' OR a.tenant_id<>NEW.tenant_id OR a.organization_id<>NEW.organization_id OR
     a.action_plan_id<>NEW.action_plan_id OR a.action_plan_hash<>NEW.action_plan_hash OR
     p.tenant_id<>NEW.tenant_id OR p.organization_id<>NEW.organization_id OR p.action_plan_hash<>NEW.action_plan_hash OR
     a.agent_decision_id<>p.agent_decision_id OR a.recommendation_id<>p.recommendation_id OR
     a.impact<>p.impact OR a.reversibility<>p.reversibility OR
     p.required_autonomy<3 OR p.required_autonomy>a.effective_autonomy_ceiling OR
     (p.required_autonomy=4 AND (p.reversibility<>'reversible' OR p.impact='high')) OR
     d.action_plan_id<>p.id OR d.action_plan_hash<>p.action_plan_hash OR d.validation_status<>'passed' THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionExecution exact authorization/plan/policy validation failed';
  END IF;
  SELECT max(decided_at) INTO latest_time FROM qms.approval WHERE agent_decision_id=a.agent_decision_id;
  SELECT count(DISTINCT decision) INTO latest_outcomes FROM qms.approval
   WHERE agent_decision_id=a.agent_decision_id AND decided_at=latest_time;
  IF latest_outcomes<>1 OR NOT EXISTS(
    SELECT 1 FROM qms.approval ap WHERE ap.id=a.effective_approval_id AND
    ap.agent_decision_id=a.agent_decision_id AND ap.decided_at=latest_time AND ap.decision='approve') THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionExecution effective Approval validation failed';
  END IF;
  IF EXISTS(
    SELECT 1 FROM jsonb_array_elements(p.preconditions) pc
    WHERE COALESCE((pc->>'required')::boolean,true) AND
          COALESCE(NEW.precondition_results->>(pc->>'identity'),'unknown')<>'satisfied') OR
     EXISTS(SELECT 1 FROM jsonb_object_keys(NEW.precondition_results) k
            WHERE NOT EXISTS(SELECT 1 FROM jsonb_array_elements(p.preconditions) pc WHERE pc->>'identity'=k)) THEN
   RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionExecution precondition revalidation failed';
  END IF;
  IF NEW.retry_of_execution_id IS NULL THEN
   IF NEW.attempt_number<>1 THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='initial attempt must be one'; END IF;
  ELSE
   SELECT * INTO STRICT parent FROM qms.action_execution WHERE id=NEW.retry_of_execution_id;
   IF parent.status<>'failed' OR parent.execution_authorization_id<>NEW.execution_authorization_id OR
      parent.action_plan_hash<>NEW.action_plan_hash OR NEW.attempt_number<>parent.attempt_number+1 THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='invalid ActionExecution retry lineage';
   END IF;
  END IF;
  RETURN NEW;
 END $fn$;
 CREATE TRIGGER qms_action_execution_validate BEFORE INSERT OR UPDATE OR DELETE ON qms.action_execution
 FOR EACH ROW EXECUTE FUNCTION qms.foundation_0014_validate_execution_start();

 CREATE FUNCTION qms.foundation_0014_reject_receipt_mutation() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog AS $fn$
 BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='ActionExecutionReceipt is append-only'; END $fn$;
 CREATE TRIGGER qms_action_execution_receipt_immutable BEFORE UPDATE OR DELETE ON qms.action_execution_receipt
 FOR EACH ROW EXECUTE FUNCTION qms.foundation_0014_reject_receipt_mutation();

 ALTER TABLE qms.action_execution ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.action_execution FORCE ROW LEVEL SECURITY;
 ALTER TABLE qms.action_execution_receipt ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.action_execution_receipt FORCE ROW LEVEL SECURITY;
 EXECUTE format('CREATE POLICY qms_action_execution_select ON qms.action_execution FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_insert ON qms.action_execution FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_update ON qms.action_execution FOR UPDATE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_delete ON qms.action_execution FOR DELETE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_migrator ON qms.action_execution FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
 EXECUTE format('CREATE POLICY qms_action_execution_receipt_select ON qms.action_execution_receipt FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_receipt_insert ON qms.action_execution_receipt FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_receipt_update ON qms.action_execution_receipt FOR UPDATE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_receipt_delete ON qms.action_execution_receipt FOR DELETE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_receipt_migrator ON qms.action_execution_receipt FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);

 EXECUTE format('GRANT USAGE ON SCHEMA qms,governance,eventing,audit TO %I',executor_role);
 EXECUTE format('GRANT SELECT ON qms.organization,qms.user_projection,qms.recommendation,qms.agent_run,qms.agent_decision,qms.approval,qms.action_plan,qms.action_plan_dry_run,qms.execution_authorization,qms.action_execution,qms.action_execution_receipt,governance.model_policy,governance.agent_definition TO %I',executor_role);
 EXECUTE format('GRANT SELECT ON qms.action_execution,qms.action_execution_receipt TO %I',app_role);

 DROP POLICY foundation_organization_select ON qms.organization;
 DROP POLICY foundation_user_projection_select ON qms.user_projection;
 DROP POLICY qms_recommendation_select ON qms.recommendation;
 DROP POLICY qms_agent_run_select ON qms.agent_run;
 DROP POLICY qms_agent_decision_select ON qms.agent_decision;
 DROP POLICY qms_approval_select ON qms.approval;
 DROP POLICY qms_action_plan_select ON qms.action_plan;
 DROP POLICY qms_action_plan_dry_run_select ON qms.action_plan_dry_run;
 DROP POLICY qms_execution_authorization_select ON qms.execution_authorization;
 EXECUTE format('CREATE POLICY foundation_organization_select ON qms.organization FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY foundation_user_projection_select ON qms.user_projection FOR SELECT TO %I,%I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY qms_recommendation_select ON qms.recommendation FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY qms_agent_run_select ON qms.agent_run FOR SELECT TO %I,%I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY qms_agent_decision_select ON qms.agent_decision FOR SELECT TO %I,%I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY qms_approval_select ON qms.approval FOR SELECT TO %I,%I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY qms_action_plan_select ON qms.action_plan FOR SELECT TO %I,%I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY qms_action_plan_dry_run_select ON qms.action_plan_dry_run FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY qms_execution_authorization_select ON qms.execution_authorization FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,authorizer_role,executor_role);

 DROP POLICY foundation_domain_event_select ON eventing.domain_event;
 DROP POLICY foundation_domain_event_insert ON eventing.domain_event;
 DROP POLICY foundation_outbox_select ON eventing.transactional_outbox;
 DROP POLICY foundation_outbox_insert ON eventing.transactional_outbox;
 EXECUTE format('CREATE POLICY foundation_domain_event_select ON eventing.domain_event FOR SELECT TO %I,%I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I,%I,%I,%I,%I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY foundation_outbox_select ON eventing.transactional_outbox FOR SELECT TO %I,%I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I,%I,%I,%I,%I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role,executor_role);
 EXECUTE format('GRANT SELECT,INSERT ON eventing.domain_event,eventing.transactional_outbox TO %I',executor_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) TO %I',executor_role);
END $migration$;

CREATE FUNCTION qms.foundation_0014_start_action_execution(
 p_id uuid,p_tenant_id uuid,p_organization_id uuid,p_authorization_id uuid,p_action_plan_id uuid,
 p_action_plan_hash text,p_executor_type text,p_status text,p_retry_of uuid,p_attempt integer,
 p_precondition_results jsonb,p_idempotency_key text,p_trace_id uuid,p_started_at timestamptz,p_actor_id text
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,qms AS $fn$
BEGIN
 IF p_tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid THEN
  RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='execution tenant context mismatch';
 END IF;
 INSERT INTO qms.action_execution(id,tenant_id,organization_id,execution_authorization_id,
  action_plan_id,action_plan_hash,executor_type,status,retry_of_execution_id,attempt_number,
  precondition_results,idempotency_key,trace_id,started_at)
 VALUES(p_id,p_tenant_id,p_organization_id,p_authorization_id,p_action_plan_id,p_action_plan_hash,
  p_executor_type,p_status,p_retry_of,p_attempt,p_precondition_results,p_idempotency_key,p_trace_id,p_started_at);
 RETURN p_id;
END $fn$;

CREATE FUNCTION qms.foundation_0014_complete_action_execution(
 p_execution_id uuid,p_receipt_id uuid,p_tenant_id uuid,p_organization_id uuid,p_status text,
 p_outcome text,p_executor_type text,p_action_plan_hash text,p_result_hash text,p_result jsonb,
 p_trace_id uuid,p_started_at timestamptz,p_completed_at timestamptz,p_actor_id text,p_contract text
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,qms AS $fn$
BEGIN
 IF p_contract<>'phase14' OR p_tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid THEN
  RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='execution completion context mismatch';
 END IF;
 PERFORM set_config('foundation.execution_completion',p_execution_id::text,true);
 UPDATE qms.action_execution SET status=p_status,completed_at=p_completed_at
  WHERE id=p_execution_id AND tenant_id=p_tenant_id AND organization_id=p_organization_id
    AND status='running' AND executor_type=p_executor_type AND action_plan_hash=p_action_plan_hash
    AND trace_id=p_trace_id AND started_at=p_started_at;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='execution is not completable'; END IF;
 IF (p_status='succeeded' AND p_outcome<>'synthetic_noop_succeeded') OR
    (p_status='failed' AND p_outcome<>'synthetic_noop_failed') THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='execution outcome mismatch';
 END IF;
 INSERT INTO qms.action_execution_receipt(id,tenant_id,organization_id,action_execution_id,
  executor_type,outcome,result,result_hash,action_plan_hash,trace_id,started_at,completed_at)
 VALUES(p_receipt_id,p_tenant_id,p_organization_id,p_execution_id,p_executor_type,p_outcome,
  p_result,p_result_hash,p_action_plan_hash,p_trace_id,p_started_at,p_completed_at);
 RETURN p_receipt_id;
END $fn$;

REVOKE ALL ON FUNCTION qms.foundation_0014_start_action_execution(uuid,uuid,uuid,uuid,uuid,text,text,text,uuid,integer,jsonb,text,uuid,timestamptz,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0014_complete_action_execution(uuid,uuid,uuid,uuid,text,text,text,text,text,jsonb,uuid,timestamptz,timestamptz,text,text) FROM PUBLIC;
DO $grant$ DECLARE r text:=current_setting('foundation.executor_role',true); BEGIN
 EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0014_start_action_execution(uuid,uuid,uuid,uuid,uuid,text,text,text,uuid,integer,jsonb,text,uuid,timestamptz,text) TO %I',r);
 EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0014_complete_action_execution(uuid,uuid,uuid,uuid,text,text,text,text,text,jsonb,uuid,timestamptz,timestamptz,text,text) TO %I',r);
END $grant$;
"""


REVERSE_SQL = r"""
DO $migration$
DECLARE app_role text:=current_setting('foundation.app_role',true); worker_role text:=current_setting('foundation.worker_role',true); human_role text:=current_setting('foundation.human_approver_role',true); authorizer_role text:=current_setting('foundation.execution_authorizer_role',true); executor_role text:=current_setting('foundation.executor_role',true);
BEGIN
 IF executor_role IS NOT NULL AND executor_role<>'' THEN
  EXECUTE format('REVOKE SELECT ON qms.organization,qms.user_projection,qms.recommendation,qms.agent_run,qms.agent_decision,qms.approval,qms.action_plan,qms.action_plan_dry_run,qms.execution_authorization,qms.action_execution,qms.action_execution_receipt,governance.model_policy,governance.agent_definition FROM %I',executor_role);
  EXECUTE format('REVOKE SELECT,INSERT ON eventing.domain_event,eventing.transactional_outbox FROM %I',executor_role);
  EXECUTE format('REVOKE EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) FROM %I',executor_role);
 END IF;
 DROP POLICY foundation_organization_select ON qms.organization;
 DROP POLICY foundation_user_projection_select ON qms.user_projection;
 DROP POLICY qms_recommendation_select ON qms.recommendation;
 DROP POLICY qms_agent_run_select ON qms.agent_run;
 DROP POLICY qms_agent_decision_select ON qms.agent_decision;
 DROP POLICY qms_approval_select ON qms.approval;
 DROP POLICY qms_action_plan_select ON qms.action_plan;
 DROP POLICY qms_action_plan_dry_run_select ON qms.action_plan_dry_run;
 DROP POLICY qms_execution_authorization_select ON qms.execution_authorization;
 EXECUTE format('CREATE POLICY foundation_organization_select ON qms.organization FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role);
 EXECUTE format('CREATE POLICY foundation_user_projection_select ON qms.user_projection FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
 EXECUTE format('CREATE POLICY qms_recommendation_select ON qms.recommendation FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role);
 EXECUTE format('CREATE POLICY qms_agent_run_select ON qms.agent_run FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
 EXECUTE format('CREATE POLICY qms_agent_decision_select ON qms.agent_decision FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
 EXECUTE format('CREATE POLICY qms_approval_select ON qms.approval FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
 EXECUTE format('CREATE POLICY qms_action_plan_select ON qms.action_plan FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
 EXECUTE format('CREATE POLICY qms_action_plan_dry_run_select ON qms.action_plan_dry_run FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role);
 EXECUTE format('CREATE POLICY qms_execution_authorization_select ON qms.execution_authorization FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,authorizer_role);
 DROP POLICY foundation_domain_event_select ON eventing.domain_event;
 DROP POLICY foundation_domain_event_insert ON eventing.domain_event;
 DROP POLICY foundation_outbox_select ON eventing.transactional_outbox;
 DROP POLICY foundation_outbox_insert ON eventing.transactional_outbox;
 EXECUTE format('CREATE POLICY foundation_domain_event_select ON eventing.domain_event FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
 EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I,%I,%I,%I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
 EXECUTE format('CREATE POLICY foundation_outbox_select ON eventing.transactional_outbox FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
 EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I,%I,%I,%I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
END $migration$;
DROP FUNCTION qms.foundation_0014_complete_action_execution(uuid,uuid,uuid,uuid,text,text,text,text,text,jsonb,uuid,timestamptz,timestamptz,text,text);
DROP FUNCTION qms.foundation_0014_start_action_execution(uuid,uuid,uuid,uuid,uuid,text,text,text,uuid,integer,jsonb,text,uuid,timestamptz,text);
DROP TABLE qms.action_execution_receipt;
DROP TABLE qms.action_execution;
DROP FUNCTION qms.foundation_0014_reject_receipt_mutation();
DROP FUNCTION qms.foundation_0014_validate_execution_start();
"""


def apply_phase14(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase14(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0013_action_execution_preparation_authorization_foundation")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase14, reverse_phase14)],
        state_operations=[
            migrations.CreateModel(name="ActionExecution", fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
                ("action_plan_hash",models.CharField(max_length=64)),
                ("executor_type",models.CharField(choices=[("synthetic_noop","Synthetic no-op")],max_length=40)),
                ("status",models.CharField(choices=[("running","Running"),("succeeded","Succeeded"),("failed","Failed")],max_length=24)),
                ("attempt_number",models.PositiveIntegerField(default=1)),
                ("precondition_results",models.JSONField(default=dict)),
                ("idempotency_key",models.CharField(max_length=200)),("trace_id",models.UUIDField()),
                ("started_at",models.DateTimeField()),("completed_at",models.DateTimeField(blank=True,null=True)),
                ("created_at",models.DateTimeField(auto_now_add=True)),
                ("tenant",models.ForeignKey(db_column="tenant_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.tenantprojection")),
                ("organization",models.ForeignKey(db_column="organization_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.organization")),
                ("execution_authorization",models.ForeignKey(db_column="execution_authorization_id",on_delete=django.db.models.deletion.PROTECT,related_name="action_executions",to="foundation.executionauthorization")),
                ("action_plan",models.ForeignKey(db_column="action_plan_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.actionplan")),
                ("retry_of",models.ForeignKey(blank=True,db_column="retry_of_execution_id",null=True,on_delete=django.db.models.deletion.PROTECT,related_name="retry_attempts",to="foundation.actionexecution")),
            ],options={"managed":False,"db_table":'qms"."action_execution'}),
            migrations.CreateModel(name="ActionExecutionReceipt", fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
                ("executor_type",models.CharField(choices=[("synthetic_noop","Synthetic no-op")],max_length=40)),
                ("outcome",models.CharField(choices=[("synthetic_noop_succeeded","Synthetic no-op succeeded"),("synthetic_noop_failed","Synthetic no-op failed")],max_length=40)),
                ("result",models.JSONField(default=dict)),("result_hash",models.CharField(max_length=64)),
                ("action_plan_hash",models.CharField(max_length=64)),("trace_id",models.UUIDField()),
                ("started_at",models.DateTimeField()),("completed_at",models.DateTimeField()),
                ("created_at",models.DateTimeField(auto_now_add=True)),
                ("tenant",models.ForeignKey(db_column="tenant_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.tenantprojection")),
                ("organization",models.ForeignKey(db_column="organization_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.organization")),
                ("action_execution",models.OneToOneField(db_column="action_execution_id",on_delete=django.db.models.deletion.PROTECT,related_name="receipt",to="foundation.actionexecution")),
            ],options={"managed":False,"db_table":'qms"."action_execution_receipt'}),
        ],
    )]

