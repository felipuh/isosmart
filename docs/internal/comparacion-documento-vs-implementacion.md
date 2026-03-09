# Comparacion documento vs implementacion

Fecha: 2026-03-09
Base documental comparada:
- `docs/internal/manual-operacion-por-roles.md`
- `docs/internal/arquitectura-integraciones-multitenancy.md`
- `docs/internal/mapeo-modulos-actuales-clave.md`

## Resumen ejecutivo
- Cobertura funcional por modulo: alta.
- Riesgo principal detectado: inconsistencia de estandar multitenant en modulos AI historicos.
- Estado tras correcciones de esta iteracion: se reducen brechas criticas en `planning`, `resources`, `sca`, compatibilidad de documentos y navegacion de operaciones.

## Matriz de brechas

### B1 - Multitenancy estricto en modulos de negocio
- Referencia documental: `arquitectura-integraciones-multitenancy.md` seccion 3.
- Evidencia previa: `planning/views.py` y `resources/views.py` sin `OrganizationScopedViewSetMixin`.
- Riesgo: filtros manuales parciales, mayor probabilidad de desalineacion entre endpoints.
- Accion aplicada: estandarizacion a `OrganizationScopedViewSetMixin` y uso de `self.get_queryset()` en acciones custom.
- Estado: resuelta.

### B2 - Seguridad tenant en Contexto (SCA)
- Referencia documental: validacion 400/403 por organizacion activa.
- Evidencia previa: `backend/ai_modules/sca/views.py` sin `IsAuthenticated` ni filtro por organizacion.
- Riesgo: lectura cruzada de analisis historicos.
- Accion aplicada: auth obligatoria + resolucion de organizacion activa + filtros por `organization_id`.
- Estado: resuelta.

### B3 - Seguridad tenant en Stakeholders (SIE)
- Referencia documental: checklist multitenancy operativo.
- Evidencia previa: `permission_classes` comentado en viewsets y querysets sin aislamiento por organizacion.
- Riesgo: exposicion de registros entre organizaciones.
- Accion aplicada: `IsAuthenticated` activo, filtrado por organizacion activa (no superuser), y escritura forzada de organizacion en create/update.
- Estado: resuelta parcialmente.
- Nota: el modelo SIE usa `organization` textual (no FK/`organization_id`), por lo que el aislamiento depende de consistencia del nombre de organizacion.

### B4 - Contrato frontend/backend en carga de documentos
- Referencia documental: operacion diaria de modulo Documentos.
- Evidencia previa: frontend enviaba `POST /documents/upload/` sin endpoint backend correspondiente.
- Riesgo: error de subida en runtime.
- Accion aplicada: frontend alineado a `POST /documents/`.
- Estado: resuelta.

### B5 - Acceso operativo a modulo Operaciones desde UI
- Referencia documental: flujo 8.7 en manual por roles.
- Evidencia previa: rutas de operaciones existentes en `App.jsx`, pero sin entrada en sidebar.
- Riesgo: modulo funcional oculto en navegacion principal.
- Accion aplicada: item `operations` agregado en `Sidebar.jsx`.
- Estado: resuelta.

### B6 - Estandar multitenancy en ASB/SPM
- Referencia documental: regla general de aislamiento por organizacion.
- Evidencia actual: modelos `asb/spm` no tienen `organization_id` directo; aislamiento no estandarizado con mixin.
- Riesgo: control tenant inconsistente y dependiente de relaciones indirectas.
- Estado: pendiente estructural.
- Recomendacion: migracion incremental para introducir `organization_id` explicito y adoptar mixin.

## Validacion de flujos documentados (impacto)
- Flujo 8.7 -> 10.2: conservado (no se altero sincronizacion en `operations`/`improvement`).
- Flujo 9.2 -> 10.2: conservado (no se altero sync de hallazgos).
- Flujo 9.3 -> 10.3: conservado (no se altero sync de revisiones).
- Dashboard principal y modulos core: sin cambios de contrato de salida.

## Conclusion
- Se cerraron las brechas operativas y de seguridad mas inmediatas sin romper los flujos E2E documentados.
- Queda una brecha estructural en `asb/spm` por modelo de datos historico sin `organization_id` estandar.
