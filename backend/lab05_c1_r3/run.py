"""R3 integrated orchestrator, invoked by AdminApps lab04/run.py --http-isosmart.

Only private fresh PostgreSQL clusters and declared loopback HTTP servers.
No R1/R2 acceptance is run. Reuse their provisioning and real schema projection.
"""
import argparse
import hashlib
import http.client
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

import jwt
import psycopg2
from psycopg2 import sql
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main():
    if not __debug__:
        raise RuntimeError('Run acceptance with assertions enabled')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admin-backend', type=Path, required=True)
    args = parser.parse_args()
    admin = args.admin_backend.resolve()
    central_root = Path(os.environ['LAB04_ROOT']).resolve()
    assert central_root.parent == Path('/tmp') and central_root.name.startswith('adminapps-lab04-')
    backend = Path(__file__).resolve().parents[1]
    root = Path(tempfile.mkdtemp(prefix='iso-c1-r2-'))
    processes, streams, cases = [], [], []
    started, passed = False, False
    env = {k: v for k, v in os.environ.items() if not k.startswith(
        ('PG', 'DJANGO_', 'ISO_', 'LAB04_', 'LAB05_', 'ADMIN_APPS', 'PYTHON'))
        and k.lower() not in ('http_proxy', 'https_proxy', 'all_proxy')}
    env.update(ISO_LAB_ROOT=str(root), PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(backend),
               DJANGO_SETTINGS_MODULE='lab05_c1_r2.settings', NO_PROXY='127.0.0.1')
    admin_env = {**env, 'LAB04_ROOT': str(central_root),
        'PYTHONPATH': str(admin / 'lab04') + os.pathsep + str(admin),
        'LAB04_PROFILE': 'sso', 'LAB04_ROLE': 'lab04_sso', 'LAB05_HTTP': '1', 'LAB05_R3': '1'}
    admin_env.pop('ISO_LAB_ROOT')
    admin_env.pop('DJANGO_SETTINGS_MODULE')
    client = json.loads((central_root / 'runtime/sso-client.json').read_text())
    # The orchestrator reads only the public export. Central private RSA stays in AdminApps.
    public = json.loads((central_root / 'runtime/r3-public-trust.json').read_text())
    bindings = {'iso_runtime_a': client['tenant'], 'iso_runtime_b': client['foreign']}
    config = {'secret': secrets.token_urlsafe(48), 'passwords': {
        name: secrets.token_urlsafe(32) for name in ('iso_owner', *bindings)}}

    def write_private(path, value):
        path.write_text(json.dumps(value))
        path.chmod(0o600)

    def run(argv, label, extra=None):
        result = subprocess.run(argv, env={**env, **(extra or {})}, cwd=backend,
                                capture_output=True, text=True, timeout=120)
        (root / (label + '.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(label + ' failed; private diagnostic logs retained by AdminApps')

    def start(command, child_env, ready, label):
        ready.unlink(missing_ok=True)
        stream = (root / (label + '.log')).open('w')
        streams.append(stream)
        process = subprocess.Popen(command, env=child_env, cwd=backend, stdout=stream, stderr=stream)
        processes.append(process)
        deadline = time.monotonic() + 30
        while not ready.exists():
            if process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError(label + ' failed readiness; inspect private diagnostic logs')
            time.sleep(.05)
        return process, json.loads(ready.read_text())['port']

    def control(action):
        child_env = {k: v for k, v in admin_env.items() if k not in ('LAB04_ROLE', 'LAB04_PROFILE')}
        child_env['LAB04_MIGRATE'] = '1'
        result = subprocess.run([sys.executable, str(admin / 'lab05/r3_control.py'), action],
            env=child_env, cwd=admin, capture_output=True, text=True, timeout=30)
        (root / (action + '.log')).write_text(result.stdout + result.stderr)
        assert result.returncode == 0, action + ': maintenance control failed'

    def db(role='iso_owner'):
        conn = psycopg2.connect(dbname='iso_lab', user=role, password=config['passwords'][role],
            host=str(root / 'socket'), port=56439)
        conn.autocommit = True
        return conn

    def snapshot():
        conn = db()
        result = {}
        try:
            with conn.cursor() as cursor:
                for table in projection['tables']:
                    cursor.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} t ORDER BY row_to_json(t)::text').format(sql.Identifier(table)))
                    result[table] = hashlib.sha256(json.dumps(cursor.fetchall()).encode()).hexdigest()
        finally:
            conn.close()
        return result

    def call(name, port, path, expected, payload=None, jar=None, supplied=None, role=None, denied=False):
        before = snapshot() if denied and role else None
        headers = {'Content-Type': 'application/json', **(supplied or {})}
        if jar:
            headers['Cookie'] = '; '.join(k + '=' + v for k, v in jar.items())
            if 'csrftoken' in jar:
                headers['X-CSRFToken'] = jar['csrftoken']
        method = 'GET' if payload is None else 'POST'
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        try:
            conn.request(method, path, None if payload is None else json.dumps(payload), headers)
            response = conn.getresponse()
            body = response.read()
            status = response.status
            assert status == expected, (name, status, expected)
            cookies = {}
            for key, value in response.getheaders():
                if key.lower() == 'set-cookie':
                    parsed = SimpleCookie()
                    parsed.load(value)
                    cookies.update({k: v.value for k, v in parsed.items()})
            data = json.loads(body) if body else None
        finally:
            conn.close()
        case = {'scenario': name, 'path': path, 'method': method, 'status': status}
        if role:
            state = json.loads((root / ('state-' + role + '.json')).read_text())
            assert state['principal'] == state['session_user'] == role
            case.update(state)
            if denied:
                assert not any(state['delta'].values()), (name, state['delta'])
                assert snapshot() == before, name + ': unauthorized database change'
                assert not any(cookies.get(k) for k in ('isosmart_access', 'isosmart_refresh'))
                case.update(protected_handler_not_executed=True, database_unchanged=True)
        cases.append(case)
        return data, cookies

    central_context = {k: client[k] for k in ('client_id', 'audience', 'product', 'contract_version')}

    def central(name, endpoint, expected, payload, headers=None):
        return call(name, central_port, '/api/integration/sso/' + endpoint, expected,
            {**central_context, **payload}, supplied=({'X-API-Key': client['credential']} if headers is None else headers))[0]

    def iso(name, role, path, expected, payload=None, jar=None, headers=None, denied=False):
        return call(name, ports[role], path, expected, payload, jar, headers, role, denied)

    def login(role, name='login', organization=None, password=None, headers=None, expected=200):
        _, csrf = iso(name + '_csrf', role, '/api/auth/csrf/', 200)
        body, cookies = iso(name, role, '/api/auth/login/', expected,
            {'email': 'viewer@example.invalid', 'password': password or client['password'],
             'organization_id': organization or bindings[role]}, csrf, headers, denied=expected != 200)
        return body, {**csrf, **cookies}

    try:
        write_private(root / 'runtime.json', config)
        write_private(root / 'bindings.json', bindings)
        (root / 'socket').mkdir(mode=0o700)
        (root / 'owner-password').write_text(config['passwords']['iso_owner'])
        (root / 'owner-password').chmod(0o600)
        run(['initdb', '-D', str(root / 'data'), '-U', 'iso_owner', '--auth-local=scram-sha-256',
             '--auth-host=reject', '--pwfile', str(root / 'owner-password'), '--no-locale', '--encoding=UTF8'], 'initdb')
        with (root / 'data/postgresql.conf').open('a') as stream:
            stream.write("\nlisten_addresses=''\nport=56439\nunix_socket_directories='" + str(root / 'socket') + "'\n")
        run(['pg_ctl', '-D', str(root / 'data'), '-l', str(root / 'postgres.log'), '-w', 'start'], 'pg-start')
        started = True
        run([sys.executable, '-m', 'lab05_c1_r2.validate', 'bootstrap'], 'r2-projection-only')
        run([sys.executable, '-m', 'lab05_c1_r3.project'], 'r3-projection')
        projection = json.loads((root / 'projection.json').read_text())
        central_process, central_port = start([sys.executable, str(admin / 'lab05/http_server.py')],
            admin_env, central_root / 'http-sso-ready.json', 'central-http')
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        local_trust = {'ALGORITHM': 'RS256', 'ISSUER': 'https://iso.lab.example.invalid',
            'AUDIENCE': 'urn:lab05:iso-local', 'SIGNING_KID': 'r3-local',
            'PUBLIC_KEYS': {'r3-local': key.public_key().public_bytes(serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo).decode()},
            'PRIVATE_KEY': key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()).decode()}
        http_config = {'secret': config['secret'], 'central_port': central_port,
            'central_trust': public, 'local_trust': local_trust,
            'credential': client['credential'], 'sso': {
                'BASE_URL': f'http://127.0.0.1:{central_port}/api/integration', 'ISSUER': public['ISSUER'],
                'CLIENT_ID': client['client_id'], 'AUDIENCE': client['audience'][0]}}
        write_private(root / 'http-config.json', http_config)
        ports = {}
        for role, tenant in bindings.items():
            write_private(root / ('instance-' + role + '.json'),
                          {'tenant': tenant, 'sql_password': config['passwords'][role]})
            _, ports[role] = start([sys.executable, '-m', 'lab05_c1_r3.server'],
                {**env, 'DJANGO_SETTINGS_MODULE': 'lab05_c1_r3.settings', 'ISO_LAB_ROLE': role},
                root / ('ready-' + role + '.json'), role)
        assert len(set([central_port, *ports.values()])) == 3
        a, b = bindings
        iso('anonymous_denied', a, '/api/auth/me/', 401, denied=True)
        iso('login_without_csrf', a, '/api/auth/login/', 403,
            {'email': 'viewer@example.invalid', 'password': client['password']}, denied=True)
        body_a, jar_a = login(a, 'legitimate_login_a')
        assert body_a['user']['email'] == 'viewer@example.invalid' and body_a['profile']['role'] == 'user'
        assert len(body_a['organizations']) == 1
        org_a = body_a['profile']['organization']
        token_a = jar_a['isosmart_access']
        local_claims = jwt.decode(token_a, local_trust['PUBLIC_KEYS']['r3-local'], algorithms=['RS256'],
            audience=local_trust['AUDIENCE'], issuer=local_trust['ISSUER'])
        proof = local_claims['central_proof']
        claims = jwt.decode(proof, public['PUBLIC_KEYS'][public['SIGNING_KID']], algorithms=['RS256'],
            audience=client['audience'][0], issuer=public['ISSUER'])
        assert claims['token_family'] == 'CENTRAL' and claims['product'] == 'ISO_SMART'
        assert claims['tenant_id'] == bindings[a] and claims['client_id'] == client['client_id']
        assert local_claims['exp'] <= claims['exp']
        introspected = central('real_central_introspection', 'introspect/', 200, {'token': proof})
        assert introspected['active'] is True
        assert 'ISO_SMART:resources.resource:create' in introspected['authorization']['scopes']
        me, _ = iso('me_a', a, '/api/auth/me/', 200, jar=jar_a)
        assert me['profile']['organization'] == org_a and me['profile']['role'] == 'user'
        resource = {'name': 'Synthetic R3 resource', 'code': 'R3-A',
                    'resource_type': 'technology', 'organization_name': 'Synthetic A'}
        created, _ = iso('authorized_resource_create_a', a, '/api/resources/', 201, resource, jar_a)
        resource_id = created['id']
        assert created['organization_id'] == org_a
        body_b, jar_b = login(b, 'shared_subject_login_b')
        assert body_b['user']['id'] == body_a['user']['id'] and body_b['profile']['role'] == 'viewer'
        org_b = body_b['profile']['organization']
        assert org_a != org_b and len(body_b['organizations']) == 1
        me_b, _ = iso('shared_subject_me_b_no_elevation', b, '/api/auth/me/', 200, jar=jar_b)
        assert me_b['profile']['role'] == 'viewer'
        values, _ = iso('rls_http_b_cannot_list_a', b, '/api/resources/', 200, jar=jar_b)
        assert values == []
        # Retrieve enters the real handler but returns no foreign object.
        before = snapshot()
        iso('cross_tenant_object_not_found', b, f'/api/resources/{resource_id}/', 404, jar=jar_b)
        assert snapshot() == before
        iso('insufficient_scopes_shared_viewer', b, '/api/resources/', 403,
            {**resource, 'code': 'FORBIDDEN-B'}, jar_b, denied=True)
        iso('cross_tenant_query', a, f'/api/resources/?organization_id={org_b}', 403, jar=jar_a, denied=True)
        iso('cross_tenant_write', a, '/api/resources/', 403,
            {**resource, 'code': 'FORBIDDEN-CROSS', 'organization_id': org_b}, jar_a, denied=True)
        login(a, 'valid_central_foreign_tenant_denied_by_instance', organization=bindings[b], expected=403)
        # Existing session validation maps an RLS-hidden local profile to 503.
        iso('foreign_cookie_replay_fail_closed', a, '/api/auth/me/', 503, jar=jar_b, denied=True)
        spoof = {'X-Tenant-ID': bindings[a], 'X-Role': 'org_admin', 'X-Client-ID': client['client_id'],
                 'X-Product': 'ISO_SMART', 'X-API-Key': client['credential']}
        iso('technical_headers_cannot_authenticate', a, '/api/auth/me/', 401, headers=spoof, denied=True)
        iso('technical_headers_cannot_elevate', b, '/api/resources/', 403,
            {**resource, 'code': 'FORBIDDEN-HEADER'}, jar_b, spoof, denied=True)
        # Negative local envelopes only. All accepted sessions/proofs above were issued by real endpoints.
        for name, changed in [('wrong_audience', {'aud': ['wrong']}),
                              ('wrong_issuer', {'iss': 'https://wrong.example.invalid'}),
                              ('wrong_client_id', {'client_id': 'unregistered'}),
                              ('wrong_product', {'product': 'MEDSUPPLIER'})]:
            invalid = jwt.encode({**local_claims, **changed}, key, algorithm='RS256', headers={'kid': 'r3-local'})
            iso(name, a, '/api/auth/me/', 401, jar={**jar_a, 'isosmart_access': invalid}, denied=True)
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        invalid = jwt.encode(local_claims, other_key, algorithm='RS256', headers={'kid': 'r3-local'})
        iso('invalid_signature', a, '/api/auth/me/', 401, jar={**jar_a, 'isosmart_access': invalid}, denied=True)
        write_private(central_root / 'runtime/r3-proof-input.json', proof)
        control('negative-proofs')
        negatives = json.loads((central_root / 'runtime/r3-negative-proofs.json').read_text())
        for name, invalid_proof in negatives.items():
            envelope = jwt.encode({**local_claims, 'central_proof': invalid_proof}, key,
                                  algorithm='RS256', headers={'kid': 'r3-local'})
            iso('embedded_central_' + name + '_rejected', a, '/api/auth/me/', 401,
                jar={**jar_a, 'isosmart_access': envelope}, denied=True)
        control('remove-scopes')
        iso('live_central_scope_removal_revokes_session', a, '/api/resources/', 401, jar=jar_a, denied=True)
        control('restore-scopes')
        iso('scope_restore_does_not_revive_session', a, '/api/resources/', 401, jar=jar_a, denied=True)
        _, jar_a = login(a, 'reauthenticate_after_scope_restore')
        token_a = jar_a['isosmart_access']
        local_claims = jwt.decode(token_a, local_trust['PUBLIC_KEYS']['r3-local'], algorithms=['RS256'],
            audience=local_trust['AUDIENCE'], issuer=local_trust['ISSUER'])
        proof = local_claims['central_proof']
        claims = jwt.decode(proof, public['PUBLIC_KEYS'][public['SIGNING_KID']], algorithms=['RS256'],
            audience=client['audience'][0], issuer=public['ISSUER'])
        listed, _ = iso('live_central_scopes_restored', a, '/api/resources/', 200, jar=jar_a)
        assert [row['id'] for row in listed] == [resource_id]
        # Maintenance changes the binding to reproduce deployment misconfiguration.
        # The worker must reject before authentication, handlers or persistence.
        conn = db()
        with conn.cursor() as cursor:
            cursor.execute('UPDATE lab_tenant_authority SET tenant_id=%s WHERE principal=%s',
                           ['00000000-0000-0000-0000-000000000999', a])
        conn.close()
        iso('sql_central_tenant_binding_mismatch', a, '/api/auth/me/', 503, jar=jar_a, denied=True)
        conn = db()
        with conn.cursor() as cursor:
            cursor.execute('UPDATE lab_tenant_authority SET tenant_id=%s WHERE principal=%s', [bindings[a], a])
        conn.close()
        credentials = {'email': 'viewer@example.invalid', 'password': client['password'], 'organization_id': bindings[a]}
        for name, changed in [('client', {'client_id': 'unauthorized'}), ('audience', {'audience': ['wrong']}),
                              ('product', {'product': 'MEDSUPPLIER'})]:
            central('central_rejects_' + name, 'login/', 401, {**credentials, **changed})
        central('central_rejects_forged_technical_headers', 'login/', 401, credentials,
            {'X-Client-ID': client['client_id'], 'X-Tenant-ID': bindings[a], 'X-Role': 'superadmin'})
        central('central_rejects_unregistered_credential', 'login/', 401, credentials,
            {'X-API-Key': client['unregistered']})
        # Actual RLS and SQL privilege tests with authenticated runtime connections.
        sql_checks = []
        for role, own, foreign in ((a, org_a, org_b), (b, org_b, org_a)):
            conn = db(role)
            try:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT current_user, session_user')
                    assert cursor.fetchone() == (role, role)
                    cursor.execute('SELECT organization_id FROM user_profiles')
                    assert cursor.fetchall() == [(own,)]
                    cursor.execute('SELECT count(*) FROM resources_resource WHERE organization_id=%s', [foreign])
                    assert cursor.fetchone()[0] == 0
                    cursor.execute('SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=session_user)')
                    assert cursor.fetchone()[0] == 0
                    cursor.execute('SELECT bool_and(relrowsecurity AND relforcerowsecurity) FROM pg_class '
                        "WHERE relname IN ('organizations','user_profiles','resources_resource')")
                    assert cursor.fetchone()[0] is True
                    for statement, params in [
                        ('UPDATE lab_tenant_authority SET tenant_id=%s WHERE principal=session_user', [bindings[b if role == a else a]]),
                        ('UPDATE auth_user SET is_superuser=true', None),
                        ('ALTER TABLE resources_resource DISABLE ROW LEVEL SECURITY', None),
                        ('CREATE TABLE forbidden (id integer)', None),
                        ('TRUNCATE resources_resource', None),
                        ('UPDATE user_profiles SET organization_id=%s WHERE organization_id=%s', [foreign, own]),
                    ]:
                        try:
                            cursor.execute(statement, params)
                        except psycopg2.Error as exc:
                            assert exc.pgcode == '42501', (statement, exc.pgcode)
                            sql_checks.append({'principal': role, 'statement': statement, 'sqlstate': exc.pgcode})
                        else:
                            raise AssertionError('Unexpected SQL permission: ' + statement)
                    if role == a:
                        try:
                            cursor.execute('UPDATE resources_resource SET organization_id=%s WHERE id=%s',
                                           [foreign, resource_id])
                        except psycopg2.Error as exc:
                            assert exc.pgcode == '42501'
                            sql_checks.append({'principal': role, 'statement': 'cross-tenant resource UPDATE',
                                               'sqlstate': exc.pgcode, 'rls_with_check': True})
                        else:
                            raise AssertionError('RLS allowed resource movement across tenants')
            finally:
                conn.close()
        # Logout at AdminApps, then replay exactly the previous cookie and proof.
        assert central('central_logout', 'logout/', 200, {'token': proof})['revoked'] is True
        sso_sql = json.loads((central_root / 'runtime/credentials-lab04_sso.json').read_text())
        conn = psycopg2.connect(dbname='lab04_human', user='lab04_sso', password=sso_sql['password'],
            host=str(central_root / 'runtime/socket'), port=56434)
        with conn.cursor() as cursor:
            cursor.execute('SELECT state, revocation_reason, revoked_at IS NOT NULL FROM sso_sessions WHERE id=%s', [claims['sid']])
            assert cursor.fetchone() == ('revoked', 'logout', True)
            cursor.execute("SELECT count(*) FROM sso_revocation_outbox WHERE session_id=%s AND reason='logout'", [claims['sid']])
            assert cursor.fetchone()[0] == 1
        conn.close()
        for iteration in (1, 2):
            iso('revoked_me_reconnect_' + str(iteration), a, '/api/auth/me/', 401, jar=jar_a, denied=True)
            iso('revoked_write_reconnect_' + str(iteration), a, '/api/resources/', 401,
                {**resource, 'code': 'FORBIDDEN-REVOKED'}, jar_a, denied=True)
        central('same_proof_revoked', 'introspect/', 401, {'token': proof})
        # A local usable password is deliberately installed only by maintenance;
        # outage must still deny login instead of using this matching password.
        from django.contrib.auth.hashers import PBKDF2PasswordHasher
        local_password = secrets.token_urlsafe(32)
        hasher = PBKDF2PasswordHasher()
        conn = db()
        with conn.cursor() as cursor:
            cursor.execute('UPDATE auth_user SET password=%s', [hasher.encode(local_password, hasher.salt())])
        conn.close()
        central_process.terminate()
        central_process.wait(timeout=10)
        iso('central_outage_protected_get', b, '/api/auth/me/', 503, jar=jar_b, denied=True)
        iso('central_outage_protected_write', b, '/api/resources/', 503,
            {**resource, 'code': 'FORBIDDEN-OFFLINE'}, jar_b, denied=True)
        login(a, 'local_password_fallback_forbidden', password=local_password, expected=503)
        login(a, 'central_outage_login', expected=503)
        central_process, restored_port = start([sys.executable, str(admin / 'lab05/http_server.py')],
            {**admin_env, 'LAB05_R3_PORT': str(central_port)}, central_root / 'http-sso-ready.json', 'central-restarted')
        assert restored_port == central_port
        iso('revocation_survives_central_restart', a, '/api/auth/me/', 401, jar=jar_a, denied=True)
        iso('active_session_recovers_after_outage', b, '/api/auth/me/', 200, jar=jar_b)
        central_requests = [json.loads(line) for line in (central_root / 'r3-central-requests.jsonl').read_text().splitlines()]
        assert sum(c['path'].endswith('/introspect/') for c in central_requests) >= 15
        pids = [c['backend_pid'] for c in cases if c.get('principal', '').startswith('iso_runtime_')]
        assert len(pids) == len(set(pids)), 'Every consumer request must reconnect PostgreSQL'
        result = {'verdict': 'LAB05_C1_R3_ISOSMART_HTTP_E2E_PASS', 'cases': cases,
            'central_requests': central_requests, 'sql_checks': sql_checks, 'projection': projection,
            'transport': 'real loopback HTTP; three WSGI servers; two disposable PostgreSQL clusters',
            'central_private_key_in_consumer': False, 'same_revoked_cookie_replayed': True,
            'same_revoked_central_proof_replayed': True, 'runtime_set_role': False,
            'durable_revocation': {'state': 'revoked', 'reason': 'logout', 'outbox_records': 1},
            'production_ready': False, 'phase31_5': 'EXECUTION_HELD',
            'S3_DECISION_02A_NOT_CLOSED': True, 'NO_DEPLOYMENT': True, 'NO_SHARED_DB_MUTATION': True}
        passed = True
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for stream in streams:
            stream.close()
        if not passed:
            diagnostic = central_root / 'r3-private-diagnostics'
            diagnostic.mkdir(mode=0o700, exist_ok=True)
            for path in root.glob('*.log'):
                shutil.copy(path, diagnostic / path.name)
        try:
            if started:
                run(['pg_ctl', '-D', str(root / 'data'), '-m', 'immediate', '-w', 'stop'], 'pg-stop')
        finally:
            shutil.rmtree(root)
        cleanup = {'http_processes_stopped': all(p.poll() is not None for p in processes),
                   'iso_cluster_stopped': started, 'iso_root_removed': not root.exists()}
        (central_root / 'r3-cleanup.json').write_text(json.dumps(cleanup, indent=2))
    result['cleanup'] = cleanup
    (central_root / 'r3-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['verdict'])


if __name__ == '__main__':
    main()
