"""Phase 11 catalog and governed synthetic AgentRun command boundaries."""

import json
from dataclasses import dataclass
from uuid import UUID, uuid4

from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    AgentCatalogCurationAudit,
    AgentDefinition,
    AgentRun,
    AgentRunInput,
    AgentRunRecommendation,
    DomainEvent,
    Evidence,
    KnowledgeLayerRule,
    ModelPolicy,
    Organization,
    RequirementControl,
    StandardEdition,
    TransactionalOutbox,
)
from .recommendation import RecommendationCommandService
from .tenant_context import trusted_tenant_context


EVENT_CONTRACTS = {
    "agent_run.started": 1,
    "agent_run.completed": 1,
    "agent_run.failed": 1,
}


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _json_list(value, name):
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a list")
    return [_required(item, f"{name}[{index}]") for index, item in enumerate(value)]


def _json_object(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _autonomy(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 4:
        raise ValueError(f"{name} must be an integer from A0 through A4")
    return value


class AgentCatalogCommandService:
    """Narrow write path for the distinct agent catalog curator principal."""

    def __init__(self, *, using="agent_catalog_curator"):
        self.using = using

    def _audit(self, *, action, entity_type, entity_id, actor_id, trace_id, payload):
        AgentCatalogCurationAudit.objects.using(self.using).create(
            id=uuid4(), action=action, entity_type=entity_type, entity_id=entity_id,
            actor_id=_required(str(actor_id), "actor_id"), trace_id=UUID(str(trace_id)),
            payload_hash=canonical_hash(payload), occurred_at=timezone.now(),
        )

    def create_model_policy(
        self, *, policy_key, version, approved_models, data_classes, guardrails,
        human_gate_rules, actor_id, trace_id,
    ):
        entity_id = uuid4()
        state = {
            "lineage_id": str(entity_id), "policy_key": _required(policy_key, "policy_key"),
            "version": _required(version, "version"),
            "approved_models": _json_list(approved_models, "approved_models"),
            "data_classes": _json_list(data_classes, "data_classes"),
            "guardrails": _json_object(guardrails, "guardrails"),
            "human_gate_rules": _json_object(human_gate_rules, "human_gate_rules"),
            "status": ModelPolicy.Status.DRAFT,
        }
        from django.db import transaction
        with transaction.atomic(using=self.using):
            ModelPolicy.objects.using(self.using).create(id=entity_id, **state)
            self._audit(action="model_policy.created", entity_type="model_policy",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def revise_model_policy(
        self, *, previous_revision_id, version, approved_models, data_classes,
        guardrails, human_gate_rules, actor_id, trace_id,
    ):
        from django.db import transaction
        entity_id = uuid4()
        with transaction.atomic(using=self.using):
            previous = ModelPolicy.objects.using(self.using).select_for_update().get(id=previous_revision_id)
            if previous.status != ModelPolicy.Status.PUBLISHED:
                raise ValueError("only a published ModelPolicy can be revised")
            if ModelPolicy.objects.using(self.using).filter(previous_revision_id=previous.id).exists():
                raise ValueError("only the current ModelPolicy revision can be revised")
            state = {
                "lineage_id": str(previous.lineage_id), "policy_key": previous.policy_key,
                "version": _required(version, "version"),
                "previous_revision_id": str(previous.id),
                "approved_models": _json_list(approved_models, "approved_models"),
                "data_classes": _json_list(data_classes, "data_classes"),
                "guardrails": _json_object(guardrails, "guardrails"),
                "human_gate_rules": _json_object(human_gate_rules, "human_gate_rules"),
                "status": ModelPolicy.Status.DRAFT,
            }
            ModelPolicy.objects.using(self.using).create(id=entity_id, **state)
            self._audit(action="model_policy.revised", entity_type="model_policy",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def publish_model_policy(self, *, model_policy_id, actor_id, trace_id, fail_before_commit=False):
        return self._publish(ModelPolicy, model_policy_id, "model_policy", actor_id, trace_id, fail_before_commit)

    def create_agent_definition(
        self, *, agent_key, name, version, purpose, capability, autonomy_max,
        model_policy_id, actor_id, trace_id,
    ):
        from django.db import transaction
        entity_id = uuid4()
        state = {
            "lineage_id": str(entity_id), "agent_key": _required(agent_key, "agent_key"),
            "name": _required(name, "name"), "version": _required(version, "version"),
            "purpose": _required(purpose, "purpose"),
            "capability": _required(capability, "capability"),
            "autonomy_max": _autonomy(autonomy_max, "autonomy_max"),
            "model_policy_id": str(model_policy_id), "status": AgentDefinition.Status.DRAFT,
        }
        with transaction.atomic(using=self.using):
            ModelPolicy.objects.using(self.using).get(id=model_policy_id, status=ModelPolicy.Status.PUBLISHED)
            AgentDefinition.objects.using(self.using).create(id=entity_id, **state)
            self._audit(action="agent_definition.created", entity_type="agent_definition",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def revise_agent_definition(
        self, *, previous_revision_id, version, purpose, capability, autonomy_max,
        model_policy_id, actor_id, trace_id,
    ):
        from django.db import transaction
        entity_id = uuid4()
        with transaction.atomic(using=self.using):
            previous = AgentDefinition.objects.using(self.using).select_for_update().get(id=previous_revision_id)
            if previous.status != AgentDefinition.Status.PUBLISHED:
                raise ValueError("only a published AgentDefinition can be revised")
            if AgentDefinition.objects.using(self.using).filter(previous_revision_id=previous.id).exists():
                raise ValueError("only the current AgentDefinition revision can be revised")
            ModelPolicy.objects.using(self.using).get(id=model_policy_id, status=ModelPolicy.Status.PUBLISHED)
            state = {
                "lineage_id": str(previous.lineage_id), "agent_key": previous.agent_key,
                "name": previous.name, "version": _required(version, "version"),
                "previous_revision_id": str(previous.id), "purpose": _required(purpose, "purpose"),
                "capability": _required(capability, "capability"),
                "autonomy_max": _autonomy(autonomy_max, "autonomy_max"),
                "model_policy_id": str(model_policy_id), "status": AgentDefinition.Status.DRAFT,
            }
            AgentDefinition.objects.using(self.using).create(id=entity_id, **state)
            self._audit(action="agent_definition.revised", entity_type="agent_definition",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def publish_agent_definition(self, *, agent_definition_id, actor_id, trace_id, fail_before_commit=False):
        return self._publish(AgentDefinition, agent_definition_id, "agent_definition", actor_id, trace_id, fail_before_commit)

    def _publish(self, model, entity_id, entity_type, actor_id, trace_id, fail_before_commit):
        from django.db import transaction
        with transaction.atomic(using=self.using):
            row = model.objects.using(self.using).select_for_update().get(id=entity_id)
            if row.status != model.Status.DRAFT:
                raise ValueError(f"only a draft {entity_type} can be published")
            row.status = model.Status.PUBLISHED
            row.published_at = timezone.now()
            row.save(using=self.using, update_fields=("status", "published_at"))
            self._audit(action=f"{entity_type}.published", entity_type=entity_type,
                        entity_id=row.id, actor_id=actor_id, trace_id=trace_id,
                        payload={"version": row.version, "status": row.status,
                                 "published_at": row.published_at.isoformat()})
            if fail_before_commit:
                raise RuntimeError(f"deliberate Phase 11 {entity_type} publication rollback")
        return row.id


@dataclass(frozen=True)
class AgentRunStartResult:
    agent_run_id: UUID
    input_ids: tuple[UUID, ...]
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID


@dataclass(frozen=True)
class AgentRunCompletionResult:
    agent_run_id: UUID
    recommendation_id: UUID
    link_id: UUID
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID


class AgentRunCommandService:
    """Governed recordkeeping only: no provider call, tool call or business execution."""

    def __init__(self, *, using="worker"):
        self.using = using

    def _event_outbox_audit(self, *, identity, run, event_type, actor_id, occurred_at, payload):
        event_id = uuid4()
        aggregate_version = (
            DomainEvent.objects.using(self.using)
            .filter(aggregate_type="agent_run", aggregate_id=run.id)
            .aggregate(value=Max("aggregate_version"))["value"] or 0
        ) + 1
        canonical_payload = json.loads(canonical_json(payload))["value"]
        DomainEvent.objects.using(self.using).create(
            event_id=event_id, tenant_id=identity.tenant_id, event_type=event_type,
            schema_version=EVENT_CONTRACTS[event_type], aggregate_type="agent_run",
            aggregate_id=run.id, aggregate_version=aggregate_version,
            occurred_at=occurred_at, trace_id=run.trace_id,
            correlation_id=run.correlation_id, causation_id=run.causation_id,
            source="iso-smart-agent-runtime", payload=canonical_payload,
            payload_hash=canonical_hash(canonical_payload),
        )
        outbox = TransactionalOutbox.objects.using(self.using).create(
            tenant_id=identity.tenant_id, domain_event_id=event_id,
            status=TransactionalOutbox.Status.PENDING, publish_attempts=0,
            available_at=occurred_at,
        )
        audit_id = AuditWriterService(using=self.using).append(AuditAppend(
            tenant_id=identity.tenant_id, stream_type="agent_run", stream_id=run.id,
            actor_type="worker", actor_id=str(actor_id), action=event_type,
            entity_type="agent_run", entity_id=run.id, trace_id=run.trace_id,
            occurred_at=occurred_at, after_hash=canonical_hash(payload),
            metadata={"event_id": str(event_id), "schema_version": 1,
                      "status": run.status, "provenance_hash": canonical_hash(payload)},
        ))
        return event_id, outbox.id, audit_id

    def start_agent_run(
        self, *, identity, organization_id, agent_definition_id, model_policy_id,
        capability, requested_autonomy, model_provider, model_identifier,
        model_version, prompt_version, rule_bundle_version, inputs, actor_id,
        trace_id, dataset_version_reference=None, embedding_namespace=None,
        correlation_id=None, causation_id=None, fail_before_commit=False,
    ):
        trace_id = UUID(str(trace_id)); started_at = timezone.now(); run_id = uuid4()
        requested_autonomy = _autonomy(requested_autonomy, "requested_autonomy")
        if not isinstance(inputs, (list, tuple)) or not inputs:
            raise ValueError("AgentRun requires at least one frozen input bundle")
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=trace_id, using=self.using):
            Organization.objects.using(self.using).get(id=organization_id)
            definition = AgentDefinition.objects.using(self.using).get(
                id=agent_definition_id, status=AgentDefinition.Status.PUBLISHED,
            )
            policy = ModelPolicy.objects.using(self.using).get(
                id=model_policy_id, status=ModelPolicy.Status.PUBLISHED,
            )
            normalized_capability = _required(capability, "capability")
            normalized_model = _required(model_identifier, "model_identifier")
            if definition.model_policy_id != policy.id or definition.capability != normalized_capability:
                raise ValueError("requested run is incompatible with exact AgentDefinition/ModelPolicy")
            allowed_capabilities = policy.guardrails.get("allowed_capabilities", [])
            if allowed_capabilities and normalized_capability not in allowed_capabilities:
                raise ValueError("requested capability is disallowed by ModelPolicy")
            if normalized_model not in policy.approved_models:
                raise ValueError("requested model is not approved by ModelPolicy")
            policy_ceiling = policy.guardrails.get("autonomy_max", definition.autonomy_max)
            effective_ceiling = min(definition.autonomy_max, _autonomy(policy_ceiling, "guardrails.autonomy_max"))
            if requested_autonomy > effective_ceiling:
                raise ValueError("requested autonomy exceeds governed effective ceiling")
            run = AgentRun.objects.using(self.using).create(
                id=run_id, tenant_id=identity.tenant_id, organization_id=organization_id,
                agent_definition_id=definition.id, model_policy_id=policy.id,
                capability=normalized_capability, status=AgentRun.Status.RUNNING,
                requested_autonomy=requested_autonomy, effective_autonomy_ceiling=effective_ceiling,
                model_provider=model_provider, model_identifier=normalized_model,
                model_version=_required(model_version, "model_version"),
                prompt_version=_required(prompt_version, "prompt_version"),
                rule_bundle_version=_required(rule_bundle_version, "rule_bundle_version"),
                dataset_version_reference=dataset_version_reference,
                embedding_namespace=embedding_namespace, trace_id=trace_id,
                correlation_id=correlation_id, causation_id=causation_id, started_at=started_at,
            )
            input_rows = []
            snapshots = []
            for index, item in enumerate(inputs):
                if not isinstance(item, dict):
                    raise ValueError(f"inputs[{index}] must be an object")
                edition = StandardEdition.objects.using(self.using).get(
                    id=item.get("standard_edition_id"), status=StandardEdition.Status.PUBLISHED,
                )
                requirement = RequirementControl.objects.using(self.using).get(
                    id=item.get("requirement_control_id"), standard_edition_id=edition.id,
                )
                rule = KnowledgeLayerRule.objects.using(self.using).get(
                    id=item.get("knowledge_layer_rule_id"), status=KnowledgeLayerRule.Status.PUBLISHED,
                )
                evidence = Evidence.objects.using(self.using).get(id=item.get("evidence_id"))
                row = AgentRunInput.objects.using(self.using).create(
                    id=uuid4(), tenant_id=identity.tenant_id, organization_id=organization_id,
                    agent_run_id=run.id, standard_edition_id=edition.id,
                    requirement_control_id=requirement.id, knowledge_layer_rule_id=rule.id,
                    evidence_id=evidence.id,
                )
                input_rows.append(row)
                snapshots.append({
                    "input_id": str(row.id), "standard_edition_id": str(edition.id),
                    "requirement_control_id": str(requirement.id),
                    "knowledge_layer_rule_id": str(rule.id), "knowledge_layer_rule_version": rule.version,
                    "evidence_id": str(evidence.id), "evidence_lineage_id": str(evidence.lineage_id),
                    "evidence_revision": evidence.revision,
                })
            state = self._state(run, inputs=snapshots, recommendation_id=None)
            event_id, outbox_id, audit_id = self._event_outbox_audit(
                identity=identity, run=run, event_type="agent_run.started", actor_id=actor_id,
                occurred_at=started_at, payload=state,
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 11 AgentRun start rollback")
            return AgentRunStartResult(run.id, tuple(row.id for row in input_rows), event_id, outbox_id, audit_id)

    def complete_agent_run_with_recommendation(
        self, *, identity, agent_run_id, title, body, confidence, assumptions,
        basis, actor_id, impact=None, fail_before_commit=False,
    ):
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=uuid4(), using=self.using):
            run = AgentRun.objects.using(self.using).select_for_update().get(id=agent_run_id)
            if run.status != AgentRun.Status.RUNNING:
                raise ValueError("only a running AgentRun can complete")
            expected = {
                (str(row.standard_edition_id), str(row.requirement_control_id),
                 str(row.knowledge_layer_rule_id), str(row.evidence_id))
                for row in AgentRunInput.objects.using(self.using).filter(agent_run_id=run.id)
            }
            supplied = {
                (str(item.get("standard_edition_id")), str(item.get("requirement_control_id")),
                 str(item.get("knowledge_layer_rule_id")), str(item.get("evidence_id")))
                for item in basis
            }
            if expected != supplied:
                raise ValueError("RecommendationBasis must exactly match frozen AgentRun inputs")
            governed_basis = [dict(
                item, model_provider=run.model_provider, model_identifier=run.model_identifier,
                model_version=run.model_version, prompt_version=run.prompt_version,
                rule_bundle_version=run.rule_bundle_version,
                dataset_version_reference=run.dataset_version_reference,
                embedding_namespace=run.embedding_namespace,
            ) for item in basis]
            recommendation_result = RecommendationCommandService(using=self.using)._create_recommendation_in_current_transaction(
                identity=identity, organization_id=run.organization_id, title=title, body=body,
                confidence=confidence, assumptions=assumptions,
                intended_autonomy=run.requested_autonomy, basis=governed_basis,
                actor_id=actor_id, trace_id=run.trace_id, impact=impact,
            )
            link = AgentRunRecommendation.objects.using(self.using).create(
                id=uuid4(), tenant_id=identity.tenant_id, organization_id=run.organization_id,
                agent_run_id=run.id, recommendation_id=recommendation_result.recommendation_id,
            )
            run.status = AgentRun.Status.COMPLETED
            run.completed_at = timezone.now()
            run.save(using=self.using, update_fields=("status", "completed_at"))
            snapshots = [
                {"input_id": str(row.id), "standard_edition_id": str(row.standard_edition_id),
                 "requirement_control_id": str(row.requirement_control_id),
                 "knowledge_layer_rule_id": str(row.knowledge_layer_rule_id),
                 "evidence_id": str(row.evidence_id)}
                for row in AgentRunInput.objects.using(self.using).filter(agent_run_id=run.id)
            ]
            state = self._state(run, inputs=snapshots,
                                recommendation_id=recommendation_result.recommendation_id)
            event_id, outbox_id, audit_id = self._event_outbox_audit(
                identity=identity, run=run, event_type="agent_run.completed", actor_id=actor_id,
                occurred_at=run.completed_at, payload=state,
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 11 completion rollback after Recommendation/Audit preparation")
            return AgentRunCompletionResult(run.id, recommendation_result.recommendation_id,
                                            link.id, event_id, outbox_id, audit_id)

    def fail_agent_run(self, *, identity, agent_run_id, actor_id):
        with trusted_tenant_context(identity, actor_id=actor_id, trace_id=uuid4(), using=self.using):
            run = AgentRun.objects.using(self.using).select_for_update().get(id=agent_run_id)
            if run.status != AgentRun.Status.RUNNING:
                raise ValueError("only a running AgentRun can fail")
            run.status = AgentRun.Status.FAILED; run.completed_at = timezone.now()
            run.save(using=self.using, update_fields=("status", "completed_at"))
            snapshots = [
                {"input_id": str(row.id), "standard_edition_id": str(row.standard_edition_id),
                 "requirement_control_id": str(row.requirement_control_id),
                 "knowledge_layer_rule_id": str(row.knowledge_layer_rule_id),
                 "evidence_id": str(row.evidence_id)}
                for row in AgentRunInput.objects.using(self.using).filter(agent_run_id=run.id)
            ]
            state = self._state(run, inputs=snapshots, recommendation_id=None)
            return self._event_outbox_audit(identity=identity, run=run, event_type="agent_run.failed",
                                            actor_id=actor_id, occurred_at=run.completed_at, payload=state)

    @staticmethod
    def _state(run, *, inputs, recommendation_id):
        return {
            "agent_run_id": str(run.id), "organization_id": str(run.organization_id),
            "agent_definition_id": str(run.agent_definition_id),
            "model_policy_id": str(run.model_policy_id), "capability": run.capability,
            "status": run.status, "requested_autonomy": f"A{run.requested_autonomy}",
            "effective_autonomy_ceiling": f"A{run.effective_autonomy_ceiling}",
            "deterministic_rules": {"rule_bundle_version": run.rule_bundle_version,
                                    "knowledge_layer_rule_ids": [x["knowledge_layer_rule_id"] for x in inputs]},
            "retrieval_context": {"exact_references": inputs,
                                  "dataset_version_reference": run.dataset_version_reference,
                                  "embedding_namespace": run.embedding_namespace},
            "model_inference": {"provider": run.model_provider,
                                "model_identifier": run.model_identifier,
                                "model_version": run.model_version,
                                "prompt_version": run.prompt_version,
                                "synthetic_only": True},
            "governance_policy": {"model_policy_id": str(run.model_policy_id)},
            "recommendation_id": str(recommendation_id) if recommendation_id else None,
            "trace_id": str(run.trace_id), "correlation_id": str(run.correlation_id) if run.correlation_id else None,
            "causation_id": str(run.causation_id) if run.causation_id else None,
            "started_at": run.started_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "no_execution": True,
        }
