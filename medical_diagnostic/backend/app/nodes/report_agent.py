from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from app.state import MedicalState

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

REPORT_SYSTEM = """Tu es un agent de génération de rapports d'orientation clinique académique.
Génère un rapport final structuré professionnel incluant :
1. En-tête (date, référence)
2. Informations patient
3. Synthèse clinique préliminaire
4. Recommandation intermédiaire
5. Décision du médecin traitant
6. Conclusion
7. Mentions légales obligatoires

OBLIGATOIRE : inclure exactement ces phrases :
"Ce système ne remplace pas une consultation médicale."
"Ce rapport est issu d'un exercice académique et ne constitue pas un acte médical."
"""


async def report_agent_node(state: MedicalState) -> MedicalState:
    patient_info = state.get("patient_info", "Non renseigné")
    diagnostic_summary = state.get("diagnostic_summary", "")
    interim_care = state.get("interim_care", "")
    physician_treatment = state.get("physician_treatment", "")
    patient_qa = state.get("patient_qa", [])
    messages = state.get("messages", [])

    qa_text = "\n".join([f"Q: {qa.get('question','')}\nR: {qa.get('answer','')}" for qa in patient_qa])

    context = f"""Date : {datetime.now().strftime("%d/%m/%Y %H:%M")}
PATIENT : {patient_info}
Q/R : {qa_text}
SYNTHÈSE : {diagnostic_summary}
RECOMMANDATION : {interim_care}
MÉDECIN : {physician_treatment}"""

    response = await llm.ainvoke([SystemMessage(content=REPORT_SYSTEM), HumanMessage(content=context)])
    final_report = response.content

    return {**state, "messages": messages + [AIMessage(content=final_report)], "final_report": final_report}