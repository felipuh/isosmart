# ISO Smart AI — transactional outbox e inbox

## Decisión

Primera etapa: PostgreSQL 18 + worker Celery/Redis existente como señal/ejecutor. No se introduce Kafka, RabbitMQ ni NATS sin volumen, ordering, retention o SLO que lo justifique. La durabilidad está en PostgreSQL; Redis no es system of record.

```text
business command
  -> one PostgreSQL transaction
     [aggregate changes + DomainEvent + TransactionalOutbox]
  -> commit
  -> dispatcher leases rows
  -> publish/dispatch at least once
  -> consumer EventInbox/ConsumerReceipt + effects atomically
```

## Registros

### DomainEvent (append-only)

`event_id uuidv7 PK`, `tenant_id uuid` (nullable sólo para tipos system allow-listed), `event_type`, `aggregate_type`, `aggregate_id`, `aggregate_version`, `schema_version`, `payload jsonb`, `occurred_at timestamptz`, `trace_id`, `causation_id`, `correlation_id`, `source`, `actor_type`, `actor_id`, `payload_hash`. Event type + schema version identifican un contrato inmutable.

### TransactionalOutbox

`outbox_id uuidv7`, `event_id UNIQUE FK`, `tenant_id`, `destination`, `partition_key`, `available_at`, `lease_owner`, `lease_expires_at`, `publish_attempts`, `last_error_code`, `published_at`, `dead_lettered_at`, timestamps. Payload canónico se toma del DomainEvent o snapshot hash-verificado; no mantener dos payloads divergentes.

### EventInbox / ConsumerReceipt

`receipt_id`, `event_id`, `tenant_id`, `consumer_name`, `schema_version`, `payload_hash`, `received_at`, `processing_started_at`, `processed_at`, `attempts`, `status`, `last_error_code`, `effect_reference`; `UNIQUE(consumer_name,event_id)`. Para webhooks externos también guarda signature key ID, timestamp/nonce y source external event ID tras redacción.

## Atomicidad e idempotencia

- El servicio de aplicación crea aggregate/event/outbox en la misma `transaction.atomic`; no se publica dentro de la transacción.
- Dispatcher usa `SELECT ... FOR UPDATE SKIP LOCKED`, lease acotado y update condicional. Crash tras publish antes de `published_at` causa duplicado permitido.
- Consumer inserta/locks receipt y aplica efecto en una transacción. Un receipt `processed` retorna éxito sin repetir; handlers usan business idempotency keys además del receipt.
- Mismo event ID con payload hash distinto es forgery/conflict: quarantine + alerta, nunca overwrite.

## Ordering, retry y poison

- Garantía baseline: ordering por agregado mediante `partition_key = tenant_id:aggregate_type:aggregate_id` y `aggregate_version`; no existe ordering global.
- Consumer rechaza gaps que requieran orden, reintenta después; eventos conmutativos documentan esa propiedad.
- Backoff exponencial con jitter, máximo/ventana configurable por consumer; errores permanentes (`unknown_schema`, bad signature, invariant violation) no se reintentan ciegamente.
- Poison messages pasan a estado dead-letter en PostgreSQL con error sanitizado. DLQ externo es opcional futuro; nunca se borra la evidencia del fallo.
- Alertas: oldest unpublished age, ready depth, attempts, lease expirations, dead-letter count, duplicate receipts, schema rejects y per-tenant lag.

## Replay

Replay es comando administrativo explícito: selección por IDs/tipo/tenant/ventana, dry-run, schema compatibility/upcaster aprobado, reason/ticket, actor, new replay correlation ID y audit. El event original no cambia. Consumers deben diferenciar reconstrucción de side effects externos; acciones no reversibles requieren human gate y no se replay automáticamente.

## AdminApps ingress

Eventos de identity/tenant/entitlement/subscription se verifican criptográficamente antes del Inbox. `payment.confirmed` sólo se acepta de la autoridad acordada; nunca se genera por redirect del navegador ni por ISO Smart. Unknown tenant/source version conflict queda quarantined; no crea una nueva identidad por heurística.

## Catálogo inicial reconciliado

Los 14 eventos oficiales son candidatos de dominio: `payment.confirmed`, `tenant.provisioned`, `iso9000.foundation.completed`, `context.signal.detected`, `stakeholder.requirement.changed`, `kpi.threshold.breached`, `supplier.performance.degraded`, `customer.complaint.received`, `change.requested`, `document.updated`, `measurement.out_of_tolerance`, `audit.finding.created`, `nonconformity.detected`, `standard.edition.published`. Ownership definitivo de los dos primeros es AdminApps; cada uno requiere schema/contract test antes de consumo.

El endpoint OpenAPI genérico `POST /v1/events` no se publica como event injection. Se reemplaza incrementalmente por comandos autorizados o webhooks tipados, signed, rate-limited e idempotentes.

## Retención y operación

Retention de DomainEvent/Inbox/Outbox se aprueba por legal/replay needs. Purge, si existe, conserva manifest/hashes y no rompe audit/provenance. Backups incluyen event tables y se prueban restores. El dispatcher usa el worker role tenant-scoped; un enumerador de plataforma puede leasear filas, pero cada handler abre una transacción con el tenant del envelope y valida que coincida con projection/aggregate.

## Gate de implementación

Pruebas obligatorias: rollback no deja event/outbox; commit crea ambos; duplicate publish; crash/lease expiry; duplicate consumer; hash mismatch; out-of-order; poison/DLQ; replay auditado; RLS A/B/no tenant; pool/worker bleed; AdminApps signature/replay/source-version. Sin estas pruebas, “event-driven” no está validado.
