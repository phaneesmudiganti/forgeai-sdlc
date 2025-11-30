import logging
from src.workflow.state import SDLCState
from src.workflow.llms import smart_llm

logger = logging.getLogger(__name__)


def backend_node(state: SDLCState) -> SDLCState:
    logger.info("backend_node() - starting Backend Engineer processing")
    logger.debug(f"backend_node() - input architecture length: {len(state.architecture) if state.architecture else 0} chars")

    if not state.architecture:
        logger.error("backend_node() - architecture is missing or empty")
        raise ValueError("Architecture is required for backend implementation")

    try:
        prompt = (
            "You are a senior Backend Engineer.\n\n"
            "Implement Python backend code based on this architecture:\n\n"
            f"{state.architecture}\n\n"
            "Return code only, with markers like:\n"
            "# file: backend/app/main.py\n"
            "<code here>\n"
        )
        logger.debug("backend_node() - invoking smart_llm with backend implementation prompt")
        resp = smart_llm.invoke(prompt) if smart_llm else None
        state.backend_code = getattr(resp, "content", str(resp)) if resp is not None else None
        logger.info(
            f"backend_node() - successfully generated backend code ({len(state.backend_code) if state.backend_code else 0} chars)"
        )
        return state
    except Exception as e:
        logger.error(f"backend_node() - failed to generate backend code: {e}", exc_info=True)
        raise
