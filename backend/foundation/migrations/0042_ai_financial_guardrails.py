"""Product-scoped, auditable AI financial reservations for controlled tests."""

import uuid

from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = r'''
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
        worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'AI financial guardrail runtime roles are required';
  END IF;
  CREATE TABLE ai_usage.financial_guardrail_policy (
    id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    product_identifier varchar(80) NOT NULL, provider varchar(120) NOT NULL, model_identifier varchar(200) NOT NULL,
    period_start timestamptz NOT NULL, period_end timestamptz NOT NULL, currency char(3) NOT NULL,
    max_request_count integer NOT NULL CHECK(max_request_count > 0),
    max_input_tokens bigint NOT NULL CHECK(max_input_tokens >= 0),
    max_output_tokens bigint NOT NULL CHECK(max_output_tokens > 0),
    max_reserved_cost numeric(20,10) NOT NULL CHECK(max_reserved_cost >= 0),
    policy_scope varchar(40) NOT NULL CHECK(policy_scope IN ('controlled_test')),
    authority_reference text NOT NULL, status varchar(24) NOT NULL CHECK(status IN ('enabled','disabled')),
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(), updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT ai_usage_guardrail_policy_period CHECK(period_end > period_start),
    CONSTRAINT ai_usage_guardrail_policy_product CHECK(product_identifier='iso-smart')
  );
  CREATE TABLE ai_usage.financial_reservation (
    id uuid PRIMARY KEY, policy_id uuid NOT NULL REFERENCES ai_usage.financial_guardrail_policy(id) ON DELETE RESTRICT,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    invocation_id varchar(200) NOT NULL, usage_record_id uuid NULL UNIQUE REFERENCES ai_usage.usage_record(id) ON DELETE RESTRICT,
    reserved_input_tokens bigint NOT NULL CHECK(reserved_input_tokens >= 0),
    reserved_output_tokens bigint NOT NULL CHECK(reserved_output_tokens > 0),
    reserved_cost numeric(20,10) NOT NULL CHECK(reserved_cost >= 0), settled_cost numeric(20,10) NULL CHECK(settled_cost >= 0),
    currency char(3) NOT NULL, status varchar(24) NOT NULL CHECK(status IN ('reserved','settled','released','unresolved')),
    resolution_reason varchar(80) NULL, created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    settled_at timestamptz NULL, updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT ai_usage_financial_reservation_invocation UNIQUE(tenant_id, invocation_id)
  );
  CREATE INDEX ai_usage_financial_policy_lookup_idx ON ai_usage.financial_guardrail_policy(tenant_id, product_identifier, provider, model_identifier, period_start DESC);
  CREATE INDEX ai_usage_financial_reservation_policy_idx ON ai_usage.financial_reservation(policy_id, status);
  ALTER TABLE ai_usage.financial_guardrail_policy ENABLE ROW LEVEL SECURITY;
  ALTER TABLE ai_usage.financial_guardrail_policy FORCE ROW LEVEL SECURITY;
  ALTER TABLE ai_usage.financial_reservation ENABLE ROW LEVEL SECURITY;
  ALTER TABLE ai_usage.financial_reservation FORCE ROW LEVEL SECURITY;
  EXECUTE format($policy$
    CREATE POLICY ai_usage_guardrail_policy_tenant ON ai_usage.financial_guardrail_policy FOR ALL TO %I,%I
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  $policy$, app_role, worker_role);
  EXECUTE format($policy$
    CREATE POLICY ai_usage_financial_reservation_tenant ON ai_usage.financial_reservation FOR ALL TO %I,%I
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  $policy$, app_role, worker_role);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON ai_usage.financial_guardrail_policy TO %I,%I', app_role, worker_role);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON ai_usage.financial_reservation TO %I,%I', app_role, worker_role);
END
$migration$;
'''

REVERSE_SQL = 'DROP TABLE ai_usage.financial_reservation; DROP TABLE ai_usage.financial_guardrail_policy;'


class Migration(migrations.Migration):
    dependencies = [("foundation", "0041_ai_usage_retry_exhausted_recovery")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(name="AIFinancialGuardrailPolicy", fields=[
                    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                    ("product_identifier", models.CharField(max_length=80)), ("provider", models.CharField(max_length=120)), ("model_identifier", models.CharField(max_length=200)),
                    ("period_start", models.DateTimeField()), ("period_end", models.DateTimeField()), ("currency", models.CharField(max_length=3)),
                    ("max_request_count", models.PositiveIntegerField()), ("max_input_tokens", models.BigIntegerField()), ("max_output_tokens", models.BigIntegerField()),
                    ("max_reserved_cost", models.DecimalField(max_digits=20, decimal_places=10)), ("policy_scope", models.CharField(max_length=40)),
                    ("authority_reference", models.TextField()), ("status", models.CharField(max_length=24)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                    ("tenant", models.ForeignKey(to="foundation.tenantprojection", on_delete=django.db.models.deletion.PROTECT, db_column="tenant_id")),
                ], options={"managed": False, "db_table": 'ai_usage"."financial_guardrail_policy'}),
                migrations.CreateModel(name="AIFinancialReservation", fields=[
                    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)), ("invocation_id", models.CharField(max_length=200)),
                    ("reserved_input_tokens", models.BigIntegerField()), ("reserved_output_tokens", models.BigIntegerField()),
                    ("reserved_cost", models.DecimalField(max_digits=20, decimal_places=10)), ("settled_cost", models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                    ("currency", models.CharField(max_length=3)), ("status", models.CharField(max_length=24)), ("resolution_reason", models.CharField(max_length=80, null=True, blank=True)),
                    ("created_at", models.DateTimeField(auto_now_add=True)), ("settled_at", models.DateTimeField(null=True, blank=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                    ("policy", models.ForeignKey(to="foundation.aifinancialguardrailpolicy", on_delete=django.db.models.deletion.PROTECT, db_column="policy_id")),
                    ("tenant", models.ForeignKey(to="foundation.tenantprojection", on_delete=django.db.models.deletion.PROTECT, db_column="tenant_id")),
                    ("usage_record", models.OneToOneField(to="foundation.aiusagerecord", on_delete=django.db.models.deletion.PROTECT, db_column="usage_record_id", null=True, blank=True)),
                ], options={"managed": False, "db_table": 'ai_usage"."financial_reservation'}),
            ],
        ),
    ]
