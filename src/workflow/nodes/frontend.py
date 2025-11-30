import logging
from src.workflow.state import SDLCState
from src.workflow.llms import smart_llm

logger = logging.getLogger(__name__)


def frontend_node(state: SDLCState) -> SDLCState:
    logger.info("frontend_node() - starting Frontend Engineer processing")
    logger.debug(f"frontend_node() - input architecture length: {len(state.architecture) if state.architecture else 0} chars")

    if not state.architecture:
        logger.error("frontend_node() - architecture is missing or empty")
        raise ValueError("Architecture is required for frontend implementation")

    try:
        prompt = (
            "You are a senior Frontend Engineer.\n\n"
            "Implement a React (TypeScript) frontend based on this architecture:\n\n"
            f"{state.architecture}\n\n"
            "Return code only, with markers like:\n"
            "# file: frontend/src/App.tsx\n"
            "<code here>\n"
        )
        logger.debug("frontend_node() - invoking smart_llm with frontend implementation prompt")
        resp = smart_llm.invoke(prompt) if smart_llm else None
        state.frontend_code = getattr(resp, "content", str(resp)) if resp is not None else None
        logger.info(
            f"frontend_node() - successfully generated frontend code ({len(state.frontend_code) if state.frontend_code else 0} chars)"
        )
        return state
    except Exception as e:
        logger.error(f"frontend_node() - failed to generate frontend code: {e}", exc_info=True)
        raise
