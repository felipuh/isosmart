# Blueprint de implementacion - Onboarding conversacional IsoSmart

Fecha: 2026-04-10
Estado: Aplicado como guia oficial de ejecucion incremental sin ruptura

## Objetivo
Aterrizar el onboarding conversacional con ISO Coach y Gemelo Digital ISO sobre la base actual de IsoSmart, preservando compatibilidad con flujos existentes.

## Estado actual confirmado
- Frontend cuenta con wizard de onboarding y orquestacion inicial.
- Backend ya expone endpoints para estado de onboarding, finalizacion y orquestacion.
- Existe soporte de tono preferido (manager/technical) y perfil inicial de organizacion.
- Existe base de billing para evolucionar a pagador separado.

## Diseño de experiencia objetivo (doble panel)
- Panel izquierdo: conversacion ISO Coach, preguntas adaptativas por expertise y selector de tono gerencial/tecnico.
- Panel derecho: Gemelo Digital ISO en tiempo real con:
  - alcance preliminar
  - mapa de procesos
  - partes interesadas
  - top riesgos/oportunidades
  - barra de progreso del sistema base

## Etapas funcionales
1. Bienvenida inteligente (rol, expertise, tamano)
2. Radiografia del negocio por nivel
3. Proposito y metas del lider
4. Esqueleto ISO automatico y momento WOW (20%)
5. Ruta adaptativa por expertise
6. Roadmap automatico 3/6/12 meses

## Flujo de pago separado (usuario vs pagador)
- Entidades de referencia:
  - UserAccount (operador)
  - BillingAccount (responsable de pagos)
  - ContractWorkspace (espacio SGC)
- Reglas UX:
  - no pedir pago antes del valor visible
  - mostrar checkout luego del momento WOW
  - permitir invitar pagador por email/whatsapp
  - mantener avance en modo lectura hasta activacion

## Plan tecnico incremental recomendado
### Fase A - UX onboarding conversacional
- Extender OnboardingPage con layout doble panel.
- Hidratar panel derecho con snapshot incremental de orquestacion.
- Agregar indicador de confianza del diagnostico.

### Fase B - Motor de rutas y tono
- Formalizar reglas de adaptive route por expertise.
- Persistir tono elegido y aplicarlo en respuestas de IA y textos clave.

### Fase C - Pagador delegado
- Introducir BillingAccount desacoplado.
- Invitar responsable de pagos con token firmado y expiracion.
- Activacion por webhook del PSP y estado de gracia configurable.

### Fase D - Observabilidad y calidad
- Medir drop-off por etapa.
- Medir tiempo de finalizacion y activacion a dia 7.
- Registrar trazabilidad de recomendaciones IA.

## Riesgos y mitigacion
- Riesgo: sobrecarga cognitiva de onboarding.
  - Mitigacion: progress semantico + simplificacion por nivel.
- Riesgo: friccion por pago temprano.
  - Mitigacion: pago posterior al valor generado.
- Riesgo: inconsistencia de tono gerencial/tecnico.
  - Mitigacion: resolver tono en backend y frontend desde configuracion central.

## Criterio de salida de esta guia
- Cero ruptura de rutas actuales.
- Implementacion por feature flags por organizacion.
- Validacion funcional y comercial con empresas piloto de manufactura, servicios e importacion/distribucion.
