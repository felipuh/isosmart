"""Phase 3 additive eventing, inbox and tamper-evident audit foundation."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
    projector_role text := current_setting('foundation.projector_role', true);
    audit_writer_role text := current_setting('foundation.audit_writer_role', true);
    eventing_created boolean := false;
    audit_created boolean := false;
BEGIN
    IF app_role IS NULL OR app_role = '' OR worker_role IS NULL OR worker_role = '' OR
       projector_role IS NULL OR projector_role = '' OR audit_writer_role IS NULL OR audit_writer_role = '' THEN
        RAISE EXCEPTION 'foundation app, worker, projector and audit writer roles are required';
    END IF;
    IF NOT EXISTS (
        SELECT FROM pg_roles WHERE rolname = audit_writer_role AND rolcanlogin
          AND NOT rolsuper AND NOT rolbypassrls
    ) THEN
        RAISE EXCEPTION 'foundation audit writer must be a non-superuser, non-BYPASSRLS LOGIN principal';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_namespace WHERE nspname = 'eventing') THEN
        CREATE SCHEMA eventing;
        eventing_created := true;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_namespace WHERE nspname = 'audit') THEN
        CREATE SCHEMA audit;
        audit_created := true;
    END IF;

    CREATE TABLE qms.foundation_0003_ownership (
        singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
        eventing_schema_was_created boolean NOT NULL,
        audit_schema_was_created boolean NOT NULL
    );
    INSERT INTO qms.foundation_0003_ownership(eventing_schema_was_created, audit_schema_was_created)
    VALUES (eventing_created, audit_created);

    CREATE TABLE eventing.domain_event (
        event_id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        event_type varchar(160) NOT NULL,
        schema_version integer NOT NULL,
        aggregate_type varchar(120) NOT NULL,
        aggregate_id uuid NOT NULL,
        aggregate_version bigint NOT NULL,
        occurred_at timestamptz NOT NULL,
        recorded_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        trace_id uuid NOT NULL,
        correlation_id uuid,
        causation_id uuid,
        source varchar(120) NOT NULL,
        payload jsonb NOT NULL,
        payload_hash char(64) NOT NULL,
        CONSTRAINT foundation_domain_event_schema_version_positive CHECK (schema_version > 0),
        CONSTRAINT foundation_domain_event_aggregate_version_nonnegative CHECK (aggregate_version >= 0),
        CONSTRAINT foundation_domain_event_payload_hash_hex CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
        CONSTRAINT foundation_domain_event_tenant_event_unique UNIQUE (tenant_id,event_id)
    );
    CREATE INDEX foundation_domain_event_tenant_recorded_idx
      ON eventing.domain_event(tenant_id,recorded_at,event_id);
    CREATE INDEX foundation_domain_event_aggregate_idx
      ON eventing.domain_event(tenant_id,aggregate_type,aggregate_id,aggregate_version);

    CREATE TABLE eventing.transactional_outbox (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        domain_event_id uuid NOT NULL UNIQUE,
        status varchar(24) NOT NULL DEFAULT 'pending',
        publish_attempts integer NOT NULL DEFAULT 0,
        available_at timestamptz NOT NULL,
        lease_owner varchar(160),
        lease_expires_at timestamptz,
        published_at timestamptz,
        last_error_code varchar(64),
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT foundation_outbox_event_tenant_fk FOREIGN KEY (tenant_id,domain_event_id)
          REFERENCES eventing.domain_event(tenant_id,event_id) ON DELETE RESTRICT,
        CONSTRAINT foundation_outbox_status_valid CHECK (status IN ('pending','processing','published','failed')),
        CONSTRAINT foundation_outbox_attempts_nonnegative CHECK (publish_attempts >= 0),
        CONSTRAINT foundation_outbox_lease_state CHECK (
          (status = 'processing' AND lease_owner IS NOT NULL AND lease_expires_at IS NOT NULL) OR
          (status <> 'processing' AND lease_owner IS NULL AND lease_expires_at IS NULL)
        ),
        CONSTRAINT foundation_outbox_published_timestamp CHECK
          ((status = 'published' AND published_at IS NOT NULL) OR (status <> 'published' AND published_at IS NULL))
    );
    CREATE INDEX foundation_outbox_ready_idx
      ON eventing.transactional_outbox(tenant_id,available_at,created_at)
      WHERE status IN ('pending','failed');

    CREATE TABLE eventing.consumer_receipt (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        consumer_name varchar(160) NOT NULL,
        event_id uuid NOT NULL,
        payload_hash char(64) NOT NULL,
        received_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        processed_at timestamptz,
        status varchar(24) NOT NULL DEFAULT 'received',
        attempts integer NOT NULL DEFAULT 0,
        last_error_code varchar(64),
        trace_id uuid NOT NULL,
        CONSTRAINT foundation_consumer_receipt_consumer_event_unique UNIQUE (consumer_name,event_id),
        CONSTRAINT foundation_consumer_receipt_status_valid CHECK (status IN ('received','processing','processed','failed')),
        CONSTRAINT foundation_consumer_receipt_attempts_nonnegative CHECK (attempts >= 0),
        CONSTRAINT foundation_consumer_receipt_hash_hex CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
        CONSTRAINT foundation_consumer_receipt_processed_timestamp CHECK
          ((status = 'processed' AND processed_at IS NOT NULL) OR (status <> 'processed' AND processed_at IS NULL))
    );
    CREATE INDEX foundation_consumer_receipt_tenant_received_idx
      ON eventing.consumer_receipt(tenant_id,received_at,event_id);

    CREATE TABLE audit.immutable_audit_log (
        id uuid PRIMARY KEY,
        tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
        stream_type varchar(120) NOT NULL,
        stream_id uuid NOT NULL,
        sequence_number bigint NOT NULL,
        actor_type varchar(80) NOT NULL,
        actor_id varchar(255),
        action varchar(160) NOT NULL,
        entity_type varchar(120) NOT NULL,
        entity_id uuid NOT NULL,
        trace_id uuid NOT NULL,
        occurred_at timestamptz NOT NULL,
        before_hash char(64),
        after_hash char(64),
        payload_hash char(64),
        previous_entry_hash char(64),
        entry_hash char(64) NOT NULL,
        metadata_canonical text NOT NULL DEFAULT '{}',
        created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
        CONSTRAINT foundation_audit_stream_sequence_unique
          UNIQUE (tenant_id,stream_type,stream_id,sequence_number),
        CONSTRAINT foundation_audit_sequence_positive CHECK (sequence_number > 0),
        CONSTRAINT foundation_audit_hashes_hex CHECK (
          (before_hash IS NULL OR before_hash ~ '^[0-9a-f]{64}$') AND
          (after_hash IS NULL OR after_hash ~ '^[0-9a-f]{64}$') AND
          (payload_hash IS NULL OR payload_hash ~ '^[0-9a-f]{64}$') AND
          (previous_entry_hash IS NULL OR previous_entry_hash ~ '^[0-9a-f]{64}$') AND
          entry_hash ~ '^[0-9a-f]{64}$'
        ),
        CONSTRAINT foundation_audit_metadata_bounded CHECK (octet_length(metadata_canonical) <= 32768)
    );
    CREATE INDEX foundation_audit_tenant_stream_idx
      ON audit.immutable_audit_log(tenant_id,stream_type,stream_id,sequence_number);

    CREATE FUNCTION eventing.foundation_reject_domain_event_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,eventing AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='domain events are append-only';
    END $fn$;
    CREATE TRIGGER foundation_domain_event_append_only
      BEFORE UPDATE OR DELETE ON eventing.domain_event FOR EACH ROW
      EXECUTE FUNCTION eventing.foundation_reject_domain_event_mutation();

    CREATE FUNCTION eventing.foundation_guard_outbox_update()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,eventing AS $fn$
    BEGIN
        IF OLD.id IS DISTINCT FROM NEW.id OR OLD.tenant_id IS DISTINCT FROM NEW.tenant_id OR
           OLD.domain_event_id IS DISTINCT FROM NEW.domain_event_id OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='outbox identity and tenant are immutable';
        END IF;
        IF OLD.status = 'published' OR NOT (
          (OLD.status IN ('pending','failed') AND NEW.status = 'processing') OR
          (OLD.status = 'processing' AND NEW.status = 'processing' AND OLD.lease_expires_at <= statement_timestamp()) OR
          (OLD.status = 'processing' AND NEW.status IN ('published','failed'))
        ) THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='invalid outbox state transition';
        END IF;
        IF NEW.status = 'processing' AND NEW.publish_attempts <> OLD.publish_attempts + 1 THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='outbox claim must increment attempts exactly once';
        END IF;
        IF NEW.status <> 'processing' AND NEW.publish_attempts <> OLD.publish_attempts THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='outbox completion cannot change attempts';
        END IF;
        RETURN NEW;
    END $fn$;
    CREATE TRIGGER foundation_outbox_guard_update BEFORE UPDATE ON eventing.transactional_outbox
      FOR EACH ROW EXECUTE FUNCTION eventing.foundation_guard_outbox_update();

    CREATE FUNCTION eventing.foundation_guard_receipt_update()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,eventing AS $fn$
    BEGIN
        IF OLD.id IS DISTINCT FROM NEW.id OR OLD.tenant_id IS DISTINCT FROM NEW.tenant_id OR
           OLD.consumer_name IS DISTINCT FROM NEW.consumer_name OR OLD.event_id IS DISTINCT FROM NEW.event_id OR
           OLD.payload_hash IS DISTINCT FROM NEW.payload_hash OR OLD.received_at IS DISTINCT FROM NEW.received_at OR
           OLD.trace_id IS DISTINCT FROM NEW.trace_id THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='consumer receipt identity, tenant and payload hash are immutable';
        END IF;
        IF NOT ((OLD.status = 'received' AND NEW.status = 'processing') OR
                (OLD.status = 'failed' AND NEW.status = 'processing') OR
                (OLD.status = 'processing' AND NEW.status IN ('processed','failed'))) THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='invalid consumer receipt state transition';
        END IF;
        IF NEW.status = 'processing' AND NEW.attempts <> OLD.attempts + 1 THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='receipt processing must increment attempts exactly once';
        END IF;
        IF NEW.status <> 'processing' AND NEW.attempts <> OLD.attempts THEN
            RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='receipt completion cannot change attempts';
        END IF;
        RETURN NEW;
    END $fn$;
    CREATE TRIGGER foundation_receipt_guard_update BEFORE UPDATE ON eventing.consumer_receipt
      FOR EACH ROW EXECUTE FUNCTION eventing.foundation_guard_receipt_update();

    CREATE FUNCTION audit.foundation_reject_audit_mutation()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,audit AS $fn$
    BEGIN
        RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='immutable audit log is append-only';
    END $fn$;
    CREATE TRIGGER foundation_audit_append_only
      BEFORE UPDATE OR DELETE ON audit.immutable_audit_log FOR EACH ROW
      EXECUTE FUNCTION audit.foundation_reject_audit_mutation();
    CREATE TRIGGER foundation_audit_no_truncate
      BEFORE TRUNCATE ON audit.immutable_audit_log FOR EACH STATEMENT
      EXECUTE FUNCTION audit.foundation_reject_audit_mutation();

    ALTER TABLE eventing.domain_event ENABLE ROW LEVEL SECURITY;
    ALTER TABLE eventing.domain_event FORCE ROW LEVEL SECURITY;
    ALTER TABLE eventing.transactional_outbox ENABLE ROW LEVEL SECURITY;
    ALTER TABLE eventing.transactional_outbox FORCE ROW LEVEL SECURITY;
    ALTER TABLE eventing.consumer_receipt ENABLE ROW LEVEL SECURITY;
    ALTER TABLE eventing.consumer_receipt FORCE ROW LEVEL SECURITY;
    ALTER TABLE audit.immutable_audit_log ENABLE ROW LEVEL SECURITY;
    ALTER TABLE audit.immutable_audit_log FORCE ROW LEVEL SECURITY;

    EXECUTE format('CREATE POLICY foundation_domain_event_select ON eventing.domain_event FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_domain_event_insert ON eventing.domain_event FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY foundation_domain_event_migrator ON eventing.domain_event FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);
    EXECUTE format('CREATE POLICY foundation_outbox_select ON eventing.transactional_outbox FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_outbox_insert ON eventing.transactional_outbox FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role);
    EXECUTE format('CREATE POLICY foundation_outbox_update ON eventing.transactional_outbox FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
    EXECUTE format('CREATE POLICY foundation_outbox_migrator ON eventing.transactional_outbox FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);
    EXECUTE format('CREATE POLICY foundation_receipt_select ON eventing.consumer_receipt FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_receipt_insert ON eventing.consumer_receipt FOR INSERT TO %I WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
    EXECUTE format('CREATE POLICY foundation_receipt_update ON eventing.consumer_receipt FOR UPDATE TO %I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',worker_role);
    EXECUTE format('CREATE POLICY foundation_receipt_migrator ON eventing.consumer_receipt FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);
    EXECUTE format('CREATE POLICY foundation_audit_select ON audit.immutable_audit_log FOR SELECT TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
    EXECUTE format('CREATE POLICY foundation_audit_migrator ON audit.immutable_audit_log FOR ALL TO %I USING (true) WITH CHECK (true)',current_user);

    EXECUTE format('GRANT USAGE ON SCHEMA eventing TO %I,%I',app_role,worker_role);
    EXECUTE format('GRANT SELECT,INSERT ON eventing.domain_event TO %I',app_role);
    EXECUTE format('GRANT SELECT ON eventing.domain_event TO %I',worker_role);
    EXECUTE format('GRANT SELECT,INSERT ON eventing.transactional_outbox TO %I',app_role);
    EXECUTE format('GRANT SELECT,UPDATE(status,publish_attempts,lease_owner,lease_expires_at,published_at,last_error_code,updated_at) ON eventing.transactional_outbox TO %I',worker_role);
    EXECUTE format('GRANT SELECT ON eventing.consumer_receipt TO %I',app_role);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE(status,attempts,processed_at,last_error_code) ON eventing.consumer_receipt TO %I',worker_role);
    EXECUTE format('GRANT USAGE ON SCHEMA audit TO %I,%I,%I',app_role,worker_role,audit_writer_role);
    EXECUTE format('GRANT SELECT ON audit.immutable_audit_log TO %I,%I',app_role,worker_role);
END
$migration$;

CREATE FUNCTION audit.foundation_canonical_part(value text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog AS $fn$
  SELECT CASE WHEN value IS NULL THEN '-1:' ELSE octet_length(value)::text || ':' || value END
$fn$;

CREATE FUNCTION audit.append_immutable_audit(
    p_tenant_id uuid, p_stream_type text, p_stream_id uuid,
    p_actor_type text, p_actor_id text, p_action text,
    p_entity_type text, p_entity_id uuid, p_trace_id uuid,
    p_occurred_at timestamptz, p_before_hash text, p_after_hash text,
    p_metadata_canonical text
) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,audit
AS $fn$
DECLARE
    v_id uuid := uuidv7();
    v_sequence bigint;
    v_previous text;
    v_payload_hash text;
    v_entry_hash text;
    v_timestamp text;
    v_canonical text;
BEGIN
    IF p_tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid THEN
        RAISE EXCEPTION USING ERRCODE='42501', MESSAGE='audit tenant context mismatch';
    END IF;
    IF p_stream_type IS NULL OR btrim(p_stream_type) = '' OR p_action IS NULL OR btrim(p_action) = '' OR
       p_actor_type IS NULL OR btrim(p_actor_type) = '' OR p_entity_type IS NULL OR btrim(p_entity_type) = '' OR
       p_trace_id IS NULL OR p_occurred_at IS NULL OR p_metadata_canonical IS NULL THEN
        RAISE EXCEPTION USING ERRCODE='22023', MESSAGE='audit append arguments are incomplete';
    END IF;
    IF octet_length(p_metadata_canonical) > 32768 OR p_metadata_canonical ~* '(password|secret|authorization|access[_-]?token|refresh[_-]?token|cookie)' THEN
        RAISE EXCEPTION USING ERRCODE='22023', MESSAGE='audit metadata is unsafe or too large';
    END IF;
    IF (p_before_hash IS NOT NULL AND p_before_hash !~ '^[0-9a-f]{64}$') OR
       (p_after_hash IS NOT NULL AND p_after_hash !~ '^[0-9a-f]{64}$') THEN
        RAISE EXCEPTION USING ERRCODE='22023', MESSAGE='audit state hashes must be lowercase SHA-256';
    END IF;

    PERFORM pg_advisory_xact_lock(hashtextextended(p_tenant_id::text || ':' || p_stream_type || ':' || p_stream_id::text, 0));
    SELECT sequence_number + 1, entry_hash INTO v_sequence, v_previous
      FROM audit.immutable_audit_log
     WHERE tenant_id=p_tenant_id AND stream_type=p_stream_type AND stream_id=p_stream_id
     ORDER BY sequence_number DESC LIMIT 1;
    IF v_sequence IS NULL THEN
        v_sequence := 1;
        v_previous := NULL;
    END IF;

    v_payload_hash := encode(sha256(convert_to(p_metadata_canonical,'UTF8')),'hex');
    v_timestamp := to_char(p_occurred_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"');
    v_canonical := concat(
      audit.foundation_canonical_part('iso-smart-audit-chain-v1'),
      audit.foundation_canonical_part(p_tenant_id::text),
      audit.foundation_canonical_part(p_stream_type),
      audit.foundation_canonical_part(p_stream_id::text),
      audit.foundation_canonical_part(v_sequence::text),
      audit.foundation_canonical_part(v_previous),
      audit.foundation_canonical_part(p_actor_type),
      audit.foundation_canonical_part(p_actor_id),
      audit.foundation_canonical_part(p_action),
      audit.foundation_canonical_part(p_entity_type),
      audit.foundation_canonical_part(p_entity_id::text),
      audit.foundation_canonical_part(p_trace_id::text),
      audit.foundation_canonical_part(v_timestamp),
      audit.foundation_canonical_part(p_before_hash),
      audit.foundation_canonical_part(p_after_hash),
      audit.foundation_canonical_part(v_payload_hash)
    );
    v_entry_hash := encode(sha256(convert_to(v_canonical,'UTF8')),'hex');

    INSERT INTO audit.immutable_audit_log(
      id,tenant_id,stream_type,stream_id,sequence_number,actor_type,actor_id,action,
      entity_type,entity_id,trace_id,occurred_at,before_hash,after_hash,payload_hash,
      previous_entry_hash,entry_hash,metadata_canonical
    ) VALUES (
      v_id,p_tenant_id,p_stream_type,p_stream_id,v_sequence,p_actor_type,p_actor_id,p_action,
      p_entity_type,p_entity_id,p_trace_id,p_occurred_at,p_before_hash,p_after_hash,v_payload_hash,
      v_previous,v_entry_hash,p_metadata_canonical
    );
    RETURN v_id;
END
$fn$;

REVOKE ALL ON FUNCTION audit.foundation_canonical_part(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) FROM PUBLIC;

DO $grants$
DECLARE
    app_role text := current_setting('foundation.app_role', true);
    worker_role text := current_setting('foundation.worker_role', true);
    audit_writer_role text := current_setting('foundation.audit_writer_role', true);
BEGIN
    EXECUTE format('GRANT EXECUTE ON FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text) TO %I,%I,%I',app_role,worker_role,audit_writer_role);
END
$grants$;
"""


REVERSE_SQL = r"""
DO $migration$
DECLARE
    eventing_created boolean;
    audit_created boolean;
BEGIN
    SELECT eventing_schema_was_created,audit_schema_was_created
      INTO eventing_created,audit_created FROM qms.foundation_0003_ownership WHERE singleton;

    DROP FUNCTION audit.append_immutable_audit(uuid,text,uuid,text,text,text,text,uuid,uuid,timestamptz,text,text,text);
    DROP FUNCTION audit.foundation_canonical_part(text);
    DROP TABLE audit.immutable_audit_log;
    DROP FUNCTION audit.foundation_reject_audit_mutation();
    DROP TABLE eventing.consumer_receipt;
    DROP FUNCTION eventing.foundation_guard_receipt_update();
    DROP TABLE eventing.transactional_outbox;
    DROP FUNCTION eventing.foundation_guard_outbox_update();
    DROP TABLE eventing.domain_event;
    DROP FUNCTION eventing.foundation_reject_domain_event_mutation();
    DROP TABLE qms.foundation_0003_ownership;

    IF audit_created THEN DROP SCHEMA audit; END IF;
    IF eventing_created THEN DROP SCHEMA eventing; END IF;
END
$migration$;
"""


def apply_phase3(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse_phase3(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0002_projection_organization_user_foundation")]
    operations = [
        migrations.CreateModel(
            name="DomainEvent",
            fields=[
                ("event_id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=160)),
                ("schema_version", models.PositiveIntegerField()),
                ("aggregate_type", models.CharField(max_length=120)),
                ("aggregate_id", models.UUIDField()),
                ("aggregate_version", models.PositiveBigIntegerField()),
                ("occurred_at", models.DateTimeField()),
                ("recorded_at", models.DateTimeField(auto_now_add=True)),
                ("trace_id", models.UUIDField()),
                ("correlation_id", models.UUIDField(blank=True, null=True)),
                ("causation_id", models.UUIDField(blank=True, null=True)),
                ("source", models.CharField(max_length=120)),
                ("payload", models.JSONField()),
                ("payload_hash", models.CharField(max_length=64)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
            ],
            options={"db_table": 'eventing"."domain_event', "managed": False},
        ),
        migrations.CreateModel(
            name="TransactionalOutbox",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("published", "Published"), ("failed", "Failed")], default="pending", max_length=24)),
                ("publish_attempts", models.PositiveIntegerField(default=0)),
                ("available_at", models.DateTimeField()),
                ("lease_owner", models.CharField(blank=True, max_length=160, null=True)),
                ("lease_expires_at", models.DateTimeField(blank=True, null=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("last_error_code", models.CharField(blank=True, max_length=64, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("domain_event", models.OneToOneField(db_column="domain_event_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.domainevent")),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
            ],
            options={"db_table": 'eventing"."transactional_outbox', "managed": False},
        ),
        migrations.CreateModel(
            name="ConsumerReceipt",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("consumer_name", models.CharField(max_length=160)),
                ("event_id", models.UUIDField()),
                ("payload_hash", models.CharField(max_length=64)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("received", "Received"), ("processing", "Processing"), ("processed", "Processed"), ("failed", "Failed")], max_length=24)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("last_error_code", models.CharField(blank=True, max_length=64, null=True)),
                ("trace_id", models.UUIDField()),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
            ],
            options={
                "db_table": 'eventing"."consumer_receipt',
                "managed": False,
                "constraints": [models.UniqueConstraint(fields=("consumer_name", "event_id"), name="foundation_consumer_receipt_consumer_event_unique")],
            },
        ),
        migrations.CreateModel(
            name="ImmutableAuditLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("stream_type", models.CharField(max_length=120)),
                ("stream_id", models.UUIDField()),
                ("sequence_number", models.PositiveBigIntegerField()),
                ("actor_type", models.CharField(max_length=80)),
                ("actor_id", models.CharField(blank=True, max_length=255, null=True)),
                ("action", models.CharField(max_length=160)),
                ("entity_type", models.CharField(max_length=120)),
                ("entity_id", models.UUIDField()),
                ("trace_id", models.UUIDField()),
                ("occurred_at", models.DateTimeField()),
                ("before_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("after_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("payload_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("previous_entry_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("entry_hash", models.CharField(max_length=64)),
                ("metadata_canonical", models.TextField(default="{}")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
            ],
            options={
                "db_table": 'audit"."immutable_audit_log',
                "managed": False,
                "constraints": [models.UniqueConstraint(fields=("tenant", "stream_type", "stream_id", "sequence_number"), name="foundation_audit_stream_sequence_unique")],
            },
        ),
        migrations.RunPython(apply_phase3, reverse_phase3),
    ]
