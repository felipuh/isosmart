"""Attempt 1 governance invocation and observation; no implementation overrides."""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import traceback
from datetime import datetime, timezone

ROOT = Path('/home/felipe/proyectos/isosmart')
CONTROL = Path(__file__).resolve().parent
PREFIX = 'PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_ATTEMPT_1'
AUTH = ROOT / 'docs/governance/evidence' / (PREFIX + '_AUTHORIZATION_V1.json')
A = json.loads(AUTH.read_text())
EVIDENCE = ROOT / A['evidence_root']
sys.path.insert(0, str(ROOT / 'backend'))

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    with (CONTROL / name).open('x') as output:
        json.dump(value, output, indent=2, default=str)
        output.write('\n')

def command(argv):
    start = now()
    result = subprocess.run(argv, text=True, capture_output=True, cwd=ROOT, timeout=30)
    return dict(argv=argv, started_at=start, completed_at=now(), returncode=result.returncode,
                stdout=result.stdout, stderr=result.stderr)

def inventory():
    return {kind: command(argv) for kind, argv in {
        'containers': ['podman', 'ps', '-a', '--format', '{{.Names}}'],
        'networks': ['podman', 'network', 'ls', '--format', '{{.Name}}'],
        'volumes': ['podman', 'volume', 'ls', '--format', '{{.Name}}'],
        'listeners': ['ss', '-ltnp'],
    }.items()}

def matching_processes():
    matches = []
    for path in Path('/proc').glob('[0-9]*/environ'):
        try:
            env = path.read_bytes().split(b'\0')
            if ('PHASE31_RUN_ID=' + A['run_id']).encode() in env:
                matches.append(int(path.parent.name))
        except (OSError, PermissionError):
            continue
    return matches

def inputs():
    from foundation.phase31_4_v2_5_disposable_runner import RunInputs
    return RunInputs(repository_root=ROOT, run_id=A['run_id'], authorization_artifact=AUTH,
        expected_authorization_sha256='488d98c0d74c3ea508841285c0a744b4723d859ce0b55b7bab6d2aed57b5f225',
        current_integrity_generation=A['integrity']['generation'],
        expected_integrity_sha256=A['integrity']['sha256'], evidence_root=EVIDENCE,
        execution_kind=A['execution_kind'], validation_attempt=1,
        consumption_registry=Path(A['consumption_registry']))

def preflight():
    from foundation.phase31_4_integrity_generations import verify_v25_current_integrity, verify_v24_historical_integrity
    from foundation.phase31_4_v2_5_disposable_runner import verify_authorization, _resource_prefix, _database_name
    checks = {}
    assert digest(ROOT / A['parent_cycle_authorization']['artifact_path']) == 'c8633d150784c23170585627b1bf3bd738bcf62197998d5ea8e7bd3d9d08aac9'
    assert digest(ROOT / A['integrity']['artifact_path']) == 'ed7bed0108e790c93e0c40625b215dde02ae25566b2397533b11b6aae7040946'
    current = verify_v25_current_integrity(ROOT)
    verify_v24_historical_integrity(ROOT)
    previous = json.loads((ROOT / 'docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V7.json').read_text())
    paths = {x['path'] for x in current['sources']}
    prior = {x['path'] for x in previous['sources']}
    assert len(paths) == 28 and paths == prior
    checks['integrity'] = dict(status='PASS', protected=28, missing=0, unexpected=0, migration_hashes=24, historical_v24='PASS')
    history = json.loads((CONTROL / 'historical_hashes_before.json').read_text())
    changes = [p for p, sha in history.items() if not (ROOT / p).is_file() or digest(ROOT / p) != sha]
    assert not changes, changes
    checks['history'] = dict(status='PASS', files=len(history), changed=changes)
    review = json.loads((ROOT / 'docs/governance/evidence/PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_CYCLE_REVIEW_EVIDENCE_V1.json').read_text())
    launcher = review['historical_launcher_disposition']
    assert digest(ROOT / launcher['path']) == launcher['sha256']
    checks['historical_launcher'] = launcher
    verified = verify_authorization(inputs())
    checks['authorization'] = dict(status='PASS', sha256=verified.authorization_sha256, consumed=False)
    observed = inventory()
    assert all(x['returncode'] == 0 for x in observed.values()), observed
    prefix = _resource_prefix(A['canonical_run_slug'])
    resources = {role: dict(container=prefix+'_'+role, network=prefix+'_'+role+'_net',
        volume=prefix+'_'+role+'_data', database=_database_name(A['canonical_run_slug'], role)) for role in ('adminapps', 'isosmart')}
    for role in resources.values():
        for kind, plural in [('container', 'containers'), ('network', 'networks'), ('volume', 'volumes')]:
            assert role[kind] not in observed[plural]['stdout'].splitlines()
    processes = matching_processes()
    assert not processes
    assert not EVIDENCE.exists()
    checks.update(status='PASS', checked_at=now(), run_id=A['run_id'], planned_resources=resources,
        resource_inventory=observed, previous_attempt_processes=processes,
        active_manifest='ABSENT', evidence_root='ABSENT', ports=dict(status='DYNAMIC_ALLOCATION_REQUIRED',
        assigned_before_allocation=[], policy='V8 Podman 127.0.0.1::5432 and service bind(127.0.0.1,0); no fixed-port reuse'))
    write('preflight.json', checks)
    print(json.dumps({'preflight':'PASS', 'planned_resources':resources}), flush=True)

def launch():
    assert json.loads((CONTROL / 'preflight.json').read_text())['status'] == 'PASS'
    write('technical_launch_once.json', dict(at=now(), run_id=A['run_id'], attempt=1,
        argv=sys.argv, authorization_sha256=digest(AUTH), boundary='LAUNCHER_STARTED'))
    runner = executor = None
    outcome = {'run_id': A['run_id'], 'started_at': now(), 'boundaries': ['LAUNCHER_STARTED']}
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
        import django
        django.setup()
        outcome['boundaries'].append('DJANGO_SETUP_COMPLETE')
        from foundation.phase31_4_v2_5_disposable_runner import DisposableEvidenceRunner
        from foundation.phase31_4_v2_5_live_executor import Phase31_4V25LiveEvidenceExecutor, build_live_execution_context
        from foundation.phase31_4_v2_5_operational_adapters import SubprocessOperationalAdapter, repository_operational_environment
        runner = DisposableEvidenceRunner(inputs())
        outcome['boundaries'].append('RUNNER_INITIALIZED')
        def live():
            nonlocal executor
            if executor is None:
                context = build_live_execution_context(repository_root=ROOT, runner=runner, evidence_root=EVIDENCE,
                    authorization_reference=str(AUTH.relative_to(ROOT)), integrity_generation=A['integrity']['generation'])
                executor = Phase31_4V25LiveEvidenceExecutor(runner=runner, context=context,
                    adapter=SubprocessOperationalAdapter(environment=repository_operational_environment(ROOT, os.environ)),
                    mode='diagnostic', allow_runtime_execution=False)
            return executor
        def stage(manifest):
            result = dict(live().stage_ext(manifest))
            write('stage_ext_live.json', result)
            bundle = live().build_capture_bundle()
            bundle.validate_for_retry(A['run_id'])
            write('capture_bundle_live.json', dict(bundle=dataclasses.asdict(bundle), independent_readbacks=result,
                observed_at=now(), run_id=A['run_id']))
            live().prepare_runtime()
            write('runtime_handoff.json', dict(status='PASS', allow_runtime_execution=False, observed_at=now()))
            outcome['boundaries'].extend(['STAGE_EXT_6_OF_6', 'CAPTURE_BUNDLE_READY'])
            return dict(result, capture_bundle='PASS', capture_count=len(bundle.captures))
        runner.run_evidence(precreation=lambda manifest: live().precreation(manifest), stage_ext=stage)
        outcome['execution_result'] = 'PASS'
    except BaseException as exc:
        outcome.update(execution_result='FAIL', exception_type=type(exc).__name__, exception=str(exc), traceback=traceback.format_exc())
    finally:
        if executor is not None:
            outcome['service_endpoints'] = dict(executor.context.service_urls)
            outcome['service_pids'] = {k:v.pid for k,v in executor.adapter.processes.items()}
            try:
                outcome['service_cleanup'] = executor.stop_services()
            except BaseException as exc:
                outcome['service_cleanup'] = dict(status='FAIL', exception=str(exc))
        if runner is not None and runner._manifest is not None:
            outcome['manifest_path'] = str(runner.manifest_path)
            outcome['manifest_sha256'] = digest(runner.manifest_path)
            outcome['failure'] = runner.manifest.get('failure')
            outcome['cleanup'] = runner.manifest.get('cleanup')
        outcome['completed_at'] = now()
        write('execution_outcome.json', outcome)
        print(json.dumps(outcome, indent=2), flush=True)

if __name__ == '__main__':
    {'preflight': preflight, 'launch': launch}[sys.argv[1]]()
