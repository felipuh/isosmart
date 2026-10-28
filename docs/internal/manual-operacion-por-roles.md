# Manual de Operación por Roles

Fecha: 24-02-2026

## 1) Objetivo

Definir cómo opera ISO Smart por tipo de usuario, con pasos prácticos en la interfaz y flujos end-to-end para el ciclo ISO 9001:2015.

Este manual está orientado a operación diaria (no a desarrollo).

---

## 2) Roles del sistema

Roles configurados en backend (`UserProfile.role`):

- `org_admin` (Administrador)
- `iso_manager` (Responsable SGC)
- `auditor` (Auditor)
- `user` (Usuario)
- `viewer` (Solo Lectura)

Nota actual de producto:

- En frontend, la única restricción explícita por ruta es `settings` (solo `org_admin` e `iso_manager`).
- El resto de módulos están protegidos por autenticación general.

---

## 3) Mapa de acceso operativo por rol

## 3.1 `org_admin`

Responsabilidades:

- Administración general de organización y usuarios.
- Supervisión transversal de cláusulas 4 a 10.
- Validación de configuración del sistema.

Accesos clave:

- Todos los módulos del sidebar.
- Configuración (`/settings`).
- Flujos de sincronización operativa (8.7, 9.2, 9.3 → 10.x).

## 3.2 `iso_manager`

Responsabilidades:

- Gobierno del SGC.
- Seguimiento de indicadores, hallazgos, no conformidades y mejora.
- Cierre de brechas ISO por cláusula.

Accesos clave:

- Todos los módulos funcionales.
- Configuración (`/settings`).
- Monitoreo del Dashboard principal y dashboards por módulo.

## 3.3 `auditor`

Responsabilidades:

- Planificación/ejecución de auditorías internas (9.2).
- Registro de hallazgos y seguimiento de su estado.
- Validación de evidencia.

Accesos clave:

- Performance: auditorías, hallazgos, revisiones.
- Consulta de módulos de soporte para evidencia.

## 3.4 `user`

Responsabilidades:

- Carga y mantenimiento de datos operativos del módulo asignado.
- Ejecución de tareas planificadas y actualización de estados.

Accesos clave:

- Módulos funcionales según asignación.
- Sin acceso de configuración avanzada.

## 3.5 `viewer`

Responsabilidades:

- Consulta y seguimiento.
- Verificación de estado y trazabilidad.

Accesos clave:

- Lectura de dashboards y registros.

---

## 4) Flujo base de trabajo (día a día)

## 4.1 Inicio de jornada

1. Iniciar sesión con usuario y organización activa.
2. Validar organización actual en header y contexto.
3. Abrir Dashboard principal (`/`).
4. Revisar progreso por cláusula 4–10.
5. Entrar a módulos con menor avance.

## 4.2 Cierre de jornada

1. Confirmar que registros del día quedaron guardados.
2. Verificar estados de NC/hallazgos/revisiones.
3. Revisar módulo Mejora para sincronizaciones esperadas.
4. Cerrar sesión.

---

## 5) Procedimientos operativos por módulo

## 5.1 Operaciones (Cláusula 8)

Ruta principal:

- `/operations`

Procedimiento estándar (NC 8.7):

1. Ir a `Operaciones` → `No conformidades`.
2. Crear no conformidad con datos mínimos:
   - número, descripción, severidad, etapa, estado.
3. Guardar y verificar que aparezca en listado.
4. Confirmar en módulo Mejora que exista NC sincronizada (`OPS-*`).

Resultado esperado:

- Cada NC de operaciones queda reflejada en Mejora (10.2).

## 5.2 Desempeño (Cláusula 9)

Ruta principal:

- `/performance`

Procedimiento estándar (Hallazgos 9.2):

1. Ir a `Performance` → `Hallazgos`.
2. Crear hallazgo tipo `nc_major` o `nc_minor`.
3. Guardar y verificar estado inicial.
4. Ir a `Mejora` → `No conformidades`.
5. Confirmar existencia de NC `AUD-*`.

Procedimiento estándar (Revisión 9.3):

1. Ir a `Performance` → `Revisiones`.
2. Crear/editar revisión con:
   - oportunidades de mejora y/o decisiones de mejora.
3. Guardar.
4. Ir a `Mejora` → `Mejora Continua`.
5. Confirmar iniciativa `MR-*`.

## 5.3 Mejora (Cláusula 10)

Ruta principal:

- `/improvement`

Procedimiento estándar:

1. Revisar dashboard de Mejora.
2. Verificar NC abiertas, acciones correctivas y mejora continua.
3. Priorizar iniciativas y completar seguimientos.
4. Mantener `status` y `completion_percentage` actualizados.

---

## 6) Flujos end-to-end obligatorios (operación)

## 6.1 Flujo E2E A: 8.7 → 10.2

Actor principal:

- `user` / `iso_manager`

Pasos:

1. Crear NC en Operaciones (`/operations/nonconformities`).
2. Verificar registro en listado de Operaciones.
3. Ir a Mejora (`/improvement/nonconformities`).
4. Verificar NC equivalente (`OPS-*`) con severidad/estado mapeados.

Criterio de éxito:

- Hay trazabilidad completa entre origen operativo y tratamiento en mejora.

## 6.2 Flujo E2E B: 9.2 → 10.2

Actor principal:

- `auditor`

Pasos:

1. Crear auditoría (`/performance/audits`) si no existe.
2. Crear hallazgo NC (`nc_major` o `nc_minor`) en `/performance/findings`.
3. Verificar listado de hallazgos.
4. Abrir Mejora NC y validar creación/actualización automática (`AUD-*`).

Criterio de éxito:

- El hallazgo genera NC de Mejora sin proceso manual adicional.

## 6.3 Flujo E2E C: 9.3 → 10.3

Actor principal:

- `iso_manager`

Pasos:

1. Crear o actualizar revisión por dirección (`/performance/reviews`).
2. Completar campos de mejora (oportunidades/decisiones).
3. Guardar revisión.
4. Ir a `/improvement/continual`.
5. Verificar iniciativa `MR-*`.

Criterio de éxito:

- Las decisiones de dirección alimentan mejora continua con trazabilidad.

---

## 7) Validación rápida de multitenancy (operación)

Objetivo:

- Asegurar aislamiento por organización.

Checklist:

1. Trabajar en Organización A y crear registros.
2. Cambiar organización desde la sesión (si aplica) o usar usuario de Organización B.
3. Confirmar que no se muestran datos de A en B.
4. Confirmar que operaciones sin `organization_id` fallan en APIs críticas.

Criterio de éxito:

- No hay mezcla de datos entre organizaciones.

---

## 8) Errores frecuentes y respuesta operativa

## 8.1 Error 400 `organization_id required`

Causa probable:

- Solicitud API sin organización resoluble.

Acción:

- Validar organización activa de sesión.
- Reintentar flujo desde UI autenticada.

## 8.2 Error 403 por organización

Causa probable:

- `organization_id` enviado no coincide con tenant del token.

Acción:

- Cambiar a organización correcta o corregir request.

## 8.3 No aparece sincronización esperada

Causa probable:

- Tipo de hallazgo no sincronizable o datos incompletos.

Acción:

- Verificar tipo de hallazgo (`nc_major`/`nc_minor` para 9.2→10.2).
- Verificar campos de revisión con contenido de mejora para 9.3→10.3.

---

## 9) Cadencia sugerida de gestión

## 9.1 Semanal

- Revisión de no conformidades abiertas (8.7/10.2).
- Revisión de hallazgos pendientes de cierre (9.2).
- Actualización de acciones correctivas.

## 9.2 Mensual

- Revisión por dirección (9.3).
- Priorización de iniciativas de mejora continua (10.3).
- Control del avance de cláusulas en Dashboard principal.

---

## 10) KPI operativos mínimos recomendados

- % de hallazgos 9.2 convertidos en NC 10.2.
- Tiempo promedio de cierre de NC (10.2).
- % de iniciativas 10.3 en estado `implemented`/`successful`.
- % de cláusulas con avance > 0 en Dashboard.

---

## 11) Referencias internas

- Arquitectura e integraciones: `docs/internal/arquitectura-integraciones-multitenancy.md`
- Índice de documentación: `docs/internal/README.md`
