import json
import unittest
from unittest.mock import Mock

from .phase31_4_v2_5_runtime import (
    BindingResolutionError,
    CaptureRecord,
    CleanRetry4Harness,
    MissingCaptureError,
    NativeCaptureRegistry,
    NativeOperationRegistry,
    NativePhaseRegistry,
    ResolvedBindingRegistry,
    RuntimeInvariantEngine,
    V25Contract,
    V25ExecutionSession,
    build_v25_native_phase_registry,
    build_v25_runtime,
)
from .phase31_4_v2_5_structural_gate import build_report


class V25RuntimeTests(unittest.TestCase):
    def test_stage_b1_reports_complete_structural_coverage(self):
        report = build_report("..")
        self.assertEqual(report["native_sources"], {"required": 16, "registered": 16, "unresolved": 0, "duplicates": 0})
        self.assertEqual(report["native_phases"], {"required": 33, "registered": 33, "missing": 0, "duplicates": 0, "concrete_executors": 33})
        self.assertEqual(report["capture_producers"], {"expected": 509, "covered": 509, "uncovered": 0, "ambiguous": 0})
        self.assertEqual(report["production_runtime_factory"], "PASS")

    def test_structural_gate_rejects_missing_source_phase_and_capture_producer(self):
        runtime = build_v25_runtime(project_root="..")
        bindings = tuple(runtime.operation_registry._bindings.values())
        source = bindings[0].native_source
        reduced = NativeOperationRegistry(tuple(binding for binding in bindings if binding.native_source != source))
        self.assertIn(source, reduced.coverage_report(runtime.contract.raw)["unresolved"])
        phases = NativePhaseRegistry(required_phase_ids=("MISSING",))
        self.assertEqual(phases.coverage_report()["missing"], ["MISSING"])
        contract = json.loads(json.dumps(runtime.contract.raw))
        capture = next(
            field for member in contract["field_bindings"] for field in member["fields"]
            if field["value_binding"].get("kind") == "CAPTURE_NATIVE_OUTPUT"
        )
        capture["value_binding"]["native_source"] = "missing producer"
        self.assertEqual(V25Contract(contract).structural_capture_report(runtime.operation_registry)["uncovered"], 1)

    def test_structural_gate_rejects_duplicate_phase_and_dependency_cycle(self):
        runtime = build_v25_runtime(project_root="..")
        registry = NativePhaseRegistry(required_phase_ids=("PHASE",))
        executor = Mock()
        executor.execute = lambda session, context: None
        registry.register("PHASE", executor)
        with self.assertRaisesRegex(RuntimeError, "duplicate native phase executor"):
            registry.register("PHASE", executor)
        cyclic = ResolvedBindingRegistry({
            ("a", "id"): {"kind": "REFERENCE_RESOLVED_BINDING", "source_member": "b", "source_field": "id"},
            ("b", "id"): {"kind": "REFERENCE_RESOLVED_BINDING", "source_member": "a", "source_field": "id"},
        })
        with self.assertRaisesRegex(BindingResolutionError, "cyclic binding"):
            cyclic.resolve("a", "id", NativeCaptureRegistry())
        self.assertEqual(runtime.contract.dependency_graph_report()["status"], "PASS")

    def test_production_factory_has_no_business_callback_parameter(self):
        runtime = build_v25_runtime(project_root="..")
        self.assertEqual(len(runtime.phase_registry.phase_ids()), 33)
        self.assertFalse(any(name == "handlers" for name in runtime.__dict__))

    def test_root_bootstrap_uses_the_native_publication_service(self):
        runtime = build_v25_runtime(project_root="..")
        binding = runtime.operation_registry.resolve("root.bootstrap.publish")
        self.assertEqual(binding.source_service, "KnowledgeLayerRulePublicationService")
        self.assertEqual(binding.source_operation, "publish_native")
        self.assertEqual(binding.source_file, "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py")
        with self.assertRaisesRegex(BindingResolutionError, "publication authority"):
            runtime.contract.native_phase_inputs("PRECREATION_INTEGRITY")

    def test_precreation_integrity_uses_native_support_producer(self):
        runtime = build_v25_runtime(project_root="..")
        executor = runtime.phase_registry.get("PRECREATION_INTEGRITY")
        self.assertIsNone(executor.native_operation)
    def test_product_registry_resolves_only_real_native_operations(self):
        registry = NativeOperationRegistry.product_default()

        self.assertEqual(len(registry.source_manifest()), 16)
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        coverage = registry.coverage_report(contract.raw)
        self.assertEqual(coverage["required"], 16)
        self.assertEqual(coverage["registered"], 16)
        self.assertEqual(coverage["unresolved"], [])
        self.assertEqual(coverage["unknown"], [])
        self.assertEqual(coverage["duplicate_conflicting"], [])
        self.assertEqual(
            registry.resolve("opportunity.create").source_operation,
            "create_opportunity",
        )
        self.assertEqual(
            registry.resolve("action_plan.prepare").source_service,
            "ActionPreparationService",
        )
        with self.assertRaisesRegex(RuntimeError, "unregistered native operation"):
            registry.resolve("missing.operation")

    def test_registry_rejects_duplicate_operation_and_invalid_handler(self):
        registry = NativeOperationRegistry.product_default()
        binding = next(iter(registry._bindings.values()))
        with self.assertRaisesRegex(RuntimeError, "duplicate native operation binding"):
            NativeOperationRegistry((binding, binding))

        invalid = binding.__class__(
            binding.name, object(), binding.source_service, binding.source_operation,
            binding.native_source, binding.source_file, binding.phases,
        )
        with self.assertRaisesRegex(RuntimeError, "orphan native operation binding"):
            NativeOperationRegistry((invalid,))

    def test_capture_registry_keeps_trace_and_rejects_mismatch_or_missing(self):
        registry = NativeCaptureRegistry()
        registry.capture(CaptureRecord(
            logical_member="qms.opportunity::live",
            logical_field="id",
            source_service="RiskOpportunityObjectiveCommandService",
            source_operation="create_opportunity",
            returned_value="native-id",
            persisted_value="native-id",
            expected_type="uuid",
            phase="PHASE_18",
        ))

        self.assertTrue(registry.get("qms.opportunity::live", "id").equality_assertion)
        with self.assertRaises(MissingCaptureError):
            registry.get("qms.opportunity::live", "lineage_id")
        with self.assertRaises(RuntimeError):
            registry.capture(CaptureRecord(
                logical_member="qms.opportunity::other",
                logical_field="id",
                source_service="native",
                source_operation="create",
                returned_value="returned",
                persisted_value="persisted",
                expected_type="string",
                phase="PHASE_18",
            ))


    def test_resolver_rejects_missing_dependency_and_cycle(self):
        captures = NativeCaptureRegistry()
        missing = ResolvedBindingRegistry({
            ("member", "field"): {
                "kind": "REFERENCE_RESOLVED_BINDING",
                "source_member": "missing",
                "source_field": "id",
            },
        })
        with self.assertRaisesRegex(BindingResolutionError, "missing dependency"):
            missing.resolve("member", "field", captures)

        cyclic = ResolvedBindingRegistry({
            ("a", "id"): {"kind": "REFERENCE_RESOLVED_BINDING", "source_member": "b", "source_field": "id"},
            ("b", "id"): {"kind": "REFERENCE_RESOLVED_BINDING", "source_member": "a", "source_field": "id"},
        })
        with self.assertRaisesRegex(BindingResolutionError, "cyclic binding"):
            cyclic.resolve("a", "id", captures)


    def test_revision_invariants_use_native_ids_not_historical_literals(self):
        initial = {"id": "native-initial", "lineage_id": "native-initial", "revision": 1, "previous_revision_id": None}
        successor = {"id": "native-successor", "lineage_id": "native-initial", "revision": 2, "previous_revision_id": "native-initial"}
        RuntimeInvariantEngine.assert_revision(initial=initial, successor=successor)


    def test_clean_retry_4_requires_and_runs_all_33_phases(self):
        session = V25ExecutionSession()
        called = []
        handlers = {
            phase: (lambda selected=phase: called.append(selected))
            for phase in CleanRetry4Harness.PHASES
        }

        records = CleanRetry4Harness(
            session,
            handlers,
            contract=V25Contract.from_path(
                "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
            ),
            operation_registry=NativeOperationRegistry.product_default(),
        ).run()

        self.assertEqual(len(records), 33)
        self.assertTrue(all(record.status == "PASS" for record in records))
        self.assertEqual(called, list(CleanRetry4Harness.PHASES))