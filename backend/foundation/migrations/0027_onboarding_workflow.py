from django.db import migrations, models
import django.db.models.deletion
import uuid


FORWARD_SQL = r"""
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
DECLARE worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'Onboarding workflow roles are required';
  END IF;

  CREATE SCHEMA onboarding;
  CREATE TABLE onboarding.workflow_instance (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL,
    current_step varchar(80) NOT NULL,
    status varchar(24) NOT NULL DEFAULT 'in_progress',
    completed_steps jsonb NOT NULL DEFAULT '[]'::jsonb,
    state jsonb NOT NULL DEFAULT '{}'::jsonb,
    version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT onboarding_workflow_status CHECK(status IN ('in_progress','complete','blocked')),
    CONSTRAINT onboarding_workflow_steps CHECK(jsonb_typeof(completed_steps)='array'),
    CONSTRAINT onboarding_workflow_state CHECK(jsonb_typeof(state)='object'),
    CONSTRAINT onboarding_workflow_version CHECK(version > 0),
    CONSTRAINT onboarding_workflow_user_fk FOREIGN KEY(tenant_id,user_id)
      REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT onboarding_workflow_tenant_user_unique UNIQUE(tenant_id,user_id)
  );
  CREATE TABLE onboarding.workflow_transition (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    workflow_id uuid NOT NULL REFERENCES onboarding.workflow_instance(id) ON DELETE RESTRICT,
    step_key varchar(80) NOT NULL,
    from_status varchar(24),
    to_status varchar(24) NOT NULL,
    event_id uuid NOT NULL UNIQUE,
    event_type varchar(160) NOT NULL,
    source_reference text NOT NULL,
    provenance_hash char(64) NOT NULL CHECK(provenance_hash ~ '^[0-9a-f]{64}$'),
    actor_id varchar(255) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT onboarding_transition_status CHECK(to_status IN ('locked','available','in_progress','complete','blocked'))
  );
  CREATE INDEX onboarding_workflow_tenant_status_idx ON onboarding.workflow_instance(tenant_id,status);
  CREATE INDEX onboarding_transition_workflow_time_idx ON onboarding.workflow_transition(workflow_id,created_at DESC);
  ALTER TABLE onboarding.workflow_instance ENABLE ROW LEVEL SECURITY;
  ALTER TABLE onboarding.workflow_instance FORCE ROW LEVEL SECURITY;
  ALTER TABLE onboarding.workflow_transition ENABLE ROW LEVEL SECURITY;
  ALTER TABLE onboarding.workflow_transition FORCE ROW LEVEL SECURITY;
  EXECUTE format('CREATE POLICY onboarding_workflow_tenant ON onboarding.workflow_instance FOR ALL TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('CREATE POLICY onboarding_transition_tenant ON onboarding.workflow_transition FOR ALL TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('GRANT USAGE ON SCHEMA onboarding TO %I,%I',app_role,worker_role);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON onboarding.workflow_instance TO %I',app_role);
  EXECUTE format('GRANT SELECT,INSERT ON onboarding.workflow_transition TO %I,%I',app_role,worker_role);
  EXECUTE format('GRANT SELECT ON onboarding.workflow_instance TO %I',worker_role);
END
$migration$;
"""

REVERSE_SQL = r"""
DROP TABLE onboarding.workflow_transition;
DROP TABLE onboarding.workflow_instance;
DROP SCHEMA onboarding;
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0026_question_bank_versioning")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(
                    name="OnboardingWorkflow",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("current_step", models.CharField(max_length=80)),
                        ("status", models.CharField(default="in_progress", max_length=24)),
                        ("completed_steps", models.JSONField(default=list)),
                        ("state", models.JSONField(default=dict)),
                        ("version", models.PositiveIntegerField(default=1)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                        ("user", models.ForeignKey(db_column="user_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.userprojection")),
                    ],
                    options={"db_table": 'onboarding"."workflow_instance', "managed": False},
                ),
                migrations.CreateModel(
                    name="OnboardingTransition",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("step_key", models.CharField(max_length=80)),
                        ("from_status", models.CharField(blank=True, max_length=24, null=True)),
                        ("to_status", models.CharField(max_length=24)),
                        ("event_id", models.UUIDField(unique=True)),
                        ("event_type", models.CharField(max_length=160)),
                        ("source_reference", models.TextField()),
                        ("provenance_hash", models.CharField(max_length=64)),
                        ("actor_id", models.CharField(max_length=255)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                        ("workflow", models.ForeignKey(db_column="workflow_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.onboardingworkflow")),
                    ],
                    options={"db_table": 'onboarding"."workflow_transition', "managed": False},
                ),
            ],
        ),
    ]