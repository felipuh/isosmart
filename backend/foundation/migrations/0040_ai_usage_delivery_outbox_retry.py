"""Permit the trusted worker to schedule bounded outbox retries."""

from django.db import migrations


FORWARD_SQL = r'''
DO $migration$
DECLARE worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'AI usage delivery requires the configured worker role';
  END IF;
  -- The worker already owns status/lease transitions.  This is limited to the
  -- next-attempt timestamp required for bounded backoff; RLS still scopes rows.
  EXECUTE format('GRANT UPDATE(available_at) ON eventing.transactional_outbox TO %I', worker_role);
END
$migration$;
'''

REVERSE_SQL = r'''
DO $migration$
DECLARE worker_role text := current_setting('foundation.worker_role', true);
BEGIN
  IF worker_role IS NULL OR worker_role='' THEN
    RAISE EXCEPTION 'AI usage delivery requires the configured worker role';
  END IF;
  EXECUTE format('REVOKE UPDATE(available_at) ON eventing.transactional_outbox FROM %I', worker_role);
END
$migration$;
'''


class Migration(migrations.Migration):
    dependencies = [("foundation", "0039_ai_usage_metering")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
