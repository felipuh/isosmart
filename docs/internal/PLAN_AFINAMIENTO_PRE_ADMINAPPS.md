# Plan de Afinamiento ISOSmart Pre-AdminApps

## Objetivo
Cerrar brechas funcionales y de calidad para que ISOSmart alcance un nivel profesional de salida a mercado antes de iniciar trabajo en AdminApps.

## Criterio de salida global
Se considera completado cuando:
- Los flujos criticos (auth, recuperacion de contrasena, notificaciones, reportes) funcionan end-to-end.
- Existe cobertura automatizada minima aceptable para regresion.
- Se cumplen criterios de seguridad operativa y trazabilidad.
- Se valida estabilidad en entorno similar a produccion.

## Fase 0 - Congelamiento de alcance (1 dia)
### Objetivo
Evitar dispersion y asegurar foco exclusivo en ISOSmart.

### Tareas
- Congelar nuevas funcionalidades no criticas.
- Definir rama de estabilizacion (opcional) o usar development con reglas estrictas.
- Acordar lista de requerimientos minimos de salida.

### Criterio de aceptacion
- Lista de alcance firmada y publicada en este documento.

---

## Fase 1 - Recuperacion de contrasena profesional (2-3 dias)
### Objetivo
Implementar flujo real de "Olvide mi contrasena" con seguridad de mercado.

### Tareas backend
- Endpoint para solicitar recuperacion por email.
- Generacion de token temporal de un solo uso con expiracion.
- Endpoint para confirmar nueva contrasena con token.
- Invalidacion de token tras uso.
- Rate limiting por IP y por email.
- Registro de auditoria de solicitud y confirmacion.

### Tareas frontend
- Pantalla "Olvide mi contrasena".
- Pantalla "Restablecer contrasena" desde link/token.
- Mensajes de error/estado i18n (es/en/pt).

### Pruebas minimas
- Unit/integration backend para token valido, expirado, reutilizado.
- E2E: solicitar recovery, recibir token de prueba, restablecer, iniciar sesion.

### Criterio de aceptacion
- Flujo completo funcional sin intervencion de admin.
- No se filtra si un email existe o no.

---

## Fase 2 - Notificaciones end-to-end (2-3 dias)
### Objetivo
Unificar y activar notificaciones criticas con trazabilidad.

### Tareas
- Inventario de eventos criticos (riesgo critico, objective deadline, stakeholder change, billing).
- Activar envio real donde este comentado/incompleto.
- Canal estandar de envio (cola + retry + backoff).
- Plantillas de email por idioma.
- Registro de estado: pendiente/enviado/fallido + motivo.

### Pruebas minimas
- Integration tests por evento.
- Pruebas de fallo SMTP (reintento y marcado fallido).
- E2E de configuracion de notificaciones y disparo de evento.

### Criterio de aceptacion
- Cada evento critico configurable llega al destinatario correcto.
- Fallos quedan trazados y visibles.

---

## Fase 3 - Reportes de nivel negocio (3-4 dias)
### Objetivo
Pasar de export JSON basico a reportes consumibles para cliente final.

### Tareas
- Definir 3 reportes iniciales:
  - Estado SGQ ejecutivo
  - Riesgos y oportunidades
  - Objetivos y desempeno
- Export en PDF y CSV/XLSX segun caso.
- Filtros por organizacion, rango de fechas, modulo.
- Boton de export real conectado en dashboard ejecutivo.
- Incluir metadata: fecha, organizacion, usuario exportador.

### Pruebas minimas
- Backend: generacion valida de archivos y control tenant.
- Frontend E2E: descarga y validacion de respuesta/mimetype.

### Criterio de aceptacion
- Usuario puede generar reportes utiles sin soporte tecnico.

---

## Fase 4 - Endurecimiento QA (3-5 dias)
### Objetivo
Aumentar confianza para cambios sin romper produccion.

### Tareas
- Extender E2E con casos criticos:
  - password recovery
  - notificaciones
  - reportes
  - permisos por rol
- Agregar pruebas backend para auth, billing notifications, export/reportes.
- Definir smoke suite obligatoria pre-merge.

### Metricas objetivo
- 0 fallos en smoke suite.
- Cobertura de flujos criticos: 100% de caminos principales y errores comunes.

### Criterio de aceptacion
- Cualquier regression critica es detectada antes de despliegue.

---

## Fase 5 - Seguridad y operacion (2-3 dias)
### Objetivo
Completar controles basicos de operacion segura y soporte.

### Tareas
- Validar politicas de contrasena y bloqueo por intentos.
- Revisar expiracion/rotacion de tokens.
- Sanitizar mensajes de error sensibles.
- Revisar CORS, headers de seguridad y configuracion de cookies/tokens.
- Checklist de backup/restore probado en entorno de prueba.

### Criterio de aceptacion
- Controles minimos de seguridad aplicados y verificados.

---

## Fase 6 - Go/No-Go pre AdminApps (1 dia)
### Objetivo
Tomar decision formal basada en evidencia.

### Checklist final
- Password recovery productivo.
- Notificaciones criticas end-to-end.
- Reportes PDF/CSV/XLSX operativos.
- Suite E2E critica en verde.
- Sin errores severos abiertos.
- Documentacion minima para operacion y soporte actualizada.

### Criterio de aceptacion
- Aprobacion de Go para iniciar AdminApps sin deuda critica bloqueante.

---

## Backlog recomendado (post salida)
- Centro de notificaciones in-app (campana + historial).
- Programacion de reportes recurrentes por email.
- Dashboard de salud operativa (colas, latencias, errores por modulo).
- SLO/SLA y alertas de observabilidad.

## Matriz de prioridad
- P0: Password recovery, notificaciones criticas, tenant security, smoke tests.
- P1: Reportes ejecutivos descargables y endurecimiento QA.
- P2: Mejoras de UX y automatizaciones avanzadas.

## Ritmo sugerido
- Semana 1: Fase 1 + Fase 2
- Semana 2: Fase 3 + Fase 4
- Semana 3: Fase 5 + Fase 6

## Responsable y seguimiento
- Responsable tecnico: Equipo ISOSmart.
- Cadencia: revision diaria de avances + demo interna cada 2 dias.
- Regla: no pasar a AdminApps con items P0 abiertos.

---

## Estado de ejecucion al 2026-03-19

### Resumen por fase
- Fase 0 (congelamiento de alcance): COMPLETADA.
- Fase 1 (recuperacion de contrasena): COMPLETADA.
- Fase 2 (notificaciones end-to-end): COMPLETADA en implementacion funcional.
- Fase 3 (reportes de nivel negocio): COMPLETADA.
- Fase 4 (endurecimiento QA): COMPLETADA para smoke critico y matriz de permisos.
- Fase 5 (seguridad y operacion): COMPLETADA en hardening tecnico principal.
- Fase 6 (Go/No-Go): EN CIERRE FORMAL.

### Evidencia tecnica consolidada
- Reportes PDF/CSV/XLSX en flujo funcional de negocio.
- Endurecimiento de permisos por rol en backend con pruebas de matriz por endpoint.
- Recuperacion de contrasena operativa con token temporal y auditoria.
- Notificaciones operativas y de eventos criticos con trazabilidad.
- Lockout de login por intentos fallidos y politicas de seguridad reforzadas.
- Validacion automatizada vigente:
  - Backend: 55/55 pruebas en verde (incluye 6 nuevas pruebas de onboarding orchestration).
  - E2E smoke critico: verde en los escenarios definidos.
  - Frontend: 0 vulnerabilidades npm (7 resueltas), lint limpio, build PASS.

### Checklist final Fase 6 (Go/No-Go)
- [x] Password recovery productivo.
- [x] Notificaciones criticas end-to-end.
- [x] Reportes PDF/CSV/XLSX operativos.
- [x] Suite E2E critica en verde.
- [x] Sin errores severos abiertos en los flujos criticos endurecidos.
- [ ] Validacion formal en entorno similar a produccion documentada y firmada.
- [ ] Acta final de aprobacion de Go emitida por responsable tecnico.

### Riesgos residuales (no bloqueantes, pero a cerrar)
- Formalizar corrida de preproduccion con evidencia archivada (fecha, build, resultados).
- Confirmar checklist de backup/restore en entorno de prueba con acta.
- Consolidar evidencia de operacion (capturas/logs) en carpeta unica para auditoria interna.

### Decision recomendada
- Estado: GO CONDICIONADO.
- Condicion para GO definitivo: completar los 2 items pendientes del checklist final de Fase 6.

### Responsable del cierre
- Responsable tecnico: Equipo ISOSmart.
- Fecha objetivo de cierre formal Fase 6: 2026-03-21.

### Plan operativo de cierre (pendientes obligatorios)
1. Validacion formal en entorno similar a produccion
- Responsable: QA Lead + Backend Lead.
- Fecha compromiso: 2026-03-20.
- Entregables:
  - Evidencia de ejecucion (comandos, resultados, timestamps).
  - Resultado de smoke suite y pruebas backend relevantes.
  - Registro de incidencias encontradas (si aplica) y estado de cierre.
2. Acta final de aprobacion de Go
- Responsable: Responsable tecnico ISOSmart.
- Fecha compromiso: 2026-03-21.
- Entregables:
  - Acta firmada digitalmente o aprobada por correo formal.
  - Decision final (GO o NO-GO) con justificacion.

### Formato de acta de aprobacion final (Fase 6)
- Fecha:
- Version/build evaluada:
- Entorno validado:
- Participantes:
- Evidencia revisada:
  - Pruebas backend:
  - Smoke E2E:
  - Seguridad operativa:
  - Backup/restore:
- Hallazgos abiertos (si existen):
- Riesgos aceptados:
- Decision:
  - [ ] GO
  - [ ] NO-GO
- Condiciones adicionales (si aplica):
- Responsable de aprobacion:
- Firma/confirmacion:

### Checklist ejecutable de preproduccion (una corrida)
1. Preparacion de entorno
- [ ] Variables de entorno cargadas y revisadas (incluye SECRET_KEY y credenciales).
- [ ] Servicios dependientes activos (DB, Redis, colas, email/smtp de prueba).
- [ ] Migraciones aplicadas sin errores.
2. Validacion automatizada
- [ ] Backend tests criticos en verde.
- [ ] Smoke E2E critico en verde.
- [ ] Verificacion de endpoints de auth, reportes, settings y permisos por rol.
3. Seguridad y operacion
- [ ] Lockout de login validado (umbral y desbloqueo por expiracion).
- [ ] Politica de contrasena validada en alta/cambio/reset.
- [ ] Headers de seguridad verificados en respuestas HTTP.
- [ ] CORS/CSRF validados contra dominios permitidos.
4. Respaldo y trazabilidad
- [ ] Flujo de backup ejecutado y auditado.
- [ ] Prueba de restore en entorno de prueba completada.
- [ ] Logs de auditoria y logs operativos almacenados en carpeta de evidencia.
5. Cierre
- [ ] Semaforo final actualizado (Verde/Amarillo/Rojo por criterio global).
- [ ] Acta de aprobacion completada.
- [ ] Decision final comunicada al equipo.
