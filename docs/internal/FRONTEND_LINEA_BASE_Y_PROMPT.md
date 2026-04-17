# Linea Base Frontend + Prompt Maestro (IsoSmart)

## Objetivo
Este documento define la linea base obligatoria para evolucionar el frontend sin romper compatibilidad funcional, multilenguaje ni integraciones existentes.

## Principios No Negociables
1. No romper rutas, hooks, props, contratos de componentes ni endpoints.
2. Mantener compatibilidad con integraciones IA actuales (sin cambiar URL, payload o claves de API).
3. No eliminar ni renombrar claves de traduccion existentes.
4. No introducir texto duro en pantallas multilenguaje.
5. Aplicar mejoras visuales sin alterar reglas de negocio.

## Estandar UI/UX
1. Sistema visual consistente (espaciado, tipografia, color, sombras, radios, estados).
2. Jerarquia clara: titulo, subtitulo, acciones primarias/secundarias, contenido.
3. Estados obligatorios por vista:
- loading
- empty
- error
- success/confirmation
4. Responsive first: mobile, tablet, desktop.
5. Interacciones con feedback: hover, focus, disabled, progress.

## Reglas de Multilenguaje (IsoSmart)
1. Mantener intactas las claves existentes.
2. Nuevos textos solo con nuevas claves en I18nContext.
3. Evitar cadenas literales en JSX para contenidos visibles.
4. Validar que cada nueva clave tenga traduccion en es-LATAM, en y pt.

## Reglas de IA UX
1. Mostrar estado del flujo IA: preparando, procesando, resultado, error recuperable.
2. Mensajes de error accionables (que hacer despues).
3. Resultado IA presentado en bloques escaneables:
- resumen
- hallazgos
- recomendaciones
- proximo paso
4. Mantener trazabilidad de contexto (organizacion, filtro activo, fecha).

## Accesibilidad (AA)
1. Todo control interactivo debe tener nombre accesible (aria-label o texto visible).
2. Focus visible consistente.
3. Navegacion por teclado completa (Tab, Shift+Tab, Enter, Escape).
4. aria-live en zonas de feedback dinamico.
5. Soporte prefers-reduced-motion.

## Performance Baseline
1. Lazy loading para modulos pesados por ruta.
2. Evitar rerenders innecesarios (memo, useMemo/useCallback cuando aplique).
3. Skeletons en cargas > 300ms.
4. Mantener CSS reusable y evitar sobre-estilos duplicados.

## Checklist de PR (obligatorio)
- [ ] No se rompieron rutas ni contratos.
- [ ] Sin hardcoded en vistas multilenguaje.
- [ ] Nuevas claves i18n agregadas en 3 idiomas.
- [ ] Estados loading/empty/error implementados.
- [ ] Navegacion por teclado validada.
- [ ] Build local OK.

## Prompt Maestro para Nuevos Proyectos
Usa este prompt como plantilla base:

"Actua como Tech Lead Frontend Senior experto en React, UI/UX moderno, accesibilidad WCAG AA y experiencia de IA en producto SaaS.

Contexto del proyecto:
- Stack: [React/Vite/Tailwind/etc]
- Tipo: [B2B SaaS / Dashboard / Landing]
- Modulo principal: [nombre]
- Restricciones: No romper rutas, endpoints ni contratos existentes.

Objetivos:
1) Profesionalizar UI sin cambiar logica de negocio.
2) Mantener y extender i18n sin hardcoded.
3) Mejorar UX de estados (loading/empty/error/success).
4) Mejorar accesibilidad (focus visible, teclado, aria-live, roles).
5) Optimizar performance percibida y estructura de componentes.

Entregables:
- Codigo actualizado con cambios seguros y modulares.
- Resumen por archivo con justificacion de impacto.
- Checklist de regresion funcional ejecutado.
- Recomendaciones fase 2 (arquitectura, diseno, IA UX).

Criterios de calidad:
- Sin romper compatibilidad existente.
- Sin eliminar claves de traduccion previas.
- Sin modificar endpoints ni autenticacion.
- Build/lint en estado correcto."