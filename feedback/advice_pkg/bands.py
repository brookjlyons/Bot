# feedback/advice_pkg/bands.py
from typing import Any, Optional
from feedback.catalog import PHRASE_BOOK  # uses existing catalog.py module

def safe_num(x: Any, default: float | None = None) -> Optional[float]:
    try:
        if x is None:
            return default
        if isinstance(x, bool):
            return float(x)
        return float(x)
    except (TypeError, ValueError):
        return default

def stat_allowed(stat: str, mode: str) -> bool:
    """
    Check if a stat is allowed for phrasing in this mode.
    Delegates to catalog 'modes' metadata; defaults to ALL.
    """
    if not isinstance(stat, str):
        return False
    entry = PHRASE_BOOK.get(stat)
    if not entry:
        return False
    allowed = entry.get("modes", ["ALL"])
    return "ALL" in allowed or mode in allowed

def value_from_context(stat: str, ctx: dict) -> Optional[float]:
    # Special-case KP which may be computed upstream
    if stat == "killParticipation":
        return safe_num(ctx.get("killParticipation"))
    return safe_num(ctx.get(stat))

def band_for_stat(stat: str, value: Optional[float], polarity: str) -> str:
    """
    Map a numeric value to a band for the given stat and polarity.
    Thresholds are copied 1:1 from legacy advice.py.
    """
    if value is None:
        return "moderate"

    # IMP (for stat phrasing only; title bands handled elsewhere)
    if stat == "imp":
        if polarity == "positive":
            if value >= 15: return "extreme"
            if value >= 8:  return "high"
            if value >= 3:  return "moderate"
            return "light"
        else:
            if value <= -15: return "critical"
            if value <= -8:  return "severe"
            if value <= -3:  return "moderate"
            return "light"

    if stat == "kills":
        if polarity == "positive":
            if value >= 18: return "extreme"
            if value >= 12: return "high"
            if value >= 6:  return "moderate"
            return "light"
        else:
            if value <= 0:  return "critical"
            if value <= 2:  return "severe"
            if value <= 4:  return "moderate"
            return "light"

    if stat == "deaths":
        if polarity == "positive":
            if value <= 0:  return "extreme"
            if value <= 2:  return "high"
            if value <= 5:  return "moderate"
            return "light"
        else:
            if value >= 12: return "critical"
            if value >= 9:  return "severe"
            if value >= 6:  return "moderate"
            return "light"

    if stat == "assists":
        if polarity == "positive":
            if value >= 24: return "extreme"
            if value >= 16: return "high"
            if value >= 10: return "moderate"
            return "light"
        else:
            if value <= 1:  return "critical"
            if value <= 3:  return "severe"
            if value <= 6:  return "moderate"
            return "light"

    if stat == "level":
        if polarity == "positive":
            if value >= 26: return "extreme"
            if value >= 23: return "high"
            if value >= 18: return "moderate"
            return "light"
        else:
            if value <= 12: return "critical"
            if value <= 16: return "severe"
            if value <= 18: return "moderate"
            return "light"

    if stat == "killParticipation":
        if polarity == "positive":
            if value >= 0.80: return "extreme"
            if value >= 0.65: return "high"
            if value >= 0.50: return "moderate"
            return "light"
        else:
            if value <= 0.20: return "critical"
            if value <= 0.30: return "severe"
            if value <= 0.45: return "moderate"
            return "light"

    # Economy metrics (NON_TURBO only; gating handled by stat_allowed)
    if stat == "gpm":
        if polarity == "positive":
            if value >= 650: return "extreme"
            if value >= 550: return "high"
            if value >= 450: return "moderate"
            return "light"
        else:
            if value <= 250: return "critical"
            if value <= 320: return "severe"
            if value <= 400: return "moderate"
            return "light"

    if stat == "xpm":
        if polarity == "positive":
            if value >= 700: return "extreme"
            if value >= 600: return "high"
            if value >= 500: return "moderate"
            return "light"
        else:
            if value <= 300: return "critical"
            if value <= 380: return "severe"
            if value <= 460: return "moderate"
            return "light"

    # Vision/utility
    if stat == "campStack":
        if polarity == "positive":
            if value >= 10: return "extreme"
            if value >= 7:  return "high"
            if value >= 4:  return "moderate"
            return "light"
        else:
            if value <= 0:  return "critical"
            if value <= 1:  return "severe"
            if value <= 3:  return "moderate"
            return "light"

    return "moderate"
