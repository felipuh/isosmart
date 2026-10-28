# ADR-0015: Retained cross-phase evidence and synthetic publication fixture

- Estado: Aceptado para implementacion de blockers de publicacion inerte solamente
- Fecha: 2026-09-03
- Sucede a: ADR-0014 sin reescribir ADR-0001--ADR-0014
- Alcance: evidencia, provenance y precondiciones; sin candidate, migration,
  publication, activation, RuntimeAdoption, runtime ni efectos externos

## Contexto

Phase 26 demostro en PostgreSQL efimero una lineage exacta
`vN -> vN+1 -> vN+2`. El teardown intencional elimino base, volumen y
directorio temporal. La busqueda de Phase 28.1 no encontro un dump, snapshot,
manifest de aplicacion, salida CI local o log que conserve la identidad y el
grafo exactos. Los reportes conservan resultados y hashes de codigo, pero no
los UUID, hashes de material, fingerprint, Receipts, eventos, outbox, audits y
traces necesarios para direccionar `vN+2` en una publicacion posterior.

Reconstruir esos valores desde el harness, el orden de ejecucion o una nueva
base produciria artefactos nuevos y falsearia provenance. A la vez, Phase 27.2
demostro una foundation inerte con fixtures no oficiales, y las politicas
vigentes separan KnowledgeLayerRule no certificable del contenido normativo y
prohiben incorporar cuerpos licenciados en fixtures, eventos y audit.

Finalmente, `foundation_0021_rule_semantic_hash` y
`foundation_0022_rule_semantic_hash` tienen propositos y campos distintos. El
segundo no puede sustituir al primero.

## Decision 1: disponibilidad del candidato Phase 26

Para fines de publicacion:

```text
PHASE26_PUBLICATION_CANDIDATE = PERMANENTLY_UNAVAILABLE
```

La clasificacion no invalida el POC Phase 26. Conserva dos verdades distintas:

- `vN+2` fue la hoja final y la intencion compensada verdadera en la base
  efimera;
- no existe hoy un candidato original direccionable con evidencia completa.

`vN+1` continua inelegible por ser non-leaf y haber sido superseded por la
compensacion. Recuperar identificadores parciales en el futuro no cambia esta
decision salvo que aparezca evidencia autentica, integra, asociada al run y
criptograficamente completa, sin reconstruccion.

## Decision 2: evidencia retenida antes del teardown

Todo target aplicado que pueda cruzar a un gate posterior debe generar, antes
del teardown, un `GOVERNED_TARGET_APPLICATION_EVIDENCE_MANIFEST` sanitizado,
canonico y content-hashed. Debe congelar identidad de run/target/lineage/layer,
revision y predecessor, full-material hash, fingerprint semantico versionado,
source locator/hash/classification, Proposal/CanonicalDelta/Review/Decision/
Authorization, Receipt, event/outbox/audit y trace, migrations y hashes de
politica.

El manifest se almacena en una ubicacion de evidencia aprobada, no contiene
secretos ni cuerpos normativos licenciados y es inmutable despues de promotion.
Una correccion crea una nueva version enlazada; no reemplaza silenciosamente el
archivo anterior.

## Decision 3: fixture sintetica futura

Un POC futuro, aislado y todavia sujeto a un gate de autorizacion separado,
puede usar una fixture sintetica solamente bajo esta clasificacion cerrada:

```text
NON_OFFICIAL_TEST_FIXTURE
NON_NORMATIVE
NON_LICENSED
TEST_ONLY
NON_PRODUCTION
```

La fixture no contiene texto de una norma, no afirma un locator ISO real y no
puede pasar por la rama de source provenance autoritativa. Debe existir un
manifest versionado y reproducible con namespace independiente
`publication_poc_fixture/v1`. Sus IDs y hashes pueden derivarse de contenido
canonico, pero nunca usan namespace `phase26_ephemeral` ni implican continuidad
con Phase 26.

El resultado, cuando un gate futuro autorice crearlo, sera un candidato nuevo:
nueva identidad, lineage, target hashes, canonical delta, governance chain,
Receipt, eventos, audits y autorizacion de publicacion. No se describe como
recuperado, recreado o equivalente a `vN+2`.

## Decision 4: contratos hash separados

Una publicacion futura debe validar sin aliasing:

1. full target material hash;
2. fingerprint semantico compatible con
   `iso-smart-knowledge-layer-rule-substantive-fingerprint-v1`;
3. lifecycle/publication hash de Phase 27.2 cuando aplique;
4. source locator/hash y su clasificacion de provenance; y
5. Receipt y grafo de gobernanza de la aplicacion.

El fingerprint Phase 26 incluye version del fingerprint, target type,
KnowledgeLayer ID/type, Standard/StandardEdition IDs y source hash, lineage,
rule key, logic, evidence expectation, classification y source-reference
scheme. Excluye deliberadamente rule ID, version/revision, predecessor, status,
published_at, timestamps y locator. El hash lifecycle Phase 27.2 es mas
estrecho y no lo reemplaza.

## Consecuencias

Un gate posterior puede implementar solamente manifests y precondiciones
inertes: current-leaf, Receipt/grafo completo, source classification,
fingerprint, curator evidence, actor-level separation of duties, identidad
material/idempotency, locks, TOCTOU, atomicidad y reconciliacion completa.

Esta decision no autoriza crear una lineage, migration 0023, publicar, activar,
adoptar en runtime, conectar el resolver al runtime, desplegar ni producir
efectos externos. La autorizacion de publicacion y cualquier Product Policy de
publicacion pertenecen a un gate posterior.

## Alternativas rechazadas

1. Reconstruir UUID o Receipts de Phase 26 desde fixtures u orden de tests.
2. Considerar los reportes resumen como el grafo transaccional exacto.
3. Publicar `vN+1` pese a la compensacion posterior.
4. Llamar a una nueva fixture "Phase 26 recuperada".
5. Tratar una source reference sintetica como locator autoritativo.
6. Sustituir el fingerprint Phase 26 por el hash Phase 27.2.
7. Conservar evidencia solamente despues de destruir la base.
8. Corregir un manifest promovido en sitio.
