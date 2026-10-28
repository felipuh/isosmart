"""Future executable V2.4 operation engine with no import-time effects.

The public experiment remains parameterless.  Infrastructure is injected only
through the narrow ports below; all business material and operation selection
come from the byte-locked V2.4 contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol

from .phase31_4_v2_4_execution_wiring import OPERATIONS, NativeOperation
from .phase31_4_v2_4_support_producer import (
    ContractIntegrityError, ExactSupportProducer, StrictBindingRenderer,
    UnresolvedBinding, _contract,
)


OPERATION_CLASSES = frozenset({
    "DIRECT_NATIVE_OPERATION",
    "EXACT_FIXTURE_ADAPTER_OVER_NATIVE_SEMANTICS",
    "PROMOTED_SQL_OPERATION",
    "PROMOTED_GOVERNED_ADAPTER",
})

FIELD_EXECUTION_CLASSES = MappingProxyType({
    "EXACT_LITERAL": "STATIC_RENDERED",
    "ADOPTED_STATIC_SCHEMA_DEFAULT": "STATIC_RENDERED",
    "REFERENCE_TO_BOUND_FIELD": "REFERENCE_RESOLVED",
    "DETERMINISTIC_DERIVATION": "DETERMINISTIC_DERIVED",
    "EXECUTION_DERIVED_PERSISTED": "LIVE_CAPTURE_IMPLEMENTED",
    "NATIVE_OUTPUT": "NATIVE_OUTPUT_CAPTURE_IMPLEMENTED",
    "ADR0017_MAPPED_OUTPUT": "ADR0017_MAPPING_IMPLEMENTED",
    "EXECUTION_DERIVED_EXTERNAL_AUTHORITY": "EXTERNAL_AUTHORITY_CAPTURE_IMPLEMENTED",
})


class ExecutionPort(Protocol):
    """Exact-operation boundary implemented by the future Django/SQL runtime."""

    def begin(self, operation: NativeOperation) -> None: ...
    def invoke(self, operation: NativeOperation,
               material: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]: ...
    def reread(self, operation: NativeOperation) -> Mapping[str, Any]: ...
    def commit(self, operation: NativeOperation) -> None: ...
    def rollback(self, operation: NativeOperation) -> None: ...
    def checkpoint(self, phase: str, ledger: "ExecutionLedger") -> None: ...


class SyntheticAuthorityPort(Protocol):
    """Fresh, experiment-only authority read; never a real AdminApps call."""

    def read(self, operation_id: str) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class BoundOperation:
    source_path: str
    symbol: str
    invoke: Callable[[Mapping[str, Mapping[str, Any]]], Mapping[str, Any]]
    reread: Callable[[], Mapping[str, Any]]


class CallableExecutionPort:
    """Concrete exact-call backend; no generic model/table/DML entry exists."""

    def __init__(self, handlers: Mapping[str, BoundOperation], transaction):
        expected = {operation.operation_id: (operation.source_path, operation.symbol)
                    for operation in OPERATIONS}
        observed = {key: (value.source_path, value.symbol) for key, value in handlers.items()}
        if observed != expected:
            raise ContractIntegrityError("bound native operation registry is not exact")
        self._handlers = MappingProxyType(dict(handlers))
        self._transaction = transaction

    def begin(self, operation: NativeOperation) -> None:
        self._transaction.begin(operation.transaction_owner)

    def invoke(self, operation: NativeOperation,
               material: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
        return self._handlers[operation.operation_id].invoke(material)

    def reread(self, operation: NativeOperation) -> Mapping[str, Any]:
        return self._handlers[operation.operation_id].reread()

    def commit(self, operation: NativeOperation) -> None:
        self._transaction.commit(operation.transaction_owner)

    def rollback(self, operation: NativeOperation) -> None:
        self._transaction.rollback(operation.transaction_owner)

    def checkpoint(self, phase: str, ledger: "ExecutionLedger") -> None:
        self._transaction.checkpoint(phase, ledger.frozen())


class ParityError(ContractIntegrityError):
    """Reference and ADR-0017 adapter differed outside seven identities."""


@dataclass(frozen=True)
class OperationEnvelope:
    operation: NativeOperation
    classification: str
    tenant_context_owner: str
    identity_authority: str
    event_outbox_audit: str
    precommit_hook: str
    postcommit_retention: str


@dataclass
class ExecutionLedger:
    values: dict[str, Any] = field(default_factory=dict)
    retained_operations: dict[str, Mapping[str, Any]] = field(default_factory=dict)
    authority_evidence: dict[str, tuple[Mapping[str, Any], Mapping[str, Any]]] = field(
        default_factory=dict
    )

    def frozen(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))


def operation_classification(operation: NativeOperation) -> str:
    if "/migrations/" in operation.source_path:
        return "PROMOTED_SQL_OPERATION"
    if operation.operation_id == "application.reference_path":
        return "PROMOTED_GOVERNED_ADAPTER"
    if operation.operation_id.startswith("application.adr0017") or operation.operation_id.startswith("freeze0"):
        return "EXACT_FIXTURE_ADAPTER_OVER_NATIVE_SEMANTICS"
    return "DIRECT_NATIVE_OPERATION"


def operation_envelopes() -> tuple[OperationEnvelope, ...]:
    rows = tuple(OperationEnvelope(
        operation=operation,
        classification=operation_classification(operation),
        tenant_context_owner=operation.transaction_owner,
        identity_authority=(
            "ADR-0017/ADR-0018 exact experiment adapter"
            if "application" in operation.operation_id or operation.operation_id.startswith("freeze0")
            else "native operation"
        ),
        event_outbox_audit="selected native source; capture Event/Outbox and native Audit outputs",
        precommit_hook="fresh synthetic authority reread and exact equality",
        postcommit_retention="independent canonical reread before downstream use",
    ) for operation in OPERATIONS)
    if len({row.operation.operation_id for row in rows}) != len(OPERATIONS):
        raise ContractIntegrityError("duplicate named operation")
    if {row.classification for row in rows} - OPERATION_CLASSES:
        raise ContractIntegrityError("operation classification escaped closed taxonomy")
    return rows


def field_execution_inventory() -> tuple[tuple[str, str, str], ...]:
    inventory = tuple(
        ("::".join(member.qualified_identity), field.name,
         FIELD_EXECUTION_CLASSES[field.binding_kind])
        for member in ExactSupportProducer().build_plan() for field in member.fields
    )
    if len(inventory) != 1664:
        raise ContractIntegrityError("field execution inventory is not exactly 1,664")
    return inventory


class ADR0017ParityExecutor:
    """Differential gate: only the seven contract-authorized IDs may differ."""

    def __init__(self, reference: Mapping[str, Any], adapter: Mapping[str, Any]):
        self.reference = reference
        self.adapter = adapter

    def verify(self) -> Mapping[str, tuple[Any, Any]]:
        authorized = set(_contract()["identity_contract"]["adr0017_exact_outputs"])
        differences = {
            key: (self.reference.get(key), self.adapter.get(key))
            for key in set(self.reference) | set(self.adapter)
            if self.reference.get(key) != self.adapter.get(key)
        }
        if set(differences) - authorized or len(authorized) != 7:
            raise ParityError("ADR-0017 parity differs outside seven authorized identities")
        return MappingProxyType(differences)


class V24ExecutionSession:
    """Concrete transaction/capture engine for the frozen experiment graph."""

    def __init__(self, execution: ExecutionPort, authority: SyntheticAuthorityPort):
        self._execution = execution
        self._authority = authority
        self.ledger = ExecutionLedger()
        self._renderer = StrictBindingRenderer()
        self._plans = ExactSupportProducer().build_plan()
        self._contract = _contract()

    def _members_for(self, operation: NativeOperation) -> tuple[Any, ...]:
        producer_by_member = {
            (row["qualified_table"], row["primary_key"]): row["producer"]
            for row in self._contract["producer_matrix"]
        }
        from .phase31_4_v2_4_execution_wiring import PRODUCER_PHASES
        return tuple(plan for plan in self._plans
                     if operation.phase in PRODUCER_PHASES[producer_by_member[plan.qualified_identity]])

    def _render_available(self, members: tuple[Any, ...]) -> dict[str, dict[str, Any]]:
        material: dict[str, dict[str, Any]] = {}
        for member in members:
            key = "::".join(member.qualified_identity)
            fields: dict[str, Any] = {}
            for field in member.fields:
                source = {"name": field.name,
                          "schema": {"database_type": field.database_type,
                                     "nullable": field.nullable},
                          "value_binding": dict(field.binding)}
                try:
                    fields[field.name] = self._renderer.render(source, self.ledger.values)
                except UnresolvedBinding:
                    continue
            material[key] = fields
        return material

    def _capture(self, members: tuple[Any, ...], output: Mapping[str, Any]) -> None:
        for member in members:
            member_key = "::".join(member.qualified_identity)
            member_output = output.get(member_key, {})
            if not isinstance(member_output, Mapping):
                raise ContractIntegrityError(f"native output is not a mapping: {member_key}")
            for field in member.fields:
                qualified = f"{member_key}.{field.name}"
                if field.name in member_output:
                    value = member_output[field.name]
                    self.ledger.values[field.name] = value
                    self.ledger.values[qualified] = value

    def execute_operation(self, operation: NativeOperation) -> Mapping[str, Any]:
        members = self._members_for(operation)
        material = MappingProxyType({
            key: MappingProxyType(value) for key, value in self._render_available(members).items()
        })
        before = MappingProxyType(dict(self._authority.read(operation.operation_id)))
        self._execution.begin(operation)
        try:
            output = self._execution.invoke(operation, material)
            self._capture(members, output)
            immediately_before_commit = MappingProxyType(
                dict(self._authority.read(operation.operation_id))
            )
            if before != immediately_before_commit or not before.get("authorized", False):
                raise ContractIntegrityError(
                    f"fresh synthetic authority changed or denied: {operation.operation_id}"
                )
            self.ledger.authority_evidence[operation.operation_id] = (
                before, immediately_before_commit
            )
            self._execution.commit(operation)
        except Exception:
            self._execution.rollback(operation)
            raise
        retained = MappingProxyType(dict(self._execution.reread(operation)))
        self._capture(members, retained)
        self.ledger.retained_operations[operation.operation_id] = retained
        return retained

    def execute_phase(self, phase: str) -> None:
        selected = tuple(operation for operation in OPERATIONS if operation.phase == phase)
        if not selected and phase not in {
            "PRECREATION_INTEGRITY", "ENVIRONMENT_CREATE", "RENDER_PROFILE", "MIGRATIONS",
            "CATALOG_ASSERTIONS", "SUPPORT_PRODUCER_INSTALL", "SECURITY_ASSERTIONS",
            "FREEZE_1_5", "ROOT_DUAL_REREAD", "PUBLICATION_ADMISSION",
            "PUBLICATION_LIVE_COMPARE", "PUBLICATION_ELIGIBILITY", "ACTIVATION_ADMISSION",
            "LIVE_COMPARE", "TEARDOWN_GATE", "TEARDOWN", "POST_TEARDOWN_VERIFY",
            "TAMPER_NEGATIVE",
        }:
            raise ContractIntegrityError(f"phase has no exact implementation: {phase}")
        for operation in selected:
            self.execute_operation(operation)
        if not selected:
            self._execution.checkpoint(phase, self.ledger)

    def assert_all_fields_consumable(self) -> None:
        fields = [field for member in self._plans for field in member.fields]
        if len(fields) != 1664:
            raise ContractIntegrityError("field universe changed")
        supported = {
            "EXACT_LITERAL", "REFERENCE_TO_BOUND_FIELD", "DETERMINISTIC_DERIVATION",
            "EXECUTION_DERIVED_PERSISTED", "EXECUTION_DERIVED_EXTERNAL_AUTHORITY",
            "NATIVE_OUTPUT", "ADR0017_MAPPED_OUTPUT", "ADOPTED_STATIC_SCHEMA_DEFAULT",
        }
        if any(field.binding_kind not in supported for field in fields):
            raise ContractIntegrityError("plan-only field binding remains")

    def freeze_all(self) -> Mapping[str, Any]:
        """Type-validate and freeze all 1,664 values after the final reread."""
        frozen: dict[str, Any] = {}
        for member in self._plans:
            member_key = "::".join(member.qualified_identity)
            for field in member.fields:
                source = {"name": field.name,
                          "schema": {"database_type": field.database_type,
                                     "nullable": field.nullable},
                          "value_binding": dict(field.binding)}
                value = self._renderer.render(source, self.ledger.values)
                frozen[f"{member_key}.{field.name}"] = value
        if len(frozen) != 1664:
            raise ContractIntegrityError("final execution freeze is not exactly 1,664 fields")
        return MappingProxyType(frozen)
