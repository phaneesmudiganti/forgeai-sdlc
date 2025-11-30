import logging
from src.workflow.state import SDLCState
from src.workflow.llms import fast_llm

logger = logging.getLogger(__name__)


def business_analyst_node(state: SDLCState) -> SDLCState:
    logger.info("business_analyst_node() - starting Business Analyst processing")
    logger.debug(f"business_analyst_node() - input requirements length: {len(state.requirements)} chars")
    try:
        prompt = (
            "You are a senior Business Analyst.\n\n"
            "Rewrite the following requirements to be clear, unambiguous, and structured. "
            "Identify actors, user stories, functional and non-functional requirements.\n\n"
            f"Requirements:\n{state.requirements}\n"
        )
        logger.debug("business_analyst_node() - invoking fast_llm with BA prompt")
        resp = fast_llm.invoke(prompt) if fast_llm else None
        state.ba_output = getattr(resp, "content", str(resp)) if resp is not None else None
        logger.info(
            f"business_analyst_node() - successfully generated BA output ({len(state.ba_output) if state.ba_output else 0} chars)"
        )
        return state
    except Exception as e:
        logger.error(f"business_analyst_node() - failed to process requirements: {e}", exc_info=True)
        raise
