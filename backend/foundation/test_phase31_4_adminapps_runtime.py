"""Dependency provenance, routing, isolation and cleanup checks."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
from unittest import TestCase, skipUnless
from unittest.mock import patch
from .phase31_4_adminapps_runtime import disposable_adminapps_runtime
from .phase31_4_v2_5_operational_adapters import repository_operational_environment
ROOT = Path(__file__).resolve().parents[2]

class AdminAppsRuntimeTests(TestCase):
    def test_canonical_runtime_declaration(self):
        self.assertIn('django-apscheduler==0.7.0', (ROOT.parent / 'adminapps/backend/requirements.txt').read_text().splitlines())

    def test_provisioning_uses_only_canonical_manifest_and_removes_environment(self):
        with patch('foundation.phase31_4_adminapps_runtime.subprocess.run') as run:
            with disposable_adminapps_runtime(ROOT, base={}) as (env, evidence):
                directory = Path(evidence['interpreter']).parents[1]
                self.assertTrue(directory.exists())
                self.assertEqual(run.call_args_list[1].args[0], [env['PHASE31_ADMINAPPS_PYTHON'], '-m', 'pip', 'install', '-r', str(ROOT.parent / 'adminapps/backend/requirements.txt')])
                self.assertNotIn('--system-site-packages', run.call_args_list[0].args[0])
                self.assertEqual(run.call_args_list[2].args[0][-2:], ['pip', 'check'])
            self.assertFalse(directory.exists())

    def test_install_failure_cleans_temporary_environment(self):
        directories = []
        def fail(argv, **kwargs):
            if 'venv' in argv: directories.append(Path(argv[-1]))
            else: raise subprocess.CalledProcessError(1, argv)
        with patch('foundation.phase31_4_adminapps_runtime.subprocess.run', side_effect=fail):
            with self.assertRaises(subprocess.CalledProcessError):
                with disposable_adminapps_runtime(ROOT): self.fail('must not yield a failed runtime')
        self.assertTrue(directories)
        self.assertFalse(directories[0].exists())

    def test_admin_authority_bootstrap_and_service_share_interpreter(self):
        with tempfile.NamedTemporaryFile() as python:
            env = repository_operational_environment(ROOT, {'PHASE31_ADMINAPPS_PYTHON': python.name})
            for key in ('PHASE31_ADMINAPPS_AUTHORITY_COMMAND', 'PHASE31_ADMINAPPS_BOOTSTRAP_COMMAND', 'PHASE31_ADMINAPPS_START_COMMAND'):
                self.assertEqual(shlex.split(env[key])[0], python.name)
            self.assertEqual(shlex.split(env['PHASE31_ISOSMART_START_COMMAND'])[0], str(ROOT / 'backend/.venv/bin/python'))

    def test_missing_interpreter_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'interpreter is unavailable'):
            repository_operational_environment(ROOT, {'PHASE31_ADMINAPPS_PYTHON': '/nonexistent/phase31-python'})

    def test_management_and_service_runtime_selection(self):
        spec = importlib.util.spec_from_file_location('phase31_actions_test', ROOT / 'docs/governance/tools/phase31_4_v2_5_operational_actions.py')
        actions = importlib.util.module_from_spec(spec); spec.loader.exec_module(actions)
        env = {'PHASE31_ADMINAPPS_PYTHON': '/temporary/runtime/bin/python'}
        self.assertEqual(str(actions.runtime_python(actions.ADMIN, env)), env['PHASE31_ADMINAPPS_PYTHON'])
        with patch.object(actions.subprocess, 'run') as run:
            run.return_value.returncode = 0; run.return_value.stdout = ''
            actions.run_manage(actions.ADMIN, env, 'migrate', '--noinput'); actions.pending(actions.ADMIN, env)
            self.assertTrue(all(call.args[0][0] == env['PHASE31_ADMINAPPS_PYTHON'] for call in run.call_args_list))
        with patch.object(actions, 'env_for', return_value=env), patch.object(actions.os, 'execve') as execute:
            with patch.dict(os.environ, {'PORT':'12345', 'PHASE31_INTEGRATION_KEY':'test-only'}): actions.service('adminapps')
            self.assertEqual(execute.call_args.args[0], env['PHASE31_ADMINAPPS_PYTHON'])

    @skipUnless(os.environ.get('PHASE31_PARITY_PYTHON'), 'requires canonically provisioned isolated runtime')
    def test_real_runtime_settings_setup_and_all_direct_constraints(self):
        script = '''
import importlib.metadata as m, json
from pathlib import Path
from packaging.requirements import Requirement
import django
import config.settings
django.setup()
import django_apscheduler
for line in Path('requirements.txt').read_text().splitlines():
    if line.strip() and not line.startswith('#'):
        r=Requirement(line)
        assert m.version(r.name) in r.specifier, r.name
print(json.dumps({'setup':'PASS','scheduler':m.version('django-apscheduler')}))
'''
        env = dict(os.environ, DJANGO_SETTINGS_MODULE='config.settings', BILLING_SCHEDULER_ENABLED='false', ENVIRONMENT='test', DB_HOST='127.0.0.1', DB_PORT='1')
        result = subprocess.run([os.environ['PHASE31_PARITY_PYTHON'], '-c', script], cwd=ROOT.parent / 'adminapps/backend', env=env, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)['scheduler'], '0.7.0')
