from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from app.state import MedicalState
from app.tools.patient_tools import CLINICAL_QUESTIONS, INTERIM_CARE_RULES

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)

SYNTHESIS_SYSTEM = """Tu es un agent d'orientation clinique préliminaire académique.
À partir des questions/réponses patient, produis une synthèse clinique préliminaire structurée.

Format :
## Synthèse Clinique Préliminaire
[synthèse]

## Éléments Cliniques Notables
[points importants]

## Motif d'Orientation Préliminaire
[motif principal]

IMPORTANT : Ne pose JAMAIS de diagnostic définitif.
"""


def _recommend(patient_qa: list) -> str:
    text = " ".join([qa.get("answer", "") for qa in patient_qa]).lower()
    if any(f in text for f in INTERIM_CARE_RULES["red_flags"]):
        return "⚠️ ATTENTION — Symptômes urgents détectés. Consultez un médecin ou les urgences sans délai. ⚠️ Cette recommandation ne remplace pas une consultation médicale."
    if any(s in text for s in INTERIM_CARE_RULES["moderate"]):
        return "Recommandation intermédiaire : repos, hydratation, surveillance. Consultez un médecin dans les 24-48h si persistance. ⚠️ Cette recommandation ne remplace pas une consultation médicale."
    return "Recommandation intermédiaire : repos et hydratation conseillés. Consultez un médecin si persistance. ⚠️ Cette recommandation ne remplace pas une consultation médicale."


async def diagnostic_agent_node(state: MedicalState) -> MedicalState:
    patient_info = state.get("patient_info", "")
    patient_qa = state.get("patient_qa", [])
    question_count = state.get("question_count", 0)
    messages = state.get("messages", [])

    if question_count < 5:
        next_question = CLINICAL_QUESTIONS[question_count]
        return {**state, "messages": messages + [AIMessage(content=next_question)]}

    qa_text = "\n".join([f"Q{i+1}: {qa.get('question','')}\nR{i+1}: {qa.get('answer','')}" for i, qa in enumerate(patient_qa)])
    context = f"Cas patient : {patient_info}\n\nQ/R :\n{qa_text}"

    response = await llm.ainvoke([SystemMessage(content=SYNTHESIS_SYSTEM), HumanMessage(content=context)])
    diagnostic_summary = response.content
    interim_care = _recommend(patient_qa)

    new_messages = messages + [
        AIMessage(content=f"**Synthèse clinique préliminaire :**\n\n{diagnostic_summary}"),
        AIMessage(content=f"**Recommandation intermédiaire :**\n{interim_care}"),
    ]

    return {**state, "messages": new_messages, "diagnostic_summary": diagnostic_summary, "interim_care": interim_care}