"""Phase 8 global normative core and tenant-safe EvidenceCoverage foundation."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
    projector_role text := current_setting('foundation.projector_role', true);
    curator_role text := current_setting('foundation.normative_curator_role', true);
BEGIN
    IF app_role IS NULL OR app_role = '' OR worker_role IS NULL OR worker_role = '' OR
       projector_role IS NULL OR projector_role = '' OR curator_role IS NULL OR curator_role = '' THEN
        RAISE EXCEPTION 'foundation runtime and normative curator roles are required';
    END IF;

    CREATE SCHEMA normative;

    CREATE TABLE normative.standard (
        id uuid PRIMARY KEY,
        code varchar(120) NOT NULL UNIQUE,
        title text,
        publisher varchar(160) NOT NULL DEFAULT 'ISO',
        CONSTRAINT normative_standard_code_nonblank CHECK (btrim(code) <> ''),
        CONSTRAINT normative_standard_publisher_nonblank CHECK (btrim(publisher) <> '')
    );

    CREATE TABLE normative.standard_edition (
        id uuid PRIMARY KEY,
        standard_id uuid NOT NULL REFERENCES normative.standard(id) ON DELETE RESTRICT,
        edition varchar(120) NOT NULL,
        status varchar(24) NOT NULL DEFAULT 'draft',
        effective_from date,
        effective_to date,
        source_hash varchar(64),
        CONSTRAINT normative_edition_identity_unique UNIQUE (standard_id,edition),
        CONSTRAINT normative_edition_id_pair_unique UNIQUE (id,standard_id),
        CONSTRAINT normative_edition_nonblank CHECK (btrim(edition) <> ''),
        CONSTRAINT normative_edition_status_valid CHECK (status IN ('draft','published')),
        CONSTRAINT normative_edition_dates_valid CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from),
        CONSTRAINT normative_edition_source_hash_valid CHECK (source_hash IS NULL OR source_hash ~ '^[0-9a-f]{64}$')
    );

    CREATE TABLE normative.clause (
        id uuid PRIMARY KEY,
        standard_edition_id uuid NOT NULL REFERENCES normative.standard_edition(id) ON DELETE RESTRICT,
        code varchar(80) NOT NULL,
        title text,
        parent_id uuid,
        CONSTRAINT normative_clause_edition_code_unique UNIQUE (standard_edition_id,code),
        CONSTRAINT normative_clause_edition_id_unique UNIQUE (standard_edition_id,id),
        CONSTRAINT normative_clause_parent_fk FOREIGN KEY (standard_edition_id,parent_id)
          REFERENCES normative.clause(standard_edition_id,id) ON DELETE RESTRICT,
        CONSTRAINT normative_clause_not_self CHECK (parent_id IS NULL OR parent_id <> id),
        CONSTRAINT normative_clause_code_nonblank CHECK (btrim(code) <> '')
    );

    CREATE TABLE normative.requirement_control (
        id uuid PRIMARY KEY,
        standard_edition_id uuid NOT NULL REFERENCES normative.standard_edition(id) ON DELETE RESTRICT,
        clause_id uuid NOT NULL,
        paraphrase text NOT NULL,
        applicability_rule jsonb NOT NULL DEFAULT '{}'::jsonb,
        control_type varchar(120),
        valid_from timestamptz,
        valid_to timestamptz,
        CONSTRAINT normative_requirement_clause_fk FOREIGN KEY (standard_edition_id,clause_id)
          REFERENCES normative.clause(standard_edition_id,id) ON DELETE RESTRICT,
        CONSTRAINT normative_requirement_edition_id_unique UNIQUE (standard_edition_id,id),
        CONSTRAINT normative_requirement_paraphrase_nonblank CHECK (btrim(paraphrase) <> ''),
        CONSTRAINT normative_requirement_validity CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
    );

    CREATE TABLE normative.curation_audit (
        id uuid PRIMARY KEY,
        action varchar(160) NOT NULL,
        entity_type varchar(120) NOT NULL,
        entity_id uuid NOT NULL,
        actor_id varchar(255) NOT NULL,
        trace_id uuid NOT NULL,
        payload_hash varchar(64) NOT NULL,
        occurred_at timestamptz NOT NULL,
        CONSTRAINT normative_curation_audit_nonblank CHECK (btrim(action) <> '' AND btrim(entity_type) <> '' AND btrim(actor_id) <> ''),
        CONSTRAINT normative_curation_audit_hash CHECK (payload_hash ~ '^[0-9a-f]{64}$')
    );

    CREATE TABLE qms.evidence_coverage (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        evidence_id uuid NOT NULL,
        standard_edition_id uuid NOT NULL,
        requirement_control_id uuid NOT NULL,
        confidence numeric(5,4),
        validation_status varchar(80) NOT NULL DEFAULT 'proposed',
        validated_by uuid,
        validated_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_coverage_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_coverage_evidence_fk FOREIGN KEY (tenant_id,organization_id,evidence_id)
          REFERENCES qms.evidence(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_coverage_edition_fk FOREIGN KEY (standard_edition_id)
          REFERENCES normative.standard_edition(id) ON DELETE RESTRICT,
        CONSTRAINT qms_coverage_requirement_edition_fk FOREIGN KEY (standard_edition_id,requirement_control_id)
          REFERENCES normative.requirement_control(standard_edition_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_coverage_validator_fk FOREIGN KEY (tenant_id,validated_by)
          REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_coverage_exact_assessment_unique UNIQUE (tenant_id,organization_id,evidence_id,requirement_control_id),
        CONSTRAINT qms_coverage_confidence_range CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
        CONSTRAINT qms_coverage_status_nonblank CHECK (btrim(validation_status) <> ''),
        CONSTRAINT qms_coverage_validation_pair CHECK ((validated_by IS NULL) = (validated_at IS NULL))
    );

    CREATE INDEX normative_clause_hierarchy_idx ON normative.clause(standard_edition_id,parent_id);
    CREATE INDEX normative_requirement_clause_idx ON normative.requirement_control(standard_edition_id,clause_id);
    CREATE INDEX qms_coverage_tenant_org_idx ON qms.evidence_coverage(tenant_id,organization_id,created_at);
    CREATE INDEX qms_coverage_normative_idx ON qms.evidence_coverage(standard_edition_id,requirement_control_id);

    CREATE FUNCTION normative.foundation_0008_guard_edition()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,normative AS $fn$
    BEGIN
        IF TG_OP = 'DELETE' THEN
            IF OLD.status = 'published' THEN
                RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='published standard edition is immutable';
            END IF;
            RETURN OLD;
        END IF;
        IF OLD.status = 'published' THEN
            RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='published standard edition is immutable';
        END IF;
        IF OLD.status = 'draft' AND NEW.status = 'published' THEN
            IF NOT EXISTS (SELECT 1 FROM normative.clause WHERE standard_edition_id=OLD.id) OR
               NOT EXISTS (SELECT 1 FROM normative.requirement_control WHERE standard_edition_id=OLD.id) THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='edition requires clauses and controls before publication';
            END IF;
        ELSIF OLD.status IS DISTINCT FROM NEW.status THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='invalid edition status transition';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION normative.foundation_0008_guard_published_material()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,normative AS $fn$
    DECLARE edition_id uuid; edition_status text;
    BEGIN
        edition_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.standard_edition_id ELSE NEW.standard_edition_id END;
        SELECT status INTO edition_status FROM normative.standard_edition WHERE id=edition_id;
        IF edition_status = 'published' THEN
            RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='published normative material is immutable';
        END IF;
        IF TG_OP = 'UPDATE' AND OLD.standard_edition_id IS DISTINCT FROM NEW.standard_edition_id THEN
            SELECT status INTO edition_status FROM normative.standard_edition WHERE id=OLD.standard_edition_id;
            IF edition_status = 'published' THEN
                RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='published normative material is immutable';
            END IF;
        END IF;
        RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
    END $fn$;

    CREATE FUNCTION normative.foundation_0008_validate_clause_hierarchy()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,normative AS $fn$
    DECLARE cycle_found boolean;
    BEGIN
        IF NEW.parent_id IS NULL THEN RETURN NEW; END IF;
        WITH RECURSIVE ancestors(id,parent_id) AS (
            SELECT id,parent_id FROM normative.clause WHERE id=NEW.parent_id AND standard_edition_id=NEW.standard_edition_id
            UNION ALL
            SELECT c.id,c.parent_id FROM normative.clause c JOIN ancestors a ON c.id=a.parent_id
              WHERE c.standard_edition_id=NEW.standard_edition_id
        ) SELECT EXISTS(SELECT 1 FROM ancestors WHERE id=NEW.id) INTO cycle_found;
        IF cycle_found THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='clause hierarchy cycle is forbidden';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION normative.foundation_0008_reject_audit_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,normative AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='normative curation audit is append-only';
    END $fn$;

    CREATE FUNCTION qms.foundation_0008_validate_coverage()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms,normative AS $fn$
    DECLARE edition_status text;
    BEGIN
        SELECT status INTO edition_status FROM normative.standard_edition WHERE id=NEW.standard_edition_id;
        IF edition_status IS DISTINCT FROM 'published' THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='evidence coverage requires a published standard edition';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0008_reject_coverage_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='evidence coverage assessment is append-only';
    END $fn$;

    CREATE TRIGGER normative_edition_immutable BEFORE UPDATE OR DELETE ON normative.standard_edition
      FOR EACH ROW EXECUTE FUNCTION normative.foundation_0008_guard_edition();
    CREATE TRIGGER normative_clause_publication_guard BEFORE INSERT OR UPDATE OR DELETE ON normative.clause
      FOR EACH ROW EXECUTE FUNCTION normative.foundation_0008_guard_published_material();
    CREATE TRIGGER normative_clause_hierarchy_guard BEFORE INSERT OR UPDATE ON normative.clause
      FOR EACH ROW EXECUTE FUNCTION normative.foundation_0008_validate_clause_hierarchy();
    CREATE TRIGGER normative_requirement_publication_guard BEFORE INSERT OR UPDATE OR DELETE ON normative.requirement_control
      FOR EACH ROW EXECUTE FUNCTION normative.foundation_0008_guard_published_material();
    CREATE TRIGGER normative_curation_audit_append_only BEFORE UPDATE OR DELETE ON normative.curation_audit
      FOR EACH ROW EXECUTE FUNCTION normative.foundation_0008_reject_audit_mutation();
    CREATE TRIGGER qms_coverage_validate BEFORE INSERT ON qms.evidence_coverage
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0008_validate_coverage();
    CREATE TRIGGER qms_coverage_append_only BEFORE UPDATE OR DELETE ON qms.evidence_coverage
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0008_reject_coverage_mutation();

    ALTER TABLE qms.evidence_coverage ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.evidence_coverage FORCE ROW LEVEL SECURITY;
    EXECUTE format('CREATE POLICY qms_coverage_select ON qms.evidence_coverage FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_coverage_insert ON qms.evidence_coverage FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_coverage_update ON qms.evidence_coverage FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_coverage_delete ON qms.evidence_coverage FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_coverage_migrator ON qms.evidence_coverage FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);

    EXECUTE format('GRANT USAGE ON SCHEMA normative TO %I,%I,%I,%I',app_role,worker_role,projector_role,curator_role);
    EXECUTE format('GRANT SELECT ON normative.standard,normative.standard_edition,normative.clause,normative.requirement_control TO %I,%I,%I,%I',app_role,worker_role,projector_role,curator_role);
    EXECUTE format('GRANT INSERT ON normative.standard,normative.standard_edition,normative.clause,normative.requirement_control,normative.curation_audit TO %I',curator_role);
    EXECUTE format('GRANT UPDATE(status) ON normative.standard_edition TO %I',curator_role);
    EXECUTE format('GRANT SELECT ON normative.curation_audit TO %I',curator_role);
    EXECUTE format('GRANT SELECT,INSERT ON qms.evidence_coverage TO %I',app_role);
    EXECUTE format('GRANT SELECT ON qms.evidence_coverage TO %I',worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DROP TABLE qms.evidence_coverage;
DROP FUNCTION qms.foundation_0008_reject_coverage_mutation();
DROP FUNCTION qms.foundation_0008_validate_coverage();
DROP SCHEMA normative CASCADE;
"""


def apply_phase8(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase8(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0007_document_evidence_foundation")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase8, reverse_phase8)],
        state_operations=[
            migrations.CreateModel(name="Standard", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=120, unique=True)),
                ("title", models.TextField(blank=True, null=True)),
                ("publisher", models.CharField(default="ISO", max_length=160)),
            ], options={"managed": False, "db_table": 'normative"."standard'}),
            migrations.CreateModel(name="StandardEdition", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("edition", models.CharField(max_length=120)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=24)),
                ("effective_from", models.DateField(blank=True, null=True)),
                ("effective_to", models.DateField(blank=True, null=True)),
                ("source_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("standard", models.ForeignKey(db_column="standard_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.standard")),
            ], options={"managed": False, "db_table": 'normative"."standard_edition'}),
            migrations.CreateModel(name="Clause", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=80)),
                ("title", models.TextField(blank=True, null=True)),
                ("standard_edition", models.ForeignKey(db_column="standard_edition_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.standardedition")),
                ("parent", models.ForeignKey(blank=True, db_column="parent_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="children", to="foundation.clause")),
            ], options={"managed": False, "db_table": 'normative"."clause'}),
            migrations.CreateModel(name="RequirementControl", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("paraphrase", models.TextField()),
                ("applicability_rule", models.JSONField(default=dict)),
                ("control_type", models.CharField(blank=True, max_length=120, null=True)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_to", models.DateTimeField(blank=True, null=True)),
                ("standard_edition", models.ForeignKey(db_column="standard_edition_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.standardedition")),
                ("clause", models.ForeignKey(db_column="clause_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.clause")),
            ], options={"managed": False, "db_table": 'normative"."requirement_control'}),
            migrations.CreateModel(name="NormativeCurationAudit", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("action", models.CharField(max_length=160)),
                ("entity_type", models.CharField(max_length=120)),
                ("entity_id", models.UUIDField()),
                ("actor_id", models.CharField(max_length=255)),
                ("trace_id", models.UUIDField()),
                ("payload_hash", models.CharField(max_length=64)),
                ("occurred_at", models.DateTimeField()),
            ], options={"managed": False, "db_table": 'normative"."curation_audit'}),
            migrations.CreateModel(name="EvidenceCoverage", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("confidence", models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ("validation_status", models.CharField(default="proposed", max_length=80)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("evidence", models.ForeignKey(db_column="evidence_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.evidence")),
                ("standard_edition", models.ForeignKey(db_column="standard_edition_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.standardedition")),
                ("requirement_control", models.ForeignKey(db_column="requirement_control_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.requirementcontrol")),
                ("validated_by", models.ForeignKey(blank=True, db_column="validated_by", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="validated_evidence_coverages", to="foundation.userprojection")),
            ], options={"managed": False, "db_table": 'qms"."evidence_coverage'}),
        ],
    )]
