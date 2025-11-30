import logging
from dataclasses import dataclass, field
from typing import Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class SDLCState:
    requirements: str
    ba_output: str | None = None
    architecture: str | None = None
    backend_code: str | None = None
    frontend_code: str | None = None
    qa_results: str | None = None
    review_notes: str | None = None
    review_iterations: int = 0
    devops_output: str | None = None
    approved: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)


def from_mapping(m: Dict[str, Any]) -> SDLCState:
    """Construct an SDLCState from a mapping-like object safely."""
    if not m:
        return SDLCState(requirements="")
    try:
        return SDLCState(
            requirements=m.get("requirements", ""),
            ba_output=m.get("ba_output"),
            architecture=m.get("architecture"),
            backend_code=m.get("backend_code"),
            frontend_code=m.get("frontend_code"),
            qa_results=m.get("qa_results"),
            review_notes=m.get("review_notes"),
            review_iterations=int(m.get("review_iterations", 0)),
            devops_output=m.get("devops_output"),
            approved=bool(m.get("approved", False)),
            meta=m.get("meta", {}) or {},
        )
    except Exception:
        logger.exception("from_mapping() - failed to convert mapping to SDLCState, using defaults")
        return SDLCState(requirements=m.get("requirements", "") if isinstance(m, dict) else "")
