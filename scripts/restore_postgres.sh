#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_ARTIFACT:?BACKUP_ARTIFACT is required}"
: "${BACKUP_MANIFEST:?BACKUP_MANIFEST is required}"
[ "${BACKUP_MODE:-production}" != production ] || : "${BACKUP_DECRYPTION_COMMAND:?production requires BACKUP_DECRYPTION_COMMAND}"
sha256sum --check "$BACKUP_MANIFEST"
artifact="$BACKUP_ARTIFACT"
tmp=''
if [ "${BACKUP_MODE:-production}" = production ]; then
  tmp="${BACKUP_ARTIFACT}.restore.partial"
  trap 'rm -f "$tmp"' EXIT
  BACKUP_INPUT="$BACKUP_ARTIFACT" BACKUP_OUTPUT="$tmp" sh -c "$BACKUP_DECRYPTION_COMMAND"
  artifact="$tmp"
fi
pg_restore --list "$artifact" >/dev/null
pg_restore --exit-on-error --clean --if-exists --no-owner --no-privileges --dbname "$DATABASE_URL" "$artifact"
printf 'restore=verified\n'
