"""Phase 5 additive Risk, Opportunity and Objective foundation."""

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

    CREATE TABLE qms.risk (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        process_id uuid NOT NULL,
        cause text NOT NULL,
        event text NOT NULL,
        consequence text NOT NULL,
        likelihood text NOT NULL,
        impact text NOT NULL,
        residual text NOT NULL,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_risk_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_risk_process_fk FOREIGN KEY (tenant_id,organization_id,process_id)
          REFERENCES qms.process(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_risk_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.risk(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_risk_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_risk_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_risk_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_risk_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_risk_fields_nonblank CHECK
          (btrim(cause) <> '' AND btrim(event) <> '' AND btrim(consequence) <> '' AND
           btrim(likelihood) <> '' AND btrim(impact) <> '' AND btrim(residual) <> ''),
        CONSTRAINT qms_risk_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_risk_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id)
    );

    CREATE TABLE qms.opportunity (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        process_id uuid NOT NULL,
        hypothesis text NOT NULL,
        benefit text NOT NULL,
        feasibility text NOT NULL,
        status varchar(40) NOT NULL,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_opportunity_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_opportunity_process_fk FOREIGN KEY (tenant_id,organization_id,process_id)
          REFERENCES qms.process(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_opportunity_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.opportunity(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_opportunity_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_opportunity_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_opportunity_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_opportunity_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_opportunity_fields_nonblank CHECK
          (btrim(hypothesis) <> '' AND btrim(benefit) <> '' AND btrim(feasibility) <> '' AND btrim(status) <> ''),
        CONSTRAINT qms_opportunity_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_opportunity_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id)
    );

    CREATE TABLE qms.objective (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        organization_id uuid NOT NULL,
        lineage_id uuid NOT NULL,
        revision integer NOT NULL,
        previous_revision_id uuid,
        owner_id uuid,
        target text NOT NULL,
        due_date date,
        status varchar(40) NOT NULL,
        change_reason text,
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT qms_objective_org_fk FOREIGN KEY (tenant_id,organization_id)
          REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_objective_owner_fk FOREIGN KEY (tenant_id,owner_id)
          REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_objective_previous_fk FOREIGN KEY (tenant_id,organization_id,previous_revision_id)
          REFERENCES qms.objective(tenant_id,organization_id,id) ON DELETE RESTRICT,
        CONSTRAINT qms_objective_tenant_org_id_unique UNIQUE (tenant_id,organization_id,id),
        CONSTRAINT qms_objective_lineage_revision_unique UNIQUE (tenant_id,organization_id,lineage_id,revision),
        CONSTRAINT qms_objective_previous_unique UNIQUE (tenant_id,organization_id,previous_revision_id),
        CONSTRAINT qms_objective_revision_positive CHECK (revision > 0),
        CONSTRAINT qms_objective_fields_nonblank CHECK (btrim(target) <> '' AND btrim(status) <> ''),
        CONSTRAINT qms_objective_previous_shape CHECK
          ((revision = 1 AND previous_revision_id IS NULL) OR (revision > 1 AND previous_revision_id IS NOT NULL)),
        CONSTRAINT qms_objective_not_self CHECK (previous_revision_id IS NULL OR previous_revision_id <> id)
    );

    CREATE INDEX qms_risk_lineage_idx ON qms.risk(tenant_id,organization_id,lineage_id,revision);
    CREATE INDEX qms_risk_process_idx ON qms.risk(tenant_id,organization_id,process_id);
    CREATE INDEX qms_opportunity_lineage_idx ON qms.opportunity(tenant_id,organization_id,lineage_id,revision);
    CREATE INDEX qms_opportunity_process_idx ON qms.opportunity(tenant_id,organization_id,process_id);
    CREATE INDEX qms_objective_lineage_idx ON qms.objective(tenant_id,organization_id,lineage_id,revision);

    CREATE FUNCTION qms.foundation_0005_guard_boundary_update()
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

    CREATE FUNCTION qms.foundation_0005_reject_revision_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='Phase 5 revisions are append-only';
    END $fn$;

    CREATE FUNCTION qms.foundation_0005_validate_lineage()
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

    FOREACH table_name IN ARRAY ARRAY['risk','opportunity','objective'] LOOP
        EXECUTE format('CREATE TRIGGER %I BEFORE INSERT ON qms.%I FOR EACH ROW EXECUTE FUNCTION qms.foundation_0005_validate_lineage()', 'qms_'||table_name||'_validate_lineage', table_name);
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE ON qms.%I FOR EACH ROW EXECUTE FUNCTION qms.foundation_0005_guard_boundary_update()', 'qms_'||table_name||'_a_boundary_immutable', table_name);
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON qms.%I FOR EACH ROW EXECUTE FUNCTION qms.foundation_0005_reject_revision_mutation()', 'qms_'||table_name||'_z_append_only', table_name);
        EXECUTE format('ALTER TABLE qms.%I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE qms.%I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_select', table_name, app_role, worker_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_insert', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_update', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR DELETE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)', 'qms_'||table_name||'_delete', table_name, app_role);
        EXECUTE format('CREATE POLICY %I ON qms.%I FOR ALL TO %I USING (true) WITH CHECK (true)', 'qms_'||table_name||'_migrator', table_name, current_user);
    END LOOP;

    EXECUTE format('GRANT SELECT,INSERT ON qms.risk,qms.opportunity,qms.objective TO %I', app_role);
    EXECUTE format('GRANT SELECT ON qms.risk,qms.opportunity,qms.objective TO %I', worker_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DROP TABLE qms.objective;
DROP TABLE qms.opportunity;
DROP TABLE qms.risk;
DROP FUNCTION qms.foundation_0005_validate_lineage();
DROP FUNCTION qms.foundation_0005_reject_revision_mutation();
DROP FUNCTION qms.foundation_0005_guard_boundary_update();
"""


def apply_phase5(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase5(apps, schema_editor):
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
    dependencies = [("foundation", "0004_qms_harmonized_context_foundation")]
    operations = [
        migrations.RunPython(apply_phase5, reverse_phase5),
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.CreateModel(name="Risk", fields=revision_fields([
                ("cause", models.TextField()), ("event", models.TextField()),
                ("consequence", models.TextField()), ("likelihood", models.TextField()),
                ("impact", models.TextField()), ("residual", models.TextField()),
                ("process", models.ForeignKey(db_column="process_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.process")),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.risk")),
            ]), options={"managed": False, "db_table": 'qms"."risk'}),
            migrations.CreateModel(name="Opportunity", fields=revision_fields([
                ("hypothesis", models.TextField()), ("benefit", models.TextField()),
                ("feasibility", models.TextField()), ("status", models.CharField(max_length=40)),
                ("process", models.ForeignKey(db_column="process_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.process")),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.opportunity")),
            ]), options={"managed": False, "db_table": 'qms"."opportunity'}),
            migrations.CreateModel(name="Objective", fields=revision_fields([
                ("target", models.TextField()), ("due_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(max_length=40)),
                ("owner", models.ForeignKey(blank=True, db_column="owner_id", null=True, on_delete=django.db.models.deletion.PROTECT, to="foundation.userprojection")),
                ("previous_revision", models.OneToOneField(blank=True, db_column="previous_revision_id", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_revision", to="foundation.objective")),
            ]), options={"managed": False, "db_table": 'qms"."objective'}),
        ]),
    ]
