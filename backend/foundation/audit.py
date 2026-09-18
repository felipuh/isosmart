"""Controlled append and verification boundary for the audit hash chain."""

import hashlib
import re
from dataclasses import dataclass
from datetime import timezone

from django.db import connections

from .canonical import canonical_json
from .models import ImmutableAuditLog


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class AuditAppend:
    tenant_id: object
    stream_type: str
    stream_id: object
    actor_type: str
    actor_id: str | None
    action: str
    entity_type: str
    entity_id: object
    trace_id: object
    occurred_at: object
    before_hash: str | None = None
    after_hash: str | None = None
    metadata: dict | None = None


def _validate_hash(value, name):
    if value is not None and not _HASH_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def _reject_secret_metadata(value, path="metadata"):
    forbidden = {"password", "secret", "authorization", "access_token", "refresh_token", "cookie"}
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower().replace("-", "_") in forbidden:
                raise ValueError(f"secret-like audit metadata key rejected at {path}.{key}")
            _reject_secret_metadata(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_secret_metadata(item, f"{path}[{index}]")


class AuditWriterService:
    """Calls the hardened DB append function; it never calculates sequence/previous hash."""

    def __init__(self, *, using="default"):
        self.using = using

    def append(self, entry: AuditAppend):
        _validate_hash(entry.before_hash, "before_hash")
        _validate_hash(entry.after_hash, "after_hash")
        metadata = entry.metadata or {}
        _reject_secret_metadata(metadata)
        metadata_canonical = canonical_json(metadata)
        with connections[self.using].cursor() as cursor:
            cursor.execute(
                "SELECT audit.append_immutable_audit(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [
                    str(entry.tenant_id), entry.stream_type, str(entry.stream_id),
                    entry.actor_type, entry.actor_id, entry.action, entry.entity_type,
                    str(entry.entity_id), str(entry.trace_id), entry.occurred_at,
                    entry.before_hash, entry.after_hash, metadata_canonical,
                ],
            )
            return cursor.fetchone()[0]


def _part(value):
    if value is None:
        return "-1:"
    rendered = str(value)
    return f"{len(rendered.encode('utf-8'))}:{rendered}"


def calculate_entry_hash(entry):
    occurred = entry.occurred_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    values = (
        "iso-smart-audit-chain-v1", str(entry.tenant_id), entry.stream_type,
        str(entry.stream_id), str(entry.sequence_number), entry.previous_entry_hash,
        entry.actor_type, entry.actor_id, entry.action, entry.entity_type,
        str(entry.entity_id), str(entry.trace_id), occurred, entry.before_hash,
        entry.after_hash, entry.payload_hash,
    )
    return hashlib.sha256("".join(_part(value) for value in values).encode("utf-8")).hexdigest()


def verify_audit_stream(*, tenant_id, stream_type, stream_id, using="default"):
    entries = list(
        ImmutableAuditLog.objects.using(using)
        .filter(tenant_id=tenant_id, stream_type=stream_type, stream_id=stream_id)
        .order_by("sequence_number")
    )
    previous = None
    for expected_sequence, entry in enumerate(entries, start=1):
        metadata_hash = hashlib.sha256(entry.metadata_canonical.encode("utf-8")).hexdigest()
        if entry.sequence_number != expected_sequence:
            return False
        if entry.previous_entry_hash != previous or entry.payload_hash != metadata_hash:
            return False
        if entry.entry_hash != calculate_entry_hash(entry):
            return False
        previous = entry.entry_hash
    return True

