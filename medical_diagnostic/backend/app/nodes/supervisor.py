from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from app.state import MedicalState

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


async def supervisor_node(state: MedicalState) -> MedicalState:
    diagnostic_summary = state.get("diagnostic_summary", "")
    physician_treatment = state.get("physician_treatment", "")
    final_report = state.get("final_report", "")

    if not diagnostic_summary:
        decision = "diagnostic_agent"
    elif not physician_treatment:
        decision = "physician_review"
    elif not final_report:
        decision = "report_agent"
    else:
        decision = "FINISH"

    return {**state, "next": decision}