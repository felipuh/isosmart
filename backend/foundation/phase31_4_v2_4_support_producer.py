"""Exact, inert Phase 31.4 V2.4 support-producer package.

This module deliberately builds the complete future execution plan without
opening a database connection.  Clean Retry 3 is the only authorized caller
of the plan.  All business material is read from the frozen V2.4 contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from contextvars import ContextVar
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid5

from .phase31_4_4b_strict_type_validator import canonical_type, literal_type_error
from .phase31_4_5b_source_reachability_validator import validate


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json"
CONTRACT_SHA256 = "a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387"
PRODUCER_IDENTIFIER = "phase31.4.4-exact-support-producer/v1"
EXPERIMENT_ID = "a3f8fd64-af24-5b31-977a-bcaf8146c563"

SUPPORTED_BINDINGS = frozenset({
    "EXACT_LITERAL", "DETERMINISTIC_DERIVATION", "REFERENCE_TO_BOUND_FIELD",
    "EXECUTION_DERIVED_PERSISTED", "EXECUTION_DERIVED_EXTERNAL_AUTHORITY",
    "NATIVE_OUTPUT", "ADR0017_MAPPED_OUTPUT",
    "ADOPTED_STATIC_SCHEMA_DEFAULT",
})


class ContractIntegrityError(RuntimeError):
    pass


class UnresolvedBinding(RuntimeError):
    """A value must be supplied by its named future producer, never guessed."""


_RETENTION_PORT: ContextVar[Any | None] = ContextVar("phase31_4_retention_port", default=None)


@contextmanager
def bound_retention_port(port):
    """Bind only read/retention infrastructure, never business material."""
    token = _RETENTION_PORT.set(port)
    try:
        yield
    finally:
        _RETENTION_PORT.reset(token)


def _retain(name: str) -> Any:
    port = _RETENTION_PORT.get()
    if port is None:
        raise ContractIntegrityError("Clean Retry 3 retention port is not bound")
    return port.capture(name)


@dataclass(frozen=True)
class FieldPlan:
    name: str
    database_type: str
    nullable: bool
    binding_kind: str
    binding: Mapping[str, Any]


@dataclass(frozen=True)
class MemberPlan:
    qualified_identity: tuple[str, str]
    producer: str
    fields: tuple[FieldPlan, ...]
    retention_reread: bool = True


@dataclass(frozen=True)
class DomainEventPlan:
    row_id: str
    event_type: str
    aggregate_type: str
    source_location: str
    serialization_kind: str
    event_identity_authorized: bool
    outbox_identity_authorized: bool
    audit_identity_authorized: bool


def _bytes_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _contract() -> dict[str, Any]:
    if _bytes_sha(CONTRACT_PATH) != CONTRACT_SHA256:
        raise ContractIntegrityError("V2.4 byte integrity failure")
    document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    errors = validate(document)
    if errors:
        raise ContractIntegrityError("V2.4 validation failure: " + "; ".join(errors))
    if document.get("contract_version") != "2.4":
        raise ContractIntegrityError("operational contract is not V2.4")
    return document


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


class StrictBindingRenderer:
    """Render only already-typed values; never coerce across physical types."""

    def render(self, field: Mapping[str, Any], resolved: Mapping[str, Any]) -> Any:
        binding = field["value_binding"]
        kind = binding.get("kind")
        if kind not in SUPPORTED_BINDINGS:
            raise ContractIntegrityError(f"unsupported binding kind: {kind}")
        declared = canonical_type(
            field.get("schema", {}).get("database_type")
            or field.get("schema", {}).get("type")
        )
        supplied = canonical_type(binding.get("database_type_or_schema_type"))
        if supplied and supplied != declared:
            raise ContractIntegrityError(f"physical type mismatch for {field['name']}")
        if kind == "EXACT_LITERAL":
            error = literal_type_error(field, binding.get("typed_value"))
            if error:
                raise ContractIntegrityError(f"{error}: {field['name']}")
            return _freeze(binding.get("typed_value"))
        if kind == "REFERENCE_TO_BOUND_FIELD":
            key = f"{binding['source_member']}.{binding['source_field']}"
            if key not in resolved:
                raise UnresolvedBinding(key)
            value = resolved[key]
            # A resolved value is accepted only under the exact declared type;
            # conversion is intentionally absent.
            probe = dict(field)
            probe["value_binding"] = {"kind": "EXACT_LITERAL", "typed_value": value}
            error = literal_type_error(probe, value)
            if error:
                raise ContractIntegrityError(f"resolved reference type mismatch: {key}")
            return _freeze(value)
        if kind == "DETERMINISTIC_DERIVATION":
            if binding.get("algorithm_id") != "RFC4122-UUIDv5-SHA1":
                raise ContractIntegrityError("unapproved deterministic algorithm")
            inputs = binding.get("all_preimage_inputs", {})
            try:
                value = str(uuid5(UUID(inputs["namespace_uuid"]), inputs["utf8_name"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise ContractIntegrityError("invalid UUIDv5 preimage") from exc
            if value != binding.get("expected_output"):
                raise ContractIntegrityError("UUIDv5 expected output mismatch")
            return value
        if kind == "ADR0017_MAPPED_OUTPUT":
            if binding.get("adr") != "ADR-0017":
                raise ContractIntegrityError("unapproved Application identity mapping")
            return binding["output_identity"]
        if kind == "ADOPTED_STATIC_SCHEMA_DEFAULT":
            raise UnresolvedBinding("schema default must be observed from PostgreSQL")
        # Native, authority and persisted values are accepted only after their
        # named producer retained an exact typed value under this field name.
        if field["name"] in resolved:
            value = resolved[field["name"]]
            probe = dict(field)
            probe["value_binding"] = {"kind": "EXACT_LITERAL", "typed_value": value}
            error = literal_type_error(probe, value)
            if error:
                raise ContractIntegrityError(f"retained output type mismatch: {field['name']}")
            return _freeze(value)
        raise UnresolvedBinding(
            f"{kind}:{binding.get('producer') or binding.get('derivation') or field['name']}"
        )


class ExactSupportProducer:
    """Parameterless business interface for the one frozen experiment."""

    identifier = PRODUCER_IDENTIFIER
    experiment_id = EXPERIMENT_ID

    def build_plan(self) -> tuple[MemberPlan, ...]:
        contract = _contract()
        producers = {
            (row["qualified_table"], row["primary_key"]): row["producer"]
            for row in contract["producer_matrix"]
        }
        plans = []
        seen = set()
        for member in contract["field_bindings"]:
            identity = member["member_identity"]
            key = (
                identity["qualified_table_or_artifact_index"],
                identity["primary_key_or_artifact_id"],
            )
            if key in seen or key not in producers:
                raise ContractIntegrityError(f"duplicate or unmapped member: {key}")
            seen.add(key)
            fields = tuple(
                FieldPlan(
                    name=field["name"],
                    database_type=canonical_type(
                        field.get("schema", {}).get("database_type")
                        or field.get("schema", {}).get("type")
                    ),
                    nullable=bool(field.get("schema", {}).get("nullable")),
                    binding_kind=field["value_binding"]["kind"],
                    binding=_freeze(field["value_binding"]),
                )
                for field in member["fields"]
            )
            plans.append(MemberPlan(key, producers[key], fields))
        universe = {
            (row["qualified_table"], row["primary_key"])
            for row in contract["future_row_universe"]
        }
        if len(plans) != 118 or seen != universe:
            raise ContractIntegrityError("V2.4 member coverage is not exactly 118/118")
        return tuple(plans)

    def domain_event_matrix(self) -> tuple[DomainEventPlan, ...]:
        contract = _contract()
        rows = contract["remaining_domain_event_source_audit"]["matrix"]
        aggregate_types = {}
        for member in contract["field_bindings"]:
            identity = member["member_identity"]
            if identity["qualified_table_or_artifact_index"] != "eventing.domain_event":
                continue
            for field in member["fields"]:
                if field["name"] == "aggregate_type":
                    aggregate_types[identity["primary_key_or_artifact_id"]] = field["value_binding"]["typed_value"]
        result = tuple(DomainEventPlan(
            row_id=row["row_id"], event_type=row["selected_native_producer"],
            aggregate_type=aggregate_types[row["row_id"]], source_location=row["source_location"],
            serialization_kind=row["serialization_kind"],
            event_identity_authorized=row["event_identity_authorized"],
            outbox_identity_authorized=row["outbox_identity_authorized"],
            audit_identity_authorized=row["audit_identity_authorized"],
        ) for row in rows)
        if len(result) != 13 or any(not all((row.event_identity_authorized,
                                             row.outbox_identity_authorized,
                                             row.audit_identity_authorized)) for row in result):
            raise ContractIntegrityError("DomainEvent implementation matrix is not 13/13")
        return result

    def identity_exception_inventory(self) -> Mapping[str, Any]:
        contract = _contract()["identity_contract"]
        return _freeze({
            "authorization": "ADR-0018",
            "deterministic_replacements": contract["adr0018_deterministic_replacements"],
            "adr0017_application_outputs": contract["adr0017_exact_outputs"],
            "audit_identity": "NATIVE_UUIDV7_OUTPUT",
        })

    def transaction_contract(self) -> tuple[str, ...]:
        return tuple(_contract()["support_producer"]["transaction_composition"])

    def execution_wiring(self) -> Mapping[str, tuple[str, ...]]:
        from .phase31_4_v2_4_execution_wiring import validate_execution_wiring
        return MappingProxyType(validate_execution_wiring())


# Exact retained-artifact producers.  The Clean Retry backend supplies a
# read-only cursor internally; no caller-controlled identity or material is
# accepted by the public producer entry.
def execute_freeze0() -> Any:
    return _retain("FREEZE0_EXACT_SUPPORT")


def retain_publication_checkpoint() -> Any:
    return _retain("PUBLICATION_CHECKPOINT")


def retain_b2_compatibility() -> Any:
    return _retain("B2_COMPATIBILITY")


def retain_b3_release() -> Any:
    return _retain("B3_RELEASE")


def retain_publication_closure() -> Any:
    return _retain("PUBLICATION_CLOSURE")


def retain_full_closure() -> Any:
    return _retain("FULL_CLOSURE")


def build_support_plan() -> tuple[MemberPlan, ...]:
    """The public operation intentionally accepts no arguments."""
    return ExactSupportProducer().build_plan()
