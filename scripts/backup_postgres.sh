#!/usr/bin/env bash
set -euo pipefail

# Repository-local PostgreSQL backup contract.  Production requires an
# externally managed encryption command; no destination credentials are read
# from this repository.
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_DESTINATION:?BACKUP_DESTINATION is required}"
mode="${BACKUP_MODE:-production}"
mkdir -p "$BACKUP_DESTINATION"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
artifact="$BACKUP_DESTINATION/isosmart-${stamp}.dump"
manifest="$artifact.sha256"
tmp="${artifact}.partial"
trap 'rm -f "$tmp"' EXIT

pg_dump --format=custom --no-owner --no-privileges --file "$tmp" "$DATABASE_URL"
pg_restore --list "$tmp" >/dev/null
if [ "$mode" = "production" ]; then
  : "${BACKUP_ENCRYPTION_COMMAND:?production requires BACKUP_ENCRYPTION_COMMAND}"
  # The configured KMS/age/gpg integration owns cryptography and key handling.
  BACKUP_INPUT="$tmp" BACKUP_OUTPUT="$artifact" sh -c "$BACKUP_ENCRYPTION_COMMAND"
  rm -f "$tmp"
else
  mv "$tmp" "$artifact"
fi
sha256sum "$artifact" > "$manifest"
printf 'backup=%s\nmanifest=%s\n' "$artifact" "$manifest"
