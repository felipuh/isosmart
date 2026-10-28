"""Phase 10 commands for advisory recommendations and frozen provenance."""

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from django.db import connections
from django.db.models import Max
from django.utils import timezone

from .audit import AuditAppend, AuditWriterService
from .canonical import canonical_hash, canonical_json
from .models import (
    DomainEvent,
    Evidence,
    KnowledgeLayerRule,
    Organization,
    Recommendation,
    RecommendationBasis,
    RequirementControl,
    StandardEdition,
    TransactionalOutbox,
)
from .tenant_context import trusted_tenant_context


EVENT_CONTRACTS = {"recommendation.created": 1}


@dataclass(frozen=True)
class RecommendationCreationResult:
    recommendation_id: UUID
    basis_ids: tuple[UUID, ...]
    event_id: UUID
    outbox_id: UUID
    audit_id: UUID
    trace_id: UUID


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _confidence(value):
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("confidence must be a normalized decimal in [0,1]") from exc
    if not normalized.is_finite() or normalized < 0 or normalized > 1:
        raise ValueError("confidence must be a normalized decimal in [0,1]")
    return normalized


def _assumptions(value):
    if not isinstance(value, (list, tuple)):
        raise ValueError("assumptions must be a list of strings")
    return [_required(item, f"assumptions[{index}]") for index, item in enumerate(value)]


class RecommendationCommandService:
    """The only Phase 10 material command; it persists advice and never executes it."""

    def __init__(self, *, using="app"):
        self.using = using

    def create_recommendation(
        self, *, identity, organization_id, title, body, confidence, assumptions,
        intended_autonomy, basis, actor_id, trace_id, impact=None,
        fail_before_commit=False,
    ):
        trace_id = UUID(str(trace_id))
        with trusted_tenant_context(
            identity, actor_id=actor_id, trace_id=trace_id, using=self.using,
        ):
            return self._create_recommendation_in_current_transaction(
                identity=identity, organization_id=organization_id, title=title,
                body=body, confidence=confidence, assumptions=assumptions,
                intended_autonomy=intended_autonomy, basis=basis, actor_id=actor_id,
                trace_id=trace_id, impact=impact, fail_before_commit=fail_before_commit,
            )

    def _create_recommendation_in_current_transaction(
        self, *, identity, organization_id, title, body, confidence, assumptions,
        intended_autonomy, basis, actor_id, trace_id, impact=None,
        fail_before_commit=False,
    ):
        """Internal composition seam used by a larger governed transaction.

        It verifies the active transaction-local tenant instead of opening a
        competing transaction boundary. External callers use
        ``create_recommendation``.
        """
        trace_id = UUID(str(trace_id))
        connection = connections[self.using]
        if not connection.in_atomic_block:
            raise RuntimeError("governed Recommendation composition requires an active transaction")
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('app.tenant_id', true)")
            if cursor.fetchone()[0] != str(identity.tenant_id):
                raise RuntimeError("governed Recommendation tenant context mismatch")
        occurred_at = timezone.now()
        recommendation_id = uuid4()
        normalized_confidence = _confidence(confidence)
        normalized_assumptions = _assumptions(assumptions)
        if isinstance(intended_autonomy, bool) or not isinstance(intended_autonomy, int):
            raise ValueError("intended_autonomy must be an integer from A0 through A4")
        if intended_autonomy < 0 or intended_autonomy > 4:
            raise ValueError("intended_autonomy must be an integer from A0 through A4")
        if not isinstance(basis, (list, tuple)) or not basis:
            raise ValueError("a governed recommendation requires at least one basis row")

        Organization.objects.using(self.using).get(id=organization_id)
        recommendation = Recommendation.objects.using(self.using).create(
            id=recommendation_id,
            tenant_id=identity.tenant_id,
            organization_id=organization_id,
            title=_required(title, "title"),
            body=_required(body, "body"),
            confidence=normalized_confidence,
            assumptions=normalized_assumptions,
            impact=impact,
            status=Recommendation.Status.PROPOSED,
            intended_autonomy=intended_autonomy,
        )

        basis_rows = []
        basis_snapshots = []
        for index, item in enumerate(basis):
            if not isinstance(item, dict):
                raise ValueError(f"basis[{index}] must be an object")
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
            basis_id = uuid4()
            row = RecommendationBasis.objects.using(self.using).create(
                id=basis_id, tenant_id=identity.tenant_id, organization_id=organization_id,
                recommendation_id=recommendation.id, standard_edition_id=edition.id,
                requirement_control_id=requirement.id, knowledge_layer_rule_id=rule.id,
                evidence_id=evidence.id,
                rationale=_required(item.get("rationale"), f"basis[{index}].rationale"),
                model_provider=item.get("model_provider"),
                model_identifier=_required(item.get("model_identifier"), f"basis[{index}].model_identifier"),
                model_version=_required(item.get("model_version"), f"basis[{index}].model_version"),
                prompt_version=_required(item.get("prompt_version"), f"basis[{index}].prompt_version"),
                rule_bundle_version=_required(item.get("rule_bundle_version"), f"basis[{index}].rule_bundle_version"),
                dataset_version_reference=item.get("dataset_version_reference"),
                embedding_namespace=item.get("embedding_namespace"), trace_id=trace_id,
            )
            snapshot = {
                "basis_id": str(row.id), "standard_edition_id": str(row.standard_edition_id),
                "requirement_control_id": str(row.requirement_control_id),
                "knowledge_layer_rule_id": str(row.knowledge_layer_rule_id),
                "knowledge_layer_rule_version": rule.version, "evidence_id": str(row.evidence_id),
                "evidence_lineage_id": str(evidence.lineage_id), "evidence_revision": evidence.revision,
                "rationale": row.rationale, "model_provider": row.model_provider,
                "model_identifier": row.model_identifier, "model_version": row.model_version,
                "prompt_version": row.prompt_version, "rule_bundle_version": row.rule_bundle_version,
                "dataset_version_reference": row.dataset_version_reference,
                "embedding_namespace": row.embedding_namespace, "trace_id": str(row.trace_id),
            }
            basis_rows.append(row)
            basis_snapshots.append(snapshot)

        state = {
            "recommendation_id": str(recommendation.id), "organization_id": str(recommendation.organization_id),
            "title": recommendation.title, "body": recommendation.body,
            "confidence": str(recommendation.confidence),
            "confidence_semantics": "normalized_indicator_not_statistical_probability",
            "assumptions": recommendation.assumptions, "impact": recommendation.impact,
            "status": recommendation.status, "intended_autonomy": f"A{recommendation.intended_autonomy}",
            "advisory_only": True, "basis": basis_snapshots,
        }
        payload = json.loads(canonical_json(state))["value"]
        event_id = uuid4()
        aggregate_version = (
            DomainEvent.objects.using(self.using)
            .filter(aggregate_type="recommendation", aggregate_id=recommendation.id)
            .aggregate(value=Max("aggregate_version"))["value"] or 0
        ) + 1
        DomainEvent.objects.using(self.using).create(
            event_id=event_id, tenant_id=identity.tenant_id, event_type="recommendation.created",
            schema_version=EVENT_CONTRACTS["recommendation.created"], aggregate_type="recommendation",
            aggregate_id=recommendation.id, aggregate_version=aggregate_version,
            occurred_at=occurred_at, trace_id=trace_id, source="iso-smart-qms",
            payload=payload, payload_hash=canonical_hash(payload),
        )
        outbox = TransactionalOutbox.objects.using(self.using).create(
            tenant_id=identity.tenant_id, domain_event_id=event_id,
            status=TransactionalOutbox.Status.PENDING, publish_attempts=0, available_at=occurred_at,
        )
        audit_id = AuditWriterService(using=self.using).append(AuditAppend(
            tenant_id=identity.tenant_id, stream_type="recommendation", stream_id=recommendation.id,
            actor_type="user", actor_id=str(actor_id), action="recommendation.created",
            entity_type="recommendation", entity_id=recommendation.id, trace_id=trace_id,
            occurred_at=occurred_at, after_hash=canonical_hash(state),
            metadata={"event_id": str(event_id), "schema_version": 1,
                      "status": recommendation.status,
                      "basis": [{"basis_id": item["basis_id"], "hash": canonical_hash(item)}
                                for item in basis_snapshots]},
        ))
        if fail_before_commit:
            raise RuntimeError("deliberate Phase 10 recommendation rollback before commit")
        return RecommendationCreationResult(
            recommendation.id, tuple(row.id for row in basis_rows), event_id,
            outbox.id, audit_id, trace_id,
        )

class RecommendationSemanticContract:
    """Explicit non-interchangeability contract for future serializers/UI."""

    @staticmethod
    def classify(obj):
        from .models import Evidence, KnowledgeLayerRule, Recommendation, RequirementControl

        if isinstance(obj, RequirementControl):
            return "certifiable_normative_requirement"
        if isinstance(obj, KnowledgeLayerRule):
            return "non_certifiable_guidance"
        if isinstance(obj, Evidence):
            return "observed_supporting_evidence"
        if isinstance(obj, Recommendation):
            return "derived_advisory_proposal"
        raise TypeError("object has no recommendation semantic contract")
