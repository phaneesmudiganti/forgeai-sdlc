import logging
from src.workflow.state import SDLCState
from src.workflow.llms import fast_llm

logger = logging.getLogger(__name__)


def qa_node(state: SDLCState) -> SDLCState:
    logger.info("qa_node() - starting QA Engineer processing")
    logger.debug(
        f"qa_node() - input backend code length: {len(state.backend_code) if state.backend_code else 0} chars, "
        f"frontend code length: {len(state.frontend_code) if state.frontend_code else 0} chars"
    )

    if not state.backend_code or not state.frontend_code:
        logger.error("qa_node() - backend or frontend code is missing")
        raise ValueError("Both backend and frontend code are required for QA")

    try:
        prompt = (
            "You are a QA Engineer.\n\n"
            "Write integration/E2E tests for the following backend and frontend code.\n\n"
            "Backend code:\n"
            f"{state.backend_code}\n\n"
            "Frontend code:\n"
            f"{state.frontend_code}\n\n"
            "Return test code only with markers like:\n"
            "# file: tests/integration/test_flows.py\n"
            "<code here>\n"
        )
        logger.debug("qa_node() - invoking fast_llm with QA test generation prompt")
        resp = fast_llm.invoke(prompt) if fast_llm else None
        state.qa_results = getattr(resp, "content", str(resp)) if resp is not None else None
        logger.info(
            f"qa_node() - successfully generated QA test code ({len(state.qa_results) if state.qa_results else 0} chars)"
        )
        return state
    except Exception as e:
        logger.error(f"qa_node() - failed to generate QA tests: {e}", exc_info=True)
        raise
