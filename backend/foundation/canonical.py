"""Stable, versioned canonicalization used by Phase 3 integrity hashes."""

import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID


CANONICAL_JSON_VERSION = "iso-smart-canonical-json-v1"


def _normalize(value):
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("canonical timestamps must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite decimals are not canonical")
        return format(value, "f")
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("canonical JSON object keys must be strings")
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("non-finite floats are not canonical")
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_json(value) -> str:
    envelope = {"canonicalization": CANONICAL_JSON_VERSION, "value": _normalize(value)}
    return json.dumps(
        envelope, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def canonical_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

