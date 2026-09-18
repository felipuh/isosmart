# Source Artifact Manifest — Phase 1 Design Gate

**Required location:** `/home/felipe/proyectos/isosmart/docs/transformation/source-artifacts/`  
**Previous gate (2026-08-13T12:05:58-06:00):** **0/10 → NO-GO**  
**Second recovery gate (2026-08-13T12:33:23-06:00):** **0/10 VALID at required paths → NO-GO**  
**Current recovery gate (2026-08-13):** **10/10 VALID → SOURCE INTAKE PASS**  
**Implementation verdict:** Pending completion of the Enterprise Data design gate.

## Current recovery gate — 10/10 VALID

All exact filenames are now present at the required paths. Every artifact is non-empty, has a unique SHA-256 among this package, and does not have an HTML download-page signature. DOCX and XLSX pass ZIP and required-OOXML-part validation; Draw.io parses as XML; JSON parses; both CSV files have consistent four-column rows; Mermaid, SQL, OpenAPI, and LEEME decode cleanly as UTF-8 text and contain their expected primary structures. No source file was rewritten during validation.

| # | Exact path | Bytes | SHA-256 | Detected format | Filesystem date | Read/parse result |
|---:|---|---:|---|---|---|---|
| 1 | `docs/transformation/source-artifacts/ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx` | 106253 | `8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c` | OOXML Word document | `2026-08-13 12:35:48.681608412 -0600` | VALID: ZIP CRC clean; `word/document.xml` parses |
| 2 | `docs/transformation/source-artifacts/ISO_SMART_AI_Arquitectura_Completa_Lucidchart.drawio` | 37467 | `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa` | Draw.io XML | `2026-08-13 12:35:48.311609770 -0600` | VALID: XML parses |
| 3 | `docs/transformation/source-artifacts/ISO_SMART_AI_Arquitectura_Completa.mmd` | 2310 | `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3` | UTF-8 Mermaid text | `2026-08-13 12:35:48.071610650 -0600` | VALID: 44 lines; flowchart declaration present |
| 4 | `docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx` | 54663 | `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5` | OOXML spreadsheet | `2026-08-13 12:35:48.861607752 -0600` | VALID: ZIP CRC clean; workbook plus 11 sheets parse |
| 5 | `docs/transformation/source-artifacts/ISO_SMART_AI_Nodos_Red.csv` | 11278 | `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3` | UTF-8 CSV | `2026-08-13 12:35:49.352605952 -0600` | VALID: 154 rows; four columns throughout |
| 6 | `docs/transformation/source-artifacts/ISO_SMART_AI_Aristas_Red.csv` | 40131 | `30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6` | UTF-8 CSV | `2026-08-13 12:35:47.913611229 -0600` | VALID: 732 rows; four columns throughout |
| 7 | `docs/transformation/source-artifacts/ISO_SMART_AI_DDL_PostgreSQL.sql` | 7537 | `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e` | UTF-8 PostgreSQL SQL | `2026-08-13 12:35:48.493609102 -0600` | VALID intake: 24 `CREATE TABLE` statements; balanced parentheses |
| 8 | `docs/transformation/source-artifacts/ISO_SMART_AI_OpenAPI.yaml` | 1720 | `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8` | UTF-8 OpenAPI YAML | `2026-08-13 12:35:49.708604647 -0600` | VALID intake: OpenAPI 3 header and `paths` present |
| 9 | `docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Datos.json` | 296927 | `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb` | UTF-8 JSON | `2026-08-13 12:35:49.119606806 -0600` | VALID: parses to an object with nine top-level keys |
| 10 | `docs/transformation/source-artifacts/LEEME_Importacion_ISO_SMART_AI.txt` | 1168 | `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db` | UTF-8 plain text | `2026-08-13 12:35:49.923603858 -0600` | VALID: 24 readable lines |

### Integrity interpretation

These checks establish package-level readability and absence of obvious corruption, truncation, format conversion, HTML substitution, or byte-identical duplication. Semantic completeness and cross-source agreement are evaluated separately in `ISO_SMART_AI_SOURCE_RECONCILIATION.md`; an intake PASS does not make DDL or OpenAPI authoritative or complete.

## Second recovery gate — 2026-08-13T12:33:23-06:00

All ten exact filenames were found in `docs/transformation/`, but none was found in the required `docs/transformation/source-artifacts/` directory. The intake requirement is path-specific and requires exactly `10/10 VALID`; therefore misplaced candidates do not satisfy the gate and Phases B–E were not started.

No file was moved, renamed, parsed as an authoritative source, or modified. The candidate hashes below are identification evidence only, not a declaration of valid intake.

| # | Required filename | Required-path status | Misplaced candidate | Candidate size | Candidate SHA-256 | Detected candidate type | Intake parsing |
|---:|---|---|---|---:|---|---|---|
| 1 | `ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx` | **MISSING** | `docs/transformation/ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx` | 106253 | `8308bde950c80a53dfe46976b46d135faac7b170ae84c53f748aa73146b6a82c` | DOCX | Not performed; wrong path |
| 2 | `ISO_SMART_AI_Arquitectura_Completa_Lucidchart.drawio` | **MISSING** | `docs/transformation/ISO_SMART_AI_Arquitectura_Completa_Lucidchart.drawio` | 37467 | `e0a59c91573e41e6d1bc503ed25ec6d74ddb15c74dc710d7d33b482b8dc98bfa` | Text/XML candidate | Not performed; wrong path |
| 3 | `ISO_SMART_AI_Arquitectura_Completa.mmd` | **MISSING** | `docs/transformation/ISO_SMART_AI_Arquitectura_Completa.mmd` | 2310 | `11c2b4612d9882d2baaafbb7b29ac59719f2b936cd1c29a06676cdcc41acf0c3` | Plain text candidate | Not performed; wrong path |
| 4 | `ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx` | **MISSING** | `docs/transformation/ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx` | 54663 | `952d8ac9858734915c099c8149537ab1a01108d1a4248a5328675c8a758d22d5` | XLSX | Not performed; wrong path |
| 5 | `ISO_SMART_AI_Nodos_Red.csv` | **MISSING** | `docs/transformation/ISO_SMART_AI_Nodos_Red.csv` | 11278 | `ecaecd253ae3f8c1cb9b1b4163cb0a1fed28f158d86d77c88659133ff965bdc3` | CSV candidate | Not performed; wrong path |
| 6 | `ISO_SMART_AI_Aristas_Red.csv` | **MISSING** | `docs/transformation/ISO_SMART_AI_Aristas_Red.csv` | 40131 | `30e3c052798ed492ba08cc80099fb85f6c9730bd4c041392a5b00b0b9c8bf0a6` | CSV candidate | Not performed; wrong path |
| 7 | `ISO_SMART_AI_DDL_PostgreSQL.sql` | **MISSING** | `docs/transformation/ISO_SMART_AI_DDL_PostgreSQL.sql` | 7537 | `de1b4899e7fcc2facd8e26993706dd943696aff59561515911edd5c6e9ebc22e` | Plain text candidate | Not performed; wrong path |
| 8 | `ISO_SMART_AI_OpenAPI.yaml` | **MISSING** | `docs/transformation/ISO_SMART_AI_OpenAPI.yaml` | 1720 | `29ac5c2d6b9cfddac5c4bcb2c24e5b924e2581cf2712412e5cc54ccba1c97fd8` | Plain text candidate | Not performed; wrong path |
| 9 | `ISO_SMART_AI_Mapa_Maestro_Datos.json` | **MISSING** | `docs/transformation/ISO_SMART_AI_Mapa_Maestro_Datos.json` | 296927 | `c41e847ecc34dbdf7a104f2849263851a29a6f129fac72cc559547077c3515eb` | JSON candidate | Not performed; wrong path |
| 10 | `LEEME_Importacion_ISO_SMART_AI.txt` | **MISSING** | `docs/transformation/LEEME_Importacion_ISO_SMART_AI.txt` | 1168 | `eb42315cfc3b904429b5266bacd595a368049e87b5e260846b2c9aeffe80c3db` | Plain text candidate | Not performed; wrong path |

**Recovery required:** place byte-identical copies of these ten candidates in `docs/transformation/source-artifacts/`, then rerun presence, format, corruption, truncation, duplicate, HTML-substitution, and parsing validation. Do not delete the candidates or alter either copy during recovery without an explicit file-management decision.

## Previous gate decision — 2026-08-13T12:05:58-06:00

The Phase 1 source-artifact gate is blocking. The required files were checked by exact filename in the required directory before any architecture reconciliation or design-document update. All ten are absent.

Per the gate rules:

- architecture reconciliation and the Enterprise Data & Tenant Foundation design gate are stopped;
- no source content is inferred, reconstructed, or substituted from secondary documentation;
- no SHA-256, size, media type, or filesystem timestamp is fabricated for an absent file;
- no domain migrations, RLS, outbox, models, application code, environment, secrets, or data are changed;
- implementation remains **NO-GO** until all ten byte-bearing artifacts are supplied at the required location and reconciled.

The pre-existing `README.md` in this directory is contextual documentation and is not one of the ten required source artifacts. Its earlier provisional-source approach is not used for this gate because the current gate explicitly requires stopping when any source artifact is missing.

## Required artifact inventory

| # | Required path | Status | Size | SHA-256 | Type | Filesystem date |
|---:|---|---|---|---|---|---|
| 1 | `docs/transformation/source-artifacts/ISO_SMART_AI_Especificacion_Inicial_Integrada_v1_2026.docx` | **MISSING** | N/A | N/A | Expected DOCX; not verified | N/A |
| 2 | `docs/transformation/source-artifacts/ISO_SMART_AI_Arquitectura_Completa_Lucidchart.drawio` | **MISSING** | N/A | N/A | Expected Draw.io; not verified | N/A |
| 3 | `docs/transformation/source-artifacts/ISO_SMART_AI_Arquitectura_Completa.mmd` | **MISSING** | N/A | N/A | Expected Mermaid text; not verified | N/A |
| 4 | `docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Arquitectura.xlsx` | **MISSING** | N/A | N/A | Expected XLSX; not verified | N/A |
| 5 | `docs/transformation/source-artifacts/ISO_SMART_AI_Nodos_Red.csv` | **MISSING** | N/A | N/A | Expected CSV; not verified | N/A |
| 6 | `docs/transformation/source-artifacts/ISO_SMART_AI_Aristas_Red.csv` | **MISSING** | N/A | N/A | Expected CSV; not verified | N/A |
| 7 | `docs/transformation/source-artifacts/ISO_SMART_AI_DDL_PostgreSQL.sql` | **MISSING** | N/A | N/A | Expected SQL text; not verified | N/A |
| 8 | `docs/transformation/source-artifacts/ISO_SMART_AI_OpenAPI.yaml` | **MISSING** | N/A | N/A | Expected YAML text; not verified | N/A |
| 9 | `docs/transformation/source-artifacts/ISO_SMART_AI_Mapa_Maestro_Datos.json` | **MISSING** | N/A | N/A | Expected JSON text; not verified | N/A |
| 10 | `docs/transformation/source-artifacts/LEEME_Importacion_ISO_SMART_AI.txt` | **MISSING** | N/A | N/A | Expected plain text; not verified | N/A |

## Evidence and continuation condition

Evidence command class: exact-path filesystem existence checks for each required filename. Result: ten `MISSING` outcomes.

The gate may be rerun only after all ten files are placed in the required directory. The next run must calculate size, SHA-256, detected type, and filesystem date for every file before reading and reconciling their contents. Source artifacts must remain byte-for-byte unchanged during that work.

## Previous gate run verification — historical

- The only file added by this gate run is this manifest.
- No migration or `models.py` path is changed in Git status.
- No source artifact exists to modify; the pre-existing `source-artifacts/README.md` was read and left unchanged.
- No `.env`, secret, application code, database, or external workspace was modified by this run.
- Final `git diff --check` is not clean because the pre-existing change in `frontend/src/components/Layout/Sidebar.jsx:28` contains trailing whitespace. This run did not edit that file.
- The modified `backend/test_default.sqlite3` shown by Git was already present in the initial status; this run did not read or write SQLite.
