"""Offline tests for the operational adapter command boundary."""

from pathlib import Path
import hashlib
import json
import sys
import tempfile
from unittest import TestCase
from unittest.mock import patch

from .phase31_4_v2_5_live_executor import LiveExecutionContext, LiveExecutorError
from .phase31_4_v2_5_operational_adapters import (
    SubprocessOperationalAdapter,
    repository_operational_environment,
)


class OperationalAdapterTests(TestCase):
    def test_repository_environment_defines_every_real_command(self):
        environment = repository_operational_environment(Path(__file__).resolve().parents[2])
        self.assertTrue(set(SubprocessOperationalAdapter._COMMANDS.values()) <= set(environment))
        self.assertIn("phase31_4_v2_5_operational_actions.py", environment["PHASE31_EVENT_DELIVERY_COMMAND"])
        self.assertIn("service adminapps", environment["PHASE31_ADMINAPPS_START_COMMAND"])
        self.assertIn("service isosmart", environment["PHASE31_ISOSMART_START_COMMAND"])
        self.assertEqual(environment["PHASE31_ADMINAPPS_READINESS_PATH"], "/api/integration/health/")
        self.assertEqual(environment["PHASE31_ISOSMART_READINESS_PATH"], "/health")

    def test_missing_command_fails_closed_without_fallback(self):
        adapter = SubprocessOperationalAdapter(environment={})
        with self.assertRaisesRegex(LiveExecutorError, "required command is not configured"):
            adapter._command("delivery")

    def test_success_requires_subprocess_json_and_retains_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actions = root / "actions.py"
            actions.write_text("# offline test action\n", encoding="utf-8")
            context = LiveExecutionContext(
                run_id="offline-adapter-test",
                run_slug="offline-adapter-test",
                repository_root=root,
                evidence_root=root / "evidence",
                authorization_reference="offline",
                integrity_generation="offline",
                resource_manifest={},
                adminapps_db_endpoint="postgresql://127.0.0.1:1/a",
                isosmart_db_endpoint="postgresql://127.0.0.1:2/i",
                allocated_host_ports={"adminapps": 1, "isosmart": 2},
            )
            adapter = SubprocessOperationalAdapter(
                environment={"PHASE31_EVENT_DELIVERY_COMMAND": f"python {actions}"}
            )
            completed = type("Completed", (), {
                "returncode": 0,
                "stdout": '{"status":"PASS","outbox_id":"db-row"}\n',
                "stderr": "",
            })()
            with patch("foundation.phase31_4_v2_5_operational_adapters.subprocess.run", return_value=completed):
                result = adapter._run("delivery", context)
            self.assertEqual(result["outbox_id"], "db-row")
            self.assertTrue((context.evidence_root / "delivery.log").is_file())

    def test_runtime_bearer_uses_pipe_and_never_enters_log_or_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            action = root / "credential_action.py"
            action.write_text(
                "import hashlib,json,os\n"
                "raw=('unit-runtime-'+'credential').encode()\n"
                "os.write(int(os.environ['PHASE31_BEARER_FD']),raw)\n"
                "e={'token_present':True,'token_type':'Bearer','identity_id':'synthetic-id',"
                "'token_fingerprint':hashlib.sha256(raw).hexdigest(),'token_source':'unit',"
                "'token_lifetime_seconds':900,'token_persisted':False}\n"
                "print(json.dumps({'status':'PASS','bearer':e}))\n",
                encoding="utf-8",
            )
            context = LiveExecutionContext(
                run_id="offline-credential-test", run_slug="offline-credential-test",
                repository_root=root, evidence_root=root / "evidence",
                authorization_reference="offline", integrity_generation="offline",
                resource_manifest={}, adminapps_db_endpoint="postgresql://127.0.0.1:1/a",
                isosmart_db_endpoint="postgresql://127.0.0.1:2/i",
                allocated_host_ports={"adminapps": 1, "isosmart": 2},
            )
            adapter = SubprocessOperationalAdapter(environment={
                "PHASE31_ADMINAPPS_AUTHORITY_COMMAND": f"{sys.executable} {action}"
            })
            result = adapter._run("authority", context, credential_name="isosmart_bearer")
            raw = "unit-runtime-credential"
            self.assertNotIn(raw, json.dumps(result))
            self.assertNotIn(raw, (context.evidence_root / "authority.log").read_text())
            self.assertEqual(result["bearer"]["token_fingerprint"], hashlib.sha256(raw.encode()).hexdigest())
            teardown = adapter.stop_services()
            self.assertTrue(teardown["credential_references_destroyed"]["isosmart_bearer"])
