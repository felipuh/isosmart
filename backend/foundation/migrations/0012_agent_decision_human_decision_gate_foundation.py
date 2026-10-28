"""Phase 12 AgentDecision and Human Decision Gate foundation."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
    human_role text := current_setting('foundation.human_approver_role', true);
BEGIN
    IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' OR
       human_role IS NULL OR human_role='' THEN
        RAISE EXCEPTION 'Phase 12 app, worker and human approver roles are required';
    END IF;

    CREATE TABLE qms.agent_decision (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        agent_run_id uuid NOT NULL,
        recommendation_id uuid,
        decision_type varchar(120) NOT NULL,
        payload jsonb NOT NULL DEFAULT '{}'::jsonb,
        confidence numeric(5,4) NOT NULL,
        explainability jsonb NOT NULL DEFAULT '{}'::jsonb,
        decision_autonomy smallint NOT NULL,
        human_gate_required boolean NOT NULL,
        trace_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_agent_decision_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
        CONSTRAINT qms_agent_decision_run_fk FOREIGN KEY(tenant_id,organization_id,agent_run_id)
          REFERENCES qms.agent_run(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_decision_org_fk FOREIGN KEY(tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_decision_recommendation_fk FOREIGN KEY(tenant_id,organization_id,recommendation_id)
          REFERENCES qms.recommendation(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_agent_decision_type_nonblank CHECK(btrim(decision_type)<>''),
        CONSTRAINT qms_agent_decision_json_shapes CHECK(
          jsonb_typeof(payload)='object' AND jsonb_typeof(explainability)='object'),
        CONSTRAINT qms_agent_decision_confidence CHECK(confidence BETWEEN 0 AND 1),
        CONSTRAINT qms_agent_decision_autonomy CHECK(decision_autonomy BETWEEN 0 AND 4)
    );

    CREATE TABLE qms.approval (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        agent_decision_id uuid NOT NULL,
        recommendation_id uuid,
        required_role varchar(160) NOT NULL,
        decision varchar(24) NOT NULL,
        decided_by_id uuid NOT NULL,
        adminapps_user_id_snapshot uuid NOT NULL,
        actor_type varchar(24) NOT NULL DEFAULT 'human',
        comments text,
        decided_at timestamptz NOT NULL,
        trace_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_approval_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
        CONSTRAINT qms_approval_decision_fk FOREIGN KEY(tenant_id,organization_id,agent_decision_id)
          REFERENCES qms.agent_decision(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_approval_org_fk FOREIGN KEY(tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_approval_recommendation_fk FOREIGN KEY(tenant_id,organization_id,recommendation_id)
          REFERENCES qms.recommendation(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_approval_decided_by_fk FOREIGN KEY(tenant_id,decided_by_id)
          REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_approval_required_role_nonblank CHECK(btrim(required_role)<>''),
        CONSTRAINT qms_approval_decision_valid CHECK(decision IN ('approve','reject','request_changes')),
        CONSTRAINT qms_approval_actor_human CHECK(actor_type='human')
    );

    CREATE INDEX qms_agent_decision_tenant_org_run_idx
      ON qms.agent_decision(tenant_id,organization_id,agent_run_id,created_at);
    CREATE INDEX qms_approval_tenant_org_decision_idx
      ON qms.approval(tenant_id,organization_id,agent_decision_id,decided_at);

    CREATE FUNCTION qms.foundation_0012_validate_agent_decision()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms,governance AS $fn$
    DECLARE
      run_record record;
      linked_recommendation uuid;
      rules jsonb;
      expected_gate boolean;
    BEGIN
      SELECT requested_autonomy,effective_autonomy_ceiling,model_policy_id,trace_id
        INTO run_record FROM qms.agent_run WHERE id=NEW.agent_run_id;
      IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='AgentDecision requires one exact AgentRun';
      END IF;
      IF NEW.decision_autonomy>run_record.requested_autonomy OR
         NEW.decision_autonomy>run_record.effective_autonomy_ceiling THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='AgentDecision autonomy exceeds exact AgentRun/policy ceiling';
      END IF;
      IF NEW.trace_id IS DISTINCT FROM run_record.trace_id THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='AgentDecision trace must match exact AgentRun';
      END IF;
      SELECT recommendation_id INTO linked_recommendation
        FROM qms.agent_run_recommendation WHERE agent_run_id=NEW.agent_run_id;
      IF NEW.recommendation_id IS NOT NULL AND
         NEW.recommendation_id IS DISTINCT FROM linked_recommendation THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='AgentDecision Recommendation must match exact AgentRun output';
      END IF;
      SELECT human_gate_rules INTO rules FROM governance.model_policy
       WHERE id=run_record.model_policy_id;
      IF rules ? 'required_autonomy_levels' AND
         jsonb_typeof(rules->'required_autonomy_levels')<>'array' THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='human gate autonomy levels must be an array';
      END IF;
      expected_gate := NEW.decision_autonomy=3 OR
        COALESCE((rules->>'always_required')::boolean,false) OR
        COALESCE(rules->'required_autonomy_levels','[]'::jsonb) ? ('A'||NEW.decision_autonomy::text);
      IF NEW.human_gate_required IS DISTINCT FROM expected_gate THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='AgentDecision human gate must match exact ModelPolicy';
      END IF;
      RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0012_validate_approval()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms,governance AS $fn$
    DECLARE
      decision_record record;
      expected_role text;
      projected_adminapps_user uuid;
    BEGIN
      SELECT d.recommendation_id,d.human_gate_required,r.model_policy_id
        INTO decision_record
        FROM qms.agent_decision d JOIN qms.agent_run r ON r.id=d.agent_run_id
       WHERE d.id=NEW.agent_decision_id;
      IF NOT FOUND OR NOT decision_record.human_gate_required THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='Approval requires an exact AgentDecision with Human Decision Gate';
      END IF;
      IF NEW.recommendation_id IS DISTINCT FROM decision_record.recommendation_id THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='Approval Recommendation must match exact AgentDecision';
      END IF;
      SELECT human_gate_rules->>'required_role' INTO expected_role
        FROM governance.model_policy WHERE id=decision_record.model_policy_id;
      IF expected_role IS NULL OR btrim(expected_role)='' OR NEW.required_role<>expected_role THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='Approval required role must match exact ModelPolicy gate';
      END IF;
      SELECT adminapps_user_id INTO projected_adminapps_user
        FROM qms.user_projection
       WHERE id=NEW.decided_by_id AND tenant_id=NEW.tenant_id AND lifecycle_status='active';
      IF projected_adminapps_user IS NULL OR
         NEW.adminapps_user_id_snapshot IS DISTINCT FROM projected_adminapps_user THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='Approval actor must match an active exact UserProjection';
      END IF;
      RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0012_reject_governance_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
      RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='AgentDecision and Approval are append-only governance history';
    END $fn$;

    CREATE TRIGGER qms_agent_decision_validate BEFORE INSERT ON qms.agent_decision
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0012_validate_agent_decision();
    CREATE TRIGGER qms_agent_decision_guard BEFORE UPDATE OR DELETE ON qms.agent_decision
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0012_reject_governance_mutation();
    CREATE TRIGGER qms_approval_validate BEFORE INSERT ON qms.approval
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0012_validate_approval();
    CREATE TRIGGER qms_approval_guard BEFORE UPDATE OR DELETE ON qms.approval
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0012_reject_governance_mutation();

    ALTER TABLE qms.agent_decision ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.agent_decision FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.approval ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.approval FORCE ROW LEVEL SECURITY;

    EXECUTE format('CREATE POLICY qms_agent_decision_select ON qms.agent_decision FOR SELECT TO %I,%I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
    EXECUTE format('CREATE POLICY qms_agent_decision_insert ON qms.agent_decision FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
    EXECUTE format('CREATE POLICY qms_agent_decision_update ON qms.agent_decision FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
    EXECUTE format('CREATE POLICY qms_agent_decision_delete ON qms.agent_decision FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
    EXECUTE format('CREATE POLICY qms_agent_decision_migrator ON qms.agent_decision FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);

    EXECUTE format('CREATE POLICY qms_approval_select ON qms.approval FOR SELECT TO %I,%I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
    EXECUTE format('CREATE POLICY qms_approval_insert ON qms.approval FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',human_role);
    EXECUTE format('CREATE POLICY qms_approval_update ON qms.approval FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',human_role);
    EXECUTE format('CREATE POLICY qms_approval_delete ON qms.approval FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',human_role);
    EXECUTE format('CREATE POLICY qms_approval_migrator ON qms.approval FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);

    EXECUTE format('GRANT SELECT ON qms.agent_decision,qms.approval TO %I,%I,%I',app_role,worker_role,human_role);
    EXECUTE format('GRANT INSERT ON qms.agent_decision TO %I',worker_role);
    EXECUTE format('GRANT USAGE ON SCHEMA qms,governance,eventing,audit TO %I',human_role);
    EXECUTE format('GRANT SELECT ON qms.organization,qms.user_projection,qms.agent_run,qms.agent_run_recommendation,qms.recommendation,qms.agent_decision,qms.approval,governance.model_policy,governance.agent_definition TO %I',human_role);

    DROP POLICY foundation_user_projection_select ON qms.user_projection;
    DROP POLICY qms_agent_run_select ON qms.agent_run;
    EXECUTE format('CREATE POLICY foundation_user_projection_select ON qms.user_projection FOR SELECT TO %I,%I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
    EXECUTE format('CREATE POLICY qms_agent_run_select ON qms.agent_run FOR SELECT TO %I,%I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);

    DROP POLICY foundation_domain_event_select ON eventing.domain_event;
    DROP POLICY foundation_domain_event_insert ON eventing.domain_event;
    DROP POLICY foundation_outbox_select ON eventing.transactional_outbox;
    DROP POLICY foundation_outbox_insert ON eventing.transactional_outbox;
    EXECUTE format('CREATE POLICY foundation_domain_event_select ON eventing.domain_event FOR SELECT TO %I,%I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
    EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I,%I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
    EXECUTE format('CREATE POLICY foundation_outbox_select ON eventing.transactional_outbox FOR SELECT TO %I,%I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
    EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I,%I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role,human_role);
    EXECUTE format('GRANT SELECT,INSERT ON eventing.domain_event,eventing.transactional_outbox TO %I',human_role);
    EXECUTE format('GRANT EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) TO %I',human_role);
END
$migration$;

CREATE FUNCTION qms.foundation_0012_record_human_approval(
  p_id uuid,p_tenant_id uuid,p_organization_id uuid,p_agent_decision_id uuid,
  p_recommendation_id uuid,p_required_role text,p_decision text,p_decided_by_id uuid,
  p_adminapps_user_id uuid,p_comments text,p_decided_at timestamptz,p_trace_id uuid
) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,qms
AS $fn$
BEGIN
  IF p_tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid THEN
    RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='human approval tenant context mismatch';
  END IF;
  INSERT INTO qms.approval(
    id,tenant_id,organization_id,agent_decision_id,recommendation_id,required_role,
    decision,decided_by_id,adminapps_user_id_snapshot,actor_type,comments,decided_at,trace_id
  ) VALUES (
    p_id,p_tenant_id,p_organization_id,p_agent_decision_id,p_recommendation_id,p_required_role,
    p_decision,p_decided_by_id,p_adminapps_user_id,'human',p_comments,p_decided_at,p_trace_id
  );
  RETURN p_id;
END
$fn$;
REVOKE ALL ON FUNCTION qms.foundation_0012_record_human_approval(uuid,uuid,uuid,uuid,uuid,text,text,uuid,uuid,text,timestamptz,uuid) FROM PUBLIC;
DO $grant$
DECLARE human_role text := current_setting('foundation.human_approver_role',true);
BEGIN
  EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0012_record_human_approval(uuid,uuid,uuid,uuid,uuid,text,text,uuid,uuid,text,timestamptz,uuid) TO %I',human_role);
END
$grant$;
"""


REVERSE_SQL = r"""
DO $migration$
DECLARE
  app_role text := current_setting('foundation.app_role',true);
  worker_role text := current_setting('foundation.worker_role',true);
  human_role text := current_setting('foundation.human_approver_role',true);
BEGIN
  IF human_role IS NOT NULL AND human_role<>'' THEN
    EXECUTE format('REVOKE ALL PRIVILEGES ON qms.agent_decision,qms.approval FROM %I',human_role);
    EXECUTE format('REVOKE SELECT,INSERT ON eventing.domain_event,eventing.transactional_outbox FROM %I',human_role);
    EXECUTE format('REVOKE EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) FROM %I',human_role);
  END IF;
  DROP POLICY foundation_user_projection_select ON qms.user_projection;
  DROP POLICY qms_agent_run_select ON qms.agent_run;
  EXECUTE format('CREATE POLICY foundation_user_projection_select ON qms.user_projection FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('CREATE POLICY qms_agent_run_select ON qms.agent_run FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  DROP POLICY foundation_domain_event_select ON eventing.domain_event;
  DROP POLICY foundation_domain_event_insert ON eventing.domain_event;
  DROP POLICY foundation_outbox_select ON eventing.transactional_outbox;
  DROP POLICY foundation_outbox_insert ON eventing.transactional_outbox;
  EXECUTE format('CREATE POLICY foundation_domain_event_select ON eventing.domain_event FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('CREATE POLICY foundation_outbox_select ON eventing.transactional_outbox FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I,%I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
END
$migration$;
DROP FUNCTION qms.foundation_0012_record_human_approval(uuid,uuid,uuid,uuid,uuid,text,text,uuid,uuid,text,timestamptz,uuid);
DROP TABLE qms.approval;
DROP TABLE qms.agent_decision;
DROP FUNCTION qms.foundation_0012_reject_governance_mutation();
DROP FUNCTION qms.foundation_0012_validate_approval();
DROP FUNCTION qms.foundation_0012_validate_agent_decision();
"""


def apply_phase12(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase12(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0011_agent_definition_run_provenance_foundation")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase12, reverse_phase12)],
        state_operations=[
            migrations.CreateModel(name="AgentDecision", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("decision_type", models.CharField(max_length=120)),
                ("payload", models.JSONField(default=dict)),
                ("confidence", models.DecimalField(decimal_places=4, max_digits=5)),
                ("explainability", models.JSONField(default=dict)),
                ("decision_autonomy", models.PositiveSmallIntegerField()),
                ("human_gate_required", models.BooleanField()),
                ("trace_id", models.UUIDField()), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("agent_run", models.ForeignKey(db_column="agent_run_id", on_delete=django.db.models.deletion.PROTECT, related_name="decisions", to="foundation.agentrun")),
                ("recommendation", models.ForeignKey(blank=True, db_column="recommendation_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="agent_decisions", to="foundation.recommendation")),
            ], options={"managed": False, "db_table": 'qms"."agent_decision'}),
            migrations.CreateModel(name="Approval", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("required_role", models.CharField(max_length=160)),
                ("decision", models.CharField(choices=[("approve","Approve"),("reject","Reject"),("request_changes","Request changes")], max_length=24)),
                ("adminapps_user_id_snapshot", models.UUIDField()),
                ("actor_type", models.CharField(default="human", max_length=24)),
                ("comments", models.TextField(blank=True, null=True)),
                ("decided_at", models.DateTimeField()), ("trace_id", models.UUIDField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("agent_decision", models.ForeignKey(db_column="agent_decision_id", on_delete=django.db.models.deletion.PROTECT, related_name="human_approvals", to="foundation.agentdecision")),
                ("recommendation", models.ForeignKey(blank=True, db_column="recommendation_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="human_approvals", to="foundation.recommendation")),
                ("decided_by", models.ForeignKey(db_column="decided_by_id", on_delete=django.db.models.deletion.PROTECT, related_name="human_approvals", to="foundation.userprojection")),
            ], options={"managed": False, "db_table": 'qms"."approval'}),
        ],
    )]
