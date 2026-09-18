"""Phase 6 additive Change and minimal measurement-definition foundation."""

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

    CREATE TABLE qms.measurement_definition (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        process_id uuid,
        what_is_measured text NOT NULL,
        method text NOT NULL,
        measurement_timing text NOT NULL,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_measurement_definition_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_measurement_definition_process_fk FOREIGN KEY (tenant_id,organization_id,process_id)
          REFERENCES qms.process(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_measurement_definition_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.measurement_definition(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_measurement_definition_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_measurement_definition_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_measurement_definition_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_measurement_definition_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_measurement_definition_fields_nonblank CHECK
          (btrim(what_is_measured) <> '' AND btrim(method) <> '' AND btrim(measurement_timing) <> ''),
        CONSTRAINT qms_measurement_definition_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_measurement_definition_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id)
    );

    CREATE TABLE qms.change (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        type varchar(80) NOT NULL,
        purpose text NOT NULL,
        impact text NOT NULL,
        status varchar(40) NOT NULL,
        approval_id uuid,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_change_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_change_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.change(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_change_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_change_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_change_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_change_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_change_fields_nonblank CHECK
          (btrim(type) <> '' AND btrim(purpose) <> '' AND btrim(impact) <> '' AND btrim(status) <> ''),
        CONSTRAINT qms_change_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_change_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id)
    );

    CREATE TABLE qms.change_process (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        change_revision_id uuid NOT NULL,
        process_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_change_process_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_change_process_change_fk FOREIGN KEY (tenant_id,organization_id,change_revision_id)
          REFERENCES qms.change(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_change_process_process_fk FOREIGN KEY (tenant_id,organization_id,process_id)
          REFERENCES qms.process(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_change_process_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_change_process_unique UNIQUE (tenant_id,organization_id,change_revision_id,process_id)
    );

    ALTER TABLE qms.objective ADD COLUMN metric_id uuid;
    ALTER TABLE qms.objective ADD CONSTRAINT qms_objective_metric_fk
      FOREIGN KEY (tenant_id,organization_id,metric_id)
      REFERENCES qms.measurement_definition(tenant_id,organization_id,id) ON DELETE RESTRICT;

    CREATE INDEX qms_measurement_definition_lineage_idx
      ON qms.measurement_definition(tenant_id,organization_id,lineage_id,revision);
    CREATE INDEX qms_measurement_definition_process_idx
      ON qms.measurement_definition(tenant_id,organization_id,process_id);
    CREATE INDEX qms_change_lineage_idx ON qms.change(tenant_id,organization_id,lineage_id,revision);
    CREATE INDEX qms_change_process_change_idx ON qms.change_process(tenant_id,organization_id,change_revision_id);
    CREATE INDEX qms_objective_metric_idx ON qms.objective(tenant_id,organization_id,metric_id);

    CREATE FUNCTION qms.foundation_0006_guard_boundary_update()
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

    CREATE FUNCTION qms.foundation_0006_reject_history_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='Phase 6 history is append-only';
    END $fn$;

    CREATE FUNCTION qms.foundation_0006_validate_lineage()
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

    FOREACH table_name IN ARRAY ARRAY['measurement_definition','change'] LOOP
        EXECUTE format('CREATE TRIGGER %I BEFORE INSERT ON qms.%I FOR EACH ROW EXECUTE FUNCTION qms.foundation_0006_validate_lineage()', 'qms_'||table_name||'_validate_lineage', table_name);
    END LOOP;
    FOREACH table_name IN ARRAY ARRAY['measurement_definition','change','change_process'] LOOP
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE ON qms.%I FOR EACH ROW EXECUTE FUNCTION qms.foundation_0006_guard_boundary_update()', 'qms_'||table_name||'_a_boundary_immutable', table_name);
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON qms.%I FOR EACH ROW EXECUTE FUNCTION qms.foundation_0006_reject_history_mutation()', 'qms_'||table_name||'_z_append_only', table_name);
        EXECUTE format('ALTER TABLE qms.%I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE qms.%I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_select', table_name, app_role, worker_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_insert', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_update', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_delete', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR ALL TO %I USING (true) WITH CHECK (true)', 'qms_'||table_name||'_migrator', table_name, current_user);
    END LOOP;

    EXECUTE format('GRANT SELECT,INSERT ON qms.measurement_definition,qms.change,qms.change_process TO %I', app_role);
    EXECUTE format('GRANT SELECT ON qms.measurement_definition,qms.change,qms.change_process TO %I', worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
ALTER TABLE qms.objective DROP CONSTRAINT qms_objective_metric_fk;
ALTER TABLE qms.objective DROP COLUMN metric_id;
DROP TABLE qms.change_process;
DROP TABLE qms.change;
DROP TABLE qms.measurement_definition;
DROP FUNCTION qms.foundation_0006_validate_lineage();
DROP FUNCTION qms.foundation_0006_reject_history_mutation();
DROP FUNCTION qms.foundation_0006_guard_boundary_update();
"""


def apply_phase6(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase6(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


def revision_fields(extra_fields):
    return [
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("lineage_id", models.UUIDField()),
        ("revision", models.PositiveIntegerField()),
        *extra_fields,
        ("change_reason", models.TextField(blank=True, null=True)),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
        ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
    ]


class Migration(migrations.Migration):
    dependencies = [("foundation", "0005_risk_opportunity_objective_foundation")]
    operations = [
        migrations.RunPython(apply_phase6, reverse_phase6),
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.CreateModel(name="MeasurementDefinition", fields=revision_fields([
                ("what_is_measured", models.TextField()),
                ("method", models.TextField()),
                ("measurement_timing", models.TextField()),
                ("process", models.ForeignKey(blank=True, db_column="process_id", null=True, on_delete=django.db.models.deletion.PROTECT, to="foundation.process")),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.measurementdefinition")),
            ]), options={"managed": False, "db_table": 'qms"."measurement_definition'}),
            migrations.CreateModel(name="Change", fields=revision_fields([
                ("change_type", models.CharField(db_column="type", max_length=80)),
                ("purpose", models.TextField()),
                ("impact", models.TextField()),
                ("status", models.CharField(max_length=40)),
                ("approval_id", models.UUIDField(blank=True, null=True)),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.change")),
            ]), options={"managed": False, "db_table": 'qms"."change'}),
            migrations.CreateModel(name="ChangeProcess", fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                ("organization", models.ForeignKey(db_column="organization_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.organization")),
                ("change_revision", models.ForeignKey(db_column="change_revision_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.change")),
                ("process", models.ForeignKey(db_column="process_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.process")),
            ], options={"managed": False, "db_table": 'qms"."change_process'}),
            migrations.AddField(
                model_name="objective", name="metric",
                field=models.ForeignKey(blank=True, db_column="metric_id", null=True, on_delete=django.db.models.deletion.PROTECT, to="foundation.measurementdefinition"),
            ),
        ]),
    ]
