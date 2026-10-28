"""Actual model projection and PostgreSQL assertions, never a migration recorder."""
import json
import sys
from uuid import UUID

import django
import psycopg2
from psycopg2 import sql
from . import settings as lab

TENANTS = {'iso_runtime_a': str(UUID(int=101)), 'iso_runtime_b': str(UUID(int=102))}


def initialize():
    django.setup()
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from authentication.models import User, UserProfile, RefreshTokenBlacklist, PasswordResetToken
    from core.models import Organization, AuditLog
    return [ContentType, Permission, Group, User, Organization, UserProfile,
            RefreshTokenBlacklist, PasswordResetToken, AuditLog]


def evidence_update(**values):
    path = lab.ROOT / 'evidence.json'
    data = json.loads(path.read_text()) if path.exists() else {}
    data.update(values)
    path.write_text(json.dumps(data, indent=2, default=str))


def bootstrap():
    params = dict(lab.DATABASES['default'])
    conn = psycopg2.connect(dbname='postgres', user='iso_owner',
                           password=params['PASSWORD'], host=params['HOST'], port=params['PORT'])
    conn.autocommit = True
    try:
        with conn.cursor() as q:
            q.execute('CREATE DATABASE iso_lab TEMPLATE template0')
            q.execute('REVOKE ALL ON DATABASE iso_lab FROM PUBLIC')
            for role in TENANTS:
                q.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD %s').format(sql.Identifier(role)), [lab.config['passwords'][role]])
                q.execute(sql.SQL('GRANT CONNECT ON DATABASE iso_lab TO {}').format(sql.Identifier(role)))
    finally:
        conn.close()
    models = initialize()
    from django.db import connection
    from django.db.migrations.loader import MigrationLoader
    loader = MigrationLoader(None)
    target = ('authentication', '0011_application_auth_runtime_privileges')
    plan = loader.graph.forwards_plan(target)
    assert ('core', '0011_billing_models') in plan
    assert ('core', '0012_billingpayment_evidence_fields') in plan
    assert ('foundation', '0037_qms_audit_capa_foundation') in plan
    # Resolve the real migration state, including swappable model dependencies.
    state = loader.project_state([target])
    assert state.apps.get_model('authentication', 'UserProfile')
    expected = {m._meta.db_table for m in models}
    expected |= {f.remote_field.through._meta.db_table for m in models
                 for f in m._meta.local_many_to_many}
    with connection.cursor() as q:
        assert not connection.introspection.table_names(q)
        q.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
        q.execute('GRANT USAGE ON SCHEMA public TO iso_runtime_a, iso_runtime_b')
    # Real models, complete fields/M2M/indexes/FKs; no migration executor/recorder.
    with connection.schema_editor() as editor:
        for model in models:
            editor.create_model(model)
    with connection.cursor() as q:
        assert set(connection.introspection.table_names(q)) == expected
        # Fixed database principals define tenant authority. GUCs cannot change it.
        tenant_case = "(CASE session_user WHEN 'iso_runtime_a' THEN '%s' WHEN 'iso_runtime_b' THEN '%s' END)" % tuple(TENANTS.values())
        predicates = {
            'organizations': 'external_id = ' + tenant_case,
            'user_profiles': 'organization_id IN (SELECT id FROM organizations)',
            'audit_logs': 'organization_id IN (SELECT id FROM organizations) AND (user_id IS NULL OR user_id IN (SELECT user_id FROM user_profiles WHERE organization_id = audit_logs.organization_id))',
            'refresh_token_blacklist': 'user_id IN (SELECT user_id FROM user_profiles)',
            'password_reset_tokens': 'user_id IN (SELECT user_id FROM user_profiles)',
        }
        for table, predicate in predicates.items():
            q.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            q.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            q.execute(f'CREATE POLICY lab_tenant ON "{table}" TO iso_runtime_a, iso_runtime_b USING ({predicate}) WITH CHECK ({predicate})')
        # Identity and Django authorization catalog are global. Catalog/M2M writes
        # are not required by sync_identity and receive no runtime privileges.
        grants = {
            'auth_user': 'SELECT, INSERT', 'organizations': 'SELECT, INSERT',
            'user_profiles': 'SELECT, INSERT, UPDATE',
            'refresh_token_blacklist': 'SELECT, INSERT',
            'password_reset_tokens': 'SELECT, INSERT, UPDATE',
            'audit_logs': 'SELECT, INSERT',
        }
        for table, privileges in grants.items():
            q.execute(f'GRANT {privileges} ON "{table}" TO iso_runtime_a, iso_runtime_b')
            q.execute('SELECT pg_get_serial_sequence(%s, %s)', [table, 'id'])
            sequence = q.fetchone()[0]
            q.execute(f'GRANT USAGE ON SEQUENCE {sequence} TO iso_runtime_a, iso_runtime_b')
        q.execute('GRANT UPDATE (password, failed_login_attempts, account_locked_until, must_change_password, temporary_password_set_at, password_history, last_login) ON auth_user TO iso_runtime_a, iso_runtime_b')
        # Database defense against privileged local identities in this lab only.
        q.execute('ALTER TABLE auth_user ADD CONSTRAINT lab_no_privileged_users CHECK (NOT is_superuser AND NOT is_staff)')
    evidence_update(
        graph={'target': target, 'plan': plan,
               'edges': {'.'.join(n): sorted(p.key for p in loader.graph.node_map[n].parents) for n in plan},
               'resolved_state_models': len(state.models),
               'financial_free_authentication_targets': [n for n in loader.graph.nodes
                   if n[0] == 'authentication' and ('core', '0011_billing_models') not in loader.graph.forwards_plan(n)]},
        models=[m._meta.label for m in models], expected_tables=sorted(expected),
        projection='schema_editor on actual models; no migrations executed or recorded',
        global_tables=['auth_user', 'auth_user_groups', 'auth_user_user_permissions',
                       'auth_group', 'auth_group_permissions', 'auth_permission', 'django_content_type'])


def runtime():
    initialize()
    from django.db import connection, transaction, DatabaseError, IntegrityError
    from django.test.utils import CaptureQueriesContext
    from authentication.models import User, UserProfile, RefreshTokenBlacklist, PasswordResetToken
    from core.models import Organization, AuditLog
    from integration.central_auth import sync_identity, require_user_binding
    role = lab.role
    tenant = TENANTS[role]
    index = list(TENANTS).index(role) + 1
    checks = []

    def denied(statement, params=None, code='42501'):
        try:
            with transaction.atomic():
                with connection.cursor() as q:
                    q.execute(statement, params)
        except DatabaseError as exc:
            assert exc.__cause__.pgcode == code, (statement, exc.__cause__.pgcode)
            checks.append({'denied': statement, 'sqlstate': code})
        else:
            raise AssertionError('Operation unexpectedly allowed: ' + statement)

    with connection.cursor() as q:
        q.execute('SELECT current_user, session_user, current_database(), inet_server_addr()')
        assert q.fetchone() == (role, role, 'iso_lab', None)
        q.execute('SELECT rolsuper, rolcreatedb, rolcreaterole, rolinherit, rolreplication, rolbypassrls FROM pg_roles WHERE rolname=current_user')
        assert q.fetchone() == (False,) * 6
        q.execute('SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user)')
        assert q.fetchone()[0] == 0
        q.execute("SELECT has_database_privilege(current_user, 'iso_lab', 'CREATE'), has_database_privilege(current_user, 'iso_lab', 'TEMP'), has_schema_privilege(current_user, 'public', 'CREATE')")
        assert q.fetchone() == (False, False, False)
    data = {'sub': str(UUID(int=index)), 'organization_id': tenant,
            'email': f'person{index}@example.invalid', 'role': 'admin',
            'organization_name': f'Synthetic tenant {index}', 'full_name': 'Synthetic Person'}
    with CaptureQueriesContext(connection) as captured:
        user, profile = sync_identity(data)
        again, same = sync_identity(data)
        assert (again.pk, same.pk) == (user.pk, profile.pk)
        assert not user.has_usable_password()
        require_user_binding(user, data['sub'])
        user.record_failed_login()
        user.reset_login_attempts()
        joined = UserProfile.objects.select_related('organization', 'user').get(pk=profile.pk)
        assert joined.organization.external_id == tenant
        assert Organization.objects.count() == UserProfile.objects.count() == 1
        assert user.profiles.get().pk == profile.pk
        token = RefreshTokenBlacklist.objects.create(token='synthetic-invalid-token-' + str(index), user=user)
        assert RefreshTokenBlacklist.objects.get(token_hash=token.token_hash).user_id == user.pk
        reset, raw = PasswordResetToken.issue_for_user(user)
        assert reset.matches(raw) and reset.is_available()
        replacement, raw2 = PasswordResetToken.issue_for_user(user)
        reset.refresh_from_db()
        assert not reset.is_available()
        replacement.mark_used()
        replacement.refresh_from_db()
        assert not replacement.is_available()
        AuditLog.objects.create(organization=profile.organization, user=user,
                                action='login', module='authentication', description='Synthetic schema validation')
        assert AuditLog.objects.get().user_id == user.pk
    # Reconnect: persistence, and direct role authentication are not transaction illusions.
    connection.close()
    assert UserProfile.objects.select_related('organization').get(pk=profile.pk).organization.external_id == tenant
    denied('CREATE TABLE public.forbidden (id integer)')
    denied('CREATE TEMP TABLE forbidden (id integer)')
    denied('CREATE ROLE forbidden')
    denied('SET ROLE iso_owner')
    denied('ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY')
    denied('DELETE FROM user_profiles')
    denied('TRUNCATE organizations')
    denied('UPDATE auth_user SET is_superuser=true WHERE id=%s', [user.pk])
    denied('SELECT * FROM auth_user_groups')
    denied("SELECT setval('auth_user_id_seq', 999)")
    denied('UPDATE organizations SET name=%s', ['forbidden'])
    denied('UPDATE user_profiles SET organization_id=%s WHERE id=%s', [9999, profile.pk])
    denied('UPDATE user_profiles SET user_id=99999 WHERE id=%s', [profile.pk], code='23503')
    denied('UPDATE user_profiles SET user_id=NULL WHERE id=%s', [profile.pk], code='23502')
    denied('INSERT INTO user_profiles SELECT * FROM user_profiles WHERE id=%s', [profile.pk], code='23505')
    other = TENANTS['iso_runtime_b' if role == 'iso_runtime_a' else 'iso_runtime_a']
    with connection.cursor() as q:
        q.execute("SELECT set_config('app.tenant_id', %s, false)", [other])
        q.execute('SELECT count(*) FROM organizations WHERE external_id=%s', [other])
        assert q.fetchone()[0] == 0
        q.execute('UPDATE user_profiles SET role=%s WHERE organization_id <> %s RETURNING id', ['viewer', profile.organization_id])
        assert q.fetchall() == []
    # A second principal runs after A exists: deny reads, updates and token writes for A.
    if index == 2:
        assert not UserProfile.objects.filter(user__email='person1@example.invalid').exists()
        assert not RefreshTokenBlacklist.objects.filter(user__email='person1@example.invalid').exists()
        assert not PasswordResetToken.objects.filter(email='person1@example.invalid').exists()
        foreign_user = User.objects.get(email='person1@example.invalid')  # global identity directory
        with connection.cursor() as q:
            q.execute('UPDATE password_reset_tokens SET used_at=now() WHERE user_id=%s RETURNING id', [foreign_user.pk])
            assert q.fetchall() == []
        denied('UPDATE user_profiles SET organization_id=1 WHERE id=%s', [profile.pk])
        denied('INSERT INTO refresh_token_blacklist (token,token_hash,user_id,blacklisted_at) VALUES (%s,%s,%s,now())', ['invalid', 'f' * 64, foreign_user.pk])
    # Composite membership uniqueness, independent of primary-key uniqueness.
    try:
        with transaction.atomic():
            UserProfile.objects.create(user=user, organization=profile.organization)
    except IntegrityError as exc:
        assert exc.__cause__.pgcode == '23505'
    else:
        raise AssertionError('Duplicate membership accepted')
    evidence_update(**{role: {'principal': role, 'orm_checks': 'PASS',
        'query_count': len(captured), 'prohibited_operations': checks,
        'tenant_isolation': 'fixed session_user policy; cross-tenant GUC spoof ineffective',
        'reconnect_persistence': True}})


def isolation():
    initialize()
    from django.db import connection, transaction, DatabaseError
    from core.models import Organization, AuditLog
    from authentication.models import UserProfile, PasswordResetToken, RefreshTokenBlacklist
    own = TENANTS[lab.role]
    other = next(value for value in TENANTS.values() if value != own)
    assert list(Organization.objects.values_list('external_id', flat=True)) == [own]
    assert UserProfile.objects.count() == AuditLog.objects.count() == 1
    assert PasswordResetToken.objects.count() == 2
    assert RefreshTokenBlacklist.objects.count() == 1
    for table in ('user_profiles', 'audit_logs'):
        with connection.cursor() as q:
            q.execute(f'SELECT count(*) FROM {table} WHERE organization_id NOT IN (SELECT id FROM organizations)')
            assert q.fetchone()[0] == 0
    try:
        with transaction.atomic():
            Organization.objects.create(external_id=other, slug='forbidden-cross-tenant', name='Forbidden')
    except DatabaseError as exc:
        assert exc.__cause__.pgcode == '42501'
    else:
        raise AssertionError('Cross-tenant organization insert accepted')
    evidence_update(**{lab.role + '_isolation_after_both_seeds': 'PASS'})


def inspect():
    models = initialize()
    from django.db import connection
    inventory = {}
    with connection.cursor() as q:
        tables = connection.introspection.table_names(q)
        data = json.loads((lab.ROOT / 'evidence.json').read_text())
        assert sorted(tables) == data['expected_tables']
        assert 'django_migrations' not in tables
        assert not any('billing' in name for name in tables)
        q.execute("SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname NOT IN ('information_schema', 'public')")
        assert q.fetchall() == []
        for table in tables:
            q.execute("SELECT column_name, data_type, is_nullable, column_default, is_identity FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", [table])
            columns = q.fetchall()
            q.execute('SELECT indexname,indexdef FROM pg_indexes WHERE schemaname=%s AND tablename=%s ORDER BY indexname', ['public', table])
            indexes = q.fetchall()
            constraints = connection.introspection.get_constraints(q, table)
            q.execute('SELECT conname,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid=%s::regclass ORDER BY conname', [table])
            definitions = q.fetchall()
            q.execute('SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid=%s::regclass', [table])
            rls = q.fetchone()
            inventory[table] = dict(columns=columns, indexes=indexes, constraints=constraints, definitions=definitions, rls=rls)
        q.execute("SELECT grantee, table_name, privilege_type FROM information_schema.role_table_grants WHERE grantee LIKE 'iso_runtime_%' ORDER BY 1,2,3")
        grants = q.fetchall()
        q.execute("SELECT grantee, table_name, column_name, privilege_type FROM information_schema.column_privileges WHERE grantee LIKE 'iso_runtime_%' ORDER BY 1,2,3,4")
        column_grants = q.fetchall()
        q.execute("SELECT tablename, policyname, roles, qual, with_check FROM pg_policies ORDER BY tablename")
        policies = q.fetchall()
        q.execute("SELECT c.relname, c.relacl FROM pg_class c WHERE c.relkind='S' ORDER BY c.relname")
        sequences = q.fetchall()
        for model in models:
            actual = {row[0] for row in inventory[model._meta.db_table]['columns']}
            assert actual == {field.column for field in model._meta.local_fields}
        q.execute('SELECT count(*) FROM organizations')
        assert q.fetchone()[0] == 2
        q.execute('SELECT count(*) FROM user_profiles')
        assert q.fetchone()[0] == 2
    evidence_update(verdict='LAB05_C1_R2_NONFINANCIAL_SCHEMA_PASS', inventory=inventory,
                    grants=grants, column_grants=column_grants, sequences=sequences, policies=policies,
                    financial_tables=[], executed_migrations=[], recorded_migrations=[],
                    HTTP_E2E=False, PRODUCTION_READY=False, PHASE31_5='EXECUTION_HELD',
                    S3_DECISION_02A='NOT_CLOSED', NO_DEPLOYMENT=True, NO_SHARED_DB_MUTATION=True)


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions must remain enabled for laboratory acceptance')
    {'bootstrap': bootstrap, 'runtime': runtime, 'inspect': inspect, 'isolation': isolation}[sys.argv[1]]()
