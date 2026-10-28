from datetime import datetime, timezone
from uuid import uuid4

from django.test import SimpleTestCase

from foundation.agent_execution_contract import (
    AgentExecutionRequest,
    AgentExecutionResult,
    AgentExecutionSpec,
    Autonomy,
    ExecutionContext,
    ExecutionStatus,
    EvidenceReference,
    Finding,
    execution_contract_report,
    require_autonomy,
    source_agent_specs,
)


class AgentExecutionContractTests(SimpleTestCase):
    def request(self, *, evidence=True, operation="recommend", autonomy=2):
        return AgentExecutionRequest(
            request_id=uuid4(), tenant_id=uuid4(), organization_id=uuid4(),
            agent_definition_id=uuid4(), agent_version="source-v1",
            capability="source.context_twin_orchestrator", normative_baseline="synthetic-v1",
            clause_references=("4.1",), requirement_references=(str(uuid4()),),
            evidence_references=(EvidenceReference(uuid4()),) if evidence else (),
            source_data_references=(), invocation_reason="test",
            execution_context=ExecutionContext({"tenant": "synthetic"}),
            requested_operation=operation, correlation_id=None, causation_id=None,
            idempotency_key=str(uuid4()), provenance_context={"source": "test"},
            model_policy_id=uuid4(), requested_autonomy=autonomy,
            model_provider="fixture", model_identifier="fixture-model",
            model_version="1", prompt_version="1", rule_bundle_version="1",
            inputs=({"evidence_id": str(uuid4())},), actor_id="fixture-actor", trace_id=uuid4(),
        )

    def test_all_source_agents_have_unique_typed_specs_and_bindings(self):
        specs = source_agent_specs()
        self.assertEqual(len(specs), 33)
        self.assertEqual(len({spec.agent_key for spec in specs}), 33)
        self.assertTrue(all(isinstance(spec, AgentExecutionSpec) for spec in specs))
        self.assertTrue(all(spec.capability_bindings for spec in specs))
        self.assertEqual(execution_contract_report()["missing"], 0)

    def test_autonomy_cannot_exceed_source_ceiling_or_execute_implicitly(self):
        spec = next(spec for spec in source_agent_specs() if spec.source_name == "Context Twin Orchestrator")
        with self.assertRaises(PermissionError):
            require_autonomy(requested=4, spec=spec, operation="recommend")
        with self.assertRaises(PermissionError):
            require_autonomy(requested=3, spec=spec, operation="execute_repository_local")
        require_autonomy(requested=3, spec=spec, operation="recommend")

    def test_no_evidence_no_assertion_is_fail_closed(self):
        request = self.request(evidence=False)
        result = AgentExecutionResult(
            run_id=uuid4(), agent_definition_id=request.agent_definition_id,
            status=ExecutionStatus.COMPLETED, started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            findings=(Finding("NORMATIVE", "unsupported conclusion", "PASS"),),
            deterministic_rule_results=(),
        )
        with self.assertRaisesRegex(ValueError, "NO_EVIDENCE_NO_ASSERTION"):
            result.assert_source_backed(request)

    def test_failed_execution_cannot_emit_evidence_or_recommendation(self):
        with self.assertRaises(ValueError):
            AgentExecutionResult(
                run_id=uuid4(), agent_definition_id=uuid4(), status=ExecutionStatus.FAILED,
                started_at=None, completed_at=None,
                evidence_produced=(EvidenceReference(uuid4()),),
            )

    def test_result_contract_accepts_advisory_unresolved_output(self):
        request = self.request()
        result = AgentExecutionResult(
            run_id=uuid4(), agent_definition_id=request.agent_definition_id,
            status=ExecutionStatus.UNRESOLVED, started_at=None, completed_at=None,
            warnings=("insufficient source evidence",),
        )
        result.assert_source_backed(request)
        self.assertEqual(result.status, ExecutionStatus.UNRESOLVED)

    def test_autonomy_values_are_bounded(self):
        with self.assertRaises(ValueError):
            self.request(autonomy=int(Autonomy.EXECUTE) + 1)

    def test_invalid_autonomy_types_and_negative_levels_are_rejected(self):
        for level in (True, -1, 1.5, "2"):
            with self.subTest(level=level), self.assertRaises(ValueError):
                self.request(autonomy=level)

    def test_result_cannot_claim_unprovided_evidence(self):
        request = self.request()
        result = AgentExecutionResult(
            run_id=uuid4(), agent_definition_id=request.agent_definition_id,
            status=ExecutionStatus.COMPLETED, started_at=None, completed_at=None,
            evidence_consumed=(EvidenceReference(uuid4()),),
        )
        with self.assertRaisesRegex(ValueError, "provenance"):
            result.assert_source_backed(request)
