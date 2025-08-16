# feedback/advice_pkg/flags.py
import random
from typing import List, Optional
from feedback.catalog import COMPOUND_FLAGS


def select_flag_phrase(flags: List[str], mode: str, rng: Optional[random.Random] = None) -> Optional[str]:
    """
    First matching flag wins. Honors catalog 'modes' gating.
    Determinism: prefers provided local RNG; falls back to module-level random for back-compat.
    """
    chooser = rng.choice if rng is not None else random.choice

    for flag in flags:
        if not isinstance(flag, str):
            continue
        entry = COMPOUND_FLAGS.get(flag)
        if not isinstance(entry, dict):
            continue
        allowed = entry.get("modes", ["ALL"])
        if "ALL" not in allowed and mode not in allowed:
            continue
        lines = entry.get("lines", [])
        if lines:
            return chooser(lines)
    return None
