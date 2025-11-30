import logging
from src.workflow.state import SDLCState
from src.workflow.llms import fast_llm

logger = logging.getLogger(__name__)


def devops_node(state: SDLCState) -> SDLCState:
    logger.info("devops_node() - starting DevOps Engineer processing")
    logger.debug(
        f"devops_node() - approval status: {state.approved}, "
        f"backend code length: {len(state.backend_code) if state.backend_code else 0} chars, "
        f"frontend code length: {len(state.frontend_code) if state.frontend_code else 0} chars"
    )

    try:
        prompt = (
            "You are a DevOps Engineer.\n\n"
            "Generate CI/CD (e.g. GitHub Actions) and basic IaC for deploying "
            "the backend and frontend implemented above.\n\n"
            "Return code/config only with markers like:\n"
            "# file: .github/workflows/ci_cd.yml\n"
            "<yaml>\n"
            "# file: infra/main.tf\n"
            "<terraform>\n"
        )

        logger.debug("devops_node() - invoking fast_llm with DevOps prompt")
        resp = fast_llm.invoke(prompt) if fast_llm else None

        state.devops_output = getattr(resp, "content", str(resp)) if resp is not None else None
        logger.info(
            f"devops_node() - successfully generated DevOps code ({len(state.devops_output) if state.devops_output else 0} chars)"
        )
        return state
    except Exception as e:
        logger.error(f"devops_node() - failed to generate DevOps code: {e}", exc_info=True)
        raise
