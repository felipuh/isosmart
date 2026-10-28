"""Allow an audited AI-usage retry-exhausted row to begin a new bounded cycle."""

from django.db import migrations


FORWARD_SQL = r'''
CREATE OR REPLACE FUNCTION eventing.foundation_guard_outbox_update()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,eventing AS $fn$
BEGIN
    IF OLD.id IS DISTINCT FROM NEW.id OR OLD.tenant_id IS DISTINCT FROM NEW.tenant_id OR
       OLD.domain_event_id IS DISTINCT FROM NEW.domain_event_id OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
        RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='outbox identity and tenant are immutable';
    END IF;
    IF OLD.status = 'published' OR NOT (
      (OLD.status IN ('pending','failed') AND NEW.status = 'processing') OR
      (OLD.status = 'processing' AND NEW.status = 'processing' AND OLD.lease_expires_at <= statement_timestamp()) OR
      (OLD.status = 'processing' AND NEW.status IN ('published','failed')) OR
      (OLD.status = 'failed' AND OLD.last_error_code = 'AI_USAGE_RETRY_EXHAUSTED'
       AND NEW.status = 'pending' AND NEW.last_error_code IS NULL)
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
'''


REVERSE_SQL = r'''
CREATE OR REPLACE FUNCTION eventing.foundation_guard_outbox_update()
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
'''


class Migration(migrations.Migration):
    dependencies = [("foundation", "0040_ai_usage_delivery_outbox_retry")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
