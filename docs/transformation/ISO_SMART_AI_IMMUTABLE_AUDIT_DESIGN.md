# ISO Smart AI — foundation de auditoría inmutable

## Claim preciso

La foundation será **append-only para roles de aplicación y tamper-evident**, no físicamente indestructible. Sólo puede llamarse `ImmutableAuditLog` cuando runtime/worker carezcan de UPDATE/DELETE/TRUNCATE y las alteraciones privilegiadas sean detectables y gobernadas.

## Registro mínimo

`log_id bigint identity/uuidv7`, `tenant_id` (nullable sólo para stream platform), `stream_id`, `stream_sequence`, `actor_type`, `actor_id`, `action`, `entity_type`, `entity_id`, `before_hash`, `after_hash`, `payload_hash`, `payload_schema_version`, `trace_id`, `causation_id`, `occurred_at timestamptz`, `previous_entry_hash`, `entry_hash`, `source`, `classification`, `retention_class`.

El payload completo sólo se conserva cuando es necesario, redacted y cifrado conforme clasificación; hashes usan serialización canónica versionada. Un hash no demuestra veracidad del dato original, sólo cambio respecto del valor comprometido.

## Append path y grants

- `isosmart_app`/`worker` no reciben DML directo sobre `audit.immutable_audit_log`.
- Escritura mediante una función mínima `SECURITY DEFINER` propiedad de un rol no-login, `search_path` fijo, argumentos tipados y execute grant estrecho; alternativa: rol `audit_writer` asumible sólo por la función.
- Runtime recibe cero UPDATE, DELETE, TRUNCATE y ALTER. Un trigger defensivo rechaza UPDATE/DELETE para todos salvo un break-glass role explícito; grants siguen siendo el control primario.
- La API pública es read-only, tenant-scoped y redacted. La mitigación actual de `AssistantAuditLog` no equivale aún a esta foundation.

## Hash chain

Chain por `(tenant_id, stream_id)` evita un lock global. Cada append asigna secuencia monotónica bajo lock/advisory lock y calcula:

```text
entry_hash = SHA-256(canonical(version, tenant, stream, sequence, actor,
  action, entity, before_hash, after_hash, payload_hash, trace, occurred_at,
  previous_entry_hash))
```

Un verificador periódico recalcula secuencias/hashes y publica métricas/alertas. Checkpoints firmados o manifests exportados a object storage WORM/retention-lock aportan evidencia fuera de la DB; se requiere custody y restore verification. La chain es opcional sólo si un mecanismo externo equivalente se aprueba antes del claim “tamper-evident”.

## Cobertura

Registrar: auth/denials relevantes sin secretos; projection/reconcile; role/policy/entitlement decisions; create/update/delete/supersede de registros materiales; normative releases; evidence/document hashes; recommendations/basis; approvals/rejections; actions/rollback/effectiveness; event replay/dead-letter; exports; admin/break-glass; retention/privacy operations; migrations/backfills.

## Retención, privacidad y export

- Retention por clase se aprueba con Legal/Data Owner; no se inventa un plazo único.
- Minimización: IDs opacos y hashes; no copiar documentos, prompts sensibles o tokens al log.
- Una solicitud de privacidad puede borrar/anonimizar el dato fuente según ley, pero el audit conserva un tombstone/pseudonymous proof cuando legalmente permitido. Si debe borrarse también el audit, se ejecuta una operación privilegiada documentada que rompe/segmenta la chain, conserva manifest de razón/autoridad y reinicia stream; nunca se oculta.
- Export usa formato canónico versionado, manifest de rango/row count/root hashes, firma, encryption y chain of custody. Restore debe revalidar chain + manifests.

## Break-glass

Credencial vaulted, MFA, dual approval, ticket/incidente, duración y scope mínimos, session recording/log externo, export pre/post, reconcile y revisión independiente. Una mutación excepcional no se disfraza: genera un `audit_integrity_exception` en un canal externo y bloquea el claim de integridad hasta cerrar investigación.

## Pruebas de aceptación

Runtime/worker/read-only no pueden UPDATE/DELETE/TRUNCATE; append function valida tenant/actor/trace; A no lee B; no tenant no lee/escribe; payload canonicalization es estable; concurrent sequence no duplica; alter/delete privilegiado simulado es detectado; export/verify/restore funcionan; redaction impide secrets/PII prohibida; privacy workflow deja evidencia conforme policy.
