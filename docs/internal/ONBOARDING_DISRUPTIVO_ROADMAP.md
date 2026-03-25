# Roadmap técnico - Onboarding Disruptivo ISO Smart

Fecha: 2026-02-27

## Estado actual (implementado)

### Fase 1 (completada)
- Onboarding ampliado con captura de perfil inicial:
  - Rol principal
  - Nivel de expertise ISO 9001
  - Rango de tamaño
  - Sector
  - Número de colaboradores
  - Número de sedes
  - Países
  - Estado de certificación
- Preferencia de tono del sistema:
  - Lenguaje gerente
  - Lenguaje técnico
- Persistencia backend en `OrganizationSettings`:
  - `onboarding_profile` (JSON)
  - `preferred_response_tone` (manager|technical)
- Endpoint de finalización de onboarding extendido con validaciones.

## Fase 2 - Motores de valor inmediato (completada)

Objetivo: devolver valor en la misma sesión inicial.

1. Motor Perfil Organizacional
- Input: `onboarding_profile` + estándares activos.
- Output:
  - Plantilla inicial de procesos (estratégicos, operativos, soporte)
  - Estructura de partes interesadas sugerida
  - Nivel de profundidad por expertise

2. Motor Impacto y Ahorro
- Input: dolores principales + sector + tamaño.
- Output:
  - Top 3 quick wins
  - Top 3 big bets
  - Estimación de impacto económico simple

3. Motor Propósito y Alineación
- Input: prioridades de negocio + objetivos personales del líder.
- Output:
  - Borrador de objetivos de calidad
  - Relación objetivo-negocio-bienestar

Entregable técnico:
- Servicio backend de orquestación de onboarding (`onboarding_orchestrator`)
- Endpoint único de ejecución y resumen
- Persistencia de resultados como snapshot versionado

## Fase 3 - Esqueleto ISO automático

Objetivo: crear el "20% listo" al finalizar onboarding.

- Pre-borrador de alcance SGC
- Mapa de procesos inicial
- Top 5 riesgos + Top 5 oportunidades
- Objetivos v1
- Activación de módulos sugeridos

Entregable técnico:
- Tareas asíncronas para generación (Celery)
- Estado de progreso por bloques (porcentaje)

## Fase 4 - Rutas adaptativas por expertise

Objetivo: UX dinámica según tipo de usuario.

- Nulo/Aprendiz: flujo guiado con pasos simplificados
- Intermedio: fast-track con sprints
- Experto/Consultor: importación masiva y modo consultor

Entregable técnico:
- Motor de reglas de experiencia
- Componentes de ruta por perfil

## Fase 5 - Billing y activación comercial

Objetivo: habilitar flujo comercial completo sin afectar núcleo ISO.

- Planes, checkout y estados de suscripción
- Pagador delegado (usuario distinto al solicitante)
- Regla de gracia de pago configurable
- Suspensión/reactivación automática por estado
- Notificaciones y credenciales al responsable de pago

Entregable técnico:
- Nuevo módulo aislado de billing
- Webhooks + jobs programados
- Auditoría de cambios de estado

## Riesgos y mitigación

1. Riesgo: mezclar onboarding con billing en el mismo flujo inicial.
- Mitigación: separar dominios (onboarding funcional vs habilitación comercial).

2. Riesgo: sobrecargar primer release con IA generativa compleja.
- Mitigación: iniciar con reglas + plantillas y luego enriquecer con LLM.

3. Riesgo: romper experiencia de usuarios ya activos.
- Mitigación: feature flags por organización y migración incremental.

## KPI sugeridos de éxito

- Tiempo promedio de onboarding completo
- % de organizaciones que finalizan onboarding en primer intento
- % de organizaciones con mapa/procesos/objetivos autogenerados
- Activación de módulos sugeridos
- Conversión a plan pago y retención de 90 días
