"""Phase 19 human-attested EffectivenessCheck foundation."""

import uuid

from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
  app_role text := current_setting('foundation.app_role', true);
  human_role text := current_setting('foundation.human_approver_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR human_role IS NULL OR human_role='' THEN
    RAISE EXCEPTION 'Phase 19 app and human reviewer read roles are required';
  END IF;

  CREATE TABLE qms.effectiveness_check (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    organization_id uuid NOT NULL,
    action_execution_id uuid NOT NULL,
    receipt_id uuid NOT NULL,
    action_plan_id uuid NOT NULL,
    execution_authorization_id uuid NOT NULL,
    agent_decision_id uuid NOT NULL,
    recommendation_id uuid NOT NULL,
    opportunity_lineage_id uuid NOT NULL,
    before_opportunity_revision_id uuid NOT NULL,
    resulting_opportunity_revision_id uuid NOT NULL,
    outcome varchar(24) NOT NULL,
    assessment_method varchar(32) NOT NULL,
    criteria_hash char(64) NOT NULL,
    planning_context_hash char(64) NOT NULL,
    reason_code varchar(80),
    explanation text,
    due_at timestamptz NOT NULL,
    assessed_at timestamptz NOT NULL,
    measurement_definition_id uuid,
    predecessor_id uuid UNIQUE,
    revision integer NOT NULL,
    correction_reason text,
    actor_user_projection_id uuid NOT NULL,
    actor_external_id_snapshot uuid NOT NULL,
    actor_type varchar(24) NOT NULL,
    authority_context_version varchar(120) NOT NULL,
    authority_decision_reference varchar(255) NOT NULL,
    policy_id varchar(120) NOT NULL,
    trace_id uuid NOT NULL,
    correlation_id uuid,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_effectiveness_check_tenant_org_id_unique UNIQUE(tenant_id,organization_id,id),
    CONSTRAINT qms_effectiveness_check_execution_revision_unique UNIQUE(action_execution_id,revision),
    CONSTRAINT qms_effectiveness_check_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_execution_fk FOREIGN KEY(tenant_id,organization_id,action_execution_id)
      REFERENCES qms.action_execution(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_receipt_fk FOREIGN KEY(tenant_id,organization_id,receipt_id)
      REFERENCES qms.action_execution_receipt(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_plan_fk FOREIGN KEY(tenant_id,organization_id,action_plan_id)
      REFERENCES qms.action_plan(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_authorization_fk FOREIGN KEY(tenant_id,organization_id,execution_authorization_id)
      REFERENCES qms.execution_authorization(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_decision_fk FOREIGN KEY(tenant_id,organization_id,agent_decision_id)
      REFERENCES qms.agent_decision(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_recommendation_fk FOREIGN KEY(tenant_id,organization_id,recommendation_id)
      REFERENCES qms.recommendation(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_before_fk FOREIGN KEY(tenant_id,organization_id,before_opportunity_revision_id)
      REFERENCES qms.opportunity(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_result_fk FOREIGN KEY(tenant_id,organization_id,resulting_opportunity_revision_id)
      REFERENCES qms.opportunity(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_measurement_fk FOREIGN KEY(tenant_id,organization_id,measurement_definition_id)
      REFERENCES qms.measurement_definition(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_actor_fk FOREIGN KEY(tenant_id,actor_user_projection_id)
      REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_predecessor_fk FOREIGN KEY(tenant_id,organization_id,predecessor_id)
      REFERENCES qms.effectiveness_check(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_check_outcome CHECK(outcome IN ('effective','ineffective','inconclusive','unknown')),
    CONSTRAINT qms_effectiveness_check_method CHECK(assessment_method IN ('human_review','system_assisted','measurement_derived')),
    CONSTRAINT qms_effectiveness_check_hashes CHECK(criteria_hash ~ '^[0-9a-f]{64}$' AND planning_context_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT qms_effectiveness_check_actor CHECK(actor_type='human'),
    CONSTRAINT qms_effectiveness_check_policy CHECK(policy_id='effectiveness-check-policy/v1'),
    CONSTRAINT qms_effectiveness_check_timing CHECK(assessed_at>=due_at),
    CONSTRAINT qms_effectiveness_check_uncertainty CHECK(
      (outcome IN ('inconclusive','unknown') AND reason_code IS NOT NULL AND btrim(reason_code)<>'' AND explanation IS NOT NULL AND btrim(explanation)<>'') OR
      (outcome IN ('effective','ineffective') AND reason_code IS NULL AND explanation IS NULL)),
    CONSTRAINT qms_effectiveness_check_measurement_condition CHECK(
      (assessment_method='measurement_derived' AND measurement_definition_id IS NOT NULL) OR
      (assessment_method<>'measurement_derived' AND measurement_definition_id IS NULL)),
    CONSTRAINT qms_effectiveness_check_revision_correction CHECK(
      (predecessor_id IS NULL AND revision=1 AND correction_reason IS NULL) OR
      (predecessor_id IS NOT NULL AND revision>1 AND correction_reason IS NOT NULL AND btrim(correction_reason)<>'')),
    CONSTRAINT qms_effectiveness_check_authority_nonblank CHECK(
      btrim(authority_context_version)<>'' AND btrim(authority_decision_reference)<>'')
  );

  CREATE TABLE qms.effectiveness_evidence (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    organization_id uuid NOT NULL,
    effectiveness_check_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    evidence_lineage_id_snapshot uuid NOT NULL,
    evidence_revision_snapshot integer NOT NULL CHECK(evidence_revision_snapshot>0),
    evidence_content_hash_snapshot char(64) NOT NULL CHECK(evidence_content_hash_snapshot ~ '^[0-9a-f]{64}$'),
    criterion_role varchar(160) NOT NULL CHECK(btrim(criterion_role)<>''),
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_effectiveness_evidence_check_revision_unique UNIQUE(effectiveness_check_id,evidence_id),
    CONSTRAINT qms_effectiveness_evidence_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_evidence_check_fk FOREIGN KEY(tenant_id,organization_id,effectiveness_check_id)
      REFERENCES qms.effectiveness_check(tenant_id,organization_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_effectiveness_evidence_revision_fk FOREIGN KEY(tenant_id,organization_id,evidence_id)
      REFERENCES qms.evidence(tenant_id,organization_id,id) ON DELETE RESTRICT
  );

  CREATE INDEX qms_effectiveness_check_execution_idx ON qms.effectiveness_check(tenant_id,organization_id,action_execution_id,revision);
  CREATE INDEX qms_effectiveness_check_due_idx ON qms.effectiveness_check(tenant_id,organization_id,due_at);
  CREATE INDEX qms_effectiveness_evidence_check_idx ON qms.effectiveness_evidence(tenant_id,organization_id,effectiveness_check_id);

  CREATE FUNCTION qms.foundation_0017_reject_effectiveness_mutation()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  BEGIN
    RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='EffectivenessCheck history is immutable';
  END $fn$;

  CREATE FUNCTION qms.foundation_0017_validate_effectiveness_check()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  DECLARE e record; r record; a record; p record; d record; b record; n record; u record; prior record;
  BEGIN
    IF NEW.id=NEW.predecessor_id THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='EffectivenessCheck cannot supersede itself';
    END IF;
    IF NEW.tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid OR
       NEW.organization_id IS DISTINCT FROM NULLIF(current_setting('app.organization_id',true),'')::uuid OR
       NEW.actor_external_id_snapshot::text IS DISTINCT FROM current_setting('app.actor_id',true) OR
       current_setting('app.mfa_verified',true)<>'true' OR current_setting('app.access_active',true)<>'true' OR
       position('qms.effectiveness_check.record' in current_setting('app.effectiveness_permissions',true))=0 OR
       NEW.authority_context_version IS DISTINCT FROM current_setting('app.authority_context_version',true) OR
       NEW.authority_decision_reference IS DISTINCT FROM current_setting('app.authority_decision_reference',true) THEN
      RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='trusted Effectiveness reviewer authority context required';
    END IF;
    SELECT * INTO e FROM qms.action_execution WHERE id=NEW.action_execution_id;
    SELECT * INTO r FROM qms.action_execution_receipt WHERE id=NEW.receipt_id;
    SELECT * INTO a FROM qms.execution_authorization WHERE id=NEW.execution_authorization_id;
    SELECT * INTO p FROM qms.action_plan WHERE id=NEW.action_plan_id;
    SELECT * INTO d FROM qms.agent_decision WHERE id=NEW.agent_decision_id;
    SELECT * INTO b FROM qms.opportunity WHERE id=NEW.before_opportunity_revision_id;
    SELECT * INTO n FROM qms.opportunity WHERE id=NEW.resulting_opportunity_revision_id;
    SELECT * INTO u FROM qms.user_projection WHERE id=NEW.actor_user_projection_id;
    IF e.id IS NULL OR r.id IS NULL OR a.id IS NULL OR p.id IS NULL OR d.id IS NULL OR b.id IS NULL OR n.id IS NULL OR u.id IS NULL OR
       e.status<>'succeeded' OR e.executor_type<>'controlled_opportunity' OR
       r.action_execution_id IS DISTINCT FROM e.id OR r.outcome<>'opportunity_deferred' OR
       r.executor_type<>e.executor_type OR r.action_plan_hash<>e.action_plan_hash OR
       e.execution_authorization_id IS DISTINCT FROM a.id OR e.action_plan_id IS DISTINCT FROM p.id OR
       e.action_plan_hash<>p.action_plan_hash OR a.action_plan_id IS DISTINCT FROM p.id OR
       a.action_plan_hash<>p.action_plan_hash OR a.agent_decision_id IS DISTINCT FROM d.id OR
       a.recommendation_id IS DISTINCT FROM d.recommendation_id OR p.agent_decision_id IS DISTINCT FROM d.id OR
       p.recommendation_id IS DISTINCT FROM d.recommendation_id OR NEW.recommendation_id IS DISTINCT FROM d.recommendation_id OR
       p.action_type<>'opportunity.defer_evaluation' OR p.target_type<>'Opportunity' OR
       p.target_id::uuid IS DISTINCT FROM NEW.opportunity_lineage_id OR
       b.lineage_id IS DISTINCT FROM NEW.opportunity_lineage_id OR n.lineage_id IS DISTINCT FROM NEW.opportunity_lineage_id OR
       n.previous_revision_id IS DISTINCT FROM b.id OR n.status<>'deferred' OR
       r.result->>'before_revision_id'<>b.id::text OR r.result->>'after_revision_id'<>n.id::text OR
       r.result->>'opportunity_lineage_id'<>NEW.opportunity_lineage_id::text OR
       r.result->>'action_type'<>'opportunity.defer_evaluation' OR
       COALESCE((r.result->>'effectiveness_claimed')::boolean,true)<>false OR
       NEW.due_at<=n.created_at OR u.adminapps_user_id IS DISTINCT FROM NEW.actor_external_id_snapshot THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='EffectivenessCheck exact execution provenance validation failed';
    END IF;
    IF NEW.predecessor_id IS NOT NULL THEN
      IF position('qms.effectiveness_check.supersede' in current_setting('app.effectiveness_permissions',true))=0 THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='Effectiveness supersede permission required';
      END IF;
      SELECT * INTO prior FROM qms.effectiveness_check WHERE id=NEW.predecessor_id FOR UPDATE;
      IF prior.id IS NULL OR NEW.revision<>prior.revision+1 OR
         NEW.action_execution_id IS DISTINCT FROM prior.action_execution_id OR
         NEW.receipt_id IS DISTINCT FROM prior.receipt_id OR NEW.action_plan_id IS DISTINCT FROM prior.action_plan_id OR
         NEW.execution_authorization_id IS DISTINCT FROM prior.execution_authorization_id OR
         NEW.agent_decision_id IS DISTINCT FROM prior.agent_decision_id OR
         NEW.recommendation_id IS DISTINCT FROM prior.recommendation_id OR
         NEW.opportunity_lineage_id IS DISTINCT FROM prior.opportunity_lineage_id OR
         NEW.before_opportunity_revision_id IS DISTINCT FROM prior.before_opportunity_revision_id OR
         NEW.resulting_opportunity_revision_id IS DISTINCT FROM prior.resulting_opportunity_revision_id OR
         EXISTS(SELECT 1 FROM qms.effectiveness_check WHERE predecessor_id=prior.id) THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='EffectivenessCheck supersession must be exact and linear';
      END IF;
    END IF;
    RETURN NEW;
  END $fn$;

  CREATE FUNCTION qms.foundation_0017_validate_effectiveness_evidence()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  DECLARE e record; c record;
  BEGIN
    SELECT * INTO e FROM qms.evidence WHERE id=NEW.evidence_id;
    SELECT * INTO c FROM qms.effectiveness_check WHERE id=NEW.effectiveness_check_id;
    IF e.id IS NULL OR c.id IS NULL OR e.tenant_id IS DISTINCT FROM NEW.tenant_id OR
       e.organization_id IS DISTINCT FROM NEW.organization_id OR
       e.lineage_id IS DISTINCT FROM NEW.evidence_lineage_id_snapshot OR
       e.revision IS DISTINCT FROM NEW.evidence_revision_snapshot OR
       e.content_hash IS DISTINCT FROM NEW.evidence_content_hash_snapshot THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='EffectivenessEvidence must bind one exact immutable Evidence revision';
    END IF;
    RETURN NEW;
  END $fn$;

  CREATE FUNCTION qms.foundation_0017_require_effectiveness_evidence()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  BEGIN
    IF NOT EXISTS(SELECT 1 FROM qms.effectiveness_evidence WHERE effectiveness_check_id=NEW.id) THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='EffectivenessCheck requires at least one exact Evidence revision';
    END IF;
    RETURN NULL;
  END $fn$;

  CREATE TRIGGER qms_effectiveness_check_validate BEFORE INSERT ON qms.effectiveness_check FOR EACH ROW EXECUTE FUNCTION qms.foundation_0017_validate_effectiveness_check();
  CREATE TRIGGER qms_effectiveness_check_guard BEFORE UPDATE OR DELETE ON qms.effectiveness_check FOR EACH ROW EXECUTE FUNCTION qms.foundation_0017_reject_effectiveness_mutation();
  CREATE TRIGGER qms_effectiveness_evidence_validate BEFORE INSERT ON qms.effectiveness_evidence FOR EACH ROW EXECUTE FUNCTION qms.foundation_0017_validate_effectiveness_evidence();
  CREATE TRIGGER qms_effectiveness_evidence_guard BEFORE UPDATE OR DELETE ON qms.effectiveness_evidence FOR EACH ROW EXECUTE FUNCTION qms.foundation_0017_reject_effectiveness_mutation();
  CREATE CONSTRAINT TRIGGER qms_effectiveness_check_evidence_required AFTER INSERT ON qms.effectiveness_check
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION qms.foundation_0017_require_effectiveness_evidence();

  ALTER TABLE qms.effectiveness_check ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.effectiveness_check FORCE ROW LEVEL SECURITY;
  ALTER TABLE qms.effectiveness_evidence ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.effectiveness_evidence FORCE ROW LEVEL SECURITY;
  EXECUTE format('CREATE POLICY qms_effectiveness_check_select ON qms.effectiveness_check FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,human_role);
  EXECUTE format('CREATE POLICY qms_effectiveness_check_insert ON qms.effectiveness_check FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  EXECUTE format('CREATE POLICY qms_effectiveness_check_update ON qms.effectiveness_check FOR UPDATE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  EXECUTE format('CREATE POLICY qms_effectiveness_check_migrator ON qms.effectiveness_check FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
  EXECUTE format('CREATE POLICY qms_effectiveness_evidence_select ON qms.effectiveness_evidence FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,human_role);
  EXECUTE format('CREATE POLICY qms_effectiveness_evidence_insert ON qms.effectiveness_evidence FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  EXECUTE format('CREATE POLICY qms_effectiveness_evidence_migrator ON qms.effectiveness_evidence FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.effectiveness_check TO %I',app_role);
  EXECUTE format('GRANT SELECT,INSERT ON qms.effectiveness_evidence TO %I',app_role);
  EXECUTE format('GRANT SELECT ON qms.effectiveness_check,qms.effectiveness_evidence TO %I',human_role);
END $migration$;
"""


REVERSE_SQL = r"""
DO $migration$
BEGIN
  IF EXISTS(SELECT 1 FROM qms.effectiveness_check) THEN
    RAISE EXCEPTION '0017 is forward-only after EffectivenessCheck history exists';
  END IF;
END $migration$;
DROP TABLE qms.effectiveness_evidence;
DROP TABLE qms.effectiveness_check;
DROP FUNCTION qms.foundation_0017_require_effectiveness_evidence();
DROP FUNCTION qms.foundation_0017_validate_effectiveness_evidence();
DROP FUNCTION qms.foundation_0017_validate_effectiveness_check();
DROP FUNCTION qms.foundation_0017_reject_effectiveness_mutation();
"""


def apply_phase19(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase19(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0016_controlled_execution_recovery_hardening")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase19, reverse_phase19)],
        state_operations=[
            migrations.CreateModel(name="EffectivenessCheck", fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
                ("opportunity_lineage_id",models.UUIDField()),
                ("outcome",models.CharField(choices=[("effective","Effective"),("ineffective","Ineffective"),("inconclusive","Inconclusive"),("unknown","Unknown")],max_length=24)),
                ("assessment_method",models.CharField(choices=[("human_review","Human review"),("system_assisted","System assisted"),("measurement_derived","Measurement derived")],max_length=32)),
                ("criteria_hash",models.CharField(max_length=64)),("planning_context_hash",models.CharField(max_length=64)),
                ("reason_code",models.CharField(blank=True,max_length=80,null=True)),("explanation",models.TextField(blank=True,null=True)),
                ("due_at",models.DateTimeField()),("assessed_at",models.DateTimeField()),("revision",models.PositiveIntegerField()),
                ("correction_reason",models.TextField(blank=True,null=True)),("actor_external_id_snapshot",models.UUIDField()),
                ("actor_type",models.CharField(default="human",max_length=24)),("authority_context_version",models.CharField(max_length=120)),
                ("authority_decision_reference",models.CharField(max_length=255)),("policy_id",models.CharField(default="effectiveness-check-policy/v1",max_length=120)),
                ("trace_id",models.UUIDField()),("correlation_id",models.UUIDField(blank=True,null=True)),("created_at",models.DateTimeField(auto_now_add=True)),
            ],options={"managed":False,"db_table":'qms"."effectiveness_check'}),
            migrations.CreateModel(name="EffectivenessEvidence", fields=[
                ("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
                ("evidence_lineage_id_snapshot",models.UUIDField()),("evidence_revision_snapshot",models.PositiveIntegerField()),
                ("evidence_content_hash_snapshot",models.CharField(max_length=64)),("criterion_role",models.CharField(max_length=160)),
                ("created_at",models.DateTimeField(auto_now_add=True)),
            ],options={"managed":False,"db_table":'qms"."effectiveness_evidence'}),
        ],
    )]
