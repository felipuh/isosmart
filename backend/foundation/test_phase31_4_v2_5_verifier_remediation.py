import tempfile
import unittest
from pathlib import Path

from .phase31_4_v2_5_verifier_remediation import (
    AppendOnlyEvidenceStore,
    LiveCapture,
    PhaseContract,
    PhaseExecutionResult,
    exact_compare,
    materialize_resolved_graph,
    verify_event_outbox_audit,
    verify_post_teardown,
    verify_security_probe,
)


class VerifierRemediationTests(unittest.TestCase):
    def setUp(self):
        self.contract = PhaseContract(
            phase_id="P1", phase_name="Proof", claimed_guarantee="A real operation is proven",
            executor="test.Executor", required_assertions=("operation", "readback"),
            required_evidence_types=("phase_result",),
        )

    def test_result_status_and_registration_are_fail_closed(self):
        failed = PhaseExecutionResult("P1", "Proof", "FAIL", "test.Executor", error="denied")
        failed.validate(self.contract)
        with self.assertRaisesRegex(ValueError, "PASS phase missing assertions"):
            PhaseExecutionResult(
                "P1", "Proof", "PASS", "test.Executor", operation="run", inputs_hash="hash",
                completed_at="now", evidence_artifacts=("phase_result",),
            ).validate(self.contract)
        with self.assertRaises(ValueError):
            PhaseContract("P2", "Missing", "claim", (), (), executor=None).validate_registration()

    def test_capture_requires_equal_readback_and_rejects_wrong_provenance(self):
        capture = LiveCapture(
            "qms.item::live.id", "CAPTURE_NATIVE_OUTPUT", "P1", "retry-1", "Service", "create",
            "id-1", "string", "id-1", "db:item", True, {"kind": "QMS_NATIVE_PROCESS"},
        )
        capture.validate()
        with self.assertRaises(ValueError):
            LiveCapture(
                "qms.item::live.id", "CAPTURE_NATIVE_OUTPUT", "P1", "retry-1", "Service", "create",
                "id-1", "string", "id-2", "db:item", False, {"kind": "QMS_NATIVE_PROCESS"},
            ).validate()
        with self.assertRaises(ValueError):
            LiveCapture(
                "qms.item::live.id", "LIVE_UPSTREAM_NATIVE_CAPTURE", "P1", "retry-1", "Service", "create",
                "captured:id", "string", "captured:id", "db:item", True, {"kind": "SYNTHETIC_HARNESS", "synthetic": True},
            ).validate()

    def test_graph_rejects_placeholders_and_exact_comparison_reports_mismatch(self):
        contract = {"field_bindings": [{
            "member_identity": {"qualified_table_or_artifact_index": "qms.item", "primary_key_or_artifact_id": "live"},
            "fields": [{"name": "id", "value_binding": {"kind": "CAPTURE_NATIVE_OUTPUT"}}],
        }]}
        capture = LiveCapture(
            "qms.item::live.id", "CAPTURE_NATIVE_OUTPUT", "P1", "retry-1", "Service", "create",
            "id-1", "string", "id-1", "db:item", True, {"kind": "QMS_NATIVE_PROCESS"},
        )
        graph = materialize_resolved_graph(contract, (capture,))
        self.assertEqual(exact_compare(graph, graph)["total_mismatches"], 0)
        mismatch = exact_compare(graph, {"members": []})
        self.assertEqual(mismatch["status"], "FAIL")
        with self.assertRaises(ValueError):
            materialize_resolved_graph(contract, (LiveCapture(
                "qms.item::live.id", "CAPTURE_NATIVE_OUTPUT", "P1", "retry-1", "Service", "create",
                "captured:id", "string", "captured:id", "db:item", True, {"kind": "QMS_NATIVE_PROCESS"},
            ),))

    def test_event_security_teardown_and_append_only_evidence(self):
        rows = {
            "domain_events": [{"aggregate_id": "a", "trace_id": "t", "payload_hash": "p"}],
            "transactional_outbox": [{"aggregate_id": "a", "trace_id": "t", "payload_hash": "p"}],
            "immutable_audit_log": [{"aggregate_id": "a", "trace_id": "t", "payload_hash": "p"}],
        }
        self.assertEqual(verify_event_outbox_audit(rows, aggregate_id="a", trace_id="t", payload_hash="p")["status"], "PASS")
        self.assertEqual(verify_event_outbox_audit({}, aggregate_id="a", trace_id="t", payload_hash="p")["status"], "FAIL")
        probe = {"principal": "actor", "tenant": "tenant", "operation": "read", "expected_result": "DENY", "observed_result": "DENY", "db_role": "reader", "status": "PASS"}
        self.assertEqual(verify_security_probe(probe)["status"], "PASS")
        self.assertEqual(verify_post_teardown(teardown_completed=True, observed_absence={
            "containers": False, "networks": False, "volumes": False, "db_reachability": False, "allocated_ports": False,
        })["status"], "PASS")
        with tempfile.TemporaryDirectory() as directory:
            store = AppendOnlyEvidenceStore(Path(directory) / "retry_1")
            store.write("02_phase_results.json", {"status": "PENDING"})
            store.finalize()
            with self.assertRaises(RuntimeError):
                store.write("03_native_captures.json", {})


if __name__ == "__main__":
    unittest.main()