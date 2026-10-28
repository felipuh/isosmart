# ISO Smart AI — Technology Compatibility Matrix

Fecha: 2026-08-13. No se hicieron upgrades. Versiones son manifests/locks/entornos locales; no implican soporte aprobado.

## Runtime/host

| Capa | Host observado | AdminApps | ISO Smart | MedSupplier | Baseline recomendado inicial |
|---|---|---|---|---|---|
| OS | Rocky Linux 9.8, kernel 5.14 | mismo host | mismo host | mismo host | RHEL/Rocky 9 compatible |
| Python | sistema 3.9.25 | venv 3.9; CI 3.11/3.12 | venv 3.12.13; CI 3.9 | venv 3.9/3.12; CI 3.12 | Python 3.12.x en runtime/CI |
| Node/npm | host 24.18/11.16 | CI Node 20 | CI Node 20 | CI Node 20 | Node 20.x + npm lock v3 inicialmente |
| PostgreSQL | cliente 18.4 observado durante discovery; servidor no confirmado/no ready | PostgreSQL config | PostgreSQL config | PostgreSQL config | Foundation efímera: 18.6; producción sólo tras inventario/certificación |
| Redis | binario no encontrado | no | Celery assumption localhost | Celery assumption localhost | Redis gestionado/versionado si se conserva Celery |
| Container | Docker ausente; Podman presente no consultable | sin Dockerfile | sin Dockerfile | sin Dockerfile | No introducir sin ADR/necesidad |
| Web/app | nginx 1.20.1 | Gunicorn | Nginx/Gunicorn | Nginx/Gunicorn/systemd | Nginx + Gunicorn con manifests comunes |

## Backend

| Componente | AdminApps | ISO Smart | MedSupplier | Decisión |
|---|---:|---:|---:|---|
| Django | 4.2.22 | 4.2.22 | 4.2.22 | KEEP; no major ahora |
| DRF | 3.15.2 | 3.15.2 | 3.15.2 | KEEP |
| SimpleJWT | 5.4.0 | 5.4.0 | 5.4.0 | KEEP+HARDEN issuer/audience |
| PostgreSQL driver | psycopg2-binary 2.9.10 | 2.9.10 | 2.9.10 | Freeze; evaluar psycopg3 luego |
| CORS/filter | 4.3.1/23.5 | 4.9/25.1 | 4.9/25.1 | Alinear patch/minor tras contracts |
| requests/PyJWT | 2.32.3/2.8 | 2.32.5/2.10.1 | 2.32.5/2.10.1 | Alinear coordinadamente |
| cryptography/Pillow | 46.0.3/10.2 | 46.0.7/11.3 | equivalente ISO | Alinear tras SCA/compatibility |
| Celery/Redis | no | 5.4/5.0.1 | 5.4/5.0.1 | KEEP+HARDEN env/TLS/queues |
| OpenAPI | no tooling | no tooling | no tooling | NEW drf-spectacular o decisión común |
| Tests | Django unittest | Django unittest | Django unittest | KEEP; sumar PostgreSQL/contract |
| Lint/types | sin baseline común | sin ruff/mypy visible | sin baseline común | NEW baseline gradual |
| Security | checks parciales | throttling/headers/lockout | gaps CSRF/key | SAST/SCA/SBOM + shared auth tests |

ISO Smart tiene dos entornos locales: `.venv` coincide con Python 3.12/Django 4.2; `.venv312` contiene Django 6/DRF 3.17 y no psycopg2. El segundo no es baseline y debe aislarse/retirarse después de reproducibilidad. Los requirements raíz gigantes divergen de `backend/requirements.txt` mínimos.

## Frontend y design system

| Componente | AdminApps | ISO Smart | MedSupplier | Baseline |
|---|---:|---:|---:|---|
| React/DOM | lock 19.2.7 | manifest 19.2.0 | 19.2.0 | React 19.2 patch común |
| Vite | 8.0.16 | 8.0.16 | 8.0.16 | KEEP |
| Router | lock 7.18 | manifest 7.10/resuelto por lock | similar | Fijar versión resuelta común |
| Axios | lock 1.18.1 | manifest 1.13/resuelto lock | similar | Fijar lock común probado |
| TypeScript | no | no | no | Introducción gradual para generated client |
| ESLint | 10.6 | 9.39 | 9.39 | Alinear después de runtime/contracts |
| E2E | limitado | Playwright 1.58.2 | Playwright 1.58.2 | Playwright común |
| Query/forms/a11y unit | no baseline | no baseline | no baseline | Selección ecosistémica, no aislada |
| Design system | consumidor | alias source parcial | consumidor | `@smart3ai/design-system` beta versionada |

El design system acepta React >=19 y ya ofrece buttons/forms/tables/dialog/loading/overlays. Los tres consumidores usan aliases al source checkout: útil en desarrollo, frágil para releases. Publicar tarball/package versionado y añadir consumer smoke antes de quitar aliases.

## Data

| Tema | AS-IS | Baseline objetivo |
|---|---|---|
| Engine | PostgreSQL configurado; servidor real no inventariado | PostgreSQL 18.6 para POC efímero; producción condicionada a inventario/compatibilidad/restore |
| Migrations | Django por servicio | forward/backward/drift + staging drill |
| Tenant | UUID SoR AdminApps; int+external UUID en ISO | UUID projection + RLS/defensa app |
| Extensions | no inventariadas | Allow-list; pgcrypto/vector solo por necesidad |
| Audit | logs mutables/fragmentados | append-only + trace + export WORM opcional |
| Backup | MedSupplier tiene mejores runbooks; ISO/Admin incompletos | encrypted off-host + PITR + restore tests |

## Infrastructure/SRE

- CI AdminApps está duplicado y uno usa DB port MySQL 3306 pese a PostgreSQL.
- ISO CI usa Python 3.9/root requirements y no tiene gate general frontend, deploy check ni PostgreSQL.
- MedSupplier CI es la referencia más completa: Python 3.12, migration drift, deploy check, lint/build/E2E.
- ISO `/health` de Nginx es estático y su health Django no forma una separación liveness/readiness robusta. MedSupplier tiene mejor precedente DB-aware.
- Logs tienen request ID pero no JSON/trace end-to-end; no hay métricas/traces/alerts activas verificadas.
- Redis URLs están hardcoded localhost, sin auth/TLS/queue policy. Gunicorn ISO contiene paths/usuario stale.
- No fijar RPO/RTO en esta auditoría; Product/SRE deben aprobarlos. Requerir WAL/PITR, off-host encrypted retention y restore evidence.

## Baseline única y secuencia

Baseline inicial conservadora: Rocky/RHEL9, Python 3.12.x, Node 20.x, Django 4.2.22, DRF 3.15.2, SimpleJWT 5.4, psycopg2 2.9.10, React 19.2, Vite 8, npm lock v3, Nginx/Gunicorn y Redis/Celery solo donde ya se usa. PostgreSQL 18.6 es el target de implementación de la foundation efímera por soporte, mantenimiento vigente y UUIDv7 nativo; el target productivo permanece condicionado y no se deduce sólo del cliente 18.4 observado durante discovery. El Design Gate original evaluó 18.4; esta corrección cambia sólo el patch target y excluye PostgreSQL 19 beta/desarrollo.

Orden:

1. Rotar/retirar secretos versionados y default key de MedSupplier mediante corrida autorizada.
2. Crear locks reproducibles separados runtime/dev/AI; unificar Python 3.12 y Node 20 en CI.
3. Formalizar contrato AdminApps v1, API keys hash/scoped/rotatable, JWT issuer/audience y tests fail-closed.
4. Añadir PostgreSQL CI/RLS y obtener inventario real de server/extensions/backups/pools.
5. Alinear patches backend: provider AdminApps primero, contracts, luego ISO/Med consumers.
6. Empaquetar design system y ejecutar consumer smoke en los tres.
7. Evaluar majors (Django/DRF/Node/PostgreSQL) solo en iniciativa coordinada con staging/canary/rollback.

Rollback de cada alineación: lock/image anterior, sin mezclar upgrade con migración de dominio o retiro de compatibilidad.
