"""Tenant-safe, source-field-only QMS audit/CAPA foundation."""

import uuid

from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = r"""
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
        worker_role text := current_setting('foundation.worker_role', true);
        tbl text;
BEGIN
 IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' THEN
   RAISE EXCEPTION 'QMS audit/CAPA runtime roles are required';
 END IF;
 CREATE TABLE qms.audit (
   audit_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
   organization_id uuid NOT NULL, scope text NOT NULL, criteria text NOT NULL, status varchar(80) NOT NULL,
   lead_auditor varchar(255) NOT NULL, created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
   CONSTRAINT qms_audit_org_fk FOREIGN KEY(tenant_id,organization_id) REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
   CONSTRAINT qms_audit_tenant_org_id_unique UNIQUE(tenant_id,organization_id,audit_id),
   CONSTRAINT qms_audit_text_nonblank CHECK(btrim(scope)<>'' AND btrim(criteria)<>'' AND btrim(status)<>'' AND btrim(lead_auditor)<>'')
 );
 CREATE TABLE qms.finding (
   finding_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
   organization_id uuid NOT NULL, audit_id uuid NOT NULL, requirement_id uuid NOT NULL REFERENCES normative.requirement_control(id) ON DELETE RESTRICT,
   type varchar(80) NOT NULL, statement text NOT NULL, evidence_id uuid NOT NULL REFERENCES qms.evidence(id) ON DELETE RESTRICT,
   created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
   CONSTRAINT qms_finding_audit_fk FOREIGN KEY(tenant_id,organization_id,audit_id) REFERENCES qms.audit(tenant_id,organization_id,audit_id) ON DELETE RESTRICT,
   CONSTRAINT qms_finding_org_fk FOREIGN KEY(tenant_id,organization_id) REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
   CONSTRAINT qms_finding_text_nonblank CHECK(btrim(type)<>'' AND btrim(statement)<>'')
 );
 CREATE TABLE qms.nonconformity (
   nc_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
   organization_id uuid NOT NULL, source_type varchar(80) NOT NULL, source_id uuid NOT NULL, description text NOT NULL,
   severity varchar(80) NOT NULL, status varchar(80) NOT NULL, created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
   CONSTRAINT qms_nonconformity_org_fk FOREIGN KEY(tenant_id,organization_id) REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
   CONSTRAINT qms_nonconformity_tenant_org_id_unique UNIQUE(tenant_id,organization_id,nc_id),
   CONSTRAINT qms_nonconformity_text_nonblank CHECK(btrim(source_type)<>'' AND btrim(description)<>'' AND btrim(severity)<>'' AND btrim(status)<>'')
 );
 CREATE TABLE qms.corrective_action (
   capa_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
   organization_id uuid NOT NULL, nc_id uuid NOT NULL, cause_id uuid NOT NULL, action text NOT NULL, owner_id uuid NOT NULL,
   due_date date NOT NULL, effectiveness_check_id uuid NULL REFERENCES qms.effectiveness_check(id) ON DELETE RESTRICT,
   created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
   CONSTRAINT qms_corrective_action_nc_fk FOREIGN KEY(tenant_id,organization_id,nc_id) REFERENCES qms.nonconformity(tenant_id,organization_id,nc_id) ON DELETE RESTRICT,
   CONSTRAINT qms_corrective_action_org_fk FOREIGN KEY(tenant_id,organization_id) REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
   CONSTRAINT qms_corrective_action_nonblank CHECK(btrim(action)<>'')
 );
 CREATE INDEX qms_finding_tenant_org_idx ON qms.finding(tenant_id,organization_id,audit_id);
 CREATE INDEX qms_nonconformity_source_idx ON qms.nonconformity(tenant_id,organization_id,source_type,source_id);
 CREATE INDEX qms_corrective_action_tenant_org_idx ON qms.corrective_action(tenant_id,organization_id,nc_id);
 FOREACH tbl IN ARRAY ARRAY['audit','finding','nonconformity','corrective_action'] LOOP
   EXECUTE format('ALTER TABLE qms.%I ENABLE ROW LEVEL SECURITY', tbl);
   EXECUTE format('ALTER TABLE qms.%I FORCE ROW LEVEL SECURITY', tbl);
   EXECUTE format('CREATE POLICY qms_%I_select ON qms.%I FOR SELECT TO %I,%I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', tbl,tbl,app_role,worker_role);
   EXECUTE format('CREATE POLICY qms_%I_insert ON qms.%I FOR INSERT TO %I WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', tbl,tbl,app_role);
   EXECUTE format('CREATE POLICY qms_%I_migrator ON qms.%I FOR ALL TO %I USING(true) WITH CHECK(true)', tbl,tbl,current_user);
   EXECUTE format('GRANT SELECT,INSERT ON qms.%I TO %I',tbl,app_role);
   EXECUTE format('GRANT SELECT ON qms.%I TO %I',tbl,worker_role);
 END LOOP;
END $migration$;
"""

REVERSE_SQL = r"""
DROP TABLE qms.corrective_action;
DROP TABLE qms.nonconformity;
DROP TABLE qms.finding;
DROP TABLE qms.audit;
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0036_action_execution_rollback_lineage")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(name="QmsAudit", fields=[
                    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="audit_id", serialize=False)),
                    ("scope", models.TextField()), ("criteria", models.TextField()),
                    ("status", models.CharField(max_length=80)), ("lead_auditor", models.CharField(max_length=255)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("organization", models.ForeignKey(to="foundation.organization", on_delete=django.db.models.deletion.PROTECT, db_column="organization_id")),
                    ("tenant", models.ForeignKey(to="foundation.tenantprojection", on_delete=django.db.models.deletion.PROTECT, db_column="tenant_id")),
                ], options={"managed": False, "db_table": 'qms"."audit'}),
                migrations.CreateModel(name="Finding", fields=[
                    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="finding_id", serialize=False)),
                    ("finding_type", models.CharField(max_length=80, db_column="type")), ("statement", models.TextField()),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("audit", models.ForeignKey(to="foundation.qmsaudit", on_delete=django.db.models.deletion.PROTECT, db_column="audit_id")),
                    ("evidence", models.ForeignKey(to="foundation.evidence", on_delete=django.db.models.deletion.PROTECT, db_column="evidence_id")),
                    ("organization", models.ForeignKey(to="foundation.organization", on_delete=django.db.models.deletion.PROTECT, db_column="organization_id")),
                    ("requirement", models.ForeignKey(to="foundation.requirementcontrol", on_delete=django.db.models.deletion.PROTECT, db_column="requirement_id")),
                    ("tenant", models.ForeignKey(to="foundation.tenantprojection", on_delete=django.db.models.deletion.PROTECT, db_column="tenant_id")),
                ], options={"managed": False, "db_table": 'qms"."finding'}),
                migrations.CreateModel(name="QmsNonconformity", fields=[
                    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="nc_id", serialize=False)),
                    ("source_type", models.CharField(max_length=80)), ("source_id", models.UUIDField()),
                    ("description", models.TextField()), ("severity", models.CharField(max_length=80)),
                    ("status", models.CharField(max_length=80)), ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("organization", models.ForeignKey(to="foundation.organization", on_delete=django.db.models.deletion.PROTECT, db_column="organization_id")),
                    ("tenant", models.ForeignKey(to="foundation.tenantprojection", on_delete=django.db.models.deletion.PROTECT, db_column="tenant_id")),
                ], options={"managed": False, "db_table": 'qms"."nonconformity'}),
                migrations.CreateModel(name="QmsCorrectiveAction", fields=[
                    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="capa_id", serialize=False)),
                    ("cause_id", models.UUIDField()), ("action", models.TextField()), ("owner_id", models.UUIDField()),
                    ("due_date", models.DateField()), ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("effectiveness_check", models.ForeignKey(to="foundation.effectivenesscheck", on_delete=django.db.models.deletion.PROTECT, db_column="effectiveness_check_id", null=True, blank=True)),
                    ("nonconformity", models.ForeignKey(to="foundation.qmsnonconformity", on_delete=django.db.models.deletion.PROTECT, db_column="nc_id")),
                    ("organization", models.ForeignKey(to="foundation.organization", on_delete=django.db.models.deletion.PROTECT, db_column="organization_id")),
                    ("tenant", models.ForeignKey(to="foundation.tenantprojection", on_delete=django.db.models.deletion.PROTECT, db_column="tenant_id")),
                ], options={"managed": False, "db_table": 'qms"."corrective_action'}),
            ],
        ),
    ]
