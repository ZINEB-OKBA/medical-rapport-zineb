"""
Tools patient utilisés par le Diagnostic Agent.
Ces tools sont également exposés via MCP.
"""
from langchain_core.tools import tool
from app.state import MedicalState


CLINICAL_QUESTIONS = [
    "Quels sont vos symptômes principaux et depuis combien de temps les ressentez-vous ?",
    "Avez-vous de la fièvre ? Si oui, quelle est votre température ?",
    "Avez-vous des antécédents médicaux importants (maladies chroniques, chirurgies, allergies) ?",
    "Prenez-vous des médicaments actuellement ? Si oui, lesquels ?",
    "Avez-vous d'autres symptômes associés : difficultés respiratoires, douleurs thoraciques, troubles de la conscience ?",
]

INTERIM_CARE_RULES = {
    "red_flags": [
        "difficultés respiratoires",
        "douleur thoracique",
        "trouble de la conscience",
        "convulsion",
        "paralysie",
        "saignement abondant",
    ],
    "moderate": [
        "fièvre",
        "douleur",
        "vomissement",
        "diarrhée",
    ],
}


@tool
def ask_patient(question_index: int) -> str:
    """
    Retourne la question à poser au patient selon son index (0-4).
    Utilisé en boucle jusqu'à 5 questions.

    Args:
        question_index: Index de la question (0 à 4)

    Returns:
        La question à poser au patient
    """
    if 0 <= question_index < len(CLINICAL_QUESTIONS):
        return CLINICAL_QUESTIONS[question_index]
    return "Avez-vous autre chose à signaler ?"


@tool
def recommend_interim_care(symptoms_text: str) -> str:
    """
    Génère une recommandation intermédiaire prudente basée sur les symptômes.
    NE remplace PAS l'avis médical.

    Args:
        symptoms_text: Description des symptômes du patient

    Returns:
        Recommandation intermédiaire (repos, hydratation, surveillance, etc.)
    """
    symptoms_lower = symptoms_text.lower()

    # Détection de red flags
    found_flags = [
        flag for flag in INTERIM_CARE_RULES["red_flags"]
        if flag in symptoms_lower
    ]

    if found_flags:
        return (
            "⚠️ ATTENTION — Symptômes nécessitant une évaluation médicale urgente détectés. "
            "Recommandation : consultez un médecin ou les urgences sans délai. "
            "En attendant : restez en position assise ou allongée selon votre confort, "
            "ne prenez pas de médicaments sans avis médical, "
            "signalez immédiatement toute aggravation."
        )

    # Symptômes modérés
    found_moderate = [
        s for s in INTERIM_CARE_RULES["moderate"]
        if s in symptoms_lower
    ]

    if found_moderate:
        return (
            "Recommandation intermédiaire générale (dans l'attente d'un avis médical) : "
            "1. Repos au domicile recommandé. "
            "2. Hydratation suffisante (eau, bouillons). "
            "3. Surveillance de l'évolution des symptômes. "
            "4. Consulter un médecin dans les 24-48h si persistance ou aggravation. "
            "5. Appeler le 15 (SAMU) en cas d'aggravation rapide. "
            "⚠️ Cette recommandation ne remplace pas une consultation médicale."
        )

    # Cas bénin apparent
    return (
        "Recommandation intermédiaire générale : "
        "1. Repos et hydratation conseillés. "
        "2. Surveillance des symptômes sur 24-48h. "
        "3. Consultation médicale si les symptômes persistent ou s'aggravent. "
        "⚠️ Cette recommandation ne remplace pas une consultation médicale."
    )
