"""Phase 16 first controlled internal QMS mutation POC.

The database objects are deliberately action-specific at the executor boundary.
The shared Opportunity transition function remains private from EXECUTOR and is
also the implementation used by the normal application command.
"""

from django.db import migrations, models


FORWARD_SQL = r"""
DO $roles$
DECLARE owner_role text:=current_setting('foundation.qms_action_owner_role',true);
        app_role text:=current_setting('foundation.app_role',true);
        executor_role text:=current_setting('foundation.executor_role',true);
BEGIN
 IF owner_role IS NULL OR owner_role='' OR app_role IS NULL OR app_role='' OR
    executor_role IS NULL OR executor_role='' THEN
  RAISE EXCEPTION 'Phase 16 owner/app/executor roles are required';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=owner_role AND NOT rolcanlogin
   AND NOT rolsuper AND NOT rolbypassrls AND NOT rolinherit) THEN
  RAISE EXCEPTION 'Phase 16 function owner must be NOLOGIN NOSUPERUSER NOBYPASSRLS NOINHERIT';
 END IF;
END $roles$;

CREATE FUNCTION qms.foundation_0015_canonical_json_value(p_value jsonb)
RETURNS text LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE
SET search_path=pg_catalog AS $fn$
DECLARE kind text; item record; pieces text:=''; separator text:='';
BEGIN
 kind:=jsonb_typeof(p_value);
 IF kind='object' THEN
  FOR item IN SELECT key,value FROM jsonb_each(p_value) ORDER BY key LOOP
   pieces:=pieces||separator||to_jsonb(item.key)::text||':'||
     qms.foundation_0015_canonical_json_value(item.value);
   separator:=',';
  END LOOP;
  RETURN '{'||pieces||'}';
 ELSIF kind='array' THEN
  FOR item IN SELECT value FROM jsonb_array_elements(p_value) WITH ORDINALITY a(value,n)
              ORDER BY n LOOP
   pieces:=pieces||separator||qms.foundation_0015_canonical_json_value(item.value);
   separator:=',';
  END LOOP;
  RETURN '['||pieces||']';
 END IF;
 RETURN p_value::text;
END $fn$;

CREATE FUNCTION qms.foundation_0015_canonical_hash(p_value jsonb)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog AS $fn$
 SELECT encode(sha256(convert_to(
   '{"canonicalization":"iso-smart-canonical-json-v1","value":'||
   qms.foundation_0015_canonical_json_value(p_value)||'}','UTF8')),'hex')
$fn$;

CREATE FUNCTION qms.foundation_0015_opportunity_state_hash(
 p_tenant uuid,p_organization uuid,p_lineage uuid,p_revision_id uuid,p_revision integer,
 p_process uuid,p_hypothesis text,p_benefit text,p_feasibility text,p_status text
) RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog AS $fn$
 SELECT qms.foundation_0015_canonical_hash(jsonb_build_object(
  'canonicalization','controlled-opportunity-state-v1','tenant_id',p_tenant::text,
  'organization_id',p_organization::text,'lineage_id',p_lineage::text,
  'revision_id',p_revision_id::text,'revision',p_revision,'process_id',p_process::text,
  'hypothesis',p_hypothesis,'benefit',p_benefit,'feasibility',p_feasibility,
  'status',p_status))
$fn$;

CREATE FUNCTION qms.foundation_0015_apply_opportunity_status_transition(
 p_expected_revision_id uuid,p_new_revision_id uuid,p_desired_status text,p_actor_id text,
 p_trace_id uuid,p_change_reason text,p_actor_type text
) RETURNS TABLE(revision_id uuid,lineage_id uuid,event_id uuid,outbox_id uuid,
 audit_id uuid,trace_id uuid)
LANGUAGE plpgsql SECURITY DEFINER VOLATILE SET search_path=pg_catalog,pg_temp AS $fn$
DECLARE prior qms.opportunity%ROWTYPE; created qms.opportunity%ROWTYPE;
        v_event uuid:=uuidv7(); v_outbox uuid:=uuidv7(); v_audit uuid;
        v_version bigint; v_when timestamptz:=statement_timestamp();
        v_before jsonb; v_after jsonb; v_payload jsonb; v_metadata jsonb;
        v_tenant uuid:=NULLIF(current_setting('app.tenant_id',true),'')::uuid;
BEGIN
 IF v_tenant IS NULL OR p_desired_status IS NULL OR btrim(p_desired_status)='' OR
    p_actor_id IS NULL OR btrim(p_actor_id)='' OR p_trace_id IS NULL THEN
  RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Opportunity transition context is incomplete';
 END IF;
 SELECT * INTO STRICT prior FROM qms.opportunity
  WHERE id=p_expected_revision_id AND tenant_id=v_tenant FOR UPDATE;
 IF EXISTS(SELECT 1 FROM qms.opportunity WHERE previous_revision_id=prior.id) THEN
  RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='only the current Opportunity revision can be revised';
 END IF;
 IF current_setting('foundation.phase16_fail_at',true)='before_revision_insert' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 INSERT INTO qms.opportunity(id,tenant_id,organization_id,lineage_id,revision,
  previous_revision_id,process_id,hypothesis,benefit,feasibility,status,change_reason)
 VALUES(p_new_revision_id,prior.tenant_id,prior.organization_id,prior.lineage_id,
  prior.revision+1,prior.id,prior.process_id,prior.hypothesis,prior.benefit,
  prior.feasibility,p_desired_status,p_change_reason) RETURNING * INTO created;
 IF current_setting('foundation.phase16_fail_at',true)='after_revision_insert' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;

 v_before:=jsonb_build_object('revision',prior.revision,'process_id',prior.process_id::text,
  'hypothesis',prior.hypothesis,'benefit',prior.benefit,'feasibility',prior.feasibility,
  'status',prior.status);
 v_after:=jsonb_build_object('revision',created.revision,'process_id',created.process_id::text,
  'hypothesis',created.hypothesis,'benefit',created.benefit,'feasibility',created.feasibility,
  'status',created.status);
 v_payload:=jsonb_build_object('lineage_id',prior.lineage_id::text,
  'previous_revision_id',prior.id::text,'revision_id',created.id::text,
  'changes',jsonb_build_object('status',jsonb_build_object('before',prior.status,'after',created.status)),
  'revision',created.revision);
 PERFORM pg_advisory_xact_lock(hashtextextended(
  prior.tenant_id::text||':opportunity:'||prior.lineage_id::text,0));
 SELECT COALESCE(max(aggregate_version),0)+1 INTO v_version
  FROM eventing.domain_event WHERE aggregate_type='opportunity' AND aggregate_id=prior.lineage_id;
 INSERT INTO eventing.domain_event(event_id,tenant_id,event_type,schema_version,
  aggregate_type,aggregate_id,aggregate_version,occurred_at,trace_id,source,payload,payload_hash)
 VALUES(v_event,prior.tenant_id,'opportunity.status_changed',1,'opportunity',prior.lineage_id,
  v_version,v_when,p_trace_id,'iso-smart-qms',v_payload,qms.foundation_0015_canonical_hash(v_payload));
 IF current_setting('foundation.phase16_fail_at',true)='after_opportunity_event' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 INSERT INTO eventing.transactional_outbox(id,tenant_id,domain_event_id,status,
  publish_attempts,available_at) VALUES(v_outbox,prior.tenant_id,v_event,'pending',0,v_when);
 IF current_setting('foundation.phase16_fail_at',true)='after_opportunity_outbox' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 v_metadata:=jsonb_build_object('event_id',v_event::text,'schema_version',1);
 SELECT audit.append_immutable_audit(prior.tenant_id,'opportunity',prior.lineage_id,
  p_actor_type,p_actor_id,'opportunity.status_changed','opportunity',prior.lineage_id,
  p_trace_id,v_when,qms.foundation_0015_canonical_hash(v_before),
  qms.foundation_0015_canonical_hash(v_after),
  '{"canonicalization":"iso-smart-canonical-json-v1","value":'||
    qms.foundation_0015_canonical_json_value(v_metadata)||'}') INTO v_audit;
 IF current_setting('foundation.phase16_fail_at',true)='after_opportunity_audit' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 RETURN QUERY SELECT created.id,prior.lineage_id,v_event,v_outbox,v_audit,p_trace_id;
END $fn$;

ALTER TABLE qms.action_execution DROP CONSTRAINT qms_action_execution_executor;
ALTER TABLE qms.action_execution ADD CONSTRAINT qms_action_execution_executor
 CHECK(executor_type IN ('synthetic_noop','controlled_opportunity'));
ALTER TABLE qms.action_execution_receipt DROP CONSTRAINT qms_action_execution_receipt_executor;
ALTER TABLE qms.action_execution_receipt ADD CONSTRAINT qms_action_execution_receipt_executor
 CHECK(executor_type IN ('synthetic_noop','controlled_opportunity'));
ALTER TABLE qms.action_execution_receipt DROP CONSTRAINT qms_action_execution_receipt_outcome;
ALTER TABLE qms.action_execution_receipt ADD CONSTRAINT qms_action_execution_receipt_outcome CHECK(
 outcome IN ('synthetic_noop_succeeded','synthetic_noop_failed','opportunity_deferred',
             'opportunity_evaluation_resumed'));
ALTER TABLE qms.action_execution_receipt DROP CONSTRAINT qms_action_execution_receipt_synthetic;
ALTER TABLE qms.action_execution_receipt ADD CONSTRAINT qms_action_execution_receipt_contract CHECK(
 (executor_type='synthetic_noop' AND result->>'classification'='NON-PRODUCTION' AND
  result->>'mode'='SYNTHETIC' AND result->>'effect'='NO-OP' AND
  result->>'business_state_changed'='false') OR
 (executor_type='controlled_opportunity' AND result->>'classification'='CONTROLLED-QMS-POC' AND
  result->>'business_state_changed'='true' AND result->>'effectiveness_claimed'='false'));

CREATE OR REPLACE FUNCTION qms.foundation_0014_validate_execution_start() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
DECLARE a qms.execution_authorization%ROWTYPE; p qms.action_plan%ROWTYPE;
        d qms.action_plan_dry_run%ROWTYPE; parent qms.action_execution%ROWTYPE;
        latest_time timestamptz; latest_outcomes integer;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='ActionExecution delete is forbidden'; END IF;
 IF TG_OP='UPDATE' THEN
  IF OLD.status<>'running' OR NEW.status NOT IN ('succeeded','failed') OR NEW.completed_at IS NULL OR
     ROW(NEW.tenant_id,NEW.organization_id,NEW.execution_authorization_id,NEW.action_plan_id,
       NEW.action_plan_hash,NEW.executor_type,NEW.attempt_number,NEW.retry_of_execution_id,
       NEW.precondition_results,NEW.idempotency_key,NEW.trace_id,NEW.started_at,NEW.created_at)
     IS DISTINCT FROM ROW(OLD.tenant_id,OLD.organization_id,OLD.execution_authorization_id,
       OLD.action_plan_id,OLD.action_plan_hash,OLD.executor_type,OLD.attempt_number,
       OLD.retry_of_execution_id,OLD.precondition_results,OLD.idempotency_key,OLD.trace_id,
       OLD.started_at,OLD.created_at) OR
     current_setting('foundation.execution_completion',true) IS DISTINCT FROM OLD.id::text THEN
   RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='invalid or ungoverned ActionExecution transition';
  END IF; RETURN NEW;
 END IF;
 SELECT * INTO STRICT a FROM qms.execution_authorization WHERE id=NEW.execution_authorization_id;
 SELECT * INTO STRICT p FROM qms.action_plan WHERE id=NEW.action_plan_id;
 SELECT * INTO STRICT d FROM qms.action_plan_dry_run WHERE id=a.dry_run_id;
 IF NEW.status<>'running' OR NEW.completed_at IS NOT NULL OR
    NEW.executor_type NOT IN ('synthetic_noop','controlled_opportunity') OR
    (NEW.executor_type='controlled_opportunity' AND p.action_type NOT IN
      ('opportunity.defer_evaluation','opportunity.resume_evaluation')) OR
    a.outcome<>'authorized' OR a.tenant_id<>NEW.tenant_id OR a.organization_id<>NEW.organization_id OR
    a.action_plan_id<>NEW.action_plan_id OR a.action_plan_hash<>NEW.action_plan_hash OR
    p.tenant_id<>NEW.tenant_id OR p.organization_id<>NEW.organization_id OR
    p.action_plan_hash<>NEW.action_plan_hash OR a.agent_decision_id<>p.agent_decision_id OR
    a.recommendation_id<>p.recommendation_id OR a.impact<>p.impact OR
    a.reversibility<>p.reversibility OR p.required_autonomy<3 OR
    p.required_autonomy>a.effective_autonomy_ceiling OR
    (p.required_autonomy=4 AND (p.reversibility<>'reversible' OR p.impact='high')) OR
    d.action_plan_id<>p.id OR d.action_plan_hash<>p.action_plan_hash OR d.validation_status<>'passed' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionExecution exact authorization/plan/policy validation failed';
 END IF;
 SELECT max(decided_at) INTO latest_time FROM qms.approval WHERE agent_decision_id=a.agent_decision_id;
 SELECT count(DISTINCT decision) INTO latest_outcomes FROM qms.approval
  WHERE agent_decision_id=a.agent_decision_id AND decided_at=latest_time;
 IF latest_outcomes<>1 OR NOT EXISTS(SELECT 1 FROM qms.approval ap
   WHERE ap.id=a.effective_approval_id AND ap.agent_decision_id=a.agent_decision_id
   AND ap.decided_at=latest_time AND ap.decision='approve') THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionExecution effective Approval validation failed';
 END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(p.preconditions) pc
   WHERE COALESCE((pc->>'required')::boolean,true) AND
   COALESCE(NEW.precondition_results->>(pc->>'identity'),'unknown')<>'satisfied') OR
   EXISTS(SELECT 1 FROM jsonb_object_keys(NEW.precondition_results) k WHERE NOT EXISTS(
    SELECT 1 FROM jsonb_array_elements(p.preconditions) pc WHERE pc->>'identity'=k)) THEN
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

CREATE FUNCTION qms.foundation_0015_controlled_opportunity_execution(
 p_authorization_id uuid,p_idempotency_key text,p_action_type text
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
DECLARE v_tenant uuid:=NULLIF(current_setting('app.tenant_id',true),'')::uuid;
 a qms.execution_authorization%ROWTYPE; p qms.action_plan%ROWTYPE;
 d qms.action_plan_dry_run%ROWTYPE; dec qms.agent_decision%ROWTYPE;
 run qms.agent_run%ROWTYPE; existing qms.action_execution%ROWTYPE;
 prior qms.opportunity%ROWTYPE; transitioned record; v_execution uuid:=uuidv7();
 v_receipt uuid:=uuidv7(); v_started timestamptz:=statement_timestamp();
 v_completed timestamptz; v_source text; v_destination text; v_outcome text;
 v_plan_hash text; v_state_hash text; v_result jsonb; v_result_hash text;
 v_event uuid; v_outbox uuid; v_audit uuid; v_version bigint; v_meta jsonb;
 v_preconditions jsonb:='{}'::jsonb; pc jsonb;
BEGIN
 IF v_tenant IS NULL OR p_idempotency_key IS NULL OR btrim(p_idempotency_key)='' OR
    p_action_type NOT IN ('opportunity.defer_evaluation','opportunity.resume_evaluation') THEN
  RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='controlled execution context denied';
 END IF;
 SELECT * INTO existing FROM qms.action_execution
  WHERE tenant_id=v_tenant AND idempotency_key=p_idempotency_key FOR UPDATE;
 IF FOUND THEN
  IF existing.execution_authorization_id<>p_authorization_id OR
     existing.executor_type<>'controlled_opportunity' THEN
   RAISE EXCEPTION USING ERRCODE='23505',MESSAGE='controlled execution idempotency conflict';
  END IF;
  SELECT result INTO STRICT v_result FROM qms.action_execution_receipt
   WHERE action_execution_id=existing.id;
  RETURN v_result||jsonb_build_object('replayed',true);
 END IF;
 SELECT * INTO STRICT a FROM qms.execution_authorization
  WHERE id=p_authorization_id AND tenant_id=v_tenant;
 SELECT * INTO STRICT p FROM qms.action_plan WHERE id=a.action_plan_id;
 SELECT * INTO STRICT d FROM qms.action_plan_dry_run WHERE id=a.dry_run_id;
 SELECT * INTO STRICT dec FROM qms.agent_decision WHERE id=a.agent_decision_id;
 SELECT * INTO STRICT run FROM qms.agent_run WHERE id=a.agent_run_id;
 v_plan_hash:=qms.foundation_0015_canonical_hash(jsonb_build_object(
  'canonicalization','iso-smart-action-plan-v1','organization_id',p.organization_id::text,
  'agent_decision_id',p.agent_decision_id::text,'recommendation_id',p.recommendation_id::text,
  'action_type',p.action_type,'target',jsonb_build_object('type',p.target_type,'id',p.target_id),
  'parameters',p.parameters,'impact',p.impact,'reversibility',p.reversibility,
  'preconditions',p.preconditions,'dry_run_supported',p.dry_run_supported,
  'required_autonomy','A'||p.required_autonomy::text));
 IF a.outcome<>'authorized' OR p.action_type<>p_action_type OR p.target_type<>'Opportunity' OR
    p.impact<>'standard' OR p.reversibility<>'reversible' OR p.required_autonomy<>3 OR
    p.parameters->>'policy_id'<>'controlled-qms-action-policy/v1' OR
    p.parameters->>'compensation_action_type'<>'opportunity.resume_evaluation' OR
    v_plan_hash<>p.action_plan_hash OR p.action_plan_hash<>a.action_plan_hash OR
    a.organization_id<>p.organization_id OR a.agent_decision_id<>p.agent_decision_id OR
    a.recommendation_id<>p.recommendation_id OR a.agent_run_id<>dec.agent_run_id OR
    a.model_policy_id<>run.model_policy_id OR a.agent_definition_id<>run.agent_definition_id OR
    a.effective_autonomy_ceiling<3 OR run.effective_autonomy_ceiling<3 OR
    dec.decision_autonomy<3 OR d.action_plan_id<>p.id OR d.action_plan_hash<>p.action_plan_hash OR
    d.validation_status<>'passed' OR NOT EXISTS(SELECT 1 FROM governance.model_policy mp
      JOIN governance.agent_definition ad ON ad.id=a.agent_definition_id
      WHERE mp.id=a.model_policy_id AND mp.status='published' AND ad.status='published'
      AND ad.model_policy_id=mp.id) OR NOT EXISTS(SELECT 1 FROM qms.approval ap
      WHERE ap.id=a.effective_approval_id AND ap.decision='approve' AND
      ap.agent_decision_id=a.agent_decision_id AND ap.decided_at=(SELECT max(decided_at)
       FROM qms.approval WHERE agent_decision_id=a.agent_decision_id)) OR
    (SELECT count(DISTINCT decision) FROM qms.approval WHERE agent_decision_id=a.agent_decision_id
      AND decided_at=(SELECT max(decided_at) FROM qms.approval
       WHERE agent_decision_id=a.agent_decision_id))<>1 THEN
  RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='controlled governance validation denied';
 END IF;
 FOR pc IN SELECT value FROM jsonb_array_elements(p.preconditions) LOOP
  v_preconditions:=v_preconditions||jsonb_build_object(pc->>'identity','satisfied');
 END LOOP;
 INSERT INTO qms.action_execution(id,tenant_id,organization_id,execution_authorization_id,
  action_plan_id,action_plan_hash,executor_type,status,attempt_number,precondition_results,
  idempotency_key,trace_id,started_at)
 VALUES(v_execution,v_tenant,p.organization_id,a.id,p.id,p.action_plan_hash,
  'controlled_opportunity','running',1,v_preconditions,p_idempotency_key,a.trace_id,v_started);
 SELECT * INTO STRICT prior FROM qms.opportunity
  WHERE id=(p.parameters->>'expected_revision_id')::uuid AND
        lineage_id=p.target_id::uuid AND tenant_id=v_tenant FOR UPDATE;
 IF prior.organization_id<>p.organization_id OR prior.revision<>(p.parameters->>'expected_revision')::integer OR
    EXISTS(SELECT 1 FROM qms.opportunity WHERE previous_revision_id=prior.id) THEN
  RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='controlled Opportunity leaf is stale';
 END IF;
 IF p_action_type='opportunity.defer_evaluation' THEN
  v_source:='under_evaluation'; v_destination:='deferred'; v_outcome:='opportunity_deferred';
 ELSE
  v_source:='deferred'; v_destination:='under_evaluation';
  v_outcome:='opportunity_evaluation_resumed';
 END IF;
 v_state_hash:=qms.foundation_0015_opportunity_state_hash(prior.tenant_id,
  prior.organization_id,prior.lineage_id,prior.id,prior.revision,prior.process_id,
  prior.hypothesis,prior.benefit,prior.feasibility,prior.status);
 IF prior.status<>v_source OR p.parameters->>'expected_current_state'<>v_source OR
    p.parameters->>'desired_state'<>v_destination OR
    p.parameters->>'expected_state_hash'<>v_state_hash THEN
  RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='controlled Opportunity state is stale';
 END IF;
 IF current_setting('foundation.phase16_fail_at',true)='after_target_lock' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 SELECT * INTO transitioned FROM qms.foundation_0015_apply_opportunity_status_transition(
  prior.id,uuidv7(),v_destination,'controlled-opportunity-executor',a.trace_id,
  CASE WHEN p_action_type='opportunity.defer_evaluation' THEN 'controlled defer evaluation'
       ELSE 'controlled compensation resume evaluation' END,'execution_service');
 IF current_setting('foundation.phase16_fail_at',true)='after_business_mutation' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 v_completed:=statement_timestamp();
 v_result:=jsonb_build_object('classification','CONTROLLED-QMS-POC',
  'business_state_changed',true,'effectiveness_claimed',false,'replayed',false,
  'execution_id',v_execution::text,'action_plan_hash',p.action_plan_hash,
  'action_type',p_action_type,'policy_id','controlled-qms-action-policy/v1',
  'opportunity_lineage_id',prior.lineage_id::text,'before_revision_id',prior.id::text,
  'before_revision',prior.revision,'before_status',prior.status,
  'after_revision_id',transitioned.revision_id::text,'after_revision',prior.revision+1,
  'after_status',v_destination,'domain_event_id',transitioned.event_id::text,
  'trace_id',a.trace_id::text,'compensation_eligible',
   (p_action_type='opportunity.defer_evaluation'),'completed_at',v_completed,
  'started_at',v_started);
 v_result_hash:=qms.foundation_0015_canonical_hash(v_result);
 IF current_setting('foundation.phase16_fail_at',true)='before_execution_completion' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 PERFORM set_config('foundation.execution_completion',v_execution::text,true);
 UPDATE qms.action_execution SET status='succeeded',completed_at=v_completed WHERE id=v_execution;
 IF current_setting('foundation.phase16_fail_at',true)='after_execution_completion' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 INSERT INTO qms.action_execution_receipt(id,tenant_id,organization_id,action_execution_id,
  executor_type,outcome,result,result_hash,action_plan_hash,trace_id,started_at,completed_at)
 VALUES(v_receipt,v_tenant,p.organization_id,v_execution,'controlled_opportunity',v_outcome,
  v_result,v_result_hash,p.action_plan_hash,a.trace_id,v_started,v_completed);
 IF current_setting('foundation.phase16_fail_at',true)='after_receipt' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended(v_tenant::text||':action_execution:'||v_execution::text,0));
 SELECT COALESCE(max(aggregate_version),0)+1 INTO v_version FROM eventing.domain_event
  WHERE aggregate_type='action_execution' AND aggregate_id=v_execution;
 v_event:=uuidv7(); v_outbox:=uuidv7();
 INSERT INTO eventing.domain_event(event_id,tenant_id,event_type,schema_version,aggregate_type,
  aggregate_id,aggregate_version,occurred_at,trace_id,source,payload,payload_hash)
 VALUES(v_event,v_tenant,'action_execution.succeeded',1,'action_execution',v_execution,
  v_version,v_completed,a.trace_id,'iso-smart-controlled-qms-execution',v_result,
  qms.foundation_0015_canonical_hash(v_result));
 IF current_setting('foundation.phase16_fail_at',true)='after_execution_event' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 INSERT INTO eventing.transactional_outbox(id,tenant_id,domain_event_id,status,publish_attempts,available_at)
 VALUES(v_outbox,v_tenant,v_event,'pending',0,v_completed);
 IF current_setting('foundation.phase16_fail_at',true)='after_execution_outbox' THEN RAISE EXCEPTION 'forced phase16 failure'; END IF;
 v_meta:=jsonb_build_object('event_id',v_event::text,'execution_id',v_execution::text,
  'receipt_id',v_receipt::text,'governance_artifact_id',a.id::text,
  'action_plan_id',p.id::text,'action_plan_hash',p.action_plan_hash,
  'executor','controlled_opportunity','status','succeeded','result_hash',v_result_hash,
  'effectiveness_claimed',false);
 SELECT audit.append_immutable_audit(v_tenant,'action_execution',v_execution,
  'execution_service','controlled-opportunity-executor','action_execution.succeeded',
  'action_execution',v_execution,a.trace_id,v_completed,NULL,
  qms.foundation_0015_canonical_hash(v_result),
  '{"canonicalization":"iso-smart-canonical-json-v1","value":'||
   qms.foundation_0015_canonical_json_value(v_meta)||'}') INTO v_audit;
 IF current_setting('foundation.phase16_fail_at',true) IN ('after_execution_audit','before_commit') THEN
  RAISE EXCEPTION 'forced phase16 failure';
 END IF;
 RETURN v_result;
END $fn$;

CREATE FUNCTION qms.defer_opportunity_evaluation(p_authorization_id uuid,p_idempotency_key text)
RETURNS jsonb LANGUAGE sql SECURITY DEFINER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
 SELECT qms.foundation_0015_controlled_opportunity_execution(
  p_authorization_id,p_idempotency_key,'opportunity.defer_evaluation')
$fn$;
CREATE FUNCTION qms.resume_opportunity_evaluation(p_authorization_id uuid,p_idempotency_key text)
RETURNS jsonb LANGUAGE sql SECURITY DEFINER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
 SELECT qms.foundation_0015_controlled_opportunity_execution(
  p_authorization_id,p_idempotency_key,'opportunity.resume_evaluation')
$fn$;

REVOKE ALL ON FUNCTION qms.foundation_0015_canonical_json_value(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0015_canonical_hash(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0015_opportunity_state_hash(uuid,uuid,uuid,uuid,integer,uuid,text,text,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0015_apply_opportunity_status_transition(uuid,uuid,text,text,uuid,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0015_controlled_opportunity_execution(uuid,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.defer_opportunity_evaluation(uuid,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.resume_opportunity_evaluation(uuid,text) FROM PUBLIC;

DO $grants$
DECLARE owner_role text:=current_setting('foundation.qms_action_owner_role',true);
        app_role text:=current_setting('foundation.app_role',true);
        executor_role text:=current_setting('foundation.executor_role',true);
BEGIN
 EXECUTE format('GRANT USAGE ON SCHEMA qms,eventing,audit,governance TO %I',owner_role);
 EXECUTE format('GRANT CREATE ON SCHEMA qms TO %I',owner_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION qms.defer_opportunity_evaluation(uuid,text),qms.resume_opportunity_evaluation(uuid,text) TO %I',executor_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0015_apply_opportunity_status_transition(uuid,uuid,text,text,uuid,text,text) TO %I',app_role);
 EXECUTE format('ALTER FUNCTION qms.foundation_0015_apply_opportunity_status_transition(uuid,uuid,text,text,uuid,text,text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION qms.defer_opportunity_evaluation(uuid,text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION qms.resume_opportunity_evaluation(uuid,text) OWNER TO %I',owner_role);
 EXECUTE format('REVOKE CREATE ON SCHEMA qms FROM %I',owner_role);
 -- PostgreSQL requires UPDATE privilege for SELECT FOR UPDATE; append-only
 -- triggers still make arbitrary row UPDATE impossible for this owner.
 EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.opportunity TO %I',owner_role);
 EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.action_execution TO %I',owner_role);
 EXECUTE format('GRANT SELECT,INSERT ON qms.action_execution_receipt TO %I',owner_role);
 EXECUTE format('GRANT SELECT ON qms.organization,qms.user_projection,qms.recommendation,qms.agent_run,qms.agent_decision,qms.approval,qms.action_plan,qms.action_plan_dry_run,qms.execution_authorization,governance.model_policy,governance.agent_definition TO %I',owner_role);
 EXECUTE format('GRANT SELECT,INSERT ON eventing.domain_event,eventing.transactional_outbox TO %I',owner_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) TO %I',owner_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0015_canonical_json_value(jsonb),qms.foundation_0015_canonical_hash(jsonb),qms.foundation_0015_opportunity_state_hash(uuid,uuid,uuid,uuid,integer,uuid,text,text,text,text),qms.foundation_0015_controlled_opportunity_execution(uuid,text,text) TO %I',owner_role);

 EXECUTE format('CREATE POLICY qms_opportunity_phase16_owner ON qms.opportunity FOR ALL TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_action_execution_phase16_owner ON qms.action_execution FOR ALL TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_action_execution_receipt_phase16_owner ON qms.action_execution_receipt FOR ALL TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY foundation_domain_event_phase16_owner ON eventing.domain_event FOR ALL TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY foundation_outbox_phase16_owner ON eventing.transactional_outbox FOR ALL TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY foundation_organization_phase16_owner ON qms.organization FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY foundation_user_projection_phase16_owner ON qms.user_projection FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_recommendation_phase16_owner ON qms.recommendation FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_agent_run_phase16_owner ON qms.agent_run FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_agent_decision_phase16_owner ON qms.agent_decision FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_approval_phase16_owner ON qms.approval FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_action_plan_phase16_owner ON qms.action_plan FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_action_plan_dry_run_phase16_owner ON qms.action_plan_dry_run FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_execution_authorization_phase16_owner ON qms.execution_authorization FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
END $grants$;
"""


REVERSE_SQL = r"""
DROP POLICY qms_execution_authorization_phase16_owner ON qms.execution_authorization;
DROP POLICY qms_action_plan_dry_run_phase16_owner ON qms.action_plan_dry_run;
DROP POLICY qms_action_plan_phase16_owner ON qms.action_plan;
DROP POLICY qms_approval_phase16_owner ON qms.approval;
DROP POLICY qms_agent_decision_phase16_owner ON qms.agent_decision;
DROP POLICY qms_agent_run_phase16_owner ON qms.agent_run;
DROP POLICY qms_recommendation_phase16_owner ON qms.recommendation;
DROP POLICY foundation_user_projection_phase16_owner ON qms.user_projection;
DROP POLICY foundation_organization_phase16_owner ON qms.organization;
DROP POLICY foundation_outbox_phase16_owner ON eventing.transactional_outbox;
DROP POLICY foundation_domain_event_phase16_owner ON eventing.domain_event;
DROP POLICY qms_action_execution_receipt_phase16_owner ON qms.action_execution_receipt;
DROP POLICY qms_action_execution_phase16_owner ON qms.action_execution;
DROP POLICY qms_opportunity_phase16_owner ON qms.opportunity;
DROP FUNCTION qms.resume_opportunity_evaluation(uuid,text);
DROP FUNCTION qms.defer_opportunity_evaluation(uuid,text);
DROP FUNCTION qms.foundation_0015_controlled_opportunity_execution(uuid,text,text);
DROP FUNCTION qms.foundation_0015_apply_opportunity_status_transition(uuid,uuid,text,text,uuid,text,text);
DROP FUNCTION qms.foundation_0015_opportunity_state_hash(uuid,uuid,uuid,uuid,integer,uuid,text,text,text,text);
DROP FUNCTION qms.foundation_0015_canonical_hash(jsonb);
DROP FUNCTION qms.foundation_0015_canonical_json_value(jsonb);
ALTER TABLE qms.action_execution DROP CONSTRAINT qms_action_execution_executor;
ALTER TABLE qms.action_execution ADD CONSTRAINT qms_action_execution_executor CHECK(executor_type='synthetic_noop');
ALTER TABLE qms.action_execution_receipt DROP CONSTRAINT qms_action_execution_receipt_executor;
ALTER TABLE qms.action_execution_receipt ADD CONSTRAINT qms_action_execution_receipt_executor CHECK(executor_type='synthetic_noop');
ALTER TABLE qms.action_execution_receipt DROP CONSTRAINT qms_action_execution_receipt_outcome;
ALTER TABLE qms.action_execution_receipt ADD CONSTRAINT qms_action_execution_receipt_outcome CHECK(outcome IN ('synthetic_noop_succeeded','synthetic_noop_failed'));
ALTER TABLE qms.action_execution_receipt DROP CONSTRAINT qms_action_execution_receipt_contract;
ALTER TABLE qms.action_execution_receipt ADD CONSTRAINT qms_action_execution_receipt_synthetic CHECK(
 result->>'classification'='NON-PRODUCTION' AND result->>'mode'='SYNTHETIC' AND
 result->>'effect'='NO-OP' AND result->>'business_state_changed'='false');

CREATE OR REPLACE FUNCTION qms.foundation_0014_validate_execution_start() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
DECLARE a qms.execution_authorization%ROWTYPE; p qms.action_plan%ROWTYPE;
        d qms.action_plan_dry_run%ROWTYPE; parent qms.action_execution%ROWTYPE;
        latest_time timestamptz; latest_outcomes integer;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='ActionExecution delete is forbidden'; END IF;
 IF TG_OP='UPDATE' THEN
  IF OLD.status<>'running' OR NEW.status NOT IN ('succeeded','failed') OR NEW.completed_at IS NULL OR
     ROW(NEW.tenant_id,NEW.organization_id,NEW.execution_authorization_id,NEW.action_plan_id,
       NEW.action_plan_hash,NEW.executor_type,NEW.attempt_number,NEW.retry_of_execution_id,
       NEW.precondition_results,NEW.idempotency_key,NEW.trace_id,NEW.started_at,NEW.created_at)
     IS DISTINCT FROM ROW(OLD.tenant_id,OLD.organization_id,OLD.execution_authorization_id,
       OLD.action_plan_id,OLD.action_plan_hash,OLD.executor_type,OLD.attempt_number,
       OLD.retry_of_execution_id,OLD.precondition_results,OLD.idempotency_key,OLD.trace_id,
       OLD.started_at,OLD.created_at) OR
     current_setting('foundation.execution_completion',true) IS DISTINCT FROM OLD.id::text THEN
   RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='invalid or ungoverned ActionExecution transition';
  END IF; RETURN NEW;
 END IF;
 SELECT * INTO STRICT a FROM qms.execution_authorization WHERE id=NEW.execution_authorization_id;
 SELECT * INTO STRICT p FROM qms.action_plan WHERE id=NEW.action_plan_id;
 SELECT * INTO STRICT d FROM qms.action_plan_dry_run WHERE id=a.dry_run_id;
 IF NEW.status<>'running' OR NEW.completed_at IS NOT NULL OR NEW.executor_type<>'synthetic_noop' OR
    a.outcome<>'authorized' OR a.tenant_id<>NEW.tenant_id OR a.organization_id<>NEW.organization_id OR
    a.action_plan_id<>NEW.action_plan_id OR a.action_plan_hash<>NEW.action_plan_hash OR
    p.tenant_id<>NEW.tenant_id OR p.organization_id<>NEW.organization_id OR
    p.action_plan_hash<>NEW.action_plan_hash OR a.agent_decision_id<>p.agent_decision_id OR
    a.recommendation_id<>p.recommendation_id OR a.impact<>p.impact OR
    a.reversibility<>p.reversibility OR p.required_autonomy<3 OR
    p.required_autonomy>a.effective_autonomy_ceiling OR
    (p.required_autonomy=4 AND (p.reversibility<>'reversible' OR p.impact='high')) OR
    d.action_plan_id<>p.id OR d.action_plan_hash<>p.action_plan_hash OR d.validation_status<>'passed' THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionExecution exact authorization/plan/policy validation failed';
 END IF;
 SELECT max(decided_at) INTO latest_time FROM qms.approval WHERE agent_decision_id=a.agent_decision_id;
 SELECT count(DISTINCT decision) INTO latest_outcomes FROM qms.approval
  WHERE agent_decision_id=a.agent_decision_id AND decided_at=latest_time;
 IF latest_outcomes<>1 OR NOT EXISTS(SELECT 1 FROM qms.approval ap
   WHERE ap.id=a.effective_approval_id AND ap.agent_decision_id=a.agent_decision_id
   AND ap.decided_at=latest_time AND ap.decision='approve') THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionExecution effective Approval validation failed';
 END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(p.preconditions) pc
   WHERE COALESCE((pc->>'required')::boolean,true) AND
   COALESCE(NEW.precondition_results->>(pc->>'identity'),'unknown')<>'satisfied') OR
   EXISTS(SELECT 1 FROM jsonb_object_keys(NEW.precondition_results) k WHERE NOT EXISTS(
    SELECT 1 FROM jsonb_array_elements(p.preconditions) pc WHERE pc->>'identity'=k)) THEN
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

DO $revoke$
DECLARE owner_role text:=current_setting('foundation.qms_action_owner_role',true);
BEGIN
 EXECUTE format('REVOKE ALL PRIVILEGES ON qms.opportunity,qms.action_execution,qms.action_execution_receipt,qms.organization,qms.user_projection,qms.recommendation,qms.agent_run,qms.agent_decision,qms.approval,qms.action_plan,qms.action_plan_dry_run,qms.execution_authorization FROM %I',owner_role);
 EXECUTE format('REVOKE ALL PRIVILEGES ON eventing.domain_event,eventing.transactional_outbox FROM %I',owner_role);
 EXECUTE format('REVOKE EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) FROM %I',owner_role);
 EXECUTE format('REVOKE USAGE ON SCHEMA qms,eventing,audit,governance FROM %I',owner_role);
END $revoke$;
"""


def apply_phase16(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase16(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0014_action_execution_synthetic_foundation")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(apply_phase16, reverse_phase16)],
            state_operations=[
                migrations.AlterField(
                    model_name="actionexecution",
                    name="executor_type",
                    field=models.CharField(
                        choices=[
                            ("synthetic_noop", "Synthetic no-op"),
                            ("controlled_opportunity", "Controlled Opportunity"),
                        ],
                        max_length=40,
                    ),
                ),
                migrations.AlterField(
                    model_name="actionexecutionreceipt",
                    name="outcome",
                    field=models.CharField(
                        choices=[
                            ("synthetic_noop_succeeded", "Synthetic no-op succeeded"),
                            ("synthetic_noop_failed", "Synthetic no-op failed"),
                            ("opportunity_deferred", "Opportunity deferred"),
                            ("opportunity_evaluation_resumed", "Opportunity evaluation resumed"),
                        ],
                        max_length=40,
                    ),
                ),
            ],
        )
    ]
