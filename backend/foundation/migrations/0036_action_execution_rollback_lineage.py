"""Tenant-safe rollback lineage for the one controlled reversible action."""

import uuid

from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE app_role text:=current_setting('foundation.app_role',true);
        executor_role text:=current_setting('foundation.executor_role',true);
        authorizer_role text:=current_setting('foundation.execution_authorizer_role',true);
BEGIN
 IF app_role IS NULL OR app_role='' OR executor_role IS NULL OR executor_role='' OR authorizer_role IS NULL OR authorizer_role='' THEN
   RAISE EXCEPTION 'ActionExecution rollback runtime roles are required';
 END IF;
 CREATE TABLE qms.action_execution_rollback (
   id uuid PRIMARY KEY,
   tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
   organization_id uuid NOT NULL,
   original_execution_id uuid NOT NULL,
   compensating_execution_id uuid NOT NULL,
   reason text NOT NULL,
   idempotency_key varchar(200) NOT NULL,
   trace_id uuid NOT NULL,
   created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
   CONSTRAINT qms_action_execution_rollback_original_unique UNIQUE(original_execution_id),
   CONSTRAINT qms_action_execution_rollback_compensating_unique UNIQUE(compensating_execution_id),
   CONSTRAINT qms_action_execution_rollback_tenant_key_unique UNIQUE(tenant_id,idempotency_key),
   CONSTRAINT qms_action_execution_rollback_not_self CHECK(original_execution_id<>compensating_execution_id),
   CONSTRAINT qms_action_execution_rollback_reason_nonblank CHECK(btrim(reason)<>''),
   CONSTRAINT qms_action_execution_rollback_key_nonblank CHECK(btrim(idempotency_key)<>''),
   CONSTRAINT qms_action_execution_rollback_original_fk
     FOREIGN KEY(tenant_id,organization_id,original_execution_id)
     REFERENCES qms.action_execution(tenant_id,organization_id,id) ON DELETE RESTRICT,
   CONSTRAINT qms_action_execution_rollback_compensating_fk
     FOREIGN KEY(tenant_id,organization_id,compensating_execution_id)
     REFERENCES qms.action_execution(tenant_id,organization_id,id) ON DELETE RESTRICT,
   CONSTRAINT qms_action_execution_rollback_org_fk FOREIGN KEY(tenant_id,organization_id)
     REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT
 );
 CREATE FUNCTION qms.foundation_0036_validate_action_execution_rollback() RETURNS trigger
 LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
 DECLARE original qms.action_execution%ROWTYPE; compensation qms.action_execution%ROWTYPE;
         original_plan qms.action_plan%ROWTYPE; compensation_plan qms.action_plan%ROWTYPE;
         original_receipt qms.action_execution_receipt%ROWTYPE;
         compensation_receipt qms.action_execution_receipt%ROWTYPE;
 BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='ActionExecution rollback lineage is append-only'; END IF;
  SELECT * INTO STRICT original FROM qms.action_execution WHERE id=NEW.original_execution_id;
  SELECT * INTO STRICT compensation FROM qms.action_execution WHERE id=NEW.compensating_execution_id;
  SELECT * INTO STRICT original_plan FROM qms.action_plan WHERE id=original.action_plan_id;
  SELECT * INTO STRICT compensation_plan FROM qms.action_plan WHERE id=compensation.action_plan_id;
  SELECT * INTO STRICT original_receipt FROM qms.action_execution_receipt WHERE action_execution_id=original.id;
  SELECT * INTO STRICT compensation_receipt FROM qms.action_execution_receipt WHERE action_execution_id=compensation.id;
  IF original.tenant_id<>NEW.tenant_id OR compensation.tenant_id<>NEW.tenant_id OR
     original.organization_id<>NEW.organization_id OR compensation.organization_id<>NEW.organization_id OR
     original.status<>'succeeded' OR compensation.status<>'succeeded' OR
     original.executor_type<>'controlled_opportunity' OR compensation.executor_type<>'controlled_opportunity' OR
     original_plan.action_type<>'opportunity.defer_evaluation' OR
     compensation_plan.action_type<>'opportunity.resume_evaluation' OR
     original_receipt.outcome<>'opportunity_deferred' OR
     compensation_receipt.outcome<>'opportunity_evaluation_resumed' OR
     original_receipt.result->>'opportunity_lineage_id' IS DISTINCT FROM compensation_receipt.result->>'opportunity_lineage_id' THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='invalid ActionExecution rollback compensation lineage';
  END IF;
  RETURN NEW;
 END $fn$;
 CREATE TRIGGER qms_action_execution_rollback_validate
 BEFORE INSERT OR UPDATE OR DELETE ON qms.action_execution_rollback
 FOR EACH ROW EXECUTE FUNCTION qms.foundation_0036_validate_action_execution_rollback();
 ALTER TABLE qms.action_execution_rollback ENABLE ROW LEVEL SECURITY;
 ALTER TABLE qms.action_execution_rollback FORCE ROW LEVEL SECURITY;
 EXECUTE format('CREATE POLICY qms_action_execution_rollback_select ON qms.action_execution_rollback FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_rollback_insert ON qms.action_execution_rollback FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',executor_role);
 EXECUTE format('CREATE POLICY qms_action_execution_rollback_migrator ON qms.action_execution_rollback FOR ALL TO %I USING(true) WITH CHECK(true)',current_user);
 EXECUTE format('GRANT SELECT ON qms.action_execution_rollback TO %I',app_role);
 EXECUTE format('GRANT SELECT,INSERT ON qms.action_execution_rollback TO %I',executor_role);
 -- The narrowly-scoped rollback command reads the already-authorized source,
 -- receipt, plan and compensation authorization under the executor identity.
 -- RLS remains tenant-bound; this adds no DML privilege on those histories.
 EXECUTE format('GRANT SELECT ON qms.action_execution,qms.action_execution_receipt,qms.action_plan,qms.execution_authorization TO %I',executor_role);
 EXECUTE format('DROP POLICY qms_execution_authorization_select ON qms.execution_authorization');
 EXECUTE format('CREATE POLICY qms_execution_authorization_select ON qms.execution_authorization FOR SELECT TO %I,%I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,executor_role,authorizer_role);
END $migration$;
"""

REVERSE_SQL = r"""
DROP TABLE qms.action_execution_rollback;
DROP FUNCTION IF EXISTS qms.foundation_0036_validate_action_execution_rollback();
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0035_user_projection_profile_fields")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(
                    name="ActionExecutionRollback",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("reason", models.TextField()),
                        ("idempotency_key", models.CharField(max_length=200)),
                        ("trace_id", models.UUIDField()),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                    ],
                    options={"managed": False, "db_table": 'qms"."action_execution_rollback'},
                ),
            ],
        ),
    ]
