"""
MCP Server — Expose les tools patient via le protocole MCP.

Outils exposés :
  - ask_patient          : retourne la question selon l'index
  - recommend_interim_care : génère une recommandation intermédiaire prudente
  - get_clinical_questions : liste toutes les questions cliniques

Démarrage : python server.py
Port par défaut : 8001
"""
import json
import sys
import asyncio
from typing import Any

# MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Réutiliser la logique des tools depuis le backend
sys.path.insert(0, "../backend")

# Questions et logique de recommandation
CLINICAL_QUESTIONS = [
    "Quels sont vos symptômes principaux et depuis combien de temps les ressentez-vous ?",
    "Avez-vous de la fièvre ? Si oui, quelle est votre température ?",
    "Avez-vous des antécédents médicaux importants (maladies chroniques, chirurgies, allergies) ?",
    "Prenez-vous des médicaments actuellement ? Si oui, lesquels ?",
    "Avez-vous d'autres symptômes associés : difficultés respiratoires, douleurs thoraciques, troubles de la conscience ?",
]

RED_FLAGS = [
    "difficultés respiratoires", "douleur thoracique", "trouble de la conscience",
    "convulsion", "paralysie", "saignement abondant",
]

MODERATE_SYMPTOMS = ["fièvre", "douleur", "vomissement", "diarrhée"]


def do_ask_patient(question_index: int) -> str:
    """Retourne la question clinique selon l'index."""
    if 0 <= question_index < len(CLINICAL_QUESTIONS):
        return CLINICAL_QUESTIONS[question_index]
    return "Avez-vous autre chose à signaler ?"


def do_recommend_interim_care(symptoms_text: str) -> str:
    """Génère une recommandation intermédiaire prudente."""
    s = symptoms_text.lower()
    found_flags = [f for f in RED_FLAGS if f in s]
    if found_flags:
        return (
            "⚠️ ATTENTION — Symptômes nécessitant une évaluation médicale urgente. "
            "Consultez un médecin ou les urgences sans délai. "
            "⚠️ Cette recommandation ne remplace pas une consultation médicale."
        )
    found_moderate = [sym for sym in MODERATE_SYMPTOMS if sym in s]
    if found_moderate:
        return (
            "Recommandation intermédiaire : repos, hydratation, surveillance des symptômes. "
            "Consultez un médecin dans les 24-48h si persistance ou aggravation. "
            "⚠️ Cette recommandation ne remplace pas une consultation médicale."
        )
    return (
        "Recommandation intermédiaire : repos et hydratation conseillés. "
        "Consultez un médecin si les symptômes persistent. "
        "⚠️ Cette recommandation ne remplace pas une consultation médicale."
    )


# ── Serveur MCP ───────────────────────────────────────────────────────────────

server = Server("medical-diagnostic-mcp")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Liste les outils disponibles via MCP."""
    return [
        types.Tool(
            name="ask_patient",
            description=(
                "Retourne la question clinique à poser au patient selon son index (0-4). "
                "Utilisé en boucle pour collecter 5 réponses patient."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question_index": {
                        "type": "integer",
                        "description": "Index de la question (0 à 4)",
                        "minimum": 0,
                        "maximum": 4,
                    }
                },
                "required": ["question_index"],
            },
        ),
        types.Tool(
            name="recommend_interim_care",
            description=(
                "Génère une recommandation intermédiaire prudente basée sur les symptômes. "
                "Ne remplace pas l'avis médical."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symptoms_text": {
                        "type": "string",
                        "description": "Description des symptômes du patient",
                    }
                },
                "required": ["symptoms_text"],
            },
        ),
        types.Tool(
            name="get_clinical_questions",
            description="Retourne la liste complète des 5 questions cliniques standardisées.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Exécute un outil MCP."""
    args = arguments or {}
    
    if name == "ask_patient":
        result = do_ask_patient(args.get("question_index", 0))
        return [types.TextContent(type="text", text=result)]

    elif name == "recommend_interim_care":
        result = do_recommend_interim_care(args.get("symptoms_text", ""))
        return [types.TextContent(type="text", text=result)]

    elif name == "get_clinical_questions":
        result = json.dumps({"questions": CLINICAL_QUESTIONS}, ensure_ascii=False, indent=2)
        return [types.TextContent(type="text", text=result)]

    else:
        raise ValueError(f"Outil inconnu : {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
