# I18N Pattern Guardrails (ISO Smart)

## Objetivo
Establecer un patrón único para que toda nueva UI salga multilenguaje desde el primer commit, manteniendo simplicidad y consistencia.

## Patrón obligatorio
- Todas las etiquetas visibles en UI deben pasar por `t()`.
- Evitar strings hardcoded en componentes (`jsx`, `tsx`).
- Estructura de claves recomendada:
  - `settings.<modulo>.<seccion>.<campo>`
  - `dashboard.<modulo>.<seccion>.<campo>`
  - `common.buttons.*`, `common.messages.*`, `common.forms.*`
- Para labels de dominio (`status`, `payment_method`) usar mapas por clave, no literales inline.
- Mensajes de éxito/error de acciones UI deben ir en `messages` del módulo.

## Convenciones
- Fechas: usar locale derivado de `language` (`es-LATAM` => `es-ES`, `en`, `pt`).
- Placeholder y tooltips también van por `t()`.
- Evitar mezclar `literals.*` y claves semánticas en una misma pantalla nueva; preferir claves semánticas.

## Checklist antes de merge
1. ¿La pantalla usa `useI18n()`?
2. ¿No hay textos hardcoded visibles?
3. ¿Claves agregadas en `es-LATAM`, `en`, `pt`?
4. ¿Mensajes de errores/éxito localizados?
5. ¿Build frontend pasa?

## Comando útil para auditoría rápida
Buscar posibles literales hardcoded en frontend:

```bash
grep -RIn "\>[^<{]*[A-Za-zÁÉÍÓÚáéíóúñÑ][^<{]*\<" frontend/src/components frontend/src/features | head -n 200
```

> Nota: filtrar falsos positivos (nombres de iconos, clases CSS, comentarios).
