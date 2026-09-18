# Intake de artefactos ISO Smart AI

> **Addendum 2026-08-13:** el estado descrito abajo es histórico. Los diez archivos fueron incorporados posteriormente en este directorio, validados **10/10 VALID** y reconciliados. El estado vigente, hashes y pruebas están en `SOURCE_ARTIFACT_MANIFEST.md`; ya no se usa la fuente provisional.

Fecha de búsqueda: 2026-08-13. Se buscaron los nombres exactos en `/home/felipe` (excluyendo dependencias, entornos virtuales, datos PostgreSQL y almacenamiento Podman). Ninguno estaba disponible:

- `ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx`
- `ISO_SMART_AI_Arquitectura_Completa.mmd`
- `ISO_SMART_AI_Arquitectura_Completa_Lucidchart.drawio`
- `ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx`
- `ISO_SMART_AI_Mapa_Maestro_Datos.json`
- `ISO_SMART_AI_Nodos_Red.csv`
- `ISO_SMART_AI_Aristas_Red.csv`
- `ISO_SMART_AI_DDL_PostgreSQL.sql`
- `ISO_SMART_AI_OpenAPI.yaml`
- `LEEME_Importacion_ISO_SMART_AI.txt`

Esta corrida usa como fuente provisional la especificación textual entregada en la solicitud. No se copió ni alteró ningún original. En la siguiente corrida deben colocarse copias byte-for-byte aquí, registrar SHA-256 y repetir el crosswalk; la especificación integrada y el mapa maestro prevalecerán sobre DDL/OpenAPI parciales.

La ausencia impide afirmar cobertura completa de los 17 pasos, campos, cardinalidades y contratos no transcritos en la solicitud. Es una restricción de entrada P0 para iniciar migraciones de dominio, no para producir el discovery AS-IS.
