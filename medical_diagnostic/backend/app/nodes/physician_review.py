from langchain_core.messages import AIMessage
from langgraph.types import interrupt
from app.state import MedicalState


async def physician_review_node(state: MedicalState) -> MedicalState:
    diagnostic_summary = state.get("diagnostic_summary", "")
    interim_care = state.get("interim_care", "")
    messages = state.get("messages", [])

    review_context = {
        "diagnostic_summary": diagnostic_summary,
        "interim_care": interim_care,
        "instruction": "Consultez la synthèse et saisissez votre traitement ou conduite à tenir.",
    }

    physician_input = interrupt(review_context)
    physician_treatment = physician_input if isinstance(physician_input, str) else str(physician_input)

    new_messages = messages + [AIMessage(content=f"**Traitement médecin :**\n{physician_treatment}")]

    return {**state, "messages": new_messages, "physician_treatment": physician_treatment}