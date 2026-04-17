# Smart3AI Frontend Baseline Unificada

## Alcance
Base comun para cualquier frontend nuevo o refactor de:
- IsoSmart (React + i18n por claves)
- AdminApps (React Admin)
- Landing (HTML/CSS/JS + i18n)

## Objetivo
Construir interfaces profesionales, modernas, accesibles y escalables, manteniendo compatibilidad funcional y calidad visual total.

## Reglas Criticas de Compatibilidad
1. No romper rutas, contratos de componentes, hooks ni flujo de autenticacion.
2. No cambiar endpoints, payloads ni integraciones IA sin decision de arquitectura.
3. Mantener estructuras existentes y refactorizar de forma incremental.

## Multilenguaje Obligatorio
1. No eliminar o renombrar claves existentes.
2. No hardcoded para textos visibles en modulos con i18n.
3. Nuevas claves siempre en todos los idiomas habilitados del proyecto.

## UX Baseline
1. Cada vista debe contemplar:
- loading
- empty
- error recuperable
- success
2. Feedback inmediato en acciones importantes.
3. Jerarquia visual clara en contenido y CTA.
4. Responsive real: mobile/tablet/desktop.

## Baseline Visual
1. Sistema consistente de:
- espaciado
- tipografia
- color
- sombras
- radios
2. Estados visuales accesibles: hover/focus/active/disabled.
3. Contraste compatible con AA.

## Baseline de Accesibilidad
1. Navegacion completa por teclado.
2. Focus visible en todos los controles.
3. ARIA semantica en menus, overlays y controles dinamicos.
4. aria-live para feedback dinamico.
5. reduced-motion para usuarios sensibles.

## Baseline de IA UX
1. Mostrar fase del flujo: iniciando, procesando, listo, error.
2. Respuesta estructurada por bloques:
- resumen
- hallazgos
- recomendaciones
- siguiente accion
3. Mensajes de error accionables y no ambiguos.

## Baseline de Performance
1. Lazy loading por modulo/pagina.
2. Minimizar rerenders y props inestables.
3. Skeletons para latencia percibida.
4. CSS modular y reutilizable.

## Definition of Done (DoD)
- [ ] No regresiones funcionales.
- [ ] i18n respetado sin hardcoded.
- [ ] Accesibilidad minima validada.
- [ ] Estados UX implementados.
- [ ] Build/lint/smoke check OK.
- [ ] Cambios documentados por archivo.

## Prompt Maestro Unificado (copiar/pegar)
"Actua como Tech Lead Frontend Senior experto en React, UI/UX moderno, accesibilidad WCAG AA y producto SaaS con IA.

Contexto:
- Proyecto: [IsoSmart/AdminApps/Landing/Otro]
- Stack: [React/Vite/Tailwind o HTML/CSS/JS]
- Modulo: [nombre]
- Restricciones: No romper rutas, endpoints, integraciones ni i18n existente.

Objetivos de ejecucion:
1) Modernizar UI sin alterar logica de negocio.
2) Garantizar consistencia visual profesional en toda la interfaz.
3) Reforzar accesibilidad (teclado, focus visible, ARIA, reduced-motion).
4) Mejorar UX de estados (loading, empty, error, success).
5) Optimizar performance (lazy loading, rerender controlado, componentes desacoplados).
6) Mantener compatibilidad con integraciones IA y contratos actuales.

Reglas de i18n:
- No eliminar/renombrar claves existentes.
- No hardcoded en vistas multilenguaje.
- Toda nueva clave debe incluir traducciones completas.

Entregables:
- Codigo actualizado por archivo con enfoque seguro.
- Explicacion de impacto funcional y visual.
- Checklist de regresion ejecutado.
- Recomendaciones de fase 2 (arquitectura, diseno system, IA UX)."