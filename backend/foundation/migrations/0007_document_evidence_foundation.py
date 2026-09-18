"""Phase 7 additive Document, immutable DocumentVersion and Evidence foundation."""

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

    CREATE TABLE qms.document (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        doc_type varchar(80) NOT NULL,
        owner_id uuid,
        current_version_id uuid,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_document_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_document_owner_fk FOREIGN KEY (tenant_id,owner_id)
          REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_document_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_document_type_nonblank CHECK (btrim(doc_type) <> '')
    );

    CREATE TABLE qms.document_version (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        document_id uuid NOT NULL,
        version varchar(80) NOT NULL,
        predecessor_id uuid,
        content_reference text NOT NULL,
        content_hash varchar(64) NOT NULL,
        approved_by uuid,
        effective_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_document_version_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_document_version_document_fk FOREIGN KEY (tenant_id,organization_id,document_id)
          REFERENCES qms.document(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_document_version_predecessor_fk FOREIGN KEY (tenant_id,organization_id,document_id,predecessor_id)
          REFERENCES qms.document_version(tenant_id,organization_id,document_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_document_version_approver_fk FOREIGN KEY (tenant_id,approved_by)
          REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_document_version_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_document_version_tenant_org_document_id_unique UNIQUE (tenant_id,organization_id,document_id,id),
        CONSTRAINT qms_document_version_identity_unique UNIQUE (tenant_id,organization_id,document_id,version),
        CONSTRAINT qms_document_version_predecessor_unique UNIQUE (tenant_id,organization_id,document_id,predecessor_id),
        CONSTRAINT qms_document_version_not_self CHECK (predecessor_id IS NULL OR predecessor_id <> id),
        CONSTRAINT qms_document_version_fields_nonblank CHECK (btrim(version) <> '' AND btrim(content_reference) <> ''),
        CONSTRAINT qms_document_version_sha256 CHECK (content_hash ~ '^[0-9a-f]{64}$')
    );

    ALTER TABLE qms.document ADD CONSTRAINT qms_document_current_version_fk
      FOREIGN KEY (tenant_id,organization_id,id,current_version_id)
      REFERENCES qms.document_version(tenant_id,organization_id,document_id,id) ON DELETE RESTRICT;

    CREATE TABLE qms.evidence (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        source_type varchar(80) NOT NULL,
        source_uri text,
        content_hash varchar(64) NOT NULL,
        captured_at timestamptz NOT NULL,
        trust_score numeric(5,4),
        document_version_id uuid,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_evidence_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_evidence_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.evidence(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_evidence_document_version_fk FOREIGN KEY (tenant_id,organization_id,document_version_id)
          REFERENCES qms.document_version(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_evidence_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_evidence_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_evidence_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_evidence_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_evidence_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_evidence_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id),
        CONSTRAINT qms_evidence_source_nonblank CHECK (btrim(source_type) <> ''),
        CONSTRAINT qms_evidence_sha256 CHECK (content_hash ~ '^[0-9a-f]{64}$'),
        CONSTRAINT qms_evidence_trust_range CHECK (trust_score IS NULL OR (trust_score >= 0 AND trust_score <= 1))
    );

    CREATE INDEX qms_document_tenant_org_idx ON qms.document(tenant_id,organization_id);
    CREATE INDEX qms_document_version_history_idx ON qms.document_version(tenant_id,organization_id,document_id,created_at);
    CREATE INDEX qms_evidence_lineage_idx ON qms.evidence(tenant_id,organization_id,lineage_id,revision);
    CREATE INDEX qms_evidence_source_idx ON qms.evidence(tenant_id,organization_id,source_type,captured_at);
    CREATE INDEX qms_evidence_document_version_idx ON qms.evidence(tenant_id,organization_id,document_version_id);

    CREATE FUNCTION qms.foundation_0007_guard_boundary_update()
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

    CREATE FUNCTION qms.foundation_0007_reject_history_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='Phase 7 material history is append-only';
    END $fn$;

    CREATE FUNCTION qms.foundation_0007_validate_document_version()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    DECLARE prior_count integer;
    BEGIN
        SELECT count(*) INTO prior_count FROM qms.document_version
          WHERE tenant_id=NEW.tenant_id AND organization_id=NEW.organization_id AND document_id=NEW.document_id;
        IF prior_count = 0 AND NEW.predecessor_id IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='first document version cannot have a predecessor';
        END IF;
        IF prior_count > 0 AND NEW.predecessor_id IS NULL THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='subsequent document version requires predecessor';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0007_validate_current_version()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    DECLARE candidate record; candidate_found boolean;
    BEGIN
        IF NEW.current_version_id IS NOT DISTINCT FROM OLD.current_version_id THEN RETURN NEW; END IF;
        SELECT predecessor_id INTO candidate FROM qms.document_version
          WHERE tenant_id=NEW.tenant_id AND organization_id=NEW.organization_id
            AND document_id=NEW.id AND id=NEW.current_version_id;
        candidate_found := FOUND;
        IF NOT candidate_found OR candidate.predecessor_id IS DISTINCT FROM OLD.current_version_id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='current version must advance by one direct successor';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0007_validate_evidence()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    DECLARE prior record; document_hash text;
    BEGIN
        IF NEW.revision = 1 THEN
            IF NEW.lineage_id IS DISTINCT FROM NEW.id THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='first evidence revision lineage_id must equal id';
            END IF;
        ELSE
            SELECT tenant_id,organization_id,lineage_id,revision INTO prior FROM qms.evidence WHERE id=NEW.previous_revision_id;
            IF prior IS NULL OR prior.tenant_id IS DISTINCT FROM NEW.tenant_id OR
               prior.organization_id IS DISTINCT FROM NEW.organization_id OR
               prior.lineage_id IS DISTINCT FROM NEW.lineage_id OR prior.revision + 1 <> NEW.revision THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='invalid evidence revision lineage or predecessor';
            END IF;
        END IF;
        IF NEW.document_version_id IS NOT NULL THEN
            SELECT content_hash INTO document_hash FROM qms.document_version
              WHERE tenant_id=NEW.tenant_id AND organization_id=NEW.organization_id AND id=NEW.document_version_id;
            IF document_hash IS NULL OR document_hash IS DISTINCT FROM NEW.content_hash THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='evidence hash must match referenced document version';
            END IF;
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE TRIGGER qms_document_boundary_immutable BEFORE UPDATE ON qms.document
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0007_guard_boundary_update();
    CREATE TRIGGER qms_document_current_version_linear BEFORE UPDATE ON qms.document
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0007_validate_current_version();
    CREATE TRIGGER qms_document_version_validate BEFORE INSERT ON qms.document_version
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0007_validate_document_version();
    CREATE TRIGGER qms_evidence_validate BEFORE INSERT ON qms.evidence
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0007_validate_evidence();

    FOREACH table_name IN ARRAY ARRAY['document_version','evidence'] LOOP
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE ON qms.%I FOR EACH ROW EXECUTE FUNCTION qms.foundation_0007_guard_boundary_update()', 'qms_'||table_name||'_a_boundary_immutable', table_name);
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON qms.%I FOR EACH ROW EXECUTE FUNCTION qms.foundation_0007_reject_history_mutation()', 'qms_'||table_name||'_z_append_only', table_name);
    END LOOP;
    FOREACH table_name IN ARRAY ARRAY['document','document_version','evidence'] LOOP
        EXECUTE format('ALTER TABLE qms.%I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE qms.%I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_select', table_name, app_role, worker_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_insert', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_update', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_delete', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR ALL TO %I USING (true) WITH CHECK (true)', 'qms_'||table_name||'_migrator', table_name, current_user);
    END LOOP;

    EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.document TO %I', app_role);
    EXECUTE format('GRANT SELECT,INSERT ON qms.document_version,qms.evidence TO %I', app_role);
    EXECUTE format('GRANT SELECT ON qms.document,qms.document_version,qms.evidence TO %I', worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DROP TABLE qms.evidence;
ALTER TABLE qms.document DROP CONSTRAINT qms_document_current_version_fk;
DROP TABLE qms.document_version;
DROP TABLE qms.document;
DROP FUNCTION qms.foundation_0007_validate_evidence();
DROP FUNCTION qms.foundation_0007_validate_current_version();
DROP FUNCTION qms.foundation_0007_validate_document_version();
DROP FUNCTION qms.foundation_0007_reject_history_mutation();
DROP FUNCTION qms.foundation_0007_guard_boundary_update();
"""


def apply_phase7(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase7(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0006_change_performance_measurement_foundation")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase7, reverse_phase7)],
        state_operations=[
            migrations.CreateModel(name="Document", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("document_type", models.CharField(db_column="doc_type", max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("owner", models.ForeignKey(blank=True, db_column="owner_id", null=True, on_delete=django.db.models.deletion.PROTECT, to="foundation.userprojection")),
            ], options={"managed": False, "db_table": 'qms"."document'}),
            migrations.CreateModel(name="DocumentVersion", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("version", models.CharField(max_length=80)),
                ("content_reference", models.TextField()),
                ("content_hash", models.CharField(max_length=64)),
                ("effective_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("document", models.ForeignKey(db_column="document_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.document")),
                ("predecessor", models.OneToOneField(blank=True, db_column="predecessor_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="successor", to="foundation.documentversion")),
                ("approved_by", models.ForeignKey(blank=True, db_column="approved_by", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_document_versions", to="foundation.userprojection")),
            ], options={"managed": False, "db_table": 'qms"."document_version'}),
            migrations.AddField(model_name="document", name="current_version", field=models.ForeignKey(blank=True, db_column="current_version_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="current_for_documents", to="foundation.documentversion")),
            migrations.CreateModel(name="Evidence", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("lineage_id", models.UUIDField()),
                ("revision", models.PositiveIntegerField()),
                ("source_type", models.CharField(max_length=80)),
                ("source_uri", models.TextField(blank=True, null=True)),
                ("content_hash", models.CharField(max_length=64)),
                ("captured_at", models.DateTimeField()),
                ("trust_score", models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ("change_reason", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.evidence")),
                ("document_version", models.ForeignKey(blank=True, db_column="document_version_id", null=True, on_delete=django.db.models.deletion.PROTECT, to="foundation.documentversion")),
            ], options={"managed": False, "db_table": 'qms"."evidence'}),
        ],
    )]
