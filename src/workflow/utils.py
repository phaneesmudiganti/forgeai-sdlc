import logging
from typing import Any

logger = logging.getLogger(__name__)


def safe_get_state_attr(s: Any, name: str, default=None):
    """Safely extract attribute or mapping key from state-like objects.

    Works for dataclass-like objects with attributes, dict-like mappings,
    and objects exposing a .get(...) API.
    """
    try:
        if hasattr(s, name):
            return getattr(s, name)
    except Exception:
        pass
    try:
        if isinstance(s, dict):
            return s.get(name, default)
        getter = getattr(s, "get", None)
        if callable(getter):
            return getter(name, default)
    except Exception:
        pass
    return default


def sanitize_rel_path(rel_path: str) -> str:
    """Basic sanitization for LLM-provided relative file paths.

    This removes any absolute prefix and normalises separators. It does NOT
    resolve the path; the caller should resolve and check containment.
    """
    if not rel_path:
        return rel_path
    # strip leading slashes
    p = rel_path.lstrip("/\\")
    # collapse up-level parts simply by removing them here — caller should
    # still resolve and verify the final path inside output dir.
    parts = [part for part in p.replace("\\", "/").split("/") if part and part != ".."]
    return "/".join(parts)
