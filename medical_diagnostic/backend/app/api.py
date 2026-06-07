from dotenv import load_dotenv
load_dotenv()

import uuid
import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.state import MedicalState
from app.tools.patient_tools import CLINICAL_QUESTIONS
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.nodes.supervisor import supervisor_node
from app.nodes.diagnostic_agent import diagnostic_agent_node
from app.nodes.physician_review import physician_review_node
from app.nodes.report_agent import report_agent_node


def _build_graph():
    builder = StateGraph(MedicalState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("diagnostic_agent", diagnostic_agent_node)
    builder.add_node("physician_review", physician_review_node)
    builder.add_node("report_agent", report_agent_node)
    builder.add_edge(START, "supervisor")

    def route_supervisor(state):
        nxt = state.get("next", "diagnostic_agent")
        return END if nxt == "FINISH" else nxt

    builder.add_conditional_edges("supervisor", route_supervisor, {
        "diagnostic_agent": "diagnostic_agent",
        "physician_review": "physician_review",
        "report_agent": "report_agent",
        END: END,
    })
    builder.add_edge("diagnostic_agent", "supervisor")
    builder.add_edge("physician_review", "supervisor")
    builder.add_edge("report_agent", "supervisor")

    return builder.compile(
        checkpointer=MemorySaver(),
        # Interruption avant diagnostic_agent ET physician_review
        # → le graphe s'arrête après avoir posé chaque question
        interrupt_before=["diagnostic_agent", "physician_review"],
    )


graph = _build_graph()

app = FastAPI(title="OrientaClin API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])


class SessionResponse(BaseModel):
    thread_id: str
    message: str

class ConsultationStartRequest(BaseModel):
    thread_id: str
    patient_info: str

class ConsultationResumeRequest(BaseModel):
    thread_id: str
    response: str
    response_type: str
    question_index: Optional[int] = None


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/sessions/start", response_model=SessionResponse)
def start_session():
    return SessionResponse(thread_id=str(uuid.uuid4()), message="Session créée.")


@app.post("/consultation/start")
async def start_consultation(request: ConsultationStartRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    # État initial — question_count=0, le graphe va s'arrêter
    # juste AVANT diagnostic_agent (interrupt_before)
    initial_state: MedicalState = {
        "patient_info": request.patient_info,
        "question_count": 0,
        "patient_qa": [],
        "messages": [],
    }

    try:
        # Le graphe s'arrête avant diagnostic_agent → retourne immédiatement
        await graph.ainvoke(initial_state, config=config)

        # Maintenant on exécute diagnostic_agent manuellement UNE fois
        # pour poser la première question
        await graph.ainvoke(None, config=config)

        snapshot = graph.get_state(config)
        state = snapshot.values
        msgs = state.get("messages", [])
        current_question = msgs[-1].content if msgs and hasattr(msgs[-1], "content") else CLINICAL_QUESTIONS[0]

        return {
            "thread_id": request.thread_id,
            "status": "awaiting_patient",
            "question_count": 0,
            "current_question": current_question,
            "message": "Consultation démarrée. Première question posée.",
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@app.post("/consultation/resume")
async def resume_consultation(request: ConsultationResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        snapshot = graph.get_state(config)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Thread introuvable")

        current_state = dict(snapshot.values)

        if request.response_type == "patient_answer":
            q_count = current_state.get("question_count", 0)
            patient_qa = list(current_state.get("patient_qa", []))
            question_text = CLINICAL_QUESTIONS[q_count] if q_count < len(CLINICAL_QUESTIONS) else ""

            # Enregistrer la réponse et incrémenter le compteur
            patient_qa.append({"question": question_text, "answer": request.response})
            new_count = q_count + 1

            graph.update_state(config, {
                "patient_qa": patient_qa,
                "question_count": new_count,
            })

            # Reprendre le graphe — il va repasser par supervisor puis
            # s'arrêter à nouveau avant diagnostic_agent (question suivante)
            # OU s'arrêter avant physician_review (après 5 questions)
            await graph.ainvoke(None, config=config)

            new_state = graph.get_state(config).values
            msgs = new_state.get("messages", [])

            # Vérifier si on attend le médecin
            awaiting_physician = (
                bool(new_state.get("diagnostic_summary")) and
                not bool(new_state.get("physician_treatment"))
            )

            next_question = None
            if not awaiting_physician and new_count < 5:
                # Poser la question suivante
                await graph.ainvoke(None, config=config)
                new_state = graph.get_state(config).values
                msgs = new_state.get("messages", [])
                next_question = msgs[-1].content if msgs and hasattr(msgs[-1], "content") else None

            return {
                "thread_id": request.thread_id,
                "status": "awaiting_physician" if awaiting_physician else "awaiting_patient",
                "question_count": new_state.get("question_count", new_count),
                "current_question": next_question,
                "diagnostic_summary": new_state.get("diagnostic_summary"),
                "interim_care": new_state.get("interim_care"),
            }

        elif request.response_type == "physician_treatment":
            # Résoudre l'interruption physician_review
            graph.update_state(
                config,
                {"physician_treatment": request.response},
                as_node="physician_review",
            )
            await graph.ainvoke(None, config=config)

            new_state = graph.get_state(config).values
            return {
                "thread_id": request.thread_id,
                "status": "completed",
                "final_report": new_state.get("final_report"),
                "message": "Rapport final généré.",
            }

        else:
            raise HTTPException(status_code=400, detail="response_type invalide")

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@app.get("/consultation/{thread_id}")
def get_consultation_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        snapshot = graph.get_state(config)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Consultation introuvable")

        state = snapshot.values
        if state.get("final_report"):
            status = "completed"
        elif state.get("diagnostic_summary") and not state.get("physician_treatment"):
            status = "awaiting_physician"
        else:
            status = "awaiting_patient"

        messages = [
            {"type": m.__class__.__name__, "content": m.content}
            for m in state.get("messages", []) if hasattr(m, "content")
        ]
        current_question = messages[-1]["content"] if messages and status == "awaiting_patient" else None

        return {
            "thread_id": thread_id,
            "status": status,
            "current_node": state.get("next"),
            "question_count": state.get("question_count", 0),
            "current_question": current_question,
            "diagnostic_summary": state.get("diagnostic_summary"),
            "interim_care": state.get("interim_care"),
            "physician_treatment": state.get("physician_treatment"),
            "final_report": state.get("final_report"),
            "messages": messages,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@app.get("/consultation/{thread_id}/report")
def get_report(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        snapshot = graph.get_state(config)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Consultation introuvable")
        final_report = snapshot.values.get("final_report")
        if not final_report:
            raise HTTPException(status_code=400, detail="Rapport pas encore disponible.")
        return {
            "thread_id": thread_id,
            "final_report": final_report,
            "disclaimer": "Ce système ne remplace pas une consultation médicale.",
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")