# feedback/advice_pkg/titles.py
import random
from typing import Tuple, Optional
from feedback.catalog import TITLE_BY_IMP


def get_title_phrase(
    score: float,
    won: bool,
    compound_flags: list[str],
    rng: Optional[random.Random] = None,
) -> Tuple[str, str]:
    """
    Return (emoji, phrase) for the title line based on performance score
    and win/loss outcome.

    NOTE:
    - Emojis are intentionally suppressed. The first tuple element is
      returned as an empty string for backward compatibility.
    - Deterministic: pure lookup by IMP bucket.
    - compound_flags and rng are accepted but intentionally unused.
    """
    try:
        score_val = float(score)
    except (ValueError, TypeError):
        score_val = 0.0

    score_int = int(round(score_val))

    if score_int <= -52:
        bucket = -52
    elif score_int >= 52:
        bucket = 52
    else:
        bucket = score_int

    phrase = TITLE_BY_IMP[bucket]["win" if won else "loss"]
    return "", phrase
