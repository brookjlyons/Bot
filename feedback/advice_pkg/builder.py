# feedback/advice_pkg/builder.py
from typing import Dict, List, Optional
from .bands import stat_allowed
from .selectors import choose_banded_line, choose_banded_tip
from .flags import select_flag_phrase

def generate_advice(
    tags: Dict,
    context: Dict[str, float],
    ignore_stats: Optional[List[str]] = None,
    mode: str = "NON_TURBO"
) -> Dict[str, List[str]]:
    """
    Orchestrates selection of positives, negatives, flags, and tips.
    Move-only refactor from legacy advice.py with identical behavior.
    """
    if ignore_stats is None:
        ignore_stats = []

    positives: List[str] = []
    negatives: List[str] = []
    tips: List[str] = []
    flags: List[str] = []
    used = set()

    hi = tags.get("highlight")
    lo = tags.get("lowlight")
    praises = tags.get("praises", [])
    critiques = tags.get("critiques", [])
    compound_flags = tags.get("compound_flags", [])

    # --- Praise ---
    candidates = [hi] + praises
    for stat in candidates:
        if not isinstance(stat, str):
            continue
        if not stat_allowed(stat, mode) or stat in ignore_stats:
            continue
        line = choose_banded_line(stat, "positive", context)
        if line:
            positives.append(line)
            used.add(stat)
            break

    # --- Critique ---
    candidates = [lo] + critiques
    for stat in candidates:
        if not isinstance(stat, str):
            continue
        if not stat_allowed(stat, mode) or stat in ignore_stats or stat in used:
            continue
        line = choose_banded_line(stat, "negative", context)
        if line:
            negatives.append(line)
            used.add(stat)
            break

    # --- Flag (first match wins) ---
    flag_line = select_flag_phrase(compound_flags, mode)
    if flag_line:
        flags.append(flag_line)

    # --- Tip (prefer used stat, then others) ---
    for stat in list(used) + praises + critiques:
        if not isinstance(stat, str):
            continue
        if stat in ignore_stats:
            continue
        tip_line = choose_banded_tip(stat, context, mode)
        if tip_line:
            tips.append(tip_line)
            break

    return {
        "positives": positives,
        "negatives": negatives,
        "flags": flags,
        "tips": tips
    }
