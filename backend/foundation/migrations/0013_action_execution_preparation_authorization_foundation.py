"""Phase 13 prepared-action and execution-authorization contract foundation."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
  app_role text := current_setting('foundation.app_role',true);
  worker_role text := current_setting('foundation.worker_role',true);
  human_role text := current_setting('foundation.human_approver_role',true);
  authorizer_role text := current_setting('foundation.execution_authorizer_role',true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' OR
     human_role IS NULL OR human_role='' OR authorizer_role IS NULL OR authorizer_role='' THEN
    RAISE EXCEPTION 'Phase 13 app, worker, human and execution authorizer roles are required';
  END IF;

  CREATE TABLE qms.action_plan (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    organization_id uuid NOT NULL,
    agent_decision_id uuid NOT NULL,
    recommendation_id uuid NOT NULL,
    action_type varchar(160) NOT NULL,
    target_type varchar(160) NOT NULL,
    target_id varchar(255) NOT NULL,
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    impact varchar(24) NOT NULL,
    reversibility varchar(32) NOT NULL,
    preconditions jsonb NOT NULL DEFAULT '[]'::jsonb,
    dry_run_supported boolean NOT NULL DEFAULT true,
    required_autonomy smallint NOT NULL,
    action_plan_hash char(64) NOT NULL,
    idempotency_key varchar(200) NOT NULL,
    trace_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_action_plan_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
    CONSTRAINT qms_action_plan_tenant_idempotency_unique UNIQUE(tenant_id,idempotency_key),
    CONSTRAINT qms_action_plan_decision_fk FOREIGN KEY(tenant_id,organization_id,agent_decision_id)
      REFERENCES qms.agent_decision(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_action_plan_recommendation_fk FOREIGN KEY(tenant_id,organization_id,recommendation_id)
      REFERENCES qms.recommendation(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_action_plan_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_action_plan_text_nonblank CHECK(
      btrim(action_type)<>'' AND btrim(target_type)<>'' AND btrim(target_id)<>'' AND btrim(idempotency_key)<>''),
    CONSTRAINT qms_action_plan_json_shapes CHECK(jsonb_typeof(parameters)='object' AND jsonb_typeof(preconditions)='array'),
    CONSTRAINT qms_action_plan_impact CHECK(impact IN ('standard','high')),
    CONSTRAINT qms_action_plan_reversibility CHECK(reversibility IN ('reversible','irreversible')),
    CONSTRAINT qms_action_plan_autonomy CHECK(required_autonomy BETWEEN 0 AND 4),
    CONSTRAINT qms_action_plan_hash CHECK(action_plan_hash ~ '^[0-9a-f]{64}$')
  );

  CREATE TABLE qms.action_plan_dry_run (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    organization_id uuid NOT NULL,
    action_plan_id uuid NOT NULL,
    action_plan_hash char(64) NOT NULL,
    expected_affected_objects jsonb NOT NULL DEFAULT '[]'::jsonb,
    intended_state_delta jsonb NOT NULL DEFAULT '{}'::jsonb,
    validation_status varchar(24) NOT NULL,
    precondition_results jsonb NOT NULL DEFAULT '[]'::jsonb,
    impact_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
    trace_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_action_plan_dry_run_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
    CONSTRAINT qms_action_plan_dry_run_plan_fk FOREIGN KEY(tenant_id,organization_id,action_plan_id)
      REFERENCES qms.action_plan(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_action_plan_dry_run_shapes CHECK(
      jsonb_typeof(expected_affected_objects)='array' AND jsonb_typeof(intended_state_delta)='object' AND
      jsonb_typeof(precondition_results)='array' AND jsonb_typeof(impact_summary)='object'),
    CONSTRAINT qms_action_plan_dry_run_validation CHECK(validation_status IN ('passed','failed')),
    CONSTRAINT qms_action_plan_dry_run_hash CHECK(action_plan_hash ~ '^[0-9a-f]{64}$')
  );

  CREATE TABLE qms.execution_authorization (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    organization_id uuid NOT NULL,
    action_plan_id uuid NOT NULL,
    action_plan_hash char(64) NOT NULL,
    dry_run_id uuid NOT NULL,
    agent_decision_id uuid NOT NULL,
    recommendation_id uuid NOT NULL,
    effective_approval_id uuid NOT NULL,
    agent_run_id uuid NOT NULL,
    agent_definition_id uuid NOT NULL REFERENCES governance.agent_definition(id) ON DELETE RESTRICT,
    model_policy_id uuid NOT NULL REFERENCES governance.model_policy(id) ON DELETE RESTRICT,
    effective_autonomy_ceiling smallint NOT NULL,
    impact varchar(24) NOT NULL,
    reversibility varchar(32) NOT NULL,
    outcome varchar(24) NOT NULL,
    idempotency_key varchar(200) NOT NULL,
    authorization_request_hash char(64) NOT NULL,
    actor_type varchar(40) NOT NULL,
    actor_id varchar(255) NOT NULL,
    trace_id uuid NOT NULL,
    authorized_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_execution_authorization_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
    CONSTRAINT qms_execution_authorization_tenant_idempotency_unique UNIQUE(tenant_id,idempotency_key),
    CONSTRAINT qms_execution_authorization_plan_fk FOREIGN KEY(tenant_id,organization_id,action_plan_id)
      REFERENCES qms.action_plan(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_execution_authorization_dry_run_fk FOREIGN KEY(tenant_id,organization_id,dry_run_id)
      REFERENCES qms.action_plan_dry_run(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_execution_authorization_decision_fk FOREIGN KEY(tenant_id,organization_id,agent_decision_id)
      REFERENCES qms.agent_decision(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_execution_authorization_recommendation_fk FOREIGN KEY(tenant_id,organization_id,recommendation_id)
      REFERENCES qms.recommendation(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_execution_authorization_approval_fk FOREIGN KEY(tenant_id,organization_id,effective_approval_id)
      REFERENCES qms.approval(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_execution_authorization_run_fk FOREIGN KEY(tenant_id,organization_id,agent_run_id)
      REFERENCES qms.agent_run(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_execution_authorization_outcome CHECK(outcome='authorized'),
    CONSTRAINT qms_execution_authorization_autonomy CHECK(effective_autonomy_ceiling BETWEEN 0 AND 4),
    CONSTRAINT qms_execution_authorization_impact CHECK(impact IN ('standard','high')),
    CONSTRAINT qms_execution_authorization_reversibility CHECK(reversibility IN ('reversible','irreversible')),
    CONSTRAINT qms_execution_authorization_hashes CHECK(
      action_plan_hash ~ '^[0-9a-f]{64}$' AND authorization_request_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT qms_execution_authorization_actor CHECK(actor_type='governance_service' AND btrim(actor_id)<>''),
    CONSTRAINT qms_execution_authorization_idempotency_nonblank CHECK(btrim(idempotency_key)<>'')
  );

  CREATE INDEX qms_action_plan_decision_idx ON qms.action_plan(tenant_id,organization_id,agent_decision_id,created_at);
  CREATE INDEX qms_action_plan_dry_run_plan_idx ON qms.action_plan_dry_run(tenant_id,organization_id,action_plan_id,created_at);
  CREATE INDEX qms_execution_authorization_plan_idx ON qms.execution_authorization(tenant_id,organization_id,action_plan_id,authorized_at);

  CREATE FUNCTION qms.foundation_0013_validate_action_plan()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  DECLARE d record;
  BEGIN
    SELECT recommendation_id,organization_id INTO d FROM qms.agent_decision WHERE id=NEW.agent_decision_id;
    IF NOT FOUND OR d.recommendation_id IS DISTINCT FROM NEW.recommendation_id OR
       d.organization_id IS DISTINCT FROM NEW.organization_id THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionPlan must match exact AgentDecision and Recommendation';
    END IF;
    IF EXISTS(SELECT 1 FROM jsonb_array_elements(NEW.preconditions) p
              WHERE jsonb_typeof(p)<>'object' OR NOT (p ? 'identity' AND p ? 'type' AND p ? 'expected' AND p ? 'required')
                 OR jsonb_typeof(p->'required')<>'boolean') THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ActionPlan preconditions must be structured and verifiable';
    END IF;
    RETURN NEW;
  END $fn$;

  CREATE FUNCTION qms.foundation_0013_validate_dry_run()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  DECLARE p record;
  BEGIN
    SELECT action_plan_hash,dry_run_supported INTO p FROM qms.action_plan WHERE id=NEW.action_plan_id;
    IF NOT FOUND OR NOT p.dry_run_supported OR NEW.action_plan_hash IS DISTINCT FROM p.action_plan_hash THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='dry-run must bind the exact supported ActionPlan hash';
    END IF;
    IF EXISTS(SELECT 1 FROM jsonb_array_elements(NEW.precondition_results) r
              WHERE jsonb_typeof(r)<>'object' OR NOT (r ? 'identity' AND r ? 'status')
                 OR r->>'status' NOT IN ('satisfied','not_satisfied','unknown')) THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='invalid dry-run precondition result';
    END IF;
    RETURN NEW;
  END $fn$;

  CREATE FUNCTION qms.foundation_0013_validate_authorization()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms,governance AS $fn$
  DECLARE p record; d record; r record; a record; dr record; effective_id uuid;
  BEGIN
    SELECT * INTO p FROM qms.action_plan WHERE id=NEW.action_plan_id;
    SELECT * INTO d FROM qms.agent_decision WHERE id=NEW.agent_decision_id;
    SELECT * INTO r FROM qms.agent_run WHERE id=NEW.agent_run_id;
    SELECT * INTO a FROM qms.approval WHERE id=NEW.effective_approval_id;
    SELECT * INTO dr FROM qms.action_plan_dry_run WHERE id=NEW.dry_run_id;
    SELECT id INTO effective_id FROM qms.approval
      WHERE agent_decision_id=NEW.agent_decision_id
      ORDER BY decided_at DESC,created_at DESC,id DESC LIMIT 1;
    IF p.id IS NULL OR d.id IS NULL OR r.id IS NULL OR a.id IS NULL OR dr.id IS NULL OR
       NEW.action_plan_hash IS DISTINCT FROM p.action_plan_hash OR dr.action_plan_id IS DISTINCT FROM p.id OR
       dr.action_plan_hash IS DISTINCT FROM p.action_plan_hash OR dr.validation_status<>'passed' OR
       p.agent_decision_id IS DISTINCT FROM d.id OR p.recommendation_id IS DISTINCT FROM d.recommendation_id OR
       NEW.recommendation_id IS DISTINCT FROM p.recommendation_id OR d.agent_run_id IS DISTINCT FROM r.id OR
       a.agent_decision_id IS DISTINCT FROM d.id OR a.recommendation_id IS DISTINCT FROM d.recommendation_id OR
       a.id IS DISTINCT FROM effective_id OR a.decision<>'approve' OR
       NEW.agent_definition_id IS DISTINCT FROM r.agent_definition_id OR
       NEW.model_policy_id IS DISTINCT FROM r.model_policy_id OR
       NEW.effective_autonomy_ceiling IS DISTINCT FROM r.effective_autonomy_ceiling OR
       p.required_autonomy>r.effective_autonomy_ceiling OR p.required_autonomy>d.decision_autonomy OR
       NEW.impact IS DISTINCT FROM p.impact OR NEW.reversibility IS DISTINCT FROM p.reversibility THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='ExecutionAuthorization provenance or policy validation failed';
    END IF;
    IF EXISTS(SELECT 1 FROM jsonb_array_elements(p.preconditions) pc
      WHERE COALESCE((pc->>'required')::boolean,true) AND NOT EXISTS(
        SELECT 1 FROM jsonb_array_elements(dr.precondition_results) pr
        WHERE pr->>'identity'=pc->>'identity' AND pr->>'status'='satisfied')) THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='required ActionPlan precondition is not satisfied';
    END IF;
    RETURN NEW;
  END $fn$;

  CREATE FUNCTION qms.foundation_0013_reject_mutation()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  BEGIN
    RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Phase 13 preparation and authorization artifacts are immutable';
  END $fn$;

  CREATE TRIGGER qms_action_plan_validate BEFORE INSERT ON qms.action_plan FOR EACH ROW EXECUTE FUNCTION qms.foundation_0013_validate_action_plan();
  CREATE TRIGGER qms_action_plan_guard BEFORE UPDATE OR DELETE ON qms.action_plan FOR EACH ROW EXECUTE FUNCTION qms.foundation_0013_reject_mutation();
  CREATE TRIGGER qms_action_plan_dry_run_validate BEFORE INSERT ON qms.action_plan_dry_run FOR EACH ROW EXECUTE FUNCTION qms.foundation_0013_validate_dry_run();
  CREATE TRIGGER qms_action_plan_dry_run_guard BEFORE UPDATE OR DELETE ON qms.action_plan_dry_run FOR EACH ROW EXECUTE FUNCTION qms.foundation_0013_reject_mutation();
  CREATE TRIGGER qms_execution_authorization_validate BEFORE INSERT ON qms.execution_authorization FOR EACH ROW EXECUTE FUNCTION qms.foundation_0013_validate_authorization();
  CREATE TRIGGER qms_execution_authorization_guard BEFORE UPDATE OR DELETE ON qms.execution_authorization FOR EACH ROW EXECUTE FUNCTION qms.foundation_0013_reject_mutation();

  ALTER TABLE qms.action_plan ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.action_plan FORCE ROW LEVEL SECURITY;
  ALTER TABLE qms.action_plan_dry_run ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.action_plan_dry_run FORCE ROW LEVEL SECURITY;
  ALTER TABLE qms.execution_authorization ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.execution_authorization FORCE ROW LEVEL SECURITY;

  EXECUTE format('CREATE POLICY qms_action_plan_select ON qms.action_plan FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('CREATE POLICY qms_action_plan_insert ON qms.action_plan FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
  EXECUTE format('CREATE POLICY qms_action_plan_update ON qms.action_plan FOR UPDATE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
  EXECUTE format('CREATE POLICY qms_action_plan_delete ON qms.action_plan FOR DELETE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
  EXECUTE format('CREATE POLICY qms_action_plan_migrator ON qms.action_plan FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
  EXECUTE format('CREATE POLICY qms_action_plan_dry_run_select ON qms.action_plan_dry_run FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role);
  EXECUTE format('CREATE POLICY qms_action_plan_dry_run_insert ON qms.action_plan_dry_run FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
  EXECUTE format('CREATE POLICY qms_action_plan_dry_run_update ON qms.action_plan_dry_run FOR UPDATE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
  EXECUTE format('CREATE POLICY qms_action_plan_dry_run_delete ON qms.action_plan_dry_run FOR DELETE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
  EXECUTE format('CREATE POLICY qms_action_plan_dry_run_migrator ON qms.action_plan_dry_run FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
  EXECUTE format('CREATE POLICY qms_execution_authorization_select ON qms.execution_authorization FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,authorizer_role);
  EXECUTE format('CREATE POLICY qms_execution_authorization_insert ON qms.execution_authorization FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',authorizer_role);
  EXECUTE format('CREATE POLICY qms_execution_authorization_update ON qms.execution_authorization FOR UPDATE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',authorizer_role);
  EXECUTE format('CREATE POLICY qms_execution_authorization_delete ON qms.execution_authorization FOR DELETE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',authorizer_role);
  EXECUTE format('CREATE POLICY qms_execution_authorization_migrator ON qms.execution_authorization FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
  EXECUTE format('GRANT SELECT ON qms.action_plan TO %I,%I,%I,%I',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('GRANT INSERT ON qms.action_plan TO %I',worker_role);
  EXECUTE format('GRANT SELECT ON qms.action_plan_dry_run TO %I,%I,%I',app_role,worker_role,authorizer_role);
  EXECUTE format('GRANT INSERT ON qms.action_plan_dry_run TO %I',worker_role);
  EXECUTE format('GRANT SELECT ON qms.execution_authorization TO %I,%I',app_role,authorizer_role);
  EXECUTE format('GRANT USAGE ON SCHEMA qms,governance,eventing,audit TO %I',authorizer_role);
  EXECUTE format('GRANT SELECT ON qms.organization,qms.user_projection,qms.recommendation,qms.agent_run,qms.agent_decision,qms.approval,qms.action_plan,qms.action_plan_dry_run,qms.execution_authorization,governance.model_policy,governance.agent_definition TO %I',authorizer_role);

  DROP POLICY foundation_organization_select ON qms.organization;
  DROP POLICY foundation_user_projection_select ON qms.user_projection;
  DROP POLICY qms_recommendation_select ON qms.recommendation;
  DROP POLICY qms_agent_run_select ON qms.agent_run;
  DROP POLICY qms_agent_decision_select ON qms.agent_decision;
  DROP POLICY qms_approval_select ON qms.approval;
  EXECUTE format('CREATE POLICY foundation_organization_select ON qms.organization FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role);
  EXECUTE format('CREATE POLICY foundation_user_projection_select ON qms.user_projection FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('CREATE POLICY qms_recommendation_select ON qms.recommendation FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,authorizer_role);
  EXECUTE format('CREATE POLICY qms_agent_run_select ON qms.agent_run FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('CREATE POLICY qms_agent_decision_select ON qms.agent_decision FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('CREATE POLICY qms_approval_select ON qms.approval FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);

  DROP POLICY foundation_domain_event_select ON eventing.domain_event;
  DROP POLICY foundation_domain_event_insert ON eventing.domain_event;
  DROP POLICY foundation_outbox_select ON eventing.transactional_outbox;
  DROP POLICY foundation_outbox_insert ON eventing.transactional_outbox;
  EXECUTE format('CREATE POLICY foundation_domain_event_select ON eventing.domain_event FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I,%I,%I,%I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('CREATE POLICY foundation_outbox_select ON eventing.transactional_outbox FOR SELECT TO %I,%I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I,%I,%I,%I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role,authorizer_role);
  EXECUTE format('GRANT SELECT,INSERT ON eventing.domain_event,eventing.transactional_outbox TO %I',authorizer_role);
  EXECUTE format('GRANT EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) TO %I',authorizer_role);
END $migration$;

CREATE FUNCTION qms.foundation_0013_grant_execution_authorization(
 p_id uuid,p_tenant_id uuid,p_organization_id uuid,p_action_plan_id uuid,p_action_plan_hash text,
 p_dry_run_id uuid,p_agent_decision_id uuid,p_recommendation_id uuid,p_effective_approval_id uuid,
 p_agent_run_id uuid,p_agent_definition_id uuid,p_model_policy_id uuid,p_effective_autonomy_ceiling smallint,
 p_impact text,p_reversibility text,p_outcome text,p_idempotency_key text,p_request_hash text,
 p_actor_type text,p_actor_id text,p_trace_id uuid
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,qms AS $fn$
BEGIN
 IF p_tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid THEN
   RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='execution authorization tenant context mismatch';
 END IF;
 INSERT INTO qms.execution_authorization(
  id,tenant_id,organization_id,action_plan_id,action_plan_hash,dry_run_id,agent_decision_id,
  recommendation_id,effective_approval_id,agent_run_id,agent_definition_id,model_policy_id,
  effective_autonomy_ceiling,impact,reversibility,outcome,idempotency_key,
  authorization_request_hash,actor_type,actor_id,trace_id)
 VALUES(p_id,p_tenant_id,p_organization_id,p_action_plan_id,p_action_plan_hash,p_dry_run_id,
  p_agent_decision_id,p_recommendation_id,p_effective_approval_id,p_agent_run_id,
  p_agent_definition_id,p_model_policy_id,p_effective_autonomy_ceiling,p_impact,
  p_reversibility,p_outcome,p_idempotency_key,p_request_hash,p_actor_type,p_actor_id,p_trace_id);
 RETURN p_id;
END $fn$;
REVOKE ALL ON FUNCTION qms.foundation_0013_grant_execution_authorization(uuid,uuid,uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,smallint,text,text,text,text,text,text,text,uuid) FROM PUBLIC;
DO $grant$ DECLARE r text:=current_setting('foundation.execution_authorizer_role',true); BEGIN
 EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0013_grant_execution_authorization(uuid,uuid,uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,smallint,text,text,text,text,text,text,text,uuid) TO %I',r);
END $grant$;
"""


REVERSE_SQL = r"""
DO $migration$
DECLARE app_role text:=current_setting('foundation.app_role',true); worker_role text:=current_setting('foundation.worker_role',true); human_role text:=current_setting('foundation.human_approver_role',true); authorizer_role text:=current_setting('foundation.execution_authorizer_role',true);
BEGIN
 IF authorizer_role IS NOT NULL AND authorizer_role<>'' THEN
  EXECUTE format('REVOKE ALL PRIVILEGES ON qms.action_plan,qms.action_plan_dry_run,qms.execution_authorization FROM %I',authorizer_role);
  EXECUTE format('REVOKE SELECT,INSERT ON eventing.domain_event,eventing.transactional_outbox FROM %I',authorizer_role);
  EXECUTE format('REVOKE EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) FROM %I',authorizer_role);
 END IF;
 DROP POLICY foundation_organization_select ON qms.organization;
 DROP POLICY foundation_user_projection_select ON qms.user_projection;
 DROP POLICY qms_recommendation_select ON qms.recommendation;
 DROP POLICY qms_agent_run_select ON qms.agent_run;
 DROP POLICY qms_agent_decision_select ON qms.agent_decision;
 DROP POLICY qms_approval_select ON qms.approval;
 EXECUTE format('CREATE POLICY foundation_organization_select ON qms.organization FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
 EXECUTE format('CREATE POLICY foundation_user_projection_select ON qms.user_projection FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
 EXECUTE format('CREATE POLICY qms_recommendation_select ON qms.recommendation FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
 EXECUTE format('CREATE POLICY qms_agent_run_select ON qms.agent_run FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
 EXECUTE format('CREATE POLICY qms_agent_decision_select ON qms.agent_decision FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
 EXECUTE format('CREATE POLICY qms_approval_select ON qms.approval FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
 DROP POLICY foundation_domain_event_select ON eventing.domain_event;
 DROP POLICY foundation_domain_event_insert ON eventing.domain_event;
 DROP POLICY foundation_outbox_select ON eventing.transactional_outbox;
 DROP POLICY foundation_outbox_insert ON eventing.transactional_outbox;
 EXECUTE format('CREATE POLICY foundation_domain_event_select ON eventing.domain_event FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
 EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I,%I,%I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
 EXECUTE format('CREATE POLICY foundation_outbox_select ON eventing.transactional_outbox FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
 EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I,%I,%I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
END $migration$;
DROP FUNCTION qms.foundation_0013_grant_execution_authorization(uuid,uuid,uuid,uuid,text,uuid,uuid,uuid,uuid,uuid,uuid,uuid,smallint,text,text,text,text,text,text,text,uuid);
DROP TABLE qms.execution_authorization;
DROP TABLE qms.action_plan_dry_run;
DROP TABLE qms.action_plan;
DROP FUNCTION qms.foundation_0013_reject_mutation();
DROP FUNCTION qms.foundation_0013_validate_authorization();
DROP FUNCTION qms.foundation_0013_validate_dry_run();
DROP FUNCTION qms.foundation_0013_validate_action_plan();
"""


def apply_phase13(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase13(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0012_agent_decision_human_decision_gate_foundation")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase13, reverse_phase13)],
        state_operations=[
            migrations.CreateModel(name="ActionPlan", fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
                ("action_type",models.CharField(max_length=160)),("target_type",models.CharField(max_length=160)),
                ("target_id",models.CharField(max_length=255)),("parameters",models.JSONField(default=dict)),
                ("impact",models.CharField(choices=[("standard","Standard"),("high","High")],max_length=24)),
                ("reversibility",models.CharField(choices=[("reversible","Reversible"),("irreversible","Irreversible")],max_length=32)),
                ("preconditions",models.JSONField(default=list)),("dry_run_supported",models.BooleanField(default=True)),
                ("required_autonomy",models.PositiveSmallIntegerField()),("action_plan_hash",models.CharField(max_length=64)),
                ("idempotency_key",models.CharField(max_length=200)),("trace_id",models.UUIDField()),("created_at",models.DateTimeField(auto_now_add=True)),
                ("tenant",models.ForeignKey(db_column="tenant_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.tenantprojection")),
                ("organization",models.ForeignKey(db_column="organization_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.organization")),
                ("agent_decision",models.ForeignKey(db_column="agent_decision_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.agentdecision")),
                ("recommendation",models.ForeignKey(db_column="recommendation_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.recommendation")),
            ],options={"managed":False,"db_table":'qms"."action_plan'}),
            migrations.CreateModel(name="ActionPlanDryRun", fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
                ("action_plan_hash",models.CharField(max_length=64)),("expected_affected_objects",models.JSONField(default=list)),
                ("intended_state_delta",models.JSONField(default=dict)),("validation_status",models.CharField(max_length=24)),
                ("precondition_results",models.JSONField(default=list)),("impact_summary",models.JSONField(default=dict)),
                ("trace_id",models.UUIDField()),("created_at",models.DateTimeField(auto_now_add=True)),
                ("tenant",models.ForeignKey(db_column="tenant_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.tenantprojection")),
                ("organization",models.ForeignKey(db_column="organization_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.organization")),
                ("action_plan",models.ForeignKey(db_column="action_plan_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.actionplan")),
            ],options={"managed":False,"db_table":'qms"."action_plan_dry_run'}),
            migrations.CreateModel(name="ExecutionAuthorization", fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
                ("action_plan_hash",models.CharField(max_length=64)),("effective_autonomy_ceiling",models.PositiveSmallIntegerField()),
                ("impact",models.CharField(choices=[("standard","Standard"),("high","High")],max_length=24)),
                ("reversibility",models.CharField(choices=[("reversible","Reversible"),("irreversible","Irreversible")],max_length=32)),
                ("outcome",models.CharField(choices=[("authorized","Authorized")],max_length=24)),
                ("idempotency_key",models.CharField(max_length=200)),("authorization_request_hash",models.CharField(max_length=64)),
                ("actor_type",models.CharField(default="governance_service",max_length=40)),("actor_id",models.CharField(max_length=255)),
                ("trace_id",models.UUIDField()),("authorized_at",models.DateTimeField()),
                ("tenant",models.ForeignKey(db_column="tenant_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.tenantprojection")),
                ("organization",models.ForeignKey(db_column="organization_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.organization")),
                ("action_plan",models.ForeignKey(db_column="action_plan_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.actionplan")),
                ("dry_run",models.ForeignKey(db_column="dry_run_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.actionplandryrun")),
                ("agent_decision",models.ForeignKey(db_column="agent_decision_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.agentdecision")),
                ("recommendation",models.ForeignKey(db_column="recommendation_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.recommendation")),
                ("effective_approval",models.ForeignKey(db_column="effective_approval_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.approval")),
                ("agent_run",models.ForeignKey(db_column="agent_run_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.agentrun")),
                ("agent_definition",models.ForeignKey(db_column="agent_definition_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.agentdefinition")),
                ("model_policy",models.ForeignKey(db_column="model_policy_id",on_delete=django.db.models.deletion.PROTECT,to="foundation.modelpolicy")),
            ],options={"managed":False,"db_table":'qms"."execution_authorization'}),
        ],
    )]
