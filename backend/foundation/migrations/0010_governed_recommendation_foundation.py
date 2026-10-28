"""Phase 10 governed Recommendation and frozen RecommendationBasis."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
BEGIN
    IF app_role IS NULL OR app_role = '' OR worker_role IS NULL OR worker_role = '' THEN
        RAISE EXCEPTION 'foundation app and worker roles are required';
    END IF;

    CREATE TABLE qms.recommendation (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        title text NOT NULL,
        body text NOT NULL,
        confidence numeric(5,4) NOT NULL,
        assumptions jsonb NOT NULL DEFAULT '[]'::jsonb,
        impact text,
        status varchar(24) NOT NULL DEFAULT 'proposed',
        intended_autonomy smallint NOT NULL,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_recommendation_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_recommendation_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_recommendation_title_nonblank CHECK (btrim(title) <> ''),
        CONSTRAINT qms_recommendation_body_nonblank CHECK (btrim(body) <> ''),
        CONSTRAINT qms_recommendation_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
        CONSTRAINT qms_recommendation_assumptions_array CHECK (jsonb_typeof(assumptions) = 'array'),
        CONSTRAINT qms_recommendation_status_source_backed CHECK (status = 'proposed'),
        CONSTRAINT qms_recommendation_autonomy_range CHECK (intended_autonomy BETWEEN 0 AND 4)
    );

    CREATE TABLE qms.recommendation_basis (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        recommendation_id uuid NOT NULL,
        standard_edition_id uuid NOT NULL,
        requirement_control_id uuid NOT NULL,
        knowledge_layer_rule_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
        evidence_id uuid NOT NULL,
        rationale text NOT NULL,
        model_provider varchar(120),
        model_identifier varchar(200) NOT NULL,
        model_version varchar(120) NOT NULL,
        prompt_version varchar(120) NOT NULL,
        rule_bundle_version varchar(120) NOT NULL,
        dataset_version_reference text,
        embedding_namespace text,
        trace_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_recommendation_basis_parent_fk
          FOREIGN KEY (tenant_id,organization_id,recommendation_id)
          REFERENCES qms.recommendation(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_recommendation_basis_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_recommendation_basis_requirement_edition_fk
          FOREIGN KEY (standard_edition_id,requirement_control_id)
          REFERENCES normative.requirement_control(standard_edition_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_recommendation_basis_evidence_fk
          FOREIGN KEY (tenant_id,organization_id,evidence_id)
          REFERENCES qms.evidence(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_recommendation_basis_exact_unique
          UNIQUE (recommendation_id,requirement_control_id,knowledge_layer_rule_id,evidence_id),
        CONSTRAINT qms_recommendation_basis_rationale_nonblank CHECK (btrim(rationale) <> ''),
        CONSTRAINT qms_recommendation_basis_model_identifier_nonblank CHECK (btrim(model_identifier) <> ''),
        CONSTRAINT qms_recommendation_basis_model_version_nonblank CHECK (btrim(model_version) <> ''),
        CONSTRAINT qms_recommendation_basis_prompt_version_nonblank CHECK (btrim(prompt_version) <> ''),
        CONSTRAINT qms_recommendation_basis_rule_bundle_nonblank CHECK (btrim(rule_bundle_version) <> '')
    );

    CREATE INDEX qms_recommendation_tenant_org_created_idx
      ON qms.recommendation(tenant_id,organization_id,created_at);
    CREATE INDEX qms_recommendation_basis_parent_idx
      ON qms.recommendation_basis(tenant_id,organization_id,recommendation_id);
    CREATE INDEX qms_recommendation_basis_normative_idx
      ON qms.recommendation_basis(standard_edition_id,requirement_control_id,knowledge_layer_rule_id);
    CREATE INDEX qms_recommendation_basis_evidence_idx
      ON qms.recommendation_basis(tenant_id,organization_id,evidence_id);

    CREATE FUNCTION qms.foundation_0010_validate_recommendation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    DECLARE assumption jsonb;
    BEGIN
        FOR assumption IN SELECT value FROM jsonb_array_elements(NEW.assumptions)
        LOOP
            IF jsonb_typeof(assumption) <> 'string' OR btrim(assumption #>> '{}') = '' THEN
                RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='assumptions must contain only nonblank strings';
            END IF;
        END LOOP;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0010_validate_basis()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms,normative AS $fn$
    DECLARE rule_status text; edition_status text;
    BEGIN
        SELECT status INTO rule_status FROM normative.knowledge_layer_rule
         WHERE id=NEW.knowledge_layer_rule_id;
        IF rule_status IS DISTINCT FROM 'published' THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='recommendation basis requires an exact published rule revision';
        END IF;
        SELECT status INTO edition_status FROM normative.standard_edition
         WHERE id=NEW.standard_edition_id;
        IF edition_status IS DISTINCT FROM 'published' THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='recommendation basis requires an exact published standard edition';
        END IF;
        RETURN NEW;
    END $fn$;

    CREATE FUNCTION qms.foundation_0010_reject_recommendation_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='recommendation history is immutable; create a new recommendation';
    END $fn$;

    CREATE FUNCTION qms.foundation_0010_reject_basis_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='recommendation basis is append-only frozen provenance';
    END $fn$;

    CREATE FUNCTION qms.foundation_0010_require_basis()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM qms.recommendation_basis WHERE recommendation_id=NEW.id) THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='governed recommendation requires at least one basis row';
        END IF;
        RETURN NULL;
    END $fn$;

    CREATE TRIGGER qms_recommendation_validate BEFORE INSERT ON qms.recommendation
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0010_validate_recommendation();
    CREATE TRIGGER qms_recommendation_append_only BEFORE UPDATE OR DELETE ON qms.recommendation
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0010_reject_recommendation_mutation();
    CREATE TRIGGER qms_recommendation_basis_validate BEFORE INSERT ON qms.recommendation_basis
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0010_validate_basis();
    CREATE TRIGGER qms_recommendation_basis_append_only BEFORE UPDATE OR DELETE ON qms.recommendation_basis
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0010_reject_basis_mutation();
    CREATE CONSTRAINT TRIGGER qms_recommendation_basis_complete
      AFTER INSERT ON qms.recommendation DEFERRABLE INITIALLY DEFERRED
      FOR EACH ROW EXECUTE FUNCTION qms.foundation_0010_require_basis();

    ALTER TABLE qms.recommendation ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.recommendation FORCE ROW LEVEL SECURITY;
    ALTER TABLE qms.recommendation_basis ENABLE ROW LEVEL SECURITY;
    ALTER TABLE qms.recommendation_basis FORCE ROW LEVEL SECURITY;

    EXECUTE format('CREATE POLICY qms_recommendation_select ON qms.recommendation FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_recommendation_insert ON qms.recommendation FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_recommendation_update ON qms.recommendation FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_recommendation_delete ON qms.recommendation FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_recommendation_migrator ON qms.recommendation FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);

    EXECUTE format('CREATE POLICY qms_recommendation_basis_select ON qms.recommendation_basis FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY qms_recommendation_basis_insert ON qms.recommendation_basis FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_recommendation_basis_update ON qms.recommendation_basis FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_recommendation_basis_delete ON qms.recommendation_basis FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY qms_recommendation_basis_migrator ON qms.recommendation_basis FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);

    EXECUTE format('GRANT SELECT,INSERT ON qms.recommendation,qms.recommendation_basis TO %I',app_role);
    EXECUTE format('GRANT SELECT ON qms.recommendation,qms.recommendation_basis TO %I',worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DROP TABLE qms.recommendation_basis;
DROP TABLE qms.recommendation;
DROP FUNCTION qms.foundation_0010_require_basis();
DROP FUNCTION qms.foundation_0010_reject_basis_mutation();
DROP FUNCTION qms.foundation_0010_reject_recommendation_mutation();
DROP FUNCTION qms.foundation_0010_validate_basis();
DROP FUNCTION qms.foundation_0010_validate_recommendation();
"""


def apply_phase10(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase10(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0009_knowledge_layer_foundation")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(apply_phase10, reverse_phase10)],
        state_operations=[
            migrations.CreateModel(name="Recommendation", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.TextField()),
                ("body", models.TextField()),
                ("confidence", models.DecimalField(decimal_places=4, max_digits=5)),
                ("assumptions", models.JSONField(default=list)),
                ("impact", models.TextField(blank=True, null=True)),
                ("status", models.CharField(choices=[("proposed", "Proposed")], default="proposed", max_length=24)),
                ("intended_autonomy", models.PositiveSmallIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
            ], options={"managed": False, "db_table": 'qms"."recommendation'}),
            migrations.CreateModel(name="RecommendationBasis", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("rationale", models.TextField()),
                ("model_provider", models.CharField(blank=True, max_length=120, null=True)),
                ("model_identifier", models.CharField(max_length=200)),
                ("model_version", models.CharField(max_length=120)),
                ("prompt_version", models.CharField(max_length=120)),
                ("rule_bundle_version", models.CharField(max_length=120)),
                ("dataset_version_reference", models.TextField(blank=True, null=True)),
                ("embedding_namespace", models.TextField(blank=True, null=True)),
                ("trace_id", models.UUIDField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("recommendation", models.ForeignKey(db_column="recommendation_id", on_delete=django.db.models.deletion.PROTECT, related_name="basis_rows", to="foundation.recommendation")),
                ("standard_edition", models.ForeignKey(db_column="standard_edition_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.standardedition")),
                ("requirement_control", models.ForeignKey(db_column="requirement_control_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.requirementcontrol")),
                ("knowledge_layer_rule", models.ForeignKey(db_column="knowledge_layer_rule_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.knowledgelayerrule")),
                ("evidence", models.ForeignKey(db_column="evidence_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.evidence")),
            ], options={"managed": False, "db_table": 'qms"."recommendation_basis'}),
        ],
    )]
