"""Owner-approved Step 11 execution provenance; not a source-defined catalog row."""

import uuid

from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = r'''
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
        worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'Value Discovery runtime roles are required';
  END IF;
  CREATE TABLE onboarding.value_discovery_execution (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    organization_id uuid NOT NULL,
    user_id uuid NOT NULL,
    transition_event_id uuid NOT NULL UNIQUE,
    profile_hash char(64) NOT NULL CHECK(profile_hash ~ '^[0-9a-f]{64}$'),
    declared_purpose_hash char(64) NOT NULL CHECK(declared_purpose_hash ~ '^[0-9a-f]{64}$'),
    execution_mode varchar(32) NOT NULL CHECK(execution_mode IN ('REAL_AI','CONTROLLED_TEST')),
    provider varchar(120) NOT NULL,
    model_identifier varchar(200) NOT NULL,
    result jsonb NOT NULL,
    result_hash char(64) NOT NULL CHECK(result_hash ~ '^[0-9a-f]{64}$'),
    evidence_id uuid NOT NULL REFERENCES qms.evidence(id) ON DELETE RESTRICT,
    transition_id uuid NOT NULL REFERENCES onboarding.workflow_transition(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT onboarding_value_discovery_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT onboarding_value_discovery_user_fk FOREIGN KEY(tenant_id,user_id)
      REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT onboarding_value_discovery_result_object CHECK(jsonb_typeof(result)='object'),
    CONSTRAINT onboarding_value_discovery_nonblank CHECK(btrim(provider)<>'' AND btrim(model_identifier)<>'')
  );
  CREATE INDEX onboarding_value_discovery_tenant_org_idx ON onboarding.value_discovery_execution(tenant_id,organization_id,created_at DESC);
  ALTER TABLE onboarding.value_discovery_execution ENABLE ROW LEVEL SECURITY;
  ALTER TABLE onboarding.value_discovery_execution FORCE ROW LEVEL SECURITY;
  EXECUTE format($policy$
    CREATE POLICY onboarding_value_discovery_tenant
    ON onboarding.value_discovery_execution
    FOR ALL TO %I,%I
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  $policy$, app_role, worker_role);
  EXECUTE format('GRANT SELECT,INSERT ON onboarding.value_discovery_execution TO %I,%I', app_role, worker_role);
END
$migration$;
'''

REVERSE_SQL = 'DROP TABLE onboarding.value_discovery_execution;'


class Migration(migrations.Migration):
    dependencies = [("foundation", "0037_qms_audit_capa_foundation")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(
                    name="ValueDiscoveryExecution",
                    fields=[
                        ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                        ("transition_event_id", models.UUIDField(unique=True)),
                        ("profile_hash", models.CharField(max_length=64)),
                        ("declared_purpose_hash", models.CharField(max_length=64)),
                        ("execution_mode", models.CharField(max_length=32)),
                        ("provider", models.CharField(max_length=120)),
                        ("model_identifier", models.CharField(max_length=200)),
                        ("result", models.JSONField()),
                        ("result_hash", models.CharField(max_length=64)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("tenant", models.ForeignKey(to="foundation.tenantprojection", on_delete=django.db.models.deletion.PROTECT, db_column="tenant_id")),
                        ("organization", models.ForeignKey(to="foundation.organization", on_delete=django.db.models.deletion.PROTECT, db_column="organization_id")),
                        ("user", models.ForeignKey(to="foundation.userprojection", on_delete=django.db.models.deletion.PROTECT, db_column="user_id")),
                        ("evidence", models.ForeignKey(to="foundation.evidence", on_delete=django.db.models.deletion.PROTECT, db_column="evidence_id")),
                        ("transition", models.ForeignKey(to="foundation.onboardingtransition", on_delete=django.db.models.deletion.PROTECT, db_column="transition_id")),
                    ],
                    options={"managed": False, "db_table": 'onboarding"."value_discovery_execution'},
                ),
            ],
        ),
    ]
