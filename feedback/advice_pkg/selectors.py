# feedback/advice_pkg/selectors.py
import random
from typing import Any, List, Optional, Dict
from feedback.catalog import PHRASE_BOOK, TIP_LINES
from .bands import band_for_stat, value_from_context

def _flatten_bands(lines_def: Any) -> List[str]:
    """Accept either a flat list or a dict-of-bands and return a flat list of lines."""
    if isinstance(lines_def, list):
        return [s for s in lines_def if isinstance(s, str) and s.strip()]
    if isinstance(lines_def, dict):
        out: List[str] = []
        for v in lines_def.values():
            if isinstance(v, list):
                out.extend([s for s in v if isinstance(s, str) and s.strip()])
        return out
    return []

def choose_banded_line(stat: str, polarity: str, context: Dict[str, Any]) -> Optional[str]:
    entry = PHRASE_BOOK.get(stat, {})
    lines_def = entry.get(polarity, [])

    # Legacy flat list support
    if isinstance(lines_def, list):
        flat = _flatten_bands(lines_def)
        return random.choice(flat) if flat else None

    # Banded dict
    if isinstance(lines_def, dict):
        val = value_from_context(stat, context)
        band = band_for_stat(stat, val, polarity)
        lines = lines_def.get(band) or []
        if not lines:
            flat = _flatten_bands(lines_def)
            return random.choice(flat) if flat else None
        return random.choice(lines)

    return None

def choose_banded_tip(stat: str, context: Dict[str, Any], mode: str) -> Optional[str]:
    tip_entry = TIP_LINES.get(stat)
    if not isinstance(tip_entry, dict):
        return None
    allowed_modes = tip_entry.get("modes", ["ALL"])
    if "ALL" not in allowed_modes and mode not in allowed_modes:
        return None
    tip_text = tip_entry.get("text")
    if isinstance(tip_text, str):
        return tip_text
    if isinstance(tip_text, dict):
        val = value_from_context(stat, context)
        # Tips are constructive: map via positive polarity bands
        band = band_for_stat(stat, val, "positive")
        lines = tip_text.get(band) or []
        if lines and isinstance(lines, list):
            return random.choice(lines)
    return None
