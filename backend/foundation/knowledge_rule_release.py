"""Phase 27.2 inert publication, activation and runtime-adoption boundary.

This module is deliberately not imported by AgentRun or Recommendation.  Its
resolver is an explicit foundation/test boundary and accepts one immutable
runtime-adoption UUID only.
"""

from dataclasses import dataclass
from enum import Enum
import re
from uuid import UUID

from django.db import connections, transaction


HASH_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLICATION_PERMISSION = "qms.knowledge_layer_rule.publish"
ACTIVATION_PERMISSION = "qms.knowledge_layer_rule.activate"
ADOPTION_PERMISSION = "qms.knowledge_layer_rule.runtime_adopt"
REPAIR_PERMISSION = "qms.knowledge_layer_rule.release_repair"
CAPABILITY_PERMISSION = "qms.knowledge_layer_rule.release_capability_admin"


class GovernanceConflict(RuntimeError):
    """Exact replay identity exists with different immutable material."""


class ReconciliationOutcome(str, Enum):
    COMMITTED = "COMMITTED"
    NOT_COMMITTED = "NOT_COMMITTED"
    ABANDONED = "ABANDONED"
    INCONSISTENT = "INCONSISTENT"


@dataclass(frozen=True)
class _Authority:
    actor_external_id: UUID
    permissions: frozenset[str]
    mfa_verified: bool
    access_active: bool
    global_governance: bool
    authority_context_version: str
    authority_decision_reference: str
    governance_policy_version: str


@dataclass(frozen=True)
class TrustedPublicationAuthority(_Authority):
    pass


@dataclass(frozen=True)
class TrustedActivationAuthority(_Authority):
    pass


@dataclass(frozen=True)
class TrustedRuntimeAdoptionAuthority(_Authority):
    pass


@dataclass(frozen=True)
class TrustedRepairAuthority(_Authority):
    pass


@dataclass(frozen=True)
class TrustedCapabilityAuthority(_Authority):
    pass


@dataclass(frozen=True)
class GovernanceArtifactResult:
    artifact_id: UUID
    replayed: bool


@dataclass(frozen=True)
class ResolvedRuntimeRule:
    runtime_adoption_id: UUID
    activation_id: UUID | None
    publication_id: UUID | None
    knowledge_layer_rule_id: UUID
    lineage_id: UUID
    rule_version: str
    rule_material_hash: str


@dataclass(frozen=True)
class ReconciliationResult:
    outcome: ReconciliationOutcome
    detail: str


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _hash(value, name):
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise ValueError(f"{name} must be an exact lowercase SHA-256")
    return value


class _Boundary:
    authority_type = _Authority
    permission = ""

    def __init__(self, *, using):
        self.using = using

    def _validate_authority(self, authority):
        if type(authority) is not self.authority_type:
            raise TypeError(f"authority must be exact {self.authority_type.__name__}")
        if (not authority.mfa_verified or not authority.access_active or
                not authority.global_governance or self.permission not in authority.permissions):
            raise PermissionError("fresh active global authority, MFA, and exact permission required")
        _required(authority.authority_context_version, "authority_context_version")
        _required(authority.authority_decision_reference, "authority_decision_reference")
        _required(authority.governance_policy_version, "governance_policy_version")

    def _bind(self, authority, trace_id):
        with connections[self.using].cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.actor_id',%s,true),"
                "set_config('app.trace_id',%s,true),"
                "set_config('app.release_permission',%s,true),"
                "set_config('app.mfa_verified','true',true),"
                "set_config('app.access_active','true',true),"
                "set_config('app.governance_scope','global',true),"
                "set_config('app.authority_context_version',%s,true),"
                "set_config('app.authority_decision_reference',%s,true),"
                "set_config('app.governance_policy_version',%s,true)",
                [str(authority.actor_external_id), str(trace_id), self.permission,
                 authority.authority_context_version, authority.authority_decision_reference,
                 authority.governance_policy_version],
            )

    def _execute(self, authority, trace_id, sql, params):
        self._validate_authority(authority)
        trace_id = UUID(str(trace_id))
        try:
            with transaction.atomic(using=self.using, savepoint=False):
                self._bind(authority, trace_id)
                with connections[self.using].cursor() as cursor:
                    cursor.execute(sql, params)
                    row = cursor.fetchone()
            return GovernanceArtifactResult(UUID(str(row[0])), bool(row[1]))
        except Exception as exc:
            if "identity conflict" in str(exc).lower():
                raise GovernanceConflict(str(exc)) from exc
            raise


class KnowledgeLayerRulePublicationService(_Boundary):
    authority_type = TrustedPublicationAuthority
    permission = PUBLICATION_PERMISSION

    def __init__(self, *, using="rule_publisher"):
        super().__init__(using=using)

    def publish_native(self, *, authority, publication_id, rule_id,
                       expected_rule_material_hash, idempotency_key_hash,
                       reason, trace_id):
        values = [UUID(str(publication_id)), UUID(str(rule_id)),
                  _hash(expected_rule_material_hash, "expected_rule_material_hash"),
                  _hash(idempotency_key_hash, "idempotency_key_hash"),
                  _required(reason, "reason"), str(authority.actor_external_id), UUID(str(trace_id))]
        return self._execute(
            authority, trace_id,
            "SELECT artifact_id,replayed FROM normative.publish_knowledge_layer_rule_v1"
            "(%s,%s,%s,%s,%s,%s,%s)", [str(v) for v in values],
        )

    def import_legacy_evidence(self, *, authority, publication_id, rule_id,
                               expected_rule_material_hash, curation_audit_id,
                               historical_published_at, evidence_reference,
                               idempotency_key_hash, reason, trace_id):
        params = [publication_id, rule_id, expected_rule_material_hash, curation_audit_id,
                  historical_published_at, evidence_reference, idempotency_key_hash, reason,
                  authority.actor_external_id, trace_id]
        return self._execute(
            authority, trace_id,
            "SELECT artifact_id,replayed FROM normative.import_knowledge_layer_rule_publication_evidence_v1"
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [str(value) if isinstance(value, UUID) else value for value in params],
        )


class KnowledgeLayerRuleActivationService(_Boundary):
    authority_type = TrustedActivationAuthority
    permission = ACTIVATION_PERMISSION

    def __init__(self, *, using="rule_activator"):
        super().__init__(using=using)

    def activate(self, *, authority, activation_id, publication_id,
                 expected_rule_material_hash, expected_predecessor_activation_id,
                 compatibility_hash, idempotency_key_hash, reason, trace_id):
        params = [activation_id, publication_id, expected_rule_material_hash,
                  expected_predecessor_activation_id, compatibility_hash,
                  idempotency_key_hash, reason, authority.actor_external_id, trace_id]
        return self._execute(
            authority, trace_id,
            "SELECT artifact_id,replayed FROM normative.activate_knowledge_layer_rule_v1"
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [str(value) if isinstance(value, UUID) else value for value in params],
        )


class KnowledgeLayerRuleRuntimeAdoptionService(_Boundary):
    authority_type = TrustedRuntimeAdoptionAuthority
    permission = ADOPTION_PERMISSION

    def __init__(self, *, using="rule_adopter"):
        super().__init__(using=using)

    def adopt(self, *, authority, runtime_adoption_id, activation_id,
              expected_rule_material_hash, expected_predecessor_adoption_id,
              release_configuration_reference, release_configuration_hash,
              idempotency_key_hash, reason, trace_id):
        params = [runtime_adoption_id, activation_id, expected_rule_material_hash,
                  expected_predecessor_adoption_id, release_configuration_reference,
                  release_configuration_hash, idempotency_key_hash, reason,
                  authority.actor_external_id, trace_id]
        return self._execute(
            authority, trace_id,
            "SELECT artifact_id,replayed FROM normative.adopt_knowledge_layer_rule_runtime_v1"
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [str(value) if isinstance(value, UUID) else value for value in params],
        )

    def bootstrap_legacy(self, *, authority, runtime_adoption_id, rule_id,
                         expected_rule_material_hash, release_configuration_reference,
                         release_configuration_hash, idempotency_key_hash, reason, trace_id):
        params = [runtime_adoption_id, rule_id, expected_rule_material_hash,
                  release_configuration_reference, release_configuration_hash,
                  idempotency_key_hash, reason, authority.actor_external_id, trace_id]
        return self._execute(
            authority, trace_id,
            "SELECT artifact_id,replayed FROM normative.bootstrap_legacy_knowledge_layer_rule_runtime_v1"
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [str(value) if isinstance(value, UUID) else value for value in params],
        )


class InertRuntimeAdoptionResolver:
    """Foundation-only exact-ID resolver; deliberately has no selector overload."""

    def __init__(self, *, using="rule_resolver"):
        self.using = using

    def resolve(self, *, runtime_adoption_id):
        if runtime_adoption_id is None:
            raise ValueError("runtime_adoption_id is required; fallback is forbidden")
        try:
            adoption_id = UUID(str(runtime_adoption_id))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError("runtime_adoption_id must be an exact immutable UUID") from exc
        with connections[self.using].cursor() as cursor:
            cursor.execute(
                "SELECT runtime_adoption_id,activation_id,publication_id,knowledge_layer_rule_id,"
                "lineage_id,rule_version,rule_material_hash "
                "FROM normative.resolve_knowledge_layer_rule_runtime_adoption_v1(%s)",
                [str(adoption_id)],
            )
            row = cursor.fetchone()
        if row is None:
            raise LookupError("exact runtime adoption is absent or invalid")
        return ResolvedRuntimeRule(
            UUID(str(row[0])), UUID(str(row[1])) if row[1] else None,
            UUID(str(row[2])) if row[2] else None, UUID(str(row[3])),
            UUID(str(row[4])), row[5], row[6],
        )


class GovernanceRepairService(_Boundary):
    authority_type = TrustedRepairAuthority
    permission = REPAIR_PERMISSION

    def __init__(self, *, using="release_repair"):
        super().__init__(using=using)

    def reconcile_publication(self, artifact_id):
        return self._reconcile("reconcile_knowledge_layer_rule_publication_v1", artifact_id)

    def reconcile_activation(self, artifact_id):
        return self._reconcile("reconcile_knowledge_layer_rule_activation_v1", artifact_id)

    def reconcile_adoption(self, artifact_id):
        return self._reconcile("reconcile_knowledge_layer_rule_runtime_adoption_v1", artifact_id)

    def _reconcile(self, function_name, artifact_id):
        artifact_id = UUID(str(artifact_id))
        with connections[self.using].cursor() as cursor:
            cursor.execute(f"SELECT outcome,detail FROM normative.{function_name}(%s)", [str(artifact_id)])
            row = cursor.fetchone()
        return ReconciliationResult(ReconciliationOutcome(row[0]), row[1])

    def record_abandoned(self, *, authority, operation_kind, artifact_id, material_hash,
                         reason, trace_id):
        self._validate_authority(authority)
        if operation_kind not in {"PUBLICATION", "ACTIVATION", "RUNTIME_ADOPTION"}:
            raise ValueError("closed operation_kind required")
        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, UUID(str(trace_id)))
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT normative.record_abandoned_rule_governance_operation_v1"
                    "(%s,%s,%s,%s,%s,%s)",
                    [operation_kind, str(UUID(str(artifact_id))), _hash(material_hash, "material_hash"),
                     _required(reason, "reason"), str(authority.actor_external_id), str(UUID(str(trace_id)))],
                )


class GovernanceCapabilityService(_Boundary):
    authority_type = TrustedCapabilityAuthority
    permission = CAPABILITY_PERMISSION

    def __init__(self, *, using="release_controller"):
        super().__init__(using=using)

    def decide(self, *, authority, decision_id, capability, enabled,
               expected_predecessor_id, reason, trace_id):
        self._validate_authority(authority)
        if capability not in {"PUBLICATION", "ACTIVATION", "RUNTIME_ADOPTION"}:
            raise ValueError("closed capability required")
        with transaction.atomic(using=self.using, savepoint=False):
            self._bind(authority, UUID(str(trace_id)))
            with connections[self.using].cursor() as cursor:
                cursor.execute(
                    "SELECT normative.record_rule_governance_capability_decision_v1"
                    "(%s,%s,%s,%s,%s,%s,%s)",
                    [str(UUID(str(decision_id))), capability, enabled,
                     str(UUID(str(expected_predecessor_id))) if expected_predecessor_id else None,
                     _required(reason, "reason"), str(authority.actor_external_id), str(UUID(str(trace_id)))],
                )
                return UUID(str(cursor.fetchone()[0]))
