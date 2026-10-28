# ADR-0004: eventos mediante transactional outbox

- Estado: Propuesto
- Fecha: 2026-08-13

## Decisión

Los cambios de dominio y su `DomainEvent`/outbox se persisten en la misma transacción. Un dispatcher con lease publica después del commit. Consumers deduplican por `event_id`, preservan `trace_id`, registran intentos y soportan reintentos/DLQ.

La primera implementación usa PostgreSQL como durabilidad y Celery/Redis existente como señal/worker. Ordering es por agregado, entrega al menos una vez e idempotencia mediante `EventInbox/ConsumerReceipt(consumer,event_id)` y business keys. El endpoint genérico de publicación de eventos no autoriza event injection público.

## Consecuencias

Se evita publicar cambios que luego hagan rollback. Antes de incorporar broker especializado puede utilizarse PostgreSQL + Celery/Redis existente; la selección definitiva depende de volumen y SLO medidos.
