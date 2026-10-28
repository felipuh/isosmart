import json
import unittest
from unittest.mock import Mock
from uuid import uuid4

from .phase31_4_v2_5_runtime import (
    BindingResolutionError,
    CaptureBundle,
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
        self.assertEqual(report["capture_producers"], {"expected": 565, "covered": 565, "uncovered": 0, "ambiguous": 0})
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
        self.assertEqual(executor.source_service, "PrecreationIntegrityExecutor")
        self.assertEqual(executor.source_operation, "verify_precreation_integrity")
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

    def test_initial_opportunity_uses_live_native_process_capture_not_historical_fixture(self):
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        session = V25ExecutionSession()
        process_id = "35ae9e96-478d-40d9-8cdd-be52a0c7048d"
        session.captures.capture(CaptureRecord(
            logical_member="qms.process::primary",
            logical_field="id",
            source_service="QmsContextCommandService",
            source_operation="create_process",
            returned_value=process_id,
            persisted_value=process_id,
            expected_type="uuid",
            phase="UPSTREAM_NATIVE_CHAIN",
        ))
        session.captures.capture(CaptureRecord(
            logical_member="qms.tenant_projection::live",
            logical_field="id",
            source_service="TenantProjectionWriter",
            source_operation="project_tenant_event",
            returned_value="live-tenant",
            persisted_value="live-tenant",
            expected_type="uuid",
            phase="AUTHENTICATED_TENANT_PROJECTION",
        ))
        session.captures.capture(CaptureRecord(
            logical_member="qms.user_projection::live",
            logical_field="adminapps_user_id",
            source_service="AdminApps",
            source_operation="create_user",
            returned_value="live-actor",
            persisted_value="live-actor",
            expected_type="uuid",
            phase="AUTHENTICATED_TENANT_PROJECTION",
        ))

        payload = contract.native_phase_inputs("INITIAL_OPPORTUNITY", session=session)

        self.assertEqual(str(payload["process_id"]), process_id)
        self.assertEqual(str(payload["identity"].tenant_id), "live-tenant")
        self.assertNotEqual(str(payload["process_id"]), "506d920c-fe62-53c0-aac8-9c1ca8ca78ed")

    def test_live_external_and_local_tenant_ids_remain_distinct(self):
        external_tenant = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        local_projection = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        self.assertNotEqual(external_tenant, local_projection)
        session = V25ExecutionSession()
        session.captures.capture(CaptureRecord(
            logical_member="qms.process::live", logical_field="id",
            source_service="QmsContextCommandService", source_operation="create_process",
            returned_value="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            persisted_value="cccccccc-cccc-4ccc-8ccc-cccccccccccc", expected_type="uuid",
            phase="UPSTREAM_NATIVE_CAPTURE",
        ))
        session.captures.capture(CaptureRecord(
            logical_member="qms.tenant_projection::live", logical_field="id",
            source_service="TenantProjectionWriter", source_operation="project_tenant_event",
            returned_value=local_projection, persisted_value=local_projection, expected_type="uuid",
            phase="AUTHENTICATED_TENANT_PROJECTION",
        ))
        session.captures.capture(CaptureRecord(
            logical_member="qms.user_projection::live", logical_field="adminapps_user_id",
            source_service="AdminApps", source_operation="create_user",
            returned_value="live-actor", persisted_value="live-actor", expected_type="uuid",
            phase="AUTHENTICATED_TENANT_PROJECTION",
        ))
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        payload = contract.native_phase_inputs("INITIAL_OPPORTUNITY", session=session)
        self.assertEqual(str(payload["identity"].tenant_id), local_projection)
        self.assertNotEqual(str(payload["identity"].tenant_id), external_tenant)

    def test_initial_opportunity_requires_live_process_capture_before_invocation(self):
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        session = V25ExecutionSession()

        with self.assertRaises(MissingCaptureError):
            contract.native_phase_inputs("INITIAL_OPPORTUNITY", session=session)

    def test_initial_opportunity_requires_live_tenant_capture_for_identity(self):
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        session = V25ExecutionSession()
        session.captures.capture(CaptureRecord(
            logical_member="qms.process::live",
            logical_field="id",
            source_service="QmsContextCommandService",
            source_operation="create_process",
            returned_value="live-process",
            persisted_value="live-process",
            expected_type="uuid",
            phase="UPSTREAM_NATIVE_CAPTURE",
        ))

        with self.assertRaisesRegex(MissingCaptureError, "missing live capture"):
            contract.native_phase_inputs("INITIAL_OPPORTUNITY", session=session)

    def test_stage_ext_capture_bridge_imports_five_fresh_captures_before_initial_opportunity(self):
        retry_id = "Phase 31.4 V2.5 Clean Retry 16"
        stage_ext = {
            "retry_id": retry_id,
            "tenant_id": "11111111-1111-4111-8111-111111111111",
            "tenant_projection_id": "22222222-2222-4222-8222-222222222222",
            "actor_id": "33333333-3333-4333-8333-333333333333",
            "organization_id": "44444444-4444-4444-8444-444444444444",
            "process_id": "55555555-5555-4555-8555-555555555555",
        }
        bundle = CaptureBundle.from_stage_ext(stage_ext, retry_id=retry_id)
        runtime = build_v25_runtime(
            project_root="..",
            capture_bundle=bundle,
            retry_id=retry_id,
        )

        self.assertEqual(len(bundle.captures), 5)
        self.assertEqual(len(runtime.session.captures.values()), 5)
        self.assertTrue(all(
            record.provenance == "LIVE_UPSTREAM_NATIVE_CAPTURE"
            for record in runtime.session.captures.values()
        ))
        payload = runtime.contract.native_phase_inputs("INITIAL_OPPORTUNITY", session=runtime.session)
        self.assertEqual(str(payload["process_id"]), stage_ext["process_id"])
        self.assertEqual(str(payload["identity"].tenant_id), stage_ext["tenant_projection_id"])
        self.assertEqual(payload["actor_id"], stage_ext["actor_id"])
        self.assertNotEqual(str(payload["process_id"]), "506d920c-fe62-53c0-aac8-9c1ca8ca78ed")

    def test_stage_ext_capture_bridge_rejects_bundle_from_another_retry(self):
        retry_id = "Phase 31.4 V2.5 Clean Retry 16"
        stage_ext = {
            "retry_id": retry_id,
            "tenant_id": "11111111-1111-4111-8111-111111111111",
            "tenant_projection_id": "22222222-2222-4222-8222-222222222222",
            "actor_id": "33333333-3333-4333-8333-333333333333",
            "organization_id": "44444444-4444-4444-8444-444444444444",
            "process_id": "55555555-5555-4555-8555-555555555555",
        }
        bundle = CaptureBundle.from_stage_ext(stage_ext, retry_id=retry_id)

        with self.assertRaisesRegex(RuntimeError, "capture bundle retry mismatch"):
            build_v25_runtime(project_root="..", capture_bundle=bundle, retry_id="Retry 17")

    def _contract_and_randomized_identity_captures(self):
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        captures = NativeCaptureRegistry()
        for member in contract.raw["field_bindings"]:
            identity = member["member_identity"]
            member_key = (
                f"{identity['qualified_table_or_artifact_index']}::"
                f"{identity['primary_key_or_artifact_id']}"
            )
            for field in member["fields"]:
                kind = field["value_binding"].get("kind")
                if kind not in {"CAPTURE_NATIVE_OUTPUT", "LIVE_UPSTREAM_NATIVE_CAPTURE"}:
                    continue
                value = str(uuid4())
                captures.capture(CaptureRecord(
                    logical_member=member_key, logical_field=field["name"],
                    source_service="randomized-native-producer", source_operation="produce",
                    returned_value=value, persisted_value=value, expected_type="string",
                    phase="WHOLE_GRAPH_NATIVE_IDENTITY_INDEPENDENCE",
                ))
        return contract, captures

    def test_action_plan_native_identity_is_used_by_downstream_references(self):
        contract, captures = self._contract_and_randomized_identity_captures()
        member = "qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a"
        live_id = captures.get(member, "id").returned_value
        resolver = contract.binding_registry()
        self.assertEqual(resolver.resolve(member, "id", captures), live_id)
        self.assertNotEqual(live_id, member.rsplit("::", 1)[1])

    def test_agent_run_native_identity_is_used_by_decision(self):
        contract, captures = self._contract_and_randomized_identity_captures()
        run = "qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8"
        decision = "qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63"
        self.assertEqual(
            contract.binding_registry().resolve(decision, "agent_run_id", captures),
            captures.get(run, "id").returned_value,
        )

    def test_decision_native_identity_is_used_by_action_plan_and_authorization(self):
        contract, captures = self._contract_and_randomized_identity_captures()
        decision = "qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63"
        live_id = captures.get(decision, "id").returned_value
        resolver = contract.binding_registry()
        for member in (
            "qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a",
            "qms.execution_authorization::040b78af-e99d-5154-bb8f-246a87819be5",
        ):
            self.assertEqual(resolver.resolve(member, "agent_decision_id", captures), live_id)

    def test_missing_action_plan_agent_run_and_decision_captures_fail_closed(self):
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        for member in (
            "qms.action_plan::ae682a8f-d782-5b27-a148-aa10a940e03a",
            "qms.agent_run::b87bdcde-c623-522f-a0ac-ff81f61df8e8",
            "qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63",
        ):
            with self.subTest(member=member), self.assertRaises(MissingCaptureError):
                contract.binding_registry().resolve(member, "id", NativeCaptureRegistry())

    def test_historical_identity_cannot_substitute_for_missing_capture(self):
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        member = "qms.agent_decision::2a100aee-ebdd-5807-aab0-f8c4265e8e63"
        with self.assertRaises(MissingCaptureError):
            contract.binding_registry().resolve(member, "id", NativeCaptureRegistry())

    def test_whole_graph_native_identity_independence(self):
        contract, captures = self._contract_and_randomized_identity_captures()
        resolver = contract.binding_registry()
        resolved = 0
        for member in contract.raw["field_bindings"]:
            identity = member["member_identity"]
            member_key = (
                f"{identity['qualified_table_or_artifact_index']}::"
                f"{identity['primary_key_or_artifact_id']}"
            )
            for field in member["fields"]:
                resolver.resolve(member_key, field["name"], captures)
                resolved += 1
        self.assertEqual(resolved, 1664)

    def test_uuid_audit_has_zero_exact_literal_physical_identities(self):
        contract = V25Contract.from_path(
            "../docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
        )
        literals = []
        for member in contract.raw["field_bindings"]:
            for field in member["fields"]:
                binding = field["value_binding"]
                value = binding.get("typed_value")
                if binding.get("kind") == "EXACT_LITERAL" and isinstance(value, str):
                    try:
                        __import__("uuid").UUID(value)
                    except ValueError:
                        continue
                    literals.append(value)
        self.assertEqual(literals, [])

    def test_clean_retry_4_rejects_callbacks_without_phase_results(self):
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
        self.assertTrue(all(record.status == "FAIL" for record in records))
        self.assertTrue(all("PhaseExecutionResult" in record.error for record in records))
        self.assertEqual(called, list(CleanRetry4Harness.PHASES))
