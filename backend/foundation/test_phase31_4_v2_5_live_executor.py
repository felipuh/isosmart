from types import SimpleNamespace
import tempfile
import unittest
from pathlib import Path

from .phase31_4_v2_5_live_executor import LiveExecutorError, Phase31_4V25LiveEvidenceExecutor, build_live_execution_context

IDS = {
    "tenant": "11111111-1111-4111-8111-111111111111",
    "actor": "22222222-2222-4222-8222-222222222222",
    "tenant_projection": "33333333-3333-4333-8333-333333333333",
    "user_projection": "44444444-4444-4444-8444-444444444444",
    "organization": "55555555-5555-4555-8555-555555555555",
    "process": "66666666-6666-4666-8666-666666666666",
}


class FakeAdapter:
    test_only = True
    def __init__(self): self.calls = []; self.readback_override = None
    def _call(self, name, result): self.calls.append(name); return result
    def bootstrap_adminapps(self, c): return self._call("bootstrap_adminapps", {"status":"PASS","database_readiness":"PASS","migrations_pending":0})
    def bootstrap_isosmart(self, c): return self._call("bootstrap_isosmart", {"status":"PASS","database_readiness":"PASS","migrations_pending":0,"roles_verified":True,"session_configuration_verified":True})
    def start_adminapps(self,c): return self._call("start_adminapps", {"status":"PASS","pid":101,"readiness":"PASS","base_url":"http://127.0.0.1:41001"})
    def start_isosmart(self,c): return self._call("start_isosmart", {"status":"PASS","pid":102,"readiness":"PASS","base_url":"http://127.0.0.1:41002"})
    def create_adminapps_authority(self,c): return self._call("authority", {"status":"PASS","tenant_id":IDS["tenant"],"actor_id":IDS["actor"],"tenant_readback":{"id":IDS["tenant"]},"actor_readback":{"id":IDS["actor"]}})
    def deliver_projection_events(self,c,a): return self._call("delivery", {"status":"PASS","outbox_id":"real-outbox-row","delivery_result":"DELIVERED","ingress_receipt":"real-ingress-row","tenant_projection_id":IDS["tenant_projection"],"user_projection_id":IDS["user_projection"]})
    def read_tenant_projection(self,c,d): return self._call("tenant_projection_readback", {"id": self.readback_override or IDS["tenant_projection"]})
    def read_user_projection(self,c,d): return self._call("user_projection_readback", {"id":IDS["user_projection"]})
    def create_qms_organization(self,c,a,d): return self._call("organization_create", {"status":"PASS","returned_id":IDS["organization"],"entitlement_decision":"ALLOW"})
    def read_qms_organization(self,c,i): return self._call("organization_readback", {"id":IDS["organization"],"tenant_id":IDS["tenant_projection"]})
    def create_process(self,c,o,a): return self._call("process_create", {"status":"PASS","returned_id":IDS["process"]})
    def read_process(self,c,i): return self._call("process_readback", {"id":IDS["process"],"organization_id":IDS["organization"]})
    def stop_services(self): return {"status":"PASS"}


class LiveExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.manifest = {"run_id":"Live Diagnostic", "run_slug":"Live_Diagnostic", "resources":{
            "adminapps":{"host_port":51001,"database_name":"admin_db"}, "isosmart":{"host_port":51002,"database_name":"iso_db"}}}
        self.runner = SimpleNamespace(manifest=self.manifest)
        self.context = build_live_execution_context(repository_root=self.root, runner=self.runner,
            evidence_root=self.root/"docs/governance/evidence/runs/Live_Diagnostic",
            authorization_reference="auth.json", integrity_generation="V7")
        self.adapter = FakeAdapter()
    def tearDown(self): self.temp.cleanup()
    def executor(self, **kwargs): return Phase31_4V25LiveEvidenceExecutor(runner=self.runner, context=self.context, adapter=self.adapter, mode="test", **kwargs)

    def test_operational_mode_rejects_fake_and_missing_adapter(self):
        with self.assertRaisesRegex(LiveExecutorError, "OPERATIONAL_ADAPTER_REQUIRED"):
            Phase31_4V25LiveEvidenceExecutor(runner=self.runner, context=self.context, adapter=self.adapter, mode="evidence")

    def test_bootstrap_calls_real_boundary_and_verifies_roles(self):
        result = self.executor().bootstrap_runtime()
        self.assertEqual(result["isosmart"]["migrations_pending"], 0)
        self.assertEqual(self.adapter.calls, ["bootstrap_adminapps", "bootstrap_isosmart"])

    def test_pid_and_readiness_are_mandatory(self):
        self.adapter.start_adminapps = lambda c: {"status":"PASS","pid":0,"readiness":"PASS","base_url":"http://x"}
        with self.assertRaisesRegex(LiveExecutorError, "ADMINAPPS_START_FAILURE"): self.executor().start_services()

    def test_authority_and_bearer_acquisition_precede_service_readiness(self):
        self.executor().start_services()
        self.assertEqual(self.adapter.calls[:3], ["authority", "start_adminapps", "start_isosmart"])

    def test_stage_ext_uses_six_separate_readbacks_and_provenance(self):
        result = self.executor().resolve_stage_ext_identities()
        self.assertEqual(result["resolved_identity_count"], 6)
        self.assertIn("tenant_projection_readback", self.adapter.calls)
        self.assertEqual(result["identity_summary"]["tenant"]["provenance"], "LIVE_UPSTREAM_EXTERNAL_AUTHORITY")
        self.assertEqual(result["identity_summary"]["organization"]["provenance"], "LIVE_ISOSMART_QMS_NATIVE")

    def test_independent_readback_mismatch_fails(self):
        self.adapter.readback_override = "77777777-7777-4777-8777-777777777777"
        with self.assertRaisesRegex(LiveExecutorError, "PROJECTION_READBACK_FAILURE"): self.executor().resolve_stage_ext_identities()

    def test_delivery_requires_actual_receipt(self):
        self.adapter.deliver_projection_events = lambda c,a: {"status":"PASS","outbox_id":"x","delivery_result":"DELIVERED"}
        with self.assertRaisesRegex(LiveExecutorError, "EVENT_DELIVERY_FAILURE"): self.executor().deliver_event_projection()

    def test_capture_bundle_only_after_six_of_six(self):
        executor = self.executor()
        with self.assertRaisesRegex(LiveExecutorError, "CAPTURE_BUNDLE_FAILURE"): executor.build_capture_bundle()
        executor.resolve_stage_ext_identities()
        self.assertEqual(len(executor.build_capture_bundle().captures), 5)

    def test_runtime_handoff_receives_live_bundle_without_formal_run(self):
        observed = {}
        runtime = SimpleNamespace(session=SimpleNamespace(composition={}, phases=[]), run_clean_retry=lambda: observed.update(ran=True))
        executor = self.executor(runtime_factory=lambda **kw: (observed.update(kw=kw) or runtime))
        executor.resolve_stage_ext_identities(); result = executor.prepare_runtime()
        self.assertIs(result, runtime); self.assertIn("capture_bundle", observed["kw"]); self.assertNotIn("ran", observed)


if __name__ == "__main__": unittest.main()
