from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.state import MedicalState
from app.nodes.supervisor import supervisor_node
from app.nodes.diagnostic_agent import diagnostic_agent_node
from app.nodes.physician_review import physician_review_node
from app.nodes.report_agent import report_agent_node


def build_graph(use_checkpointer: bool = True):
    builder = StateGraph(MedicalState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("diagnostic_agent", diagnostic_agent_node)
    builder.add_node("physician_review", physician_review_node)
    builder.add_node("report_agent", report_agent_node)

    builder.add_edge(START, "supervisor")

    def route_supervisor(state: MedicalState) -> str:
        next_node = state.get("next", "diagnostic_agent")
        if next_node == "FINISH":
            return END
        return next_node

    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "diagnostic_agent": "diagnostic_agent",
            "physician_review": "physician_review",
            "report_agent": "report_agent",
            END: END,
        },
    )

    builder.add_edge("diagnostic_agent", "supervisor")
    builder.add_edge("physician_review", "supervisor")
    builder.add_edge("report_agent", "supervisor")

    compile_kwargs = {"interrupt_before": ["physician_review"]}

    # MemorySaver uniquement pour FastAPI local
    # LangGraph Studio gère sa propre persistance → use_checkpointer=False
    if use_checkpointer:
        compile_kwargs["checkpointer"] = MemorySaver()

    return builder.compile(**compile_kwargs)


# Pour LangGraph Studio (langgraph.json) → sans checkpointer
medical_graph = build_graph(use_checkpointer=False)