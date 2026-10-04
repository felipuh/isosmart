"""Source-backed capability activation and adapter-bound execution."""

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Protocol
from uuid import uuid4

from .agent_execution_contract import (
    AgentExecutionRequest,
    AgentExecutionResult,
    ExecutionContext,
    EvidenceReference,
    SourceDataReference,
    require_autonomy,
    source_agent_specs,
)
from .agent_runtime import AgentRunCommandService
from .agent_runtime import AgentCatalogCommandService
from .canonical import canonical_hash
from .models import AgentDefinition, CapabilityActivation, RequirementControl
from .tenant_context import trusted_tenant_context


ROOT = Path(__file__).resolve().parents[2]
SOURCE_CATALOG = ROOT / "docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Datos.json"


class CapabilityAdapter(Protocol):
    def execute(self, *, capability: str, inputs: list[Mapping[str, Any]]) -> Mapping[str, Any]: ...


class ContractCapabilityAdapter(Protocol):
    def execute(self, request: AgentExecutionRequest) -> AgentExecutionResult: ...


@dataclass(frozen=True)
class CapabilityResult:
    agent_run_id: object
    recommendation_id: object
    event_id: object
    outbox_id: object
    audit_id: object


def source_capability_catalog() -> tuple[dict[str, Any], ...]:
    document = json.loads(SOURCE_CATALOG.read_text(encoding="utf-8"))
    return tuple({
        "name": row[0],
        "module": row[1],
        "clauses": row[2],
        "autonomy": row[3],
        "purpose": row[4],
        "capability": f"source.{re.sub(r'[^a-z0-9]+', '_', row[0].lower()).strip('_')}",
    } for row in document["agents"])


class SourceCapabilityCatalogService:
    """Register every source-defined capability through the governed catalog."""

    def __init__(self, *, using="agent_catalog_curator"):
        self.using = using

    def register(self, *, model_policy_id, actor_id, trace_id):
        catalog = AgentCatalogCommandService(using=self.using)
        registered = []
        for row in source_capability_catalog():
            autonomy = max(int(value) for value in re.findall(r"[0-4]", row["autonomy"]))
            definition_id = catalog.create_agent_definition(
                agent_key=row["capability"], name=row["name"], version="source-v1",
                purpose=row["purpose"], capability=row["capability"],
                autonomy_max=autonomy, model_policy_id=model_policy_id,
                actor_id=actor_id, trace_id=trace_id,
            )
            catalog.publish_agent_definition(
                agent_definition_id=definition_id, actor_id=actor_id, trace_id=trace_id,
            )
            registered.append(definition_id)
        return tuple(registered)


class CapabilityRegistry:
    """Availability and authorization are represented by published definitions/policies."""

    def __init__(self, *, using="agent_catalog_curator", activation_using="app"):
        self.using = using
        self.activation_using = activation_using

    def get_available(self, *, capability):
        return AgentDefinition.objects.using(self.using).filter(
            capability=capability,
            status=AgentDefinition.Status.PUBLISHED,
        ).select_related("model_policy").first()

    def require_available(self, *, capability):
        definition = self.get_available(capability=capability)
        if definition is None:
            raise LookupError(f"capability is not registered and published: {capability}")
        return definition

    def activate(self, *, identity, capability, actor_id, trace_id):
        definition = self.require_available(capability=capability)
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.activation_using):
            activation, _ = CapabilityActivation.objects.using(self.activation_using).update_or_create(
                tenant_id=identity.tenant_id,
                agent_definition_id=definition.id,
                defaults={
                    "status": CapabilityActivation.Status.ACTIVE,
                    "activated_by": str(actor_id),
                    "provenance_hash": canonical_hash({
                        "tenant_id": str(identity.tenant_id),
                        "agent_definition_id": str(definition.id),
                        "capability": capability,
                    }),
                },
            )
        return activation

    def require_active(self, *, identity, capability, actor_id, trace_id):
        definition = self.require_available(capability=capability)
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.activation_using):
            if not CapabilityActivation.objects.using(self.activation_using).filter(
                tenant_id=identity.tenant_id,
                agent_definition_id=definition.id,
                status=CapabilityActivation.Status.ACTIVE,
            ).exists():
                raise PermissionError(f"capability is not activated for tenant: {capability}")
        return definition


class CapabilityInvocationService:
    """Execute a registered capability through an explicit adapter boundary."""

    def __init__(self, *, using="worker", catalog_using="agent_catalog_curator"):
        self.using = using
        self.registry = CapabilityRegistry(using=catalog_using)

    def invoke(
        self, *, identity, organization_id, capability, model_policy_id,
        requested_autonomy, model_provider, model_identifier, model_version,
        prompt_version, rule_bundle_version, inputs, actor_id, trace_id,
        adapter: CapabilityAdapter,
    ):
        definition = self.registry.require_active(
            identity=identity, capability=capability, actor_id=actor_id, trace_id=trace_id,
        )
        if str(definition.model_policy_id) != str(model_policy_id):
            raise PermissionError("capability authorization does not match its published policy")
        source_spec = next((spec for spec in source_agent_specs() if spec.agent_key == capability), None)
        if source_spec is not None:
            require_autonomy(
                requested=requested_autonomy, spec=source_spec,
                operation="recommend" if requested_autonomy < 4 else "execute_repository_local",
            )
        runtime = AgentRunCommandService(using=self.using)
        started = runtime.start_agent_run(
            identity=identity, organization_id=organization_id,
            agent_definition_id=definition.id, model_policy_id=model_policy_id,
            capability=capability, requested_autonomy=requested_autonomy,
            model_provider=model_provider, model_identifier=model_identifier,
            model_version=model_version, prompt_version=prompt_version,
            rule_bundle_version=rule_bundle_version, inputs=inputs,
            actor_id=actor_id, trace_id=trace_id,
        )
        try:
            result = adapter.execute(capability=capability, inputs=inputs)
            required = ("title", "body", "confidence", "assumptions", "basis")
            if any(key not in result for key in required):
                raise ValueError("capability adapter result is incomplete")
            completed = runtime.complete_agent_run_with_recommendation(
                identity=identity, agent_run_id=started.agent_run_id,
                title=result["title"], body=result["body"],
                confidence=result["confidence"], assumptions=result["assumptions"],
                basis=result["basis"], actor_id=actor_id,
                impact=result.get("impact"),
            )
        except Exception:
            runtime.fail_agent_run(
                identity=identity, agent_run_id=started.agent_run_id, actor_id=actor_id,
            )
            raise
        return CapabilityResult(
            completed.agent_run_id, completed.recommendation_id,
            completed.event_id, completed.outbox_id, completed.audit_id,
        )

    def build_request(
        self, *, identity, organization_id, definition, model_policy_id,
        requested_autonomy, inputs, actor_id, trace_id, model_provider="unspecified",
        model_identifier="unspecified", model_version="unspecified", prompt_version="unspecified",
        rule_bundle_version="unspecified", invocation_reason="capability.requested",
        requested_operation="recommend", correlation_id=None, causation_id=None,
        idempotency_key=None,
    ) -> AgentExecutionRequest:
        """Create the one transport contract shared by every capability."""
        evidence = tuple(EvidenceReference(item["evidence_id"]) for item in inputs)
        requirements = tuple(str(item["requirement_control_id"]) for item in inputs)
        return AgentExecutionRequest(
            request_id=uuid4(), tenant_id=identity.tenant_id,
            organization_id=organization_id, agent_definition_id=definition.id,
            agent_version=definition.version, capability=definition.capability,
            normative_baseline=None, clause_references=(), requirement_references=requirements,
            evidence_references=evidence,
            source_data_references=tuple(SourceDataReference(str(item["evidence_id"])) for item in inputs),
            invocation_reason=invocation_reason, execution_context=ExecutionContext({
                "tenant_id": str(identity.tenant_id), "organization_id": str(organization_id),
            }), requested_operation=requested_operation, correlation_id=correlation_id,
            causation_id=causation_id, idempotency_key=idempotency_key or str(uuid4()),
            provenance_context={"source": "iso-smart-capability-runtime", "actor_id": str(actor_id)},
            model_policy_id=model_policy_id, requested_autonomy=requested_autonomy,
            model_provider=model_provider, model_identifier=model_identifier,
            model_version=model_version, prompt_version=prompt_version,
            rule_bundle_version=rule_bundle_version, inputs=tuple(inputs),
            actor_id=str(actor_id), trace_id=trace_id,
        )

    def invoke_source(self, *, identity, organization_id, capability, model_policy_id,
                      requested_autonomy, inputs, actor_id, trace_id, model_provider,
                      model_identifier, model_version, prompt_version, rule_bundle_version):
        """Dispatch only implemented source adapters; persist actual typed results."""
        from .source_agent_adapters import SOURCE_ADAPTERS
        from .agent_execution_contract import ExecutionStatus
        from .canonical import canonical_json

        adapter_type = SOURCE_ADAPTERS.get(capability)
        if adapter_type is None:
            raise LookupError(f"no semantic source adapter: {capability}")
        definition = self.registry.require_active(
            identity=identity, capability=capability, actor_id=actor_id, trace_id=trace_id,
        )
        spec = next(spec for spec in source_agent_specs() if spec.agent_key == capability)
        # Evaluation at A4 remains advisory; it does not invoke an action executor.
        require_autonomy(requested=requested_autonomy, spec=spec,
                         operation="evaluate_policy" if requested_autonomy == 4 else "recommend")
        request = self.build_request(
            identity=identity, organization_id=organization_id, definition=definition,
            model_policy_id=model_policy_id, requested_autonomy=requested_autonomy,
            inputs=inputs, actor_id=actor_id, trace_id=trace_id,
            model_provider=model_provider, model_identifier=model_identifier,
            model_version=model_version, prompt_version=prompt_version,
            rule_bundle_version=rule_bundle_version, requested_operation="evaluate_policy",
        )
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            clauses = []
            for item in inputs:
                requirement = RequirementControl.objects.using(self.using).select_related("clause").get(
                    id=item["requirement_control_id"], standard_edition_id=item["standard_edition_id"],
                )
                code = requirement.clause.code
                bound = code in spec.related_references
                if "4-10" in spec.related_references:
                    bound = code.split(".")[0] in {str(number) for number in range(4, 11)}
                if not bound:
                    raise ValueError("input clause is outside the source agent binding")
                clauses.append(code)
        request = replace(request, clause_references=tuple(sorted(set(clauses))))
        runtime = AgentRunCommandService(using=self.using)
        started = runtime.start_agent_run(
            identity=identity, organization_id=organization_id, agent_definition_id=definition.id,
            model_policy_id=model_policy_id, capability=capability, requested_autonomy=requested_autonomy,
            model_provider=model_provider, model_identifier=model_identifier, model_version=model_version,
            prompt_version=prompt_version, rule_bundle_version=rule_bundle_version,
            inputs=inputs, actor_id=actor_id, trace_id=trace_id,
        )
        try:
            result = adapter_type(identity=identity, run_id=started.agent_run_id, using=self.using).execute(request)
            self.validate_result(request, result)
            if result.status != ExecutionStatus.COMPLETED or str(result.run_id) != str(started.agent_run_id):
                raise ValueError("source adapter did not complete the bound run")
            if result.result_scope is not None:
                if not result.not_normative_assessment:
                    raise ValueError("non-normative adapter must explicitly disclaim normative assessment")
                completed = runtime.complete_agent_run_with_result(
                    identity=identity, agent_run_id=started.agent_run_id,
                    result_payload={
                        "result_scope": result.result_scope,
                        "not_normative_assessment": result.not_normative_assessment,
                        "semantic_result": result.semantic_result,
                        "findings": [{"code": finding.code, "summary": finding.summary}
                                     for finding in result.findings],
                        "evidence_consumed": [str(item.evidence_id) for item in result.evidence_consumed],
                        "deterministic_rule_results": result.deterministic_rule_results,
                        "warnings": result.warnings,
                        "provenance": result.provenance,
                    },
                    actor_id=actor_id,
                )
                return replace(
                    result,
                    audit_references=(*result.audit_references, str(completed.audit_id)),
                    emitted_events=(*result.emitted_events, str(completed.event_id)),
                )
            completed = runtime.complete_agent_run_with_recommendation(
                identity=identity, agent_run_id=started.agent_run_id,
                title=spec.source_name, body=canonical_json({
                    "findings": [finding.summary for finding in result.findings],
                    "rule_results": result.deterministic_rule_results,
                    "provenance": result.provenance, "clauses": request.clause_references,
                    "warnings": result.warnings,
                }), confidence="1.0000", assumptions=["Repository algorithm executed; confidence is not compliance probability; no action authorized"],
                basis=list(result.recommendation_basis), actor_id=actor_id,
            )
        except Exception:
            runtime.fail_agent_run(
                identity=identity, agent_run_id=started.agent_run_id, actor_id=actor_id,
                failure_code="source_adapter_failed",
            )
            raise
        return replace(result, recommendations=(str(completed.recommendation_id),),
                       audit_references=(*result.audit_references, str(completed.audit_id)),
                       emitted_events=(*result.emitted_events, str(completed.event_id)))

    @staticmethod
    def validate_result(request: AgentExecutionRequest, result: AgentExecutionResult) -> AgentExecutionResult:
        if str(result.agent_definition_id) != str(request.agent_definition_id):
            raise ValueError("execution result belongs to another agent definition")
        result.assert_source_backed(request)
        return result
