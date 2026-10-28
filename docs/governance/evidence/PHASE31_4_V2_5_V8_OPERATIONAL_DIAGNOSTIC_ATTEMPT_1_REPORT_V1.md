# Phase 31.4 V2.5 V8 — Operational Diagnostic Cycle 1 — Attempt 1

## Verdict

`ATTEMPT_1_FAIL`

Blocker operacional observado: `ADMINAPPS_START_FAILURE`, salida 2 al arrancar AdminApps. No se alcanzó Stage EXT 6/6 ni CaptureBundle. Teardown PASS y `ZERO RESIDUAL RESOURCES` verificados independientemente.

## Attempt identity

- Cycle: `Phase 31.4 V2.5 V8 Operational Diagnostic Cycle 1`
- Run ID: `Phase 31.4 V2.5 V8 Operational Diagnostic Cycle 1 Attempt 1`
- Canonical slug: `Phase_31.4_V2.5_V8_Operational_Diagnostic_Cycle_1_Attempt_1`
- Workspace: `/home/felipe/proyectos/isosmart`
- Git commit: `0d2ddfdead408b7cc6cb9c6dbc08707281cb9fb7`; worktree previamente modificado, preservado.
- Inicio UTC: `2026-09-29T01:04:11.807619+00:00`; final UTC: `2026-09-29T01:05:30.332783+00:00`.
- Un único lanzamiento técnico. Attempt 1 consumido; Attempt 2 no iniciado.
- Método: `DisposableEvidenceRunner.run_evidence`, executor `diagnostic`, `allow_runtime_execution=False`, timeouts V8 por defecto.

## Authorization verification

PASS. Padre verificado antes de ejecutar: SHA-256 `c8633d150784c23170585627b1bf3bd738bcf62197998d5ea8e7bd3d9d08aac9`.

Autorización específica one-shot: `PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_ATTEMPT_1_AUTHORIZATION_V1.json`. SHA-256 `488d98c0d74c3ea508841285c0a744b4723d859ce0b55b7bab6d2aed57b5f225`. Consumo atómico registrado en `docs/governance/evidence/runs/Phase_31.4_V2.5_V8_Operational_Diagnostic_Cycle_1_Attempt_1/AUTHORIZATION_CONSUMPTION.json` y `docs/governance/evidence/diagnostic_authorization_consumptions/488d98c0d74c3ea508841285c0a744b4723d859ce0b55b7bab6d2aed57b5f225.json`. El artefacto de autorización permanece inmutable; el consumo reside en los registros separados. No reutilizable para Attempt 2.

## V8 integrity verification

PASS antes y después del intento. SHA-256 del manifest V8: `ed7bed0108e790c93e0c40625b215dde02ae25566b2397533b11b6aae7040946`. Fuentes protegidas: **28**, missing **0**, unexpected **0**, hashes modificados por este trabajo **0**. Verificación histórica V2.4 y 24 hashes de migraciones PASS. Se preservaron los **293 archivos históricos de evidencia** inventariados.

El launcher histórico V6 continúa registrado como `GOVERNANCE_TOOL`, SHA-256 `c3fdeff3ea862ee56d94a706043c69646fc2618ddf82bf604a94353b22cb568f`; no se ejecutó ni editó.

## Pre-flight

PASS. No existían directorio de ejecución, manifest activo, consumo previo ni recursos con las identidades asignadas. No había procesos con el run ID. Inventario de recursos y sockets retenido en `preflight.json`. La asignación canónica usa puertos dinámicos libres seleccionados por el kernel; no se impusieron puertos fijos ni se modificó el allocator V8.

La consulta inicial de Podman dentro del sandbox falló por filesystem de solo lectura. Se repitió únicamente la inspección con acceso permitido fuera del sandbox y pasó antes del lanzamiento. Esto no fue un intento operacional ni un cambio de implementación.

## Resource allocation

Se crearon dos instancias PostgreSQL 18.6, dos bases, dos redes y dos volúmenes nuevos, etiquetados con run slug, autorización y rol. No se reutilizaron recursos históricos.

### adminapps

- Container ID: `90ed3955b76622e6a6a0eefe2451284425f3917aaa4ec5580aa74b6ec3dd84c8`
- Container: `p314_phase_31_4_v2_5_v8_operational_dia_e4c70a7b40_adminapps`
- Network: `p314_phase_31_4_v2_5_v8_operational_dia_e4c70a7b40_adminapps_net`
- Volume: `p314_phase_31_4_v2_5_v8_operational_dia_e4c70a7b40_adminapps_data`
- Database: `p314_phase_31_4_v2_5_v8_o_adminapps_e1725e8ee0`
- Port: `127.0.0.1:40753`
- PostgreSQL: `postgres (PostgreSQL) 18.6 (Debian 18.6-1.pgdg13+2)`
- Estado final de los tres recursos: ausencia verificada.

### isosmart

- Container ID: `ed3435f648c7ad37eb3730fc742064036b44aa0660754de5f08e59c727eca9ef`
- Container: `p314_phase_31_4_v2_5_v8_operational_dia_e4c70a7b40_isosmart`
- Network: `p314_phase_31_4_v2_5_v8_operational_dia_e4c70a7b40_isosmart_net`
- Volume: `p314_phase_31_4_v2_5_v8_operational_dia_e4c70a7b40_isosmart_data`
- Database: `p314_phase_31_4_v2_5_v8_o_isosmart_f3b0ff0bc2`
- Port: `127.0.0.1:39539`
- PostgreSQL: `postgres (PostgreSQL) 18.6 (Debian 18.6-1.pgdg13+2)`
- Estado final de los tres recursos: ausencia verificada.

AdminApps usa el usuario `postgres`; ISO Smart creó 24 roles con prefijo `p314_e4c70a7b401f_`, incluidos migrator, app y roles de dominio. El inventario completo está en EVIDENCE_V1 y `bootstrap_isosmart.log`.

El proceso AdminApps terminó antes de readiness. **V8 no retuvo su PID numérico ni su puerto de servicio asignado**, y no publicó endpoint listo. ISO Smart service no llegó a iniciarse. No se inventan esas identidades.

## State-machine trace

| Timestamp UTC | Transición |
|---|---|
| 2026-09-29T01:04:12.918535+00:00 | — → AUTHORIZED |
| 2026-09-29T01:04:12.959684+00:00 | AUTHORIZED → ALLOCATING |
| 2026-09-29T01:04:16.181378+00:00 | ALLOCATING → RESOURCES_ALLOCATED |
| 2026-09-29T01:04:16.198364+00:00 | RESOURCES_ALLOCATED → BOOTSTRAPPING |
| 2026-09-29T01:04:33.910525+00:00 | BOOTSTRAPPING → READY |
| 2026-09-29T01:04:33.930781+00:00 | READY → PRECREATION_RUNNING |
| 2026-09-29T01:04:34.085532+00:00 | PRECREATION_RUNNING → PRECREATION_PASS |
| 2026-09-29T01:04:34.105996+00:00 | PRECREATION_PASS → STAGE_EXT_RUNNING |
| 2026-09-29T01:05:18.449033+00:00 | STAGE_EXT_RUNNING → FAILED |
| 2026-09-29T01:05:30.316753+00:00 | FAILED → TEARDOWN_COMPLETE |

La secuencia requerida se cumplió. El error entró en FAILED; no se forzó ningún estado. El código genérico conservado por el runner es `UNCLASSIFIED_RUNNER_FAILURE`; el traceback identifica el error concreto de AdminApps. `runner_step=verify_isosmart_postgres_version` es el último comando de infraestructura registrado, no la operación que falló.

## Precreation result

PASS: 9 assertions. Evidencia: `docs/governance/evidence/runs/Phase_31.4_V2.5_V8_Operational_Diagnostic_Cycle_1_Attempt_1/PRECREATION_INTEGRITY/precreation_integrity.json`, SHA-256 `803259b4895fa7510d44780fe931c741dc49540c59dd6ba6d7c08abfd588dd02`.

Bootstrap real: ambas instancias aceptaron SELECT 1; migraciones de ambas aplicaciones completadas con pendientes 0. ISO Smart registró `roles_verified=true` y `session_configuration_verified=true`. Última frontera operacional demostrada: **ROLES_COMPLETE**. No se declara ADMINAPPS_READY ni ninguna frontera posterior.

## Stage EXT

**0/6 PASS; 0 controles evaluados.** Se entró al callback Stage EXT, pero startup falló antes de crear autoridad, entregar eventos o leer identidades.

| Control | Identidad | Resultado individual |
|---|---|---|
| 1/6 | tenant | NOT_EXECUTED — bloqueo previo al control |
| 2/6 | actor | NOT_EXECUTED — bloqueo previo al control |
| 3/6 | tenant_projection | NOT_EXECUTED — bloqueo previo al control |
| 4/6 | user_projection | NOT_EXECUTED — bloqueo previo al control |
| 5/6 | organization | NOT_EXECUTED — bloqueo previo al control |
| 6/6 | process | NOT_EXECUTED — bloqueo previo al control |

Para cada control se esperaba igualdad entre UUID retornado y lectura persistida independiente. Requests, responses, persisted identities y autoridad observada son null porque no se ejecutaron. EVIDENCE_V1 conserva run/correlation IDs, autoridad esperada, timestamp del bloqueo y referencia al log; ese timestamp no se presenta como hora de ejecución del control.

## CaptureBundle

`NOT_REACHED`. No se creó un artefacto CaptureBundle ni se simuló su contenido. Runtime handoff tampoco alcanzado.

## Failure classification

Componente: `docs/governance/tools/phase31_4_v2_5_operational_actions.py:174`, función `service()`; llamada desde `SubprocessOperationalAdapter._start`.

Esperado: arrancar AdminApps usando su backend/manage.py y alcanzar readiness HTTP en puerto dinámico.

Observado:

```text
/home/felipe/proyectos/adminapps/backend/.venv/bin/python: can't open file '/home/felipe/proyectos/isosmart/manage.py': [Errno 2] No such file or directory
```

Causa corroborada por inspección estática: `_start` usa `cwd=context.repository_root`, mientras `service()` ejecuta el intérprete de AdminApps con el argumento relativo `manage.py`. `os.execve` conserva cwd. El archivo de gestión existe en el backend correspondiente, pero no en la raíz de ISO Smart. La resolución errónea es determinista con esos mismos argumentos/cwd; no se repitió la ejecución para demostrarla.

**Única remediation mínima candidata, pendiente de revisión humana:** sustituir `"manage.py"` por `str(root / "manage.py")` en `service()`. No aplicada. Después de aprobación: focused tests de selección de ruta absoluta para AdminApps e ISO Smart, conservando argumentos y entorno; reconciliación sucesora de integridad antes de otro intento con bytes modificados. No se proponen fixes oportunistas adicionales.

## Teardown

PASS. Cleanup canónico entre `2026-09-29T01:05:18.473663+00:00` y `2026-09-29T01:05:30.301133+00:00`; remaining resources `[]`, errors `[]`. Manifest finalizado en `TEARDOWN_COMPLETE`. Se eliminaron exclusivamente recursos de Attempt 1, sin global prune.

## Residual-resource verification

`ZERO RESIDUAL RESOURCES`, comprobado independientemente a `2026-09-29T01:06:35.789610+00:00`:

- Containers, networks y volumes: consultas `exists` devolvieron ausencia para los seis nombres exactos.
- PostgreSQL y runtime de ambas bases: conexiones rechazadas; puertos 40753 y 39539 cerrados.
- Procesos: ningún proceso con entorno del run ID ni launcher activo.
- Servicios: salida 2 observada por el adapter; ningún listener TCP nuevo respecto del pre-flight. El puerto numérico del servicio fallido no fue retenido por V8; la ausencia se demuestra mediante la comparación completa de listeners y procesos.
- Inventarios de contenedores, redes y volúmenes iguales al pre-flight; recursos históricos preservados.
- No se crearon temporales auxiliares; solo se conservaron artefactos de gobernanza/evidencia y manifest finalizado.

La consulta independiente a bases ocurrió tras el teardown y produjo connection refused: sirve como evidencia de ausencia, no como lectura exitosa de migraciones o identidades.

## Evidence artifacts

- Autorización: `docs/governance/evidence/PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_ATTEMPT_1_AUTHORIZATION_V1.json`.
- Evidencia estructurada: `docs/governance/evidence/PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_ATTEMPT_1_EVIDENCE_V1.json`.
- Evidencia operacional canónica: `docs/governance/evidence/runs/Phase_31.4_V2.5_V8_Operational_Diagnostic_Cycle_1_Attempt_1`.
- Preflight, launch marker, excepción/traceback, inspección de fuente, teardown independiente, snapshots y driver de gobernanza: `docs/governance/evidence/PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_ATTEMPT_1_CONTROL_V1`.
- Manifest conserva 37 comandos de infraestructura con timestamps, outputs y resultados.
- Logs de bootstrap conservan resultados live, pending counts y hashes del stdout de migraciones; el stdout íntegro de migrate no lo retiene el flujo V8.
- El driver de observación terminó con exit 0 después de capturar la excepción. Esto **no** equivale a PASS: el manifest y el outcome registran el fallo operacional.
- No se ejecutaron retained tests como sustituto de live proof.

## SHA-256

| Artefacto | SHA-256 |
|---|---|
| Parent authorization | `c8633d150784c23170585627b1bf3bd738bcf62197998d5ea8e7bd3d9d08aac9` |
| V8 integrity | `ed7bed0108e790c93e0c40625b215dde02ae25566b2397533b11b6aae7040946` |
| Attempt authorization | `488d98c0d74c3ea508841285c0a744b4723d859ce0b55b7bab6d2aed57b5f225` |
| Attempt evidence | `fffcf07de770118f5cbbea0d28daf8b5469f317e852cd062971b4791f0ebe6b3` |
| Resource manifest | `681265c5fa844245a249b74287b703a03b58c8730a54775ca21abaac1b49c38a` |
| Independent teardown | `fd4350d2e8dc164b63af31be58c51778c273e3d21bb033be0ac4f543a3403a71` |

Todos los archivos nuevos, incluidos este informe y los registros de consumo, están indexados en `PHASE31_4_V2_5_V8_OPERATIONAL_DIAGNOSTIC_ATTEMPT_1_SHA256_V1.json`. El índice no contiene su propio hash; se publica por separado.

## Repository changes

**Governance/evidence artifacts:** autorización one-shot, driver de invocación clasificado `GOVERNANCE_TOOL`, registro técnico único, manifest/consumo, logs, preflight, verificación independiente, evidencia estructurada, informe e índice SHA-256.

**Source changes:** `0`. **Protected source changes = 0**. No se editaron código protegido, fixtures, migraciones, timeouts, contratos, artefactos históricos ni cambios locales preexistentes. No se crearon commits.

## Retry 20 authorization

`NONE`

## Retry 20 executed

`NO`

## Phase 31.5

`EXECUTION_HELD`

## Exact next step

Revisión humana de la única remediation candidata de resolución de `manage.py`. Antes de cualquier Attempt 2: aprobar/aplicar esa remediation, focused tests y reconciliación de integridad sucesora; después, autorización one-shot propia para el intento elegible. Este trabajo no inició Attempt 2, Retry 20, las 33 fases ni promoción.
