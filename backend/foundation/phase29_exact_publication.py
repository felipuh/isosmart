"""Exact-candidate-only Phase 29 publication service.

The database function takes no rule ID, lineage, target type, operation or
payload.  Those values are frozen inside the ephemeral POC installation.
"""

from dataclasses import dataclass
import re
from uuid import UUID

from django.db import connections, transaction


HASH_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLICATION_PERMISSION = "qms.knowledge_layer_rule.publish"


@dataclass(frozen=True)
class FreshPhase29PublicationAuthority:
    actor_external_id: UUID
    authority_decision_id: UUID
    authority_decision_hash: str
    authority_context_version: str
    policy_version: str
    policy_hash: str
    evaluated_at: str
    expires_at: str
    mfa_verified: bool
    access_active: bool
    global_governance: bool
    permissions: frozenset[str]
    server_resolved: bool


@dataclass(frozen=True)
class ExactPublicationResult:
    publication_id: UUID
    replayed: bool


class ExactPhase29PublicationConflict(RuntimeError):
    pass


class ExactPhase29PublicationService:
    def __init__(self, *, using="rule_publisher"):
        self.using = using

    @staticmethod
    def _validate(authority: FreshPhase29PublicationAuthority) -> None:
        if type(authority) is not FreshPhase29PublicationAuthority:
            raise TypeError("exact fresh Phase 29 publication authority required")
        if not all((authority.mfa_verified, authority.access_active, authority.global_governance, authority.server_resolved)):
            raise PermissionError("fresh active server-resolved MFA/global publication authority required")
        if PUBLICATION_PERMISSION not in authority.permissions:
            raise PermissionError("exact publication permission required")
        for value, field in ((authority.authority_decision_hash, "authority_decision_hash"), (authority.policy_hash, "policy_hash")):
            if not HASH_RE.fullmatch(value):
                raise ValueError(f"{field} must be an exact lowercase SHA-256")

    def publish(self, *, authority, publication_id, idempotency_key_hash, reason, trace_id):
        self._validate(authority)
        publication_id = UUID(str(publication_id))
        trace_id = UUID(str(trace_id))
        if not HASH_RE.fullmatch(idempotency_key_hash):
            raise ValueError("idempotency_key_hash must be an exact lowercase SHA-256")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason is required")
        try:
            with transaction.atomic(using=self.using, savepoint=False):
                with connections[self.using].cursor() as cursor:
                    cursor.execute(
                        "SELECT set_config('app.actor_id',%s,true),set_config('app.trace_id',%s,true),"
                        "set_config('app.release_permission',%s,true),set_config('app.mfa_verified','true',true),"
                        "set_config('app.access_active','true',true),set_config('app.governance_scope','global',true),"
                        "set_config('app.authority_context_version',%s,true),set_config('app.authority_decision_reference',%s,true),"
                        "set_config('app.governance_policy_version',%s,true),set_config('app.authority_decision_hash',%s,true),"
                        "set_config('app.authority_evaluated_at',%s,true),set_config('app.authority_expires_at',%s,true),"
                        "set_config('app.publication_policy_hash',%s,true)",
                        [str(authority.actor_external_id), str(trace_id), PUBLICATION_PERMISSION,
                         authority.authority_context_version, str(authority.authority_decision_id),
                         authority.policy_version, authority.authority_decision_hash,
                         authority.evaluated_at, authority.expires_at, authority.policy_hash],
                    )
                    cursor.execute(
                        "SELECT artifact_id,replayed FROM normative.publish_phase29_exact_retained_candidate_v1(%s,%s,%s,%s)",
                        [str(publication_id), idempotency_key_hash, reason.strip(), str(trace_id)],
                    )
                    row = cursor.fetchone()
            return ExactPublicationResult(UUID(str(row[0])), bool(row[1]))
        except Exception as exc:
            if "identity conflict" in str(exc).lower() or "material conflict" in str(exc).lower():
                raise ExactPhase29PublicationConflict(str(exc)) from exc
            raise
