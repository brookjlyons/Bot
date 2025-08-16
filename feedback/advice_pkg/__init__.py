# feedback/advice_pkg/__init__.py
# Public surface re-exports (keep names identical to legacy)
from .builder import generate_advice  # noqa: F401
from .titles import get_title_phrase  # noqa: F401

__all__ = ["generate_advice", "get_title_phrase"]
