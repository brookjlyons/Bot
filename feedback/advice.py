# feedback/advice.py
# Compatibility shim to preserve public API after modularization.
# Re-exports the stable surface: generate_advice, get_title_phrase
from .advice_pkg import generate_advice as _pkg_generate_advice, get_title_phrase as _pkg_get_title_phrase

__all__ = ["generate_advice", "get_title_phrase"]


def generate_advice(tags: dict, stats: dict, *, mode: str, rng=None) -> dict:
    """
    Public shim for advice generation.

    Adds optional `rng` (random.Random) for deterministic selection without relying on global RNG.
    For backward compatibility with older advice_pkg implementations that don't accept `rng`,
    we fall back to the legacy signature when needed.
    """
    try:
        # Preferred path: advice_pkg supports rng
        return _pkg_generate_advice(tags, stats, mode=mode, rng=rng)
    except TypeError:
        # Back-compat: older advice_pkg without rng kwarg
        return _pkg_generate_advice(tags, stats, mode=mode)


def get_title_phrase(score: float, is_victory: bool, compound_flags: list[str], rng=None) -> tuple[str, str]:
    """
    Public shim for title selection.

    Adds optional `rng` (random.Random). Falls back to legacy signature if advice_pkg
    does not yet accept `rng`.
    """
    try:
        # Preferred path: advice_pkg supports rng
        return _pkg_get_title_phrase(score, is_victory, compound_flags, rng=rng)
    except TypeError:
        # Back-compat: older advice_pkg without rng kwarg
        return _pkg_get_title_phrase(score, is_victory, compound_flags)
