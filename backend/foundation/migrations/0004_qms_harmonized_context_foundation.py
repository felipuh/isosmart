"""Phase 4 additive QMS harmonized organizational-context foundation."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
    table_name text;
BEGIN
    IF app_role IS NULL OR app_role = '' OR worker_role IS NULL OR worker_role = '' THEN
        RAISE EXCEPTION 'foundation app and worker roles are required';
    END IF;

    CREATE TABLE qms.stakeholder (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        stakeholder_type varchar(80) NOT NULL,
        name varchar(255) NOT NULL,
        relevance_score numeric(5,4),
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_stakeholder_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_stakeholder_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_stakeholder_relevance_range CHECK
          (relevance_score IS NULL OR relevance_score BETWEEN 0 AND 1),
        CONSTRAINT qms_stakeholder_name_nonblank CHECK (btrim(name) <> ''),
        CONSTRAINT qms_stakeholder_type_nonblank CHECK (btrim(stakeholder_type) <> '')
    );

    CREATE TABLE qms.process (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        name varchar(255) NOT NULL,
        owner_id uuid,
        process_type varchar(80),
        status varchar(40) NOT NULL DEFAULT 'active',
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_process_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_process_owner_fk FOREIGN KEY (tenant_id,owner_id)
          REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_process_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_process_name_nonblank CHECK (btrim(name) <> ''),
        CONSTRAINT qms_process_status_nonblank CHECK (btrim(status) <> '')
    );

    CREATE TABLE qms.stakeholder_requirement (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        stakeholder_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        requirement_text text NOT NULL,
        qms_addressed boolean NOT NULL DEFAULT false,
        owner_process_id uuid,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_requirement_stakeholder_fk FOREIGN KEY (tenant_id,organization_id,stakeholder_id)
          REFERENCES qms.stakeholder(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_requirement_process_fk FOREIGN KEY (tenant_id,organization_id,owner_process_id)
          REFERENCES qms.process(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_requirement_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.stakeholder_requirement(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_requirement_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_requirement_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_requirement_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_requirement_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_requirement_text_nonblank CHECK (btrim(requirement_text) <> ''),
        CONSTRAINT qms_requirement_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_requirement_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id)
    );

    CREATE TABLE qms.context_item (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        issue_type varchar(16) NOT NULL,
        description text NOT NULL,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_context_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_context_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.context_item(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_context_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_context_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_context_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_context_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_context_issue_type_valid CHECK (issue_type IN ('internal','external')),
        CONSTRAINT qms_context_description_nonblank CHECK (btrim(description) <> ''),
        CONSTRAINT qms_context_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_context_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id)
    );

    CREATE TABLE qms.qms_scope (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        boundaries text NOT NULL,
        applicability text NOT NULL,
        products_services text NOT NULL,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_scope_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_scope_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.qms_scope(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_scope_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_scope_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_scope_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_scope_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_scope_fields_nonblank CHECK
          (btrim(boundaries) <> '' AND btrim(applicability) <> '' AND btrim(products_services) <> ''),
        CONSTRAINT qms_scope_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_scope_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id)
    );

    CREATE TABLE qms.qms_scope_process (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        scope_revision_id uuid NOT NULL,
        process_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_scope_process_scope_fk FOREIGN KEY (tenant_id,organization_id,scope_revision_id)
          REFERENCES qms.qms_scope(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_scope_process_process_fk FOREIGN KEY (tenant_id,organization_id,process_id)
          REFERENCES qms.process(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_scope_process_unique UNIQUE (tenant_id,scope_revision_id,process_id)
    );

    CREATE INDEX qms_stakeholder_tenant_org_idx ON qms.stakeholder(tenant_id,organization_id,id);
    CREATE INDEX qms_process_tenant_org_idx ON qms.process(tenant_id,organization_id,id);
    CREATE INDEX qms_requirement_lineage_idx ON qms.stakeholder_requirement(tenant_id,organization_id,lineage_id,revision);
    CREATE INDEX qms_context_lineage_idx ON qms.context_item(tenant_id,organization_id,lineage_id,revision);
    CREATE INDEX qms_scope_lineage_idx ON qms.qms_scope(tenant_id,organization_id,lineage_id,revision);
    CREATE INDEX qms_scope_process_scope_idx ON qms.qms_scope_process(tenant_id,scope_revision_id,process_id);

    CREATE FUNCTION qms.foundation_0004_guard_boundary_update()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        IF OLD.tenant_id IS DISTINCT FROM NEW.tenant_id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='tenant_id is immutable';
        END IF;
        IF OLD.organization_id IS DISTINCT FROM NEW.organization_id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='organization_id is immutable';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0004_reject_version_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='QMS revisions are append-only';
    END $fn$;

    CREATE FUNCTION qms.foundation_0004_validate_lineage()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    DECLARE prior record;
    BEGIN
        IF NEW.revision = 1 THEN
            IF NEW.lineage_id IS DISTINCT FROM NEW.id THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='first revision lineage_id must equal id';
            END IF;
            RETURN NEW;
        END IF;
        EXECUTE format('SELECT tenant_id,organization_id,lineage_id,revision FROM qms.%I WHERE id=$1', TG_TABLE_NAME)
          INTO prior USING NEW.previous_revision_id;
        IF prior IS NULL OR prior.tenant_id IS DISTINCT FROM NEW.tenant_id OR
           prior.organization_id IS DISTINCT FROM NEW.organization_id OR
           prior.lineage_id IS DISTINCT FROM NEW.lineage_id OR
           prior.revision + 1 <> NEW.revision THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='invalid revision lineage or predecessor';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE TRIGGER qms_stakeholder_boundary_immutable BEFORE UPDATE ON qms.stakeholder
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_guard_boundary_update();
    CREATE TRIGGER qms_process_boundary_immutable BEFORE UPDATE ON qms.process
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_guard_boundary_update();
    CREATE TRIGGER qms_requirement_validate_lineage BEFORE INSERT ON qms.stakeholder_requirement
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_validate_lineage();
    CREATE TRIGGER qms_context_validate_lineage BEFORE INSERT ON qms.context_item
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_validate_lineage();
    CREATE TRIGGER qms_scope_validate_lineage BEFORE INSERT ON qms.qms_scope
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_validate_lineage();
    CREATE TRIGGER qms_requirement_append_only BEFORE UPDATE OR DELETE ON qms.stakeholder_requirement
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_reject_version_mutation();
    CREATE TRIGGER qms_context_append_only BEFORE UPDATE OR DELETE ON qms.context_item
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_reject_version_mutation();
    CREATE TRIGGER qms_scope_append_only BEFORE UPDATE OR DELETE ON qms.qms_scope
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_reject_version_mutation();
    CREATE TRIGGER qms_scope_process_append_only BEFORE UPDATE OR DELETE ON qms.qms_scope_process
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0004_reject_version_mutation();

    ALTER TABLE qms.stakeholder ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.stakeholder FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.process ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.process FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.stakeholder_requirement ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.stakeholder_requirement FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.context_item ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.context_item FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.qms_scope ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.qms_scope FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.qms_scope_process ENABLE ROW LEVEL SECURITY; ALTER TABLE qms.qms_scope_process FORCE ROW LEVEL SECURITY;

    -- Every operation is explicit.  Version tables deliberately receive no runtime UPDATE/DELETE grant.
    EXECUTE format('CREATE POLICY qms_stakeholder_select ON qms.stakeholder FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_stakeholder_insert ON qms.stakeholder FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_stakeholder_update ON qms.stakeholder FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_stakeholder_delete ON qms.stakeholder FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_process_select ON qms.process FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_process_insert ON qms.process FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_process_update ON qms.process FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_process_delete ON qms.process FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);

    FOREACH table_name IN ARRAY ARRAY['stakeholder_requirement','context_item','qms_scope','qms_scope_process'] LOOP
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_select', table_name, app_role, worker_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_insert', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_update', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_delete', table_name, app_role);
    END LOOP;

    -- Migrator policies are required because FORCE RLS also applies to the table owner.
    FOREACH table_name IN ARRAY ARRAY['stakeholder','process','stakeholder_requirement','context_item','qms_scope','qms_scope_process'] LOOP
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR ALL TO %I USING (true) WITH CHECK (true)', 'qms_'||table_name||'_migrator', table_name, current_user);
    END LOOP;

    EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.stakeholder,qms.process TO %I',app_role);
    EXECUTE format('GRANT SELECT,INSERT ON qms.stakeholder_requirement,qms.context_item,qms.qms_scope,qms.qms_scope_process TO %I',app_role);
    EXECUTE format('GRANT SELECT ON qms.stakeholder,qms.process,qms.stakeholder_requirement,qms.context_item,qms.qms_scope,qms.qms_scope_process TO %I',worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DROP TABLE qms.qms_scope_process;
DROP TABLE qms.qms_scope;
DROP TABLE qms.context_item;
DROP TABLE qms.stakeholder_requirement;
DROP TABLE qms.process;
DROP TABLE qms.stakeholder;
DROP FUNCTION qms.foundation_0004_validate_lineage();
DROP FUNCTION qms.foundation_0004_reject_version_mutation();
DROP FUNCTION qms.foundation_0004_guard_boundary_update();
"""


def apply_phase4(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase4(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0003_eventing_immutable_audit_foundation")]
    operations = [
        migrations.RunPython(apply_phase4, reverse_phase4),
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.CreateModel(name="Stakeholder", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("stakeholder_type", models.CharField(max_length=80)),
                ("name", models.CharField(max_length=255)),
                ("relevance_score", models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
            ], options={"managed": False, "db_table": 'qms"."stakeholder'}),
            migrations.CreateModel(name="Process", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)), ("process_type", models.CharField(blank=True, max_length=80, null=True)),
                ("status", models.CharField(default="active", max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("owner", models.ForeignKey(blank=True, db_column="owner_id", null=True, on_delete=django.db.models.deletion.PROTECT, to="foundation.userprojection")),
            ], options={"managed": False, "db_table": 'qms"."process'}),
            migrations.CreateModel(name="StakeholderRequirement", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("lineage_id", models.UUIDField()),
                ("revision", models.PositiveIntegerField()), ("requirement_text", models.TextField()), ("qms_addressed", models.BooleanField(default=False)),
                ("change_reason", models.TextField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("stakeholder", models.ForeignKey(db_column="stakeholder_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.stakeholder")),
                ("owner_process", models.ForeignKey(blank=True, db_column="owner_process_id", null=True, on_delete=django.db.models.deletion.PROTECT, to="foundation.process")),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.stakeholderrequirement")),
            ], options={"managed": False, "db_table": 'qms"."stakeholder_requirement'}),
            migrations.CreateModel(name="ContextItem", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("lineage_id", models.UUIDField()),
                ("revision", models.PositiveIntegerField()), ("issue_type", models.CharField(max_length=16)), ("description", models.TextField()),
                ("change_reason", models.TextField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.contextitem")),
            ], options={"managed": False, "db_table": 'qms"."context_item'}),
            migrations.CreateModel(name="QmsScope", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("lineage_id", models.UUIDField()),
                ("revision", models.PositiveIntegerField()), ("boundaries", models.TextField()), ("applicability", models.TextField()),
                ("products_services", models.TextField()), ("change_reason", models.TextField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.qmsscope")),
            ], options={"managed": False, "db_table": 'qms"."qms_scope'}),
            migrations.CreateModel(name="QmsScopeProcess", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("scope_revision", models.ForeignKey(db_column="scope_revision_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.qmsscope")),
                ("process", models.ForeignKey(db_column="process_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.process")),
            ], options={"managed": False, "db_table": 'qms"."qms_scope_process'}),
        ])
    ]
