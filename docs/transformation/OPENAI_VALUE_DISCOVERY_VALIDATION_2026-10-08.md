# Validación real de OpenAI — Value Discovery

Fecha: 8 de octubre de 2026 (America/Costa_Rica).
Repositorio canónico: /home/felipe/proyectos/isosmart.

## Resultado

El proveedor gpt-4o-mini recibió respuesta HTTP 200 y superó los validadores existentes para las tres capacidades, en dos contextos exclusivamente sintéticos. Esto verifica el adaptador y sus contratos, no el flujo completo de onboarding ni el frontend.

## Corrección

- Sustitución de JSON libre por JSON Schema estricto por capacidad.
- Campos requeridos, tipos anidados y procedencia exacta (hash y declaración).
- Evaluación financiera fija: NOT_ASSESSED, amount/currency null.
- Límite de 2000 tokens de salida por llamada; respuestas truncadas y rechazos fallan cerrados.
- Se conservan las restricciones locales de evidencia y afirmaciones cuantificadas.
- Sin fallback automático a JSON libre ni reintentos automáticos.

## Pruebas ejecutadas

Comando sin consumo:
```text
cd /home/felipe/proyectos/isosmart/backend
.venv/bin/python manage.py test foundation.test_value_discovery --settings=backend.settings_test --noinput --verbosity 1
```
Resultado final: 6 tests, OK. Incluye subcasos para las tres capacidades, rechazos, truncamiento, JSON inválido, objetos inválidos y capacidades desconocidas.

El intento inicial con .venv312 no pudo arrancar: Django 6.0.6 es incompatible con CheckConstraint(check=...) del proyecto. Se usó .venv, con Django 4.2.22 conforme a requirements.txt. No se cambiaron dependencias. El entorno por defecto también requiere la configuración de test para usar SQLite.

Pruebas reales: 6 llamadas, sin reintentos, utilizando directamente el adaptador corregido y los validadores originales. Tres capacidades con perfil normal y tres con perfil escaso y una declaración que contiene instrucciones no confiables. Todas: HTTP 200, PASS de contrato. En ambos casos financieros: NOT_ASSESSED y cero oportunidades sin evidencia suficiente. El cumplimiento de contrato no prueba por sí solo todas las propiedades semánticas frente a cualquier entrada adversarial.

La ejecución directa no invocó ValueDiscoveryService.execute, transacciones, auditoría, outbox ni escritura de onboarding. No se usaron datos reales.

## Consumo

- Primera ronda (antes de la corrección): 3 llamadas, HTTP 200, fallos de contrato; US$0.00034515 estimados.
- Segunda ronda: 6 llamadas; US$0.00122940 estimados.
- Acumulado: US$0.00157455 estimados, muy inferior al máximo autorizado de US$5.
- Cota conservadora reservada para la segunda ronda y consumo previo: US$0.01075785.
- Costo estimado con los tokens reportados y tarifa estándar gpt-4o-mini; la facturación definitiva corresponde a OpenAI.
- El límite autorizado rige estas pruebas; no se configuró un límite global de consumo para la aplicación.

Saldo verificado antes de las pruebas: US$5.00. Recarga automática: OFF.

## Alcance y entrega

Archivos modificados: backend/foundation/value_discovery.py y backend/foundation/test_value_discovery.py. Este documento registra los resultados. AI_ASSISTANT_API_KEY está en backend/.env, excluido de Git; ningún secreto forma parte de los resultados.

No se crearon ramas, commits, publicaciones ni despliegues. No se reiniciaron servicios. Un proceso que ya esté en ejecución necesita cargar la nueva configuración/código mediante el procedimiento de operación autorizado. No se probaron el chatbot SSE, la UI ni persistencia multi-tenant mediante inferencia real.

Referencia del contrato OpenAI: https://developers.openai.com/api/docs/guides/structured-outputs
Tarifa: https://developers.openai.com/api/docs/models/gpt-4o-mini
