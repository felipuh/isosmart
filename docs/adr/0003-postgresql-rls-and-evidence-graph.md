# ADR-0003: PostgreSQL, RLS y Compliance Evidence Graph

- Estado: Propuesto
- Fecha: 2026-08-13

## Decisión

PostgreSQL será la fuente transaccional. Las tablas tenant-scoped tendrán `tenant_id` UUID, constraints, RLS forzada y tenant context transaccional; el ORM mantiene defensa adicional. El grafo se implementa inicialmente con relaciones tipadas, índices, vistas y CTE recursivos en PostgreSQL.

La foundation efímera apunta a PostgreSQL 18.6 (minor vigente al 2026-08-13); producción queda condicionada al inventario/certificación del entorno. El runtime transmite tenant con `set_config('app.tenant_id', ..., true)` dentro de cada transacción. Runtime/worker/read-only no son owner ni tienen `BYPASSRLS`; `ENABLE` + `FORCE ROW LEVEL SECURITY` y policies separadas para SELECT/INSERT/UPDATE/DELETE son obligatorias. Ninguna extensión es obligatoria en baseline.

Registro histórico: el Design Gate original evaluó PostgreSQL 18.4. La revalidación oficial previa a implementación elevó únicamente el patch target a 18.6; no cambia la arquitectura PostgreSQL 18 aprobada. PostgreSQL 19 beta/desarrollo continúa fuera de alcance.

## Consecuencias

No se añade base de grafos hasta demostrar límites objetivos con perfiles de traversal/SLO. Conexiones de worker y web deben limpiar contexto entre requests. Migraciones RLS se despliegan por etapas con shadow validation y pruebas de escape.
