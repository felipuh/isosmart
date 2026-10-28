from django.db import migrations, models
import django.db.models.deletion
import uuid


FORWARD_SQL = r"""
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
DECLARE worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'Capability activation roles are required';
  END IF;
  CREATE TABLE qms.capability_activation (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    agent_definition_id uuid NOT NULL REFERENCES governance.agent_definition(id) ON DELETE RESTRICT,
    status varchar(16) NOT NULL DEFAULT 'active',
    activated_by varchar(255) NOT NULL,
    provenance_hash char(64) NOT NULL CHECK(provenance_hash ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_capability_activation_status CHECK(status IN ('active','revoked')),
    CONSTRAINT qms_capability_activation_unique UNIQUE(tenant_id,agent_definition_id)
  );
  CREATE INDEX qms_capability_activation_tenant_status_idx ON qms.capability_activation(tenant_id,status);
  ALTER TABLE qms.capability_activation ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.capability_activation FORCE ROW LEVEL SECURITY;
  EXECUTE format('CREATE POLICY qms_capability_activation_tenant ON qms.capability_activation FOR ALL TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.capability_activation TO %I',app_role);
  EXECUTE format('GRANT SELECT ON qms.capability_activation TO %I',worker_role);
END
$migration$;
"""

REVERSE_SQL = "DROP TABLE qms.capability_activation;"


class Migration(migrations.Migration):
    dependencies = [("foundation", "0027_onboarding_workflow")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(
                    name="CapabilityActivation",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("status", models.CharField(default="active", max_length=16)),
                        ("activated_by", models.CharField(max_length=255)),
                        ("provenance_hash", models.CharField(max_length=64)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("agent_definition", models.ForeignKey(db_column="agent_definition_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.agentdefinition")),
                        ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                    ],
                    options={"db_table": 'qms"."capability_activation', "managed": False},
                ),
            ],
        ),
    ]