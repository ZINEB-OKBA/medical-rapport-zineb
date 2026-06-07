from typing import Annotated, Optional
from typing_extensions import TypedDict, Literal
from langgraph.graph.message import add_messages


class MedicalState(TypedDict, total=False):
    """État partagé du graphe multi-agents médical."""

    # Messages LangChain (conversation history)
    messages: Annotated[list, add_messages]

    # Routing: nœud suivant décidé par le Supervisor
    next: Literal[
        "diagnostic_agent",
        "physician_review",
        "report_agent",
        "FINISH",
    ]

    # Informations patient initiales
    patient_info: str

    # Compteur de questions posées au patient
    question_count: int

    # Réponses du patient (liste de dicts {"question": ..., "answer": ...})
    patient_qa: list

    # Recommandation intermédiaire prudente
    interim_care: str

    # Synthèse clinique préliminaire produite par le Diagnostic Agent
    diagnostic_summary: str

    # Traitement / conduite à tenir proposé par le médecin (HITL)
    physician_treatment: str

    # Rapport final structuré produit par le Report Agent
    final_report: str

    # Thread ID pour la persistance LangGraph
    thread_id: Optional[str]
