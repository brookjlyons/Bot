# feedback/catalog/__init__.py
"""
Aggregator for the phrase catalog. Keeps the public API identical:
  - PHRASE_BOOK
  - COMPOUND_FLAGS
  - TIP_LINES
  - TITLE_BOOK
"""

from __future__ import annotations

# Import fragments
from .stats_core import PHRASE_BOOK as _PHRASES_CORE
from .stats_economy import PHRASE_BOOK as _PHRASES_ECON
from .stats_vision import PHRASE_BOOK as _PHRASES_VISION

from .flags import COMPOUND_FLAGS as _FLAGS
from .tips import TIP_LINES as _TIPS
from .titles import TITLE_BOOK as _TITLES


def _merge_dicts(*parts: dict) -> dict:
    out: dict = {}
    for p in parts:
        # shallow merge of top-level keys; later parts override earlier if dup
        out.update(p or {})
    return out


# Public exports (merged)
PHRASE_BOOK = _merge_dicts(_PHRASES_CORE, _PHRASES_ECON, _PHRASES_VISION)
COMPOUND_FLAGS = dict(_FLAGS)
TIP_LINES = dict(_TIPS)
TITLE_BOOK = dict(_TITLES)

__all__ = ["PHRASE_BOOK", "COMPOUND_FLAGS", "TIP_LINES", "TITLE_BOOK"]
