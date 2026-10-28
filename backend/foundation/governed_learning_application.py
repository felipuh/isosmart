"""Phase 26 exact KnowledgeLayerRule governed-application boundary.

The public command owns one Django transaction and invokes one fixed PostgreSQL
capability on that same physical connection.  It has no target, field, status,
operation, publication, activation, or replacement-payload argument.
"""

from dataclasses import dataclass
from uuid import UUID

from django.db import connections, transaction

from .learning_delta import HASH_RE
from .tenant_context import TrustedTenantIdentity, bind_trusted_tenant_context_in_transaction


APPLICATION_POLICY_ID = "knowledge-layer-rule-governed-source-reference-application-policy/v1"
APPLICATION_PERMISSION = "qms.learning_target.knowledge_rule_source_reference.apply"


class LearningTargetApplicationConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class TrustedKnowledgeRuleApplicationAuthority:
    identity: TrustedTenantIdentity
    organization_id: UUID
    actor_external_id: UUID
    permissions: frozenset[str]
    mfa_verified: bool
    access_active: bool
    global_governance: bool
    authority_context_version: str
    authority_decision_reference: str


@dataclass(frozen=True)
class LearningTargetApplicationResult:
    receipt_id: UUID
    result_rule_id: UUID
    replayed: bool


class KnowledgeLayerRuleGovernedApplicationService:
    """Only the exact source-reference correction v1 can cross this boundary."""

    def __init__(self, *, using="learning_application"):
        self.using = using

    @staticmethod
    def _required(value, name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} is required")
        return value.strip()

    def _validate_authority(self, authority):
        if not isinstance(authority, TrustedKnowledgeRuleApplicationAuthority):
            raise TypeError("authority must be the exact trusted application authority")
        if not isinstance(authority.identity, TrustedTenantIdentity):
            raise TypeError("authority identity must be TrustedTenantIdentity")
        if (not authority.mfa_verified or not authority.access_active or
                not authority.global_governance or
                APPLICATION_PERMISSION not in authority.permissions):
            raise PermissionError("active global application authority, MFA, and exact permission required")
        self._required(authority.authority_context_version, "authority_context_version")
        self._required(authority.authority_decision_reference, "authority_decision_reference")

    def _bind(self, authority, trace_id):
        bind_trusted_tenant_context_in_transaction(
            authority.identity, actor_id=authority.actor_external_id,
            trace_id=trace_id, using=self.using,
        )
        with connections[self.using].cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.organization_id',%s,true),"
                "set_config('app.learning_application_permission',%s,true),"
                "set_config('app.mfa_verified','true',true),"
                "set_config('app.access_active','true',true),"
                "set_config('app.governance_scope','global',true),"
                "set_config('app.authority_context_version',%s,true),"
                "set_config('app.authority_decision_reference',%s,true)",
                [str(authority.organization_id), APPLICATION_PERMISSION,
                 authority.authority_context_version, authority.authority_decision_reference],
            )

    def _invoke_in_caller_transaction(
        self, *, authorization_id, expected_delta_hash, actor_external_id,
        trace_id, forward_receipt_id,
    ):
        connection = connections[self.using]
        if not connection.in_atomic_block or connection.get_autocommit():
            raise RuntimeError("caller-owned transaction is required for target application")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT receipt_id,result_rule_id,replayed "
                "FROM normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1"
                "(%s,%s,%s,%s,%s)",
                [str(authorization_id), expected_delta_hash,
                 str(forward_receipt_id) if forward_receipt_id else None,
                 str(actor_external_id), str(trace_id)],
            )
            row = cursor.fetchone()
        return LearningTargetApplicationResult(UUID(str(row[0])), UUID(str(row[1])), bool(row[2]))

    def apply_validated_knowledge_layer_rule_source_reference_correction_v1(
        self, *, authority, authorization_id, expected_delta_hash, trace_id,
        forward_receipt_id=None,
    ):
        self._validate_authority(authority)
        authorization_id = UUID(str(authorization_id))
        trace_id = UUID(str(trace_id))
        forward_receipt_id = UUID(str(forward_receipt_id)) if forward_receipt_id else None
        if not isinstance(expected_delta_hash, str) or not HASH_RE.fullmatch(expected_delta_hash):
            raise ValueError("expected_delta_hash must be an exact lowercase SHA-256")
        try:
            with transaction.atomic(using=self.using, savepoint=False):
                self._bind(authority, trace_id)
                return self._invoke_in_caller_transaction(
                    authorization_id=authorization_id,
                    expected_delta_hash=expected_delta_hash,
                    actor_external_id=authority.actor_external_id,
                    trace_id=trace_id,
                    forward_receipt_id=forward_receipt_id,
                )
        except Exception as exc:
            message = str(exc)
            if "application identity conflict" in message:
                raise LearningTargetApplicationConflict(message) from exc
            raise
