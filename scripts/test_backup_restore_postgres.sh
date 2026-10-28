#!/usr/bin/env bash
# Disposable local proof for the repository backup/restore contract.
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run_id="e08-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
container="isosmart-${run_id}"
volume="isosmart-${run_id}-data"
work_dir="$(mktemp -d)"
db_password="$(openssl rand -hex 24)"
source_db="source_${RANDOM}"
target_db="target_${RANDOM}"

cleanup() {
  podman rm --force "$container" >/dev/null 2>&1 || true
  podman volume rm "$volume" >/dev/null 2>&1 || true
  rm -rf "$work_dir"
}
trap cleanup EXIT

podman volume create "$volume" >/dev/null
podman run --detach --name "$container" --publish 127.0.0.1::5432 \
  --volume "${volume}:/var/lib/postgresql:U" --env "POSTGRES_PASSWORD=$db_password" \
  docker.io/library/postgres:18.6 >/dev/null
port="$(podman port "$container" 5432/tcp | sed -n 's/.*:\([0-9][0-9]*\)$/\1/p')"
for _ in $(seq 1 60); do
  if PGPASSWORD="$db_password" psql "postgresql://postgres@127.0.0.1:${port}/postgres" -c 'SELECT 1' >/dev/null 2>&1; then break; fi
  sleep 1
done
PGPASSWORD="$db_password" psql "postgresql://postgres@127.0.0.1:${port}/postgres" -c 'SELECT 1' >/dev/null
PGPASSWORD="$db_password" psql "postgresql://postgres@127.0.0.1:${port}/postgres" -c "CREATE DATABASE ${source_db}" >/dev/null
PGPASSWORD="$db_password" psql "postgresql://postgres@127.0.0.1:${port}/${source_db}" -c 'CREATE TABLE proof_marker (id integer PRIMARY KEY, marker text NOT NULL)' >/dev/null
PGPASSWORD="$db_password" psql "postgresql://postgres@127.0.0.1:${port}/${source_db}" -c "INSERT INTO proof_marker VALUES (1, 'phase31_5_e08_synthetic')" >/dev/null

database_url="postgresql://postgres:${db_password}@127.0.0.1:${port}/${source_db}"
if DATABASE_URL="$database_url" BACKUP_DESTINATION="$work_dir" BACKUP_MODE=production bash "$root_dir/scripts/backup_postgres.sh" >/dev/null 2>&1; then
  echo 'production backup unexpectedly allowed without encryption command' >&2; exit 1
fi
DATABASE_URL="$database_url" BACKUP_DESTINATION="$work_dir" BACKUP_MODE=test bash "$root_dir/scripts/backup_postgres.sh" >/dev/null
artifact="$(find "$work_dir" -name '*.dump' -print -quit)"
manifest="${artifact}.sha256"
pg_restore --list "$artifact" >/dev/null
sha256sum --check "$manifest" >/dev/null
PGPASSWORD="$db_password" psql "postgresql://postgres@127.0.0.1:${port}/postgres" -c "CREATE DATABASE ${target_db}" >/dev/null
DATABASE_URL="postgresql://postgres:${db_password}@127.0.0.1:${port}/${target_db}" BACKUP_ARTIFACT="$artifact" BACKUP_MANIFEST="$manifest" BACKUP_MODE=test bash "$root_dir/scripts/restore_postgres.sh" >/dev/null
marker="$(PGPASSWORD="$db_password" psql -At "postgresql://postgres@127.0.0.1:${port}/${target_db}" -c 'SELECT marker FROM proof_marker WHERE id=1')"
test "$marker" = 'phase31_5_e08_synthetic'
printf 'bad  %s\n' "$artifact" > "${manifest}.bad"
if DATABASE_URL="postgresql://postgres:${db_password}@127.0.0.1:${port}/${target_db}" BACKUP_ARTIFACT="$artifact" BACKUP_MANIFEST="${manifest}.bad" BACKUP_MODE=test bash "$root_dir/scripts/restore_postgres.sh" >/dev/null 2>&1; then
  echo 'invalid backup manifest unexpectedly accepted' >&2; exit 1
fi
echo 'BACKUP_RESTORE_PROOF=PASS'
