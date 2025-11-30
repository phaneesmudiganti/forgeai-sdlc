import logging
from src.config import create_fast_llm, create_smart_llm

logger = logging.getLogger(__name__)


def create_llms():
    """Create and return a tuple (fast_llm, smart_llm).

    This wrapper centralises LLM creation in one place so tests can patch it.
    """
    try:
        fast = create_fast_llm()
        logger.debug("llms.create_llms() - fast LLM created")
    except Exception:
        logger.exception("llms.create_llms() - failed to create fast LLM")
        fast = None

    try:
        smart = create_smart_llm()
        logger.debug("llms.create_llms() - smart LLM created")
    except Exception:
        logger.exception("llms.create_llms() - failed to create smart LLM")
        smart = None

    return fast, smart


# module-level instances for backward compatibility with previous code
fast_llm, smart_llm = create_llms()
