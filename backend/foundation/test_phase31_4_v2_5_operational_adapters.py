"""Offline tests for the operational adapter command boundary."""

from pathlib import Path
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
        self.assertEqual(environment["PHASE31_ADMINAPPS_READINESS_PATH"], "/api/health/")

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
