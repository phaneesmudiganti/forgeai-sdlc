import logging
from src.workflow.state import SDLCState
from src.workflow.llms import smart_llm

logger = logging.getLogger(__name__)


def architect_node(state: SDLCState) -> SDLCState:
    logger.info("architect_node() - starting Software Architect processing")
    logger.debug(f"architect_node() - input BA output length: {len(state.ba_output) if state.ba_output else 0} chars")

    if not state.ba_output:
        logger.error("architect_node() - BA output is missing or empty")
        raise ValueError("BA output is required for architecture design")

    try:
        prompt = (
            "You are a senior Software Architect.\n\n"
            "Design a modular architecture and implementation plan based on these requirements:\n\n"
            f"{state.ba_output}\n\n"
            "Include:\n"
            "- system overview\n- key components\n- APIs\n- data flows\n"
            "- folder structure\n- technology stack\n- implementation sequence\n"
        )
        logger.debug("architect_node() - invoking smart_llm with architecture prompt")
        resp = smart_llm.invoke(prompt) if smart_llm else None
        state.architecture = getattr(resp, "content", str(resp)) if resp is not None else None
        logger.info(
            f"architect_node() - successfully generated architecture ({len(state.architecture) if state.architecture else 0} chars)"
        )
        return state
    except Exception as e:
        logger.error(f"architect_node() - failed to design architecture: {e}", exc_info=True)
        raise
