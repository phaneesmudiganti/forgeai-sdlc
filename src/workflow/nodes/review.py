import logging
import json
from src.workflow.state import SDLCState
from src.workflow.llms import smart_llm

logger = logging.getLogger(__name__)
MAX_REVIEW_LOOPS = 3


def review_node(state: SDLCState) -> SDLCState:
    logger.info("review_node() - starting Code Reviewer processing")
    logger.debug(
        f"review_node() - reviewing backend ({len(state.backend_code) if state.backend_code else 0} chars), "
        f"frontend ({len(state.frontend_code) if state.frontend_code else 0} chars), "
        f"tests ({len(state.qa_results) if state.qa_results else 0} chars)"
    )

    try:
        prompt = (
            "You are a strict senior software code reviewer.\n\n"
            "Your response MUST be ONLY valid JSON matching EXACTLY this format:\n"
            "{\n"
            '  "status": "APPROVED" | "CHANGES_REQUIRED",\n'
            '  "reasoning": "short explanation",\n'
            '  "required_changes": ["list of actionable fixes or empty if approved"]\n'
            "}\n\n"
            "Rules:\n"
            "- If the code is acceptable and functional even with minor imperfections, set status to \"APPROVED\".\n"
            "- Only ask for changes if the code has functional, security, or major architectural problems.\n"
            "- If the same issues have already been addressed in earlier cycles, do NOT repeat them — approve.\n"
            "- DO NOT add comments outside of JSON.\n\n"
            f"Backend:\n{state.backend_code}\n\nFrontend:\n{state.frontend_code}\n\nTests:\n{state.qa_results}\n"
        )

        logger.debug("review_node() - invoking smart_llm with code review prompt")
        resp = smart_llm.invoke(prompt) if smart_llm else None

        content = getattr(resp, "content", str(resp)) if resp is not None else ""
        state.review_notes = content
        logger.debug(f"review_node() - review response: {content}")

        try:
            parsed = json.loads(content)
            status = parsed.get("status", "").upper()
        except Exception:
            logger.warning("review_node() - reviewer did not return valid JSON; treating as CHANGES_REQUIRED")
            status = "CHANGES_REQUIRED"

        if status == "APPROVED":
            state.approved = True
            logger.info("review_node() - code APPROVED by reviewer")
        else:
            state.approved = False
            logger.info("review_node() - code review returned CHANGES_REQUIRED")

        state.review_iterations += 1

        if not state.approved and state.review_iterations >= MAX_REVIEW_LOOPS:
            logger.warning(
                f"review_node() - maximum review iterations ({MAX_REVIEW_LOOPS}) reached; forcing approval"
            )
            state.approved = True
            state.review_iterations = 0

        return state
    except Exception as e:
        logger.error(f"review_node() - failed to conduct code review: {e}", exc_info=True)
        raise
