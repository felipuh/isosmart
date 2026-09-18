"""Global pre-projection receipt: external tenant UUID exists before local FK."""

from django.db import migrations


FORWARD = """
CREATE TABLE eventing.adminapps_ingress_receipt (
  event_id uuid PRIMARY KEY,
  adminapps_tenant_id uuid NOT NULL,
  issuer varchar(80) NOT NULL,
  authenticated boolean NOT NULL,
  payload_hash char(64) NOT NULL,
  schema_version integer NOT NULL,
  source_version bigint NOT NULL,
  trace_id uuid NOT NULL,
  received_at timestamptz NOT NULL DEFAULT statement_timestamp(),
  processed_at timestamptz,
  status varchar(24) NOT NULL,
  replay_count integer NOT NULL DEFAULT 0,
  failure_code varchar(80),
  projection_id uuid,
  CONSTRAINT adminapps_receipt_status_valid CHECK (status IN ('received','processed','failed'))
);
CREATE INDEX adminapps_ingress_tenant_received_idx ON eventing.adminapps_ingress_receipt(adminapps_tenant_id,received_at);
CREATE TABLE qms.organization_create_request (
  tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
  request_key uuid NOT NULL,
  request_hash char(64) NOT NULL,
  result jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
  PRIMARY KEY (tenant_id,request_key)
);
ALTER TABLE qms.organization_create_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE qms.organization_create_request FORCE ROW LEVEL SECURITY;
ALTER TABLE eventing.adminapps_ingress_receipt ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventing.adminapps_ingress_receipt FORCE ROW LEVEL SECURITY;
DO $migration$ DECLARE projector_role text := current_setting('foundation.projector_role', true);
  app_role text := current_setting('foundation.app_role', true);
BEGIN
  IF projector_role IS NULL OR projector_role = '' OR app_role IS NULL OR app_role = '' THEN
    RAISE EXCEPTION 'foundation.projector_role and foundation.app_role are required';
  END IF;
  EXECUTE format('CREATE POLICY organization_create_request_app ON qms.organization_create_request FOR ALL TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
  EXECUTE format('CREATE POLICY organization_create_request_migrator ON qms.organization_create_request FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);
  EXECUTE format('GRANT SELECT,INSERT ON qms.organization_create_request TO %I',app_role);
  EXECUTE format('CREATE POLICY adminapps_receipt_projector ON eventing.adminapps_ingress_receipt FOR ALL TO %I USING (current_setting(''app.projection_source'',true)=''adminapps'') WITH CHECK (current_setting(''app.projection_source'',true)=''adminapps'')',projector_role);
  EXECUTE format('CREATE POLICY adminapps_receipt_migrator ON eventing.adminapps_ingress_receipt FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);
  EXECUTE format('GRANT USAGE ON SCHEMA eventing TO %I',projector_role);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON eventing.adminapps_ingress_receipt TO %I',projector_role);
END $migration$;
"""


def apply(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(FORWARD)


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute('DROP TABLE qms.organization_create_request; DROP TABLE eventing.adminapps_ingress_receipt')


class Migration(migrations.Migration):
    dependencies = [('foundation', '0023_retained_synthetic_source_reference_application')]
    operations = [migrations.RunPython(apply, reverse)]
