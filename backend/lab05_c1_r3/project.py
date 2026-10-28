"""Maintenance-only extension of the R2 real-model projection; no migrations."""
import json
import django
from lab05_c1_r2 import settings as lab

django.setup()
from django.db import connection
from resources.models import Resource

bindings = json.loads((lab.ROOT / 'bindings.json').read_text())
with connection.cursor() as cursor:
    cursor.execute('SELECT current_user')
    assert cursor.fetchone()[0] == 'iso_owner'
with connection.schema_editor() as editor:
    editor.create_model(Resource)
with connection.cursor() as cursor:
    cursor.execute('CREATE TABLE lab_tenant_authority (principal name PRIMARY KEY, tenant_id text NOT NULL UNIQUE)')
    for principal, tenant in bindings.items():
        cursor.execute('INSERT INTO lab_tenant_authority VALUES (%s, %s)', [principal, tenant])
    cursor.execute('REVOKE ALL ON lab_tenant_authority FROM PUBLIC')
    cursor.execute('GRANT SELECT ON lab_tenant_authority TO iso_runtime_a, iso_runtime_b')
    predicate = 'external_id = (SELECT tenant_id FROM lab_tenant_authority WHERE principal = session_user)'
    cursor.execute('DROP POLICY lab_tenant ON organizations')
    cursor.execute('CREATE POLICY lab_tenant ON organizations TO iso_runtime_a, iso_runtime_b '
                   f'USING ({predicate}) WITH CHECK ({predicate})')
    cursor.execute('ALTER TABLE resources_resource ENABLE ROW LEVEL SECURITY')
    cursor.execute('ALTER TABLE resources_resource FORCE ROW LEVEL SECURITY')
    predicate = 'organization_id IN (SELECT id FROM organizations)'
    cursor.execute('CREATE POLICY lab_tenant ON resources_resource TO iso_runtime_a, iso_runtime_b '
                   f'USING ({predicate}) WITH CHECK ({predicate})')
    cursor.execute('GRANT SELECT, INSERT, UPDATE ON resources_resource TO iso_runtime_a, iso_runtime_b')
    cursor.execute('GRANT USAGE ON SEQUENCE resources_resource_id_seq TO iso_runtime_a, iso_runtime_b')
    # R2 grants support password recovery too. R3 exposes login/protected resources:
    # retain only the writes those real paths need.
    cursor.execute('REVOKE UPDATE ON auth_user FROM iso_runtime_a, iso_runtime_b')
    cursor.execute('REVOKE UPDATE (password, failed_login_attempts, account_locked_until, '
                   'must_change_password, temporary_password_set_at, password_history, last_login) '
                   'ON auth_user FROM iso_runtime_a, iso_runtime_b')
    cursor.execute('GRANT UPDATE (password, last_login) ON auth_user TO iso_runtime_a, iso_runtime_b')
    cursor.execute('REVOKE ALL ON password_reset_tokens, refresh_token_blacklist, audit_logs '
                   'FROM iso_runtime_a, iso_runtime_b')
    cursor.execute('REVOKE ALL ON SEQUENCE password_reset_tokens_id_seq, '
                   'refresh_token_blacklist_id_seq, audit_logs_id_seq FROM iso_runtime_a, iso_runtime_b')
    cursor.execute('REVOKE UPDATE ON user_profiles FROM iso_runtime_a, iso_runtime_b')
    # Django update_or_create includes FileField.pre_save (avatar) as well as
    # auto timestamps, even when the file itself did not change.
    cursor.execute('GRANT UPDATE (role, is_active, created_at, updated_at, avatar) ON user_profiles '
                   'TO iso_runtime_a, iso_runtime_b')
    cursor.execute('SELECT tablename FROM pg_tables WHERE schemaname = %s', ['public'])
    tables = sorted(row[0] for row in cursor.fetchall())
    assert not any('billing' in name or 'trial' in name for name in tables)
    assert 'django_migrations' not in tables
    cursor.execute("SELECT grantee, table_name, privilege_type FROM information_schema.role_table_grants "
                   "WHERE grantee IN ('iso_runtime_a', 'iso_runtime_b') ORDER BY 1,2,3")
    grants = cursor.fetchall()
    cursor.execute("SELECT grantee, table_name, column_name, privilege_type FROM information_schema.role_column_grants "
                   "WHERE grantee IN ('iso_runtime_a', 'iso_runtime_b') AND privilege_type='UPDATE' "
                   "AND table_name IN ('auth_user', 'user_profiles') ORDER BY 1,2,3")
    column_grants = cursor.fetchall()
(lab.ROOT / 'projection.json').write_text(json.dumps({'tables': tables,
    'added_real_models': ['resources.Resource'], 'migration_execution': False,
    'runtime_table_grants': grants, 'identity_column_update_grants': column_grants,
    'tenant_authority': bindings}, indent=2))
