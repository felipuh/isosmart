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
