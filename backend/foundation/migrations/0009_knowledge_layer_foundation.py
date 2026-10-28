"""Phase 9 global Knowledge Layer guidance foundation."""

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

    CREATE TABLE normative.knowledge_layer (
        id uuid PRIMARY KEY,
        standard_edition_id uuid NOT NULL REFERENCES normative.standard_edition(id) ON DELETE RESTRICT,
        layer_type varchar(120) NOT NULL,
        certifiability_classification varchar(40) NOT NULL DEFAULT 'non_certifiable_guidance',
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT normative_layer_edition_unique UNIQUE (standard_edition_id),
        CONSTRAINT normative_layer_type_nonblank CHECK (btrim(layer_type) <> ''),
        CONSTRAINT normative_layer_certifiability_fixed
          CHECK (certifiability_classification = 'non_certifiable_guidance')
    );

    CREATE TABLE normative.knowledge_layer_rule (
        id uuid PRIMARY KEY,
        knowledge_layer_id uuid NOT NULL REFERENCES normative.knowledge_layer(id) ON DELETE RESTRICT,
        lineage_id uuid NOT NULL,
        rule_key varchar(160) NOT NULL,
        version varchar(80) NOT NULL,
        previous_revision_id uuid UNIQUE,
        status varchar(24) NOT NULL DEFAULT 'draft',
        logic_json jsonb NOT NULL DEFAULT '{}'::jsonb,
        evidence_expectation jsonb NOT NULL DEFAULT '{}'::jsonb,
        source_reference text,
        certifiability_classification varchar(40) NOT NULL DEFAULT 'non_certifiable_guidance',
        published_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT normative_rule_layer_key_version_unique UNIQUE (knowledge_layer_id,rule_key,version),
        CONSTRAINT normative_rule_layer_key_id_unique UNIQUE (knowledge_layer_id,rule_key,id),
        CONSTRAINT normative_rule_lineage_version_unique UNIQUE (lineage_id,version),
        CONSTRAINT normative_rule_predecessor_fk
          FOREIGN KEY (knowledge_layer_id,rule_key,previous_revision_id)
          REFERENCES normative.knowledge_layer_rule(knowledge_layer_id,rule_key,id) ON DELETE RESTRICT,
        CONSTRAINT normative_rule_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id),
        CONSTRAINT normative_rule_root_identity CHECK (previous_revision_id IS NOT NULL OR lineage_id = id),
        CONSTRAINT normative_rule_key_nonblank CHECK (btrim(rule_key) <> ''),
        CONSTRAINT normative_rule_version_nonblank CHECK (btrim(version) <> ''),
        CONSTRAINT normative_rule_status_valid CHECK (status IN ('draft','published')),
        CONSTRAINT normative_rule_publication_pair
          CHECK ((status = 'draft' AND published_at IS NULL) OR
                 (status = 'published' AND published_at IS NOT NULL)),
        CONSTRAINT normative_rule_certifiability_fixed
          CHECK (certifiability_classification = 'non_certifiable_guidance')
    );
    CREATE UNIQUE INDEX normative_rule_one_root_idx
      ON normative.knowledge_layer_rule(knowledge_layer_id,rule_key)
      WHERE previous_revision_id IS NULL;

    CREATE TABLE normative.knowledge_layer_binding (
        id uuid PRIMARY KEY,
        knowledge_layer_rule_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
        standard_edition_id uuid NOT NULL REFERENCES normative.standard_edition(id) ON DELETE RESTRICT,
        requirement_control_id uuid NOT NULL,
        relationship_type varchar(40) NOT NULL DEFAULT 'informs',
        priority varchar(40),
        rationale text,
        status varchar(24) NOT NULL DEFAULT 'draft',
        semantic_effect varchar(40) NOT NULL DEFAULT 'guidance_only',
        published_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT normative_binding_requirement_edition_fk
          FOREIGN KEY (standard_edition_id,requirement_control_id)
          REFERENCES normative.requirement_control(standard_edition_id,id) ON DELETE RESTRICT,
        CONSTRAINT normative_binding_logical_unique
          UNIQUE (knowledge_layer_rule_id,requirement_control_id,relationship_type),
        CONSTRAINT normative_binding_relationship_valid CHECK (relationship_type = 'informs'),
        CONSTRAINT normative_binding_priority_nonblank CHECK (priority IS NULL OR btrim(priority) <> ''),
        CONSTRAINT normative_binding_status_valid CHECK (status IN ('draft','published')),
        CONSTRAINT normative_binding_publication_pair
          CHECK ((status = 'draft' AND published_at IS NULL) OR
                 (status = 'published' AND published_at IS NOT NULL)),
        CONSTRAINT normative_binding_semantic_effect_fixed CHECK (semantic_effect = 'guidance_only')
    );

    CREATE INDEX normative_rule_layer_lineage_idx
      ON normative.knowledge_layer_rule(knowledge_layer_id,lineage_id,created_at);
    CREATE INDEX normative_binding_requirement_idx
      ON normative.knowledge_layer_binding(standard_edition_id,requirement_control_id);

    CREATE VIEW normative.catalog_object_classification AS
      SELECT id, 'requirement_control'::varchar(40) AS object_kind,
             'normative_requirement'::varchar(40) AS certifiability_classification
        FROM normative.requirement_control
      UNION ALL
      SELECT id, 'knowledge_layer'::varchar(40), certifiability_classification
        FROM normative.knowledge_layer
      UNION ALL
      SELECT id, 'knowledge_layer_rule'::varchar(40), certifiability_classification
        FROM normative.knowledge_layer_rule;

    CREATE FUNCTION normative.foundation_0009_reject_layer_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,normative AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='knowledge layer identity is append-only';
    END $fn$;

    CREATE FUNCTION normative.foundation_0009_guard_rule()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,normative AS $fn$
    DECLARE
        predecessor_status text;
        predecessor_lineage uuid;
        edition_status text;
        cycle_found boolean;
    BEGIN
        IF TG_OP = 'DELETE' THEN
            IF OLD.status = 'published' THEN
                RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='published knowledge layer rule is immutable';
            END IF;
            RETURN OLD;
        END IF;

        IF TG_OP = 'UPDATE' THEN
            IF OLD.status = 'published' THEN
                RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='published knowledge layer rule is immutable';
            END IF;
            IF OLD.id IS DISTINCT FROM NEW.id OR
               OLD.knowledge_layer_id IS DISTINCT FROM NEW.knowledge_layer_id OR
               OLD.lineage_id IS DISTINCT FROM NEW.lineage_id OR
               OLD.rule_key IS DISTINCT FROM NEW.rule_key OR
               OLD.version IS DISTINCT FROM NEW.version OR
               OLD.previous_revision_id IS DISTINCT FROM NEW.previous_revision_id OR
               OLD.logic_json IS DISTINCT FROM NEW.logic_json OR
               OLD.evidence_expectation IS DISTINCT FROM NEW.evidence_expectation OR
               OLD.source_reference IS DISTINCT FROM NEW.source_reference OR
               OLD.certifiability_classification IS DISTINCT FROM NEW.certifiability_classification OR
               OLD.created_at IS DISTINCT FROM NEW.created_at THEN
                RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='rule material fields are revision-only';
            END IF;
            IF NOT (OLD.status = 'draft' AND NEW.status = 'published' AND NEW.published_at IS NOT NULL) THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='invalid rule publication transition';
            END IF;
        ELSIF NEW.status <> 'draft' OR NEW.published_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='new rule revisions must start as draft';
        END IF;

        IF NEW.previous_revision_id IS NOT NULL THEN
            SELECT status,lineage_id INTO predecessor_status,predecessor_lineage
              FROM normative.knowledge_layer_rule WHERE id=NEW.previous_revision_id;
            IF predecessor_status IS DISTINCT FROM 'published' OR predecessor_lineage IS DISTINCT FROM NEW.lineage_id THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='rule predecessor must be a published revision in the same lineage';
            END IF;
            WITH RECURSIVE ancestors(id,previous_revision_id) AS (
                SELECT id,previous_revision_id FROM normative.knowledge_layer_rule WHERE id=NEW.previous_revision_id
                UNION ALL
                SELECT r.id,r.previous_revision_id FROM normative.knowledge_layer_rule r
                  JOIN ancestors a ON r.id=a.previous_revision_id
            ) SELECT EXISTS(SELECT 1 FROM ancestors WHERE id=NEW.id) INTO cycle_found;
            IF cycle_found THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='rule revision cycle is forbidden';
            END IF;
        END IF;

        IF TG_OP = 'UPDATE' AND NEW.status = 'published' THEN
            SELECT se.status INTO edition_status
              FROM normative.knowledge_layer kl
              JOIN normative.standard_edition se ON se.id=kl.standard_edition_id
             WHERE kl.id=NEW.knowledge_layer_id;
            IF edition_status IS DISTINCT FROM 'published' THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='rule publication requires a published source edition';
            END IF;
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION normative.foundation_0009_guard_binding()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,normative AS $fn$
    DECLARE rule_status text; edition_status text;
    BEGIN
        IF TG_OP = 'DELETE' THEN
            IF OLD.status = 'published' THEN
                RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='published knowledge layer binding is immutable';
            END IF;
            RETURN OLD;
        END IF;
        IF TG_OP = 'UPDATE' THEN
            IF OLD.status = 'published' THEN
                RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='published knowledge layer binding is immutable';
            END IF;
            IF OLD.id IS DISTINCT FROM NEW.id OR
               OLD.knowledge_layer_rule_id IS DISTINCT FROM NEW.knowledge_layer_rule_id OR
               OLD.standard_edition_id IS DISTINCT FROM NEW.standard_edition_id OR
               OLD.requirement_control_id IS DISTINCT FROM NEW.requirement_control_id OR
               OLD.relationship_type IS DISTINCT FROM NEW.relationship_type OR
               OLD.priority IS DISTINCT FROM NEW.priority OR
               OLD.rationale IS DISTINCT FROM NEW.rationale OR
               OLD.semantic_effect IS DISTINCT FROM NEW.semantic_effect OR
               OLD.created_at IS DISTINCT FROM NEW.created_at THEN
                RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='binding material fields are immutable';
            END IF;
            IF NOT (OLD.status = 'draft' AND NEW.status = 'published' AND NEW.published_at IS NOT NULL) THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='invalid binding publication transition';
            END IF;
        ELSIF NEW.status <> 'draft' OR NEW.published_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='new bindings must start as draft';
        END IF;
        SELECT status INTO rule_status FROM normative.knowledge_layer_rule WHERE id=NEW.knowledge_layer_rule_id;
        SELECT status INTO edition_status FROM normative.standard_edition WHERE id=NEW.standard_edition_id;
        IF rule_status IS DISTINCT FROM 'published' THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='binding requires a published exact rule revision';
        END IF;
        IF edition_status IS DISTINCT FROM 'published' THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='binding requires a published requirement edition';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE TRIGGER normative_layer_append_only BEFORE UPDATE OR DELETE ON normative.knowledge_layer
      FOR EACH ROW EXECUTE FUNCTION normative.foundation_0009_reject_layer_mutation();
    CREATE TRIGGER normative_rule_revision_guard BEFORE INSERT OR UPDATE OR DELETE ON normative.knowledge_layer_rule
      FOR EACH ROW EXECUTE FUNCTION normative.foundation_0009_guard_rule();
    CREATE TRIGGER normative_binding_publication_guard BEFORE INSERT OR UPDATE OR DELETE ON normative.knowledge_layer_binding
      FOR EACH ROW EXECUTE FUNCTION normative.foundation_0009_guard_binding();

    EXECUTE format('GRANT SELECT ON normative.knowledge_layer,normative.knowledge_layer_rule,normative.knowledge_layer_binding TO %I,%I,%I,%I',app_role,worker_role,projector_role,curator_role);
    EXECUTE format('GRANT SELECT ON normative.catalog_object_classification TO %I,%I,%I,%I',app_role,worker_role,projector_role,curator_role);
    EXECUTE format('GRANT INSERT ON normative.knowledge_layer,normative.knowledge_layer_rule,normative.knowledge_layer_binding TO %I',curator_role);
    EXECUTE format('GRANT UPDATE(status,published_at) ON normative.knowledge_layer_rule TO %I',curator_role);
    EXECUTE format('GRANT UPDATE(status,published_at) ON normative.knowledge_layer_binding TO %I',curator_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DROP VIEW normative.catalog_object_classification;
DROP TABLE normative.knowledge_layer_binding;
DROP TABLE normative.knowledge_layer_rule;
DROP TABLE normative.knowledge_layer;
DROP FUNCTION normative.foundation_0009_guard_binding();
DROP FUNCTION normative.foundation_0009_guard_rule();
DROP FUNCTION normative.foundation_0009_reject_layer_mutation();
"""


def apply_phase9(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase9(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0008_evidence_coverage_normative_core_foundation")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase9, reverse_phase9)],
        state_operations=[
            migrations.CreateModel(
                name="KnowledgeLayer",
                fields=[
                    ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                    ("layer_type", models.CharField(max_length=120)),
                    ("certifiability_classification", models.CharField(choices=[("non_certifiable_guidance", "Non-certifiable guidance")], default="non_certifiable_guidance", max_length=40)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("standard_edition", models.ForeignKey(db_column="standard_edition_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.standardedition")),
                ],
                options={"managed": False, "db_table": 'normative"."knowledge_layer'},
            ),
            migrations.CreateModel(
                name="KnowledgeLayerRule",
                fields=[
                    ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                    ("lineage_id", models.UUIDField()),
                    ("rule_key", models.CharField(max_length=160)),
                    ("version", models.CharField(max_length=80)),
                    ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=24)),
                    ("logic_json", models.JSONField(default=dict)),
                    ("evidence_expectation", models.JSONField(default=dict)),
                    ("source_reference", models.TextField(blank=True, null=True)),
                    ("certifiability_classification", models.CharField(choices=[("non_certifiable_guidance", "Non-certifiable guidance")], default="non_certifiable_guidance", max_length=40)),
                    ("published_at", models.DateTimeField(blank=True, null=True)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("knowledge_layer", models.ForeignKey(db_column="knowledge_layer_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.knowledgelayer")),
                    ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.knowledgelayerrule")),
                ],
                options={"managed": False, "db_table": 'normative"."knowledge_layer_rule'},
            ),
            migrations.CreateModel(
                name="KnowledgeLayerBinding",
                fields=[
                    ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                    ("relationship_type", models.CharField(choices=[("informs", "Informs")], default="informs", max_length=40)),
                    ("priority", models.CharField(blank=True, max_length=40, null=True)),
                    ("rationale", models.TextField(blank=True, null=True)),
                    ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=24)),
                    ("semantic_effect", models.CharField(choices=[("guidance_only", "Guidance only")], default="guidance_only", max_length=40)),
                    ("published_at", models.DateTimeField(blank=True, null=True)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("knowledge_layer_rule", models.ForeignKey(db_column="knowledge_layer_rule_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.knowledgelayerrule")),
                    ("standard_edition", models.ForeignKey(db_column="standard_edition_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.standardedition")),
                    ("requirement_control", models.ForeignKey(db_column="requirement_control_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.requirementcontrol")),
                ],
                options={"managed": False, "db_table": 'normative"."knowledge_layer_binding'},
            ),
        ],
    )]
