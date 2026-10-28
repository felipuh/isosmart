"""Create a fresh private PostgreSQL cluster, validate, and always remove it.

Usage: python backend/lab05_c1_r2/run.py --evidence /absolute/output.json
No existing cluster/database/credential arguments are accepted.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile


def main():
    if not __debug__:
        raise RuntimeError('Assertions must remain enabled for laboratory acceptance')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    backend = Path(__file__).resolve().parents[1]
    root = Path(tempfile.mkdtemp(prefix='iso-c1-r2-', dir='/tmp'))
    started = False
    result = None
    # Do not inherit PostgreSQL service files, active Django settings or dotenv.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('PG', 'DJANGO_', 'ISO_LAB_'))}
    env.update(ISO_LAB_ROOT=str(root), DJANGO_SETTINGS_MODULE='lab05_c1_r2.settings',
               PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(backend))

    def run(argv):
        return subprocess.run(argv, env=env, cwd=backend, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout

    try:
        config = {'secret': secrets.token_urlsafe(48), 'passwords': {
            name: secrets.token_urlsafe(32)
            for name in ('iso_owner', 'iso_runtime_a', 'iso_runtime_b')}}
        (root / 'runtime.json').write_text(json.dumps(config))
        (root / 'runtime.json').chmod(0o600)
        (root / 'socket').mkdir(mode=0o700)
        (root / 'owner-password').write_text(config['passwords']['iso_owner'])
        (root / 'owner-password').chmod(0o600)
        run(['initdb', '-D', str(root / 'data'), '-U', 'iso_owner',
             '--auth-local=scram-sha-256', '--auth-host=reject',
             '--pwfile', str(root / 'owner-password'), '--no-locale', '--encoding=UTF8'])
        with (root / 'data/postgresql.conf').open('a') as f:
            f.write("\nlisten_addresses = ''\nport = 56439\nunix_socket_directories = '" + str(root / 'socket') + "'\n")
        run(['pg_ctl', '-D', str(root / 'data'), '-l', str(root / 'postgres.log'), '-w', 'start'])
        started = True
        run([sys.executable, '-m', 'lab05_c1_r2.validate', 'bootstrap'])
        check = run([sys.executable, 'manage.py', 'check', '--settings=lab05_c1_r2.settings'])
        for role in ('iso_runtime_a', 'iso_runtime_b'):
            env['ISO_LAB_ROLE'] = role
            run([sys.executable, '-m', 'lab05_c1_r2.validate', 'runtime'])
        for role in ('iso_runtime_a', 'iso_runtime_b'):
            env['ISO_LAB_ROLE'] = role
            run([sys.executable, '-m', 'lab05_c1_r2.validate', 'isolation'])
        env['ISO_LAB_ROLE'] = 'iso_owner'
        run([sys.executable, '-m', 'lab05_c1_r2.validate', 'inspect'])
        result = json.loads((root / 'evidence.json').read_text())
        result['django_check'] = check.strip()
    except subprocess.CalledProcessError as exc:
        # Commands never contain credentials. PostgreSQL/Django errors may contain
        # synthetic row values, so retain failures only in private temporary output.
        print(exc.stdout[-12000:], file=sys.stderr)
        raise
    finally:
        if started:
            run(['pg_ctl', '-D', str(root / 'data'), '-m', 'immediate', '-w', 'stop'])
        shutil.rmtree(root)
    result['cleanup'] = {'cluster_stopped': True, 'root_removed': not root.exists()}
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['verdict'])


if __name__ == '__main__':
    main()
