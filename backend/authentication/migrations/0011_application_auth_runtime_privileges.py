"""Grant the application role only the legacy tables needed by authentication."""

from django.db import migrations


FORWARD_SQL = r"""
DO $migration$
DECLARE
    app_role text := NULLIF(current_setting('foundation.app_role', true), '');
    table_name text;
    sequence_name text;
BEGIN
    IF app_role IS NULL THEN
        RAISE EXCEPTION 'authentication runtime role is required';
    END IF;

    FOREACH table_name IN ARRAY ARRAY[
        'auth_user', 'user_profiles', 'organizations',
        'refresh_token_blacklist', 'password_reset_tokens'
    ] LOOP
        IF to_regclass(format('public.%I', table_name)) IS NULL THEN
            RAISE EXCEPTION 'authentication table public.% is missing', table_name;
        END IF;
        EXECUTE format(
            'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.%I TO %I',
            table_name, app_role
        );
        sequence_name := pg_get_serial_sequence(format('public.%I', table_name), 'id');
        IF sequence_name IS NULL THEN
            RAISE EXCEPTION 'authentication sequence for public.% is missing', table_name;
        END IF;
        EXECUTE format(
            'GRANT USAGE, SELECT ON SEQUENCE %s TO %I',
            sequence_name, app_role
        );
    END LOOP;
END
$migration$;
"""


REVERSE_SQL = r"""
DO $migration$
DECLARE
    app_role text := NULLIF(current_setting('foundation.app_role', true), '');
    table_name text;
    sequence_name text;
BEGIN
    IF app_role IS NULL THEN
        RAISE EXCEPTION 'authentication runtime role is required';
    END IF;

    FOREACH table_name IN ARRAY ARRAY[
        'auth_user', 'user_profiles', 'organizations',
        'refresh_token_blacklist', 'password_reset_tokens'
    ] LOOP
        IF to_regclass(format('public.%I', table_name)) IS NULL THEN
            CONTINUE;
        END IF;
        EXECUTE format(
            'REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE public.%I FROM %I',
            table_name, app_role
        );
        sequence_name := pg_get_serial_sequence(format('public.%I', table_name), 'id');
        IF sequence_name IS NOT NULL THEN
            EXECUTE format(
                'REVOKE USAGE, SELECT ON SEQUENCE %s FROM %I',
                sequence_name, app_role
            );
        END IF;
    END LOOP;
END
$migration$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0010_alter_refreshtokenblacklist_token_hash"),
        ("core", "0019_featureflag"),
        ("foundation", "0037_qms_audit_capa_foundation"),
    ]

    operations = [
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
    ]
