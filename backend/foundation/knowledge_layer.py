"""Phase 9 commands and query contract for non-certifiable guidance."""

import json

from uuid import UUID, uuid4

from django.db import connections, transaction
from django.utils import timezone

from .canonical import canonical_hash
from .models import (
    KnowledgeLayer,
    KnowledgeLayerBinding,
    KnowledgeLayerRule,
    NormativeCurationAudit,
    RequirementControl,
    StandardEdition,
)


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _json_object(value, name):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


class KnowledgeLayerCommandService:
    """Narrow material workflow for the isolated normative curator LOGIN."""

    def __init__(self, *, using="normative_curator"):
        self.using = using

    def _audit(self, *, action, entity_type, entity_id, actor_id, trace_id, payload):
        NormativeCurationAudit.objects.using(self.using).create(
            id=uuid4(), action=action, entity_type=entity_type, entity_id=entity_id,
            actor_id=_required(str(actor_id), "actor_id"), trace_id=trace_id,
            payload_hash=canonical_hash(payload), occurred_at=timezone.now(),
        )

    def create_knowledge_layer(self, *, standard_edition_id, layer_type, actor_id, trace_id):
        trace_id = UUID(str(trace_id)); entity_id = uuid4()
        state = {
            "standard_edition_id": str(standard_edition_id),
            "layer_type": _required(layer_type, "layer_type"),
            "certifiability_classification": "non_certifiable_guidance",
        }
        with transaction.atomic(using=self.using):
            StandardEdition.objects.using(self.using).get(id=standard_edition_id)
            KnowledgeLayer.objects.using(self.using).create(
                id=entity_id, standard_edition_id=standard_edition_id,
                layer_type=state["layer_type"],
                certifiability_classification=state["certifiability_classification"],
            )
            self._audit(action="knowledge_layer.created", entity_type="knowledge_layer",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def create_knowledge_layer_rule(
        self, *, knowledge_layer_id, rule_key, version, actor_id, trace_id,
        logic_json=None, evidence_expectation=None, source_reference=None,
    ):
        trace_id = UUID(str(trace_id)); entity_id = uuid4()
        state = {
            "knowledge_layer_id": str(knowledge_layer_id),
            "lineage_id": str(entity_id),
            "rule_key": _required(rule_key, "rule_key"),
            "version": _required(version, "version"),
            "previous_revision_id": None,
            "status": KnowledgeLayerRule.Status.DRAFT,
            "logic_json": _json_object(logic_json, "logic_json"),
            "evidence_expectation": _json_object(evidence_expectation, "evidence_expectation"),
            "source_reference": source_reference,
            "certifiability_classification": "non_certifiable_guidance",
        }
        with transaction.atomic(using=self.using):
            KnowledgeLayer.objects.using(self.using).get(id=knowledge_layer_id)
            KnowledgeLayerRule.objects.using(self.using).create(id=entity_id, **state)
            self._audit(action="knowledge_layer_rule.created", entity_type="knowledge_layer_rule",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def revise_knowledge_layer_rule(
        self, *, previous_revision_id, version, actor_id, trace_id,
        logic_json, evidence_expectation, source_reference=None,
    ):
        trace_id = UUID(str(trace_id)); entity_id = uuid4()
        has_shared_primitive = False
        if connections[self.using].vendor == "postgresql":
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT to_regprocedure('normative.curator_create_knowledge_layer_rule_successor_v1"
                    "(uuid,text,jsonb,jsonb,text,text,uuid)') IS NOT NULL"
                )
                has_shared_primitive = cursor.fetchone()[0]
        if has_shared_primitive:
            with transaction.atomic(using=self.using):
                with connections[self.using].cursor() as cursor:
                    cursor.execute(
                        "SELECT rule_id FROM normative.curator_create_knowledge_layer_rule_successor_v1"
                        "(%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)",
                        [str(previous_revision_id), _required(version, "version"),
                         json.dumps(_json_object(logic_json, "logic_json"), sort_keys=True, separators=(",", ":")),
                         json.dumps(_json_object(evidence_expectation, "evidence_expectation"), sort_keys=True, separators=(",", ":")),
                         source_reference, _required(str(actor_id), "actor_id"), str(trace_id)],
                    )
                    entity_id = cursor.fetchone()[0]
            return entity_id
        with transaction.atomic(using=self.using):
            previous = KnowledgeLayerRule.objects.using(self.using).select_for_update().get(
                id=previous_revision_id,
            )
            if previous.status != KnowledgeLayerRule.Status.PUBLISHED:
                raise ValueError("only a published rule revision can be revised")
            if KnowledgeLayerRule.objects.using(self.using).filter(
                previous_revision_id=previous.id,
            ).exists():
                raise ValueError("only the current rule revision can be revised")
            state = {
                "knowledge_layer_id": str(previous.knowledge_layer_id),
                "lineage_id": str(previous.lineage_id),
                "rule_key": previous.rule_key,
                "version": _required(version, "version"),
                "previous_revision_id": str(previous.id),
                "status": KnowledgeLayerRule.Status.DRAFT,
                "logic_json": _json_object(logic_json, "logic_json"),
                "evidence_expectation": _json_object(evidence_expectation, "evidence_expectation"),
                "source_reference": source_reference,
                "certifiability_classification": "non_certifiable_guidance",
            }
            KnowledgeLayerRule.objects.using(self.using).create(id=entity_id, **state)
            self._audit(action="knowledge_layer_rule.revised", entity_type="knowledge_layer_rule",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def publish_knowledge_layer_rule(
        self, *, rule_id, actor_id, trace_id, fail_before_commit=False,
    ):
        trace_id = UUID(str(trace_id))
        with transaction.atomic(using=self.using):
            rule = KnowledgeLayerRule.objects.using(self.using).select_for_update().get(id=rule_id)
            if rule.status != KnowledgeLayerRule.Status.DRAFT:
                raise ValueError("only a draft rule can be published")
            rule.status = KnowledgeLayerRule.Status.PUBLISHED
            rule.published_at = timezone.now()
            rule.save(using=self.using, update_fields=("status", "published_at"))
            self._audit(
                action="knowledge_layer_rule.published", entity_type="knowledge_layer_rule",
                entity_id=rule.id, actor_id=actor_id, trace_id=trace_id,
                payload={"lineage_id": str(rule.lineage_id), "rule_key": rule.rule_key,
                         "version": rule.version, "status": rule.status,
                         "published_at": rule.published_at.isoformat()},
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 9 rule publication rollback before commit")
        return rule.id

    def create_knowledge_layer_binding(
        self, *, knowledge_layer_rule_id, standard_edition_id, requirement_control_id,
        actor_id, trace_id, relationship_type="informs", priority=None, rationale=None,
    ):
        trace_id = UUID(str(trace_id)); entity_id = uuid4()
        relationship_type = _required(relationship_type, "relationship_type")
        if relationship_type != KnowledgeLayerBinding.RelationshipType.INFORMS:
            raise ValueError("only the source-backed INFORMS relationship is supported")
        state = {
            "knowledge_layer_rule_id": str(knowledge_layer_rule_id),
            "standard_edition_id": str(standard_edition_id),
            "requirement_control_id": str(requirement_control_id),
            "relationship_type": relationship_type,
            "priority": _required(priority, "priority") if priority is not None else None,
            "rationale": rationale,
            "status": KnowledgeLayerBinding.Status.DRAFT,
            "semantic_effect": KnowledgeLayerBinding.SemanticEffect.GUIDANCE_ONLY,
        }
        with transaction.atomic(using=self.using):
            rule = KnowledgeLayerRule.objects.using(self.using).get(id=knowledge_layer_rule_id)
            if rule.status != KnowledgeLayerRule.Status.PUBLISHED:
                raise ValueError("binding requires a published exact rule revision")
            RequirementControl.objects.using(self.using).get(
                id=requirement_control_id, standard_edition_id=standard_edition_id,
            )
            KnowledgeLayerBinding.objects.using(self.using).create(id=entity_id, **state)
            self._audit(action="knowledge_layer_binding.created", entity_type="knowledge_layer_binding",
                        entity_id=entity_id, actor_id=actor_id, trace_id=trace_id, payload=state)
        return entity_id

    def publish_knowledge_layer_binding(
        self, *, binding_id, actor_id, trace_id, fail_before_commit=False,
    ):
        trace_id = UUID(str(trace_id))
        with transaction.atomic(using=self.using):
            binding = KnowledgeLayerBinding.objects.using(self.using).select_for_update().get(
                id=binding_id,
            )
            if binding.status != KnowledgeLayerBinding.Status.DRAFT:
                raise ValueError("only a draft binding can be published")
            binding.status = KnowledgeLayerBinding.Status.PUBLISHED
            binding.published_at = timezone.now()
            binding.save(using=self.using, update_fields=("status", "published_at"))
            self._audit(
                action="knowledge_layer_binding.published", entity_type="knowledge_layer_binding",
                entity_id=binding.id, actor_id=actor_id, trace_id=trace_id,
                payload={"knowledge_layer_rule_id": str(binding.knowledge_layer_rule_id),
                         "standard_edition_id": str(binding.standard_edition_id),
                         "requirement_control_id": str(binding.requirement_control_id),
                         "relationship_type": binding.relationship_type,
                         "semantic_effect": binding.semantic_effect,
                         "status": binding.status,
                         "published_at": binding.published_at.isoformat()},
            )
            if fail_before_commit:
                raise RuntimeError("deliberate Phase 9 binding publication rollback before commit")
        return binding.id


class KnowledgeCatalogQueryService:
    """Future serialization boundary: normative requirements and guidance never merge."""

    def __init__(self, *, using="app"):
        self.using = using

    def certifiable_requirements(self):
        # Entity type is the catalog semantic boundary. Guidance tables are
        # deliberately not unioned into this queryset.
        return RequirementControl.objects.using(self.using).all()

    def certifiable_requirement_count(self):
        return self.certifiable_requirements().count()

    @staticmethod
    def classification_contract(obj):
        if isinstance(obj, RequirementControl):
            return {
                "object_kind": "requirement_control",
                "presentation_kind": "Requirement",
                "certifiability_classification": "normative_requirement",
                "is_certifiable_customer_requirement": True,
            }
        if isinstance(obj, (KnowledgeLayer, KnowledgeLayerRule)):
            return {
                "object_kind": "knowledge_layer" if isinstance(obj, KnowledgeLayer) else "knowledge_layer_rule",
                "presentation_kind": "Knowledge Layer" if isinstance(obj, KnowledgeLayer) else "Guidance",
                "certifiability_classification": "non_certifiable_guidance",
                "is_certifiable_customer_requirement": False,
            }
        raise TypeError("object has no Phase 9 certifiability contract")
