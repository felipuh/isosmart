"""Pure deterministic metadata scan shared by the ContextAnalyzer service and adapters."""


def extract_keywords(text, keywords):
    text_lower = (text or "").lower()
    return [keyword for keyword in keywords if keyword in text_lower]


def iter_document_blobs(documents):
    blobs = []
    for document in documents:
        if isinstance(document, dict):
            pieces = [
                str(document.get("title", "")),
                str(document.get("source", "")),
                str(document.get("type", "")),
                str(document.get("content", "")),
            ]
        else:
            pieces = [
                str(getattr(document, "title", "")),
                str(getattr(document, "source", "")),
                str(getattr(document, "document_type", "")),
                str(getattr(document, "content", "")),
            ]
        blobs.append(" ".join(pieces).lower())
    return blobs


def analyze_internal_factors(documents):
    joined = " ".join(iter_document_blobs(documents))
    digital_keywords = [
        "transformacion digital", "cloud", "iot", "industria 4.0", "inteligencia artificial",
        "ciberseguridad", "blockchain", "telemetria", "trabajo remoto", "hibrido",
    ]
    esg_keywords = [
        "emisiones", "co2", "energia", "residuos", "diversidad", "inclusion",
        "etica", "transparencia", "anticorrupcion", "derechos humanos",
    ]
    return {
        "fortalezas": [
            "Procesos documentados según ISO 9001",
            "Equipo capacitado en gestión de calidad",
            "Infraestructura tecnológica moderna",
        ],
        "debilidades": [
            "Necesidad de mayor integración entre áreas",
            "Procesos de comunicación por mejorar",
        ],
        "riesgos_identificados": [
            {
                "texto": "Dependencia de sistemas heredados",
                "severidad": "medio",
                "categoria": "Tecnología",
                "mitigacion": "Plan de modernización gradual",
            },
            {
                "texto": "Cambio climático puede alterar continuidad operativa y cadena de suministro",
                "severidad": "alto",
                "categoria": "Climático",
                "mitigacion": "Definir escenarios y planes de contingencia por criticidad",
            },
        ],
        "tendencias_digitales": extract_keywords(joined, digital_keywords),
        "factores_esg_detectados": extract_keywords(joined, esg_keywords),
        "recomendaciones": [
            {
                "texto": "Implementar sistema de gestión documental integrado",
                "prioridad": "alta",
                "acciones": [
                    "Evaluar plataformas disponibles",
                    "Definir requisitos específicos",
                    "Piloto en área seleccionada",
                ],
            },
        ],
    }
