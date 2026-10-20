"""Tenant-scoped AI provider metering, independent from onboarding transactions."""

import uuid

from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = r'''
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
        worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'AI usage runtime roles are required';
  END IF;
  CREATE SCHEMA IF NOT EXISTS ai_usage;
  CREATE TABLE ai_usage.model_pricing_version (
    id uuid PRIMARY KEY, provider varchar(120) NOT NULL, model_identifier varchar(200) NOT NULL,
    effective_from timestamptz NOT NULL, effective_to timestamptz NULL,
    currency char(3) NOT NULL, rate_unit integer NOT NULL CHECK(rate_unit > 0),
    input_token_rate numeric(20,10) NULL, output_token_rate numeric(20,10) NULL,
    cached_input_token_rate numeric(20,10) NULL, source_reference text NOT NULL,
    verification_status varchar(24) NOT NULL CHECK(verification_status IN ('verified','unverified','retired')),
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT ai_usage_pricing_dates CHECK(effective_to IS NULL OR effective_to > effective_from)
  );
  CREATE INDEX ai_usage_pricing_lookup_idx ON ai_usage.model_pricing_version(provider, model_identifier, effective_from DESC);
  CREATE TABLE ai_usage.usage_record (
    id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    adminapps_tenant_id uuid NULL, product_identifier varchar(80) NOT NULL, agent_name varchar(120) NOT NULL,
    capability_name varchar(120) NOT NULL, execution_id uuid NOT NULL, correlation_id uuid NOT NULL,
    invocation_id varchar(200) NOT NULL, provider_request_id varchar(255) NULL,
    provider varchar(120) NOT NULL, model_identifier varchar(200) NOT NULL, api_operation varchar(80) NOT NULL,
    provider_response_status varchar(48) NULL, duration_ms integer NULL CHECK(duration_ms >= 0),
    input_tokens bigint NULL CHECK(input_tokens >= 0), output_tokens bigint NULL CHECK(output_tokens >= 0),
    total_tokens bigint NULL CHECK(total_tokens >= 0), cached_input_tokens bigint NULL CHECK(cached_input_tokens >= 0),
    usage_status varchar(24) NOT NULL CHECK(usage_status IN ('started','reported','unknown')),
    currency char(3) NULL, pricing_version_id uuid NULL REFERENCES ai_usage.model_pricing_version(id) ON DELETE RESTRICT,
    input_token_rate numeric(20,10) NULL, output_token_rate numeric(20,10) NULL,
    cached_input_token_rate numeric(20,10) NULL, estimated_provider_cost numeric(20,10) NULL,
    cost_status varchar(24) NOT NULL CHECK(cost_status IN ('pending','estimated','unpriced')),
    attempt_status varchar(24) NOT NULL CHECK(attempt_status IN ('started','completed','rejected','failed')),
    provider_outcome varchar(48) NULL, error_category varchar(80) NULL, finalized_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(), updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT ai_usage_invocation_unique UNIQUE(tenant_id, invocation_id),
    CONSTRAINT ai_usage_total_consistent CHECK(total_tokens IS NULL OR input_tokens IS NULL OR output_tokens IS NULL OR total_tokens = input_tokens + output_tokens)
  );
  CREATE INDEX ai_usage_record_tenant_time_idx ON ai_usage.usage_record(tenant_id, created_at DESC);
  CREATE INDEX ai_usage_record_dimensions_idx ON ai_usage.usage_record(product_identifier, provider, model_identifier, capability_name, created_at DESC);
  ALTER TABLE ai_usage.usage_record ENABLE ROW LEVEL SECURITY;
  ALTER TABLE ai_usage.usage_record FORCE ROW LEVEL SECURITY;
  EXECUTE format($policy$
    CREATE POLICY ai_usage_record_tenant ON ai_usage.usage_record FOR ALL TO %I,%I
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  $policy$, app_role, worker_role);
  EXECUTE format('GRANT USAGE ON SCHEMA ai_usage TO %I,%I', app_role, worker_role);
  EXECUTE format('GRANT SELECT ON ai_usage.model_pricing_version TO %I,%I', app_role, worker_role);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON ai_usage.usage_record TO %I,%I', app_role, worker_role);
END
$migration$;
'''

REVERSE_SQL = 'DROP SCHEMA ai_usage CASCADE;'


class Migration(migrations.Migration):
    dependencies = [("foundation", "0038_value_discovery_execution")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(name="AIModelPricingVersion", fields=[
                    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                    ("provider", models.CharField(max_length=120)), ("model_identifier", models.CharField(max_length=200)),
                    ("effective_from", models.DateTimeField()), ("effective_to", models.DateTimeField(null=True, blank=True)),
                    ("currency", models.CharField(max_length=3)), ("rate_unit", models.PositiveIntegerField()),
                    ("input_token_rate", models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                    ("output_token_rate", models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                    ("cached_input_token_rate", models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                    ("source_reference", models.TextField()), ("verification_status", models.CharField(max_length=24)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                ], options={"managed": False, "db_table": 'ai_usage"."model_pricing_version'}),
                migrations.CreateModel(name="AIUsageRecord", fields=[
                    ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                    ("adminapps_tenant_id", models.UUIDField(null=True, blank=True)), ("product_identifier", models.CharField(max_length=80)),
                    ("agent_name", models.CharField(max_length=120)), ("capability_name", models.CharField(max_length=120)),
                    ("execution_id", models.UUIDField()), ("correlation_id", models.UUIDField()), ("invocation_id", models.CharField(max_length=200)),
                    ("provider_request_id", models.CharField(max_length=255, null=True, blank=True)), ("provider", models.CharField(max_length=120)),
                    ("model_identifier", models.CharField(max_length=200)), ("api_operation", models.CharField(max_length=80)),
                    ("provider_response_status", models.CharField(max_length=48, null=True, blank=True)), ("duration_ms", models.PositiveIntegerField(null=True, blank=True)),
                    ("input_tokens", models.BigIntegerField(null=True, blank=True)), ("output_tokens", models.BigIntegerField(null=True, blank=True)),
                    ("total_tokens", models.BigIntegerField(null=True, blank=True)), ("cached_input_tokens", models.BigIntegerField(null=True, blank=True)),
                    ("usage_status", models.CharField(max_length=24)), ("currency", models.CharField(max_length=3, null=True, blank=True)),
                    ("input_token_rate", models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                    ("output_token_rate", models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                    ("cached_input_token_rate", models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                    ("estimated_provider_cost", models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                    ("cost_status", models.CharField(max_length=24)), ("attempt_status", models.CharField(max_length=24)),
                    ("provider_outcome", models.CharField(max_length=48, null=True, blank=True)), ("error_category", models.CharField(max_length=80, null=True, blank=True)),
                    ("finalized_at", models.DateTimeField(null=True, blank=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                    ("tenant", models.ForeignKey(to="foundation.tenantprojection", on_delete=django.db.models.deletion.PROTECT, db_column="tenant_id")),
                    ("pricing_version", models.ForeignKey(to="foundation.aimodelpricingversion", null=True, blank=True, on_delete=django.db.models.deletion.PROTECT, db_column="pricing_version_id")),
                ], options={"managed": False, "db_table": 'ai_usage"."usage_record'}),
            ],
        ),
    ]
