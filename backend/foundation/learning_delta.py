"""Phase 24.2 inert exact learning-delta contracts.

This module validates and commits proposal material.  It deliberately contains
no target writer, successor builder, dispatcher, or application executor.
"""

from dataclasses import dataclass
import hashlib
import json
import re
from uuid import UUID


CANONICALIZATION_VERSION = "iso-smart-learning-delta-canonical-v1"
OPERATION_VERSION = "v1"
MODEL_POLICY_OPERATION = "learning.model_policy.approved_models.remove"
AGENT_DEFINITION_OPERATION = "learning.agent_definition.autonomy.reduce"
KNOWLEDGE_RULE_OPERATION = "learning.knowledge_layer_rule.source_reference.correct"
MODEL_POLICY_SCHEMA = "learning-model-policy-approved-model-removal-delta-v1"
AGENT_DEFINITION_SCHEMA = "learning-agent-definition-autonomy-reduction-delta-v1"
KNOWLEDGE_RULE_SCHEMA = "learning-knowledge-layer-rule-source-reference-correction-delta-v1"

HASH_RE = re.compile(r"^[0-9a-f]{64}$")
AUTHORITATIVE_SOURCE_REFERENCE_RE = re.compile(
    r"^iso-smart-source-ref-v1:([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}):"
    r"([0-9a-f]{64}):([A-Za-z0-9][A-Za-z0-9._:/#-]{0,255})$"
)
SYNTHETIC_SOURCE_REFERENCE_RE = re.compile(
    r"^iso-smart-synthetic-poc-source-ref-v1:"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}):"
    r"([0-9a-f]{64}):(fixture/element/[A-Za-z0-9._~-]+)$"
)
# Backwards-compatible export for callers/tests that intentionally exercise the
# established authoritative branch. Synthetic references are parsed explicitly
# below and never become authoritative by falling through this alias.
SOURCE_REFERENCE_RE = AUTHORITATIVE_SOURCE_REFERENCE_RE


class LearningDeltaContractError(ValueError):
    pass


@dataclass(frozen=True)
class ModelPolicyApprovedModelRemoval:
    removed_models: tuple[str, ...]
    successor_version: str


@dataclass(frozen=True)
class AgentDefinitionAutonomyReduction:
    new_autonomy_max: int
    successor_version: str


@dataclass(frozen=True)
class KnowledgeLayerRuleSourceReferenceCorrection:
    current_source_reference: str
    new_source_reference: str
    standard_edition_id: UUID
    standard_edition_source_hash: str
    successor_version: str


@dataclass(frozen=True)
class CanonicalDeltaMaterial:
    document: dict
    canonical_bytes: bytes
    delta_hash: str

    @property
    def operation_id(self):
        return self.document["operation_id"]

    @property
    def operation_version(self):
        return self.document["operation_version"]

    @property
    def delta_schema_version(self):
        return self.document["delta_schema_version"]


def _nonblank(value, name):
    if not isinstance(value, str) or not value or value != value.strip():
        raise LearningDeltaContractError(f"{name} must be an exact nonblank string")
    return value


def _uuid(value, name):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise LearningDeltaContractError(f"{name} must be a lowercase RFC 4122 UUID")
    return value


def _hash(value, name):
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise LearningDeltaContractError(f"{name} must be a lowercase SHA-256")
    return value


def canonical_delta_bytes(document):
    """Return the exact v1 UTF-8 JSON bytes, rejecting non-v1 value types."""
    def validate(value):
        if value is None or isinstance(value, float):
            raise LearningDeltaContractError("null and non-integer numbers are prohibited in v1")
        if isinstance(value, bool) or isinstance(value, (str, int)):
            if isinstance(value, str):
                try:
                    value.encode("utf-8")
                except UnicodeEncodeError as exc:
                    raise LearningDeltaContractError("lone Unicode surrogates are prohibited") from exc
            return
        if isinstance(value, list):
            for item in value:
                validate(item)
            return
        if isinstance(value, dict):
            if not all(isinstance(key, str) for key in value):
                raise LearningDeltaContractError("object keys must be strings")
            for item in value.values():
                validate(item)
            return
        raise LearningDeltaContractError(f"unsupported canonical value: {type(value).__name__}")
    validate(document)
    return json.dumps(document, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise LearningDeltaContractError(f"{label} fields must be exactly {sorted(expected)}")


def _source_reference_parts(value):
    """Return source identity/hash/locator for one closed provenance branch."""
    for source_classification, pattern in (
        ("AUTHORITATIVE_SOURCE", AUTHORITATIVE_SOURCE_REFERENCE_RE),
        ("RETAINED_DETERMINISTIC_SYNTHETIC_FIXTURE", SYNTHETIC_SOURCE_REFERENCE_RE),
    ):
        match = pattern.fullmatch(value or "")
        if match:
            return source_classification, match.group(1), match.group(2), match.group(3)
    return None


def validate_canonical_delta_document(document, target_snapshot, *, edition_snapshot=None):
    """Validate a parsed exact document against its frozen target vN snapshot."""
    top = {"canonicalization_version", "delta_schema_version", "operation_id",
           "operation_version", "payload", "target_hash", "target_id",
           "target_lineage_id", "target_type", "target_version"}
    _exact_keys(document, top, "delta")
    if document["canonicalization_version"] != CANONICALIZATION_VERSION:
        raise LearningDeltaContractError("canonicalization-version mismatch")
    if document["operation_version"] != OPERATION_VERSION:
        raise LearningDeltaContractError("operation-version mismatch")
    _uuid(document["target_id"], "target_id")
    _uuid(document["target_lineage_id"], "target_lineage_id")
    _hash(document["target_hash"], "target_hash")
    _nonblank(document["target_version"], "target_version")
    if (document["target_id"] != str(target_snapshot.get("id")) or
            document["target_lineage_id"] != str(target_snapshot.get("lineage_id")) or
            document["target_version"] != target_snapshot.get("version")):
        raise LearningDeltaContractError("target identity/version mismatch")
    payload = document["payload"]
    pair = (document["target_type"], document["operation_id"], document["delta_schema_version"])
    if pair == ("ModelPolicy", MODEL_POLICY_OPERATION, MODEL_POLICY_SCHEMA):
        _exact_keys(payload, {"removed_models", "successor_version"}, "payload")
        removed = payload["removed_models"]
        if (not isinstance(removed, list) or not removed or
                any(not isinstance(x, str) or not x for x in removed) or
                removed != sorted(removed) or len(set(removed)) != len(removed)):
            raise LearningDeltaContractError("removed_models must be a nonempty sorted unique string set-array")
        approved = target_snapshot.get("approved_models")
        if not isinstance(approved, list) or any(item not in approved for item in removed):
            raise LearningDeltaContractError("only already-approved models may be removed")
        _nonblank(payload["successor_version"], "successor_version")
    elif pair == ("AgentDefinition", AGENT_DEFINITION_OPERATION, AGENT_DEFINITION_SCHEMA):
        _exact_keys(payload, {"new_autonomy_max", "successor_version"}, "payload")
        new = payload["new_autonomy_max"]
        old = target_snapshot.get("autonomy_max")
        if isinstance(new, bool) or not isinstance(new, int) or not isinstance(old, int) or not 0 <= new < old <= 4:
            raise LearningDeltaContractError("autonomy must strictly decrease in the A0-A4 ordering")
        _nonblank(payload["successor_version"], "successor_version")
    elif pair == ("KnowledgeLayerRule", KNOWLEDGE_RULE_OPERATION, KNOWLEDGE_RULE_SCHEMA):
        keys = {"current_source_reference", "new_source_reference", "standard_edition_id",
                "standard_edition_source_hash", "successor_version"}
        _exact_keys(payload, keys, "payload")
        current, new = payload["current_source_reference"], payload["new_source_reference"]
        cm, nm = _source_reference_parts(current), _source_reference_parts(new)
        edition_id = _uuid(payload["standard_edition_id"], "standard_edition_id")
        source_hash = _hash(payload["standard_edition_source_hash"], "standard_edition_source_hash")
        if not cm or not nm or current == new or cm[:3] != nm[:3] or cm[3] == nm[3]:
            raise LearningDeltaContractError("only the locator of a validated source reference may change")
        if cm[1] != edition_id or cm[2] != source_hash or target_snapshot.get("source_reference") != current:
            raise LearningDeltaContractError("source reference does not bind the exact current target and edition")
        if not edition_snapshot or str(edition_snapshot.get("id")) != edition_id or edition_snapshot.get("status") != "published" or edition_snapshot.get("source_hash") != source_hash:
            raise LearningDeltaContractError("published StandardEdition source hash is not exact")
        _nonblank(payload["successor_version"], "successor_version")
    else:
        raise LearningDeltaContractError("target/schema/operation contract mismatch")
    return document


def build_canonical_delta(*, command, target_type, target_id, target_lineage_id,
                          target_version, target_hash, target_snapshot, edition_snapshot=None):
    if isinstance(command, ModelPolicyApprovedModelRemoval):
        operation, schema = MODEL_POLICY_OPERATION, MODEL_POLICY_SCHEMA
        payload = {"removed_models": list(command.removed_models), "successor_version": command.successor_version}
    elif isinstance(command, AgentDefinitionAutonomyReduction):
        operation, schema = AGENT_DEFINITION_OPERATION, AGENT_DEFINITION_SCHEMA
        payload = {"new_autonomy_max": command.new_autonomy_max, "successor_version": command.successor_version}
    elif isinstance(command, KnowledgeLayerRuleSourceReferenceCorrection):
        operation, schema = KNOWLEDGE_RULE_OPERATION, KNOWLEDGE_RULE_SCHEMA
        payload = {"current_source_reference": command.current_source_reference,
                   "new_source_reference": command.new_source_reference,
                   "standard_edition_id": str(command.standard_edition_id),
                   "standard_edition_source_hash": command.standard_edition_source_hash,
                   "successor_version": command.successor_version}
    else:
        raise TypeError("command must be one exact Phase 24.2 typed delta command")
    document = {"canonicalization_version": CANONICALIZATION_VERSION,
                "delta_schema_version": schema, "operation_id": operation,
                "operation_version": OPERATION_VERSION, "payload": payload,
                "target_hash": target_hash, "target_id": str(target_id),
                "target_lineage_id": str(target_lineage_id), "target_type": target_type,
                "target_version": target_version}
    validate_canonical_delta_document(document, target_snapshot, edition_snapshot=edition_snapshot)
    encoded = canonical_delta_bytes(document)
    return CanonicalDeltaMaterial(document, encoded, hashlib.sha256(encoded).hexdigest())


def exact_binding_tuple(artifact):
    names = ("canonical_delta_id", "canonicalization_version", "delta_schema_version",
             "operation_id", "operation_version", "delta_hash")
    values = tuple(getattr(artifact, name, None) for name in names)
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise LearningDeltaContractError("incomplete exact-delta binding is permanently ineligible")
    return values


def eligibility_classification(artifact):
    try:
        return "CANONICAL_DELTA_V1_ELIGIBLE" if exact_binding_tuple(artifact) else "LEGACY_INERT"
    except LearningDeltaContractError:
        return "LEGACY_INERT"
