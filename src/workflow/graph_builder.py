import logging
from langgraph.graph import StateGraph, END
from src.workflow.state import SDLCState
from src.workflow.nodes import (
    business_analyst_node,
    architect_node,
    backend_node,
    frontend_node,
    qa_node,
    review_node,
    devops_node,
)

logger = logging.getLogger(__name__)


def review_decision(state: SDLCState) -> str:
    if state.approved:
        return "approved"
    if state.review_iterations >= 3:
        logger.warning("Max review loops reached — forcing approval path.")
        return "approved"
    return "fix"


def build_graph():
    logger.info("build_graph() - constructing SDLC workflow graph")
    graph = StateGraph(SDLCState)

    graph.add_node("business_analyst", business_analyst_node)
    graph.add_node("architect", architect_node)
    graph.add_node("backend", backend_node)
    graph.add_node("frontend", frontend_node)
    graph.add_node("qa", qa_node)
    graph.add_node("review", review_node)
    graph.add_node("devops", devops_node)

    graph.set_entry_point("business_analyst")

    graph.add_edge("business_analyst", "architect")
    graph.add_edge("architect", "backend")
    graph.add_edge("backend", "frontend")
    graph.add_edge("frontend", "qa")
    graph.add_edge("qa", "review")

    graph.add_conditional_edges(
        "review",
        review_decision,
        {
            "approved": "devops",
            "fix": "backend",
        },
    )

    graph.add_edge("devops", END)

    compiled_graph = graph.compile()
    logger.info("build_graph() - successfully compiled SDLC workflow graph")
    return compiled_graph
