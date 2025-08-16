# feedback/advice_pkg/titles.py
import random
from typing import List, Tuple
from feedback.catalog import TITLE_BOOK

def _pick_title_bank(result_side: str, tier: str) -> List[str]:
    """
    Retrieve title lines for a given side ('win'|'loss') and tier.
    Falls back to legacy 'negative' bank if a new neg_* tier is missing.
    """
    side_book = TITLE_BOOK.get(result_side, {})
    if not isinstance(side_book, dict):
        return []
    lines = side_book.get(tier, [])
    if lines:
        return lines
    if tier in {"neg_low", "neg_mid", "neg_high", "neg_legendary"}:
        return side_book.get("negative", []) or []
    return lines or []

def get_title_phrase(score: float, won: bool, compound_flags: list[str]) -> Tuple[str, str]:
    """
    Return (emoji, phrase) for the title line based on performance score,
    win/loss, and important flags. Preserves legacy tiering and emojis,
    with a bugfix: loss-only snark cannot appear on wins.
    """
    try:
        score_val = float(score)
    except (ValueError, TypeError):
        score_val = 0.0

    # --- Flag-based overrides (guarded) ---
    # Only allow these snarky overrides on LOSSES (Bible: no snark on wins).
    if not won and "fed_no_impact" in compound_flags:
        return "☠️", "fed hard and lost the game"
    if not won and "farmed_did_nothing" in compound_flags:
        return "💀", "farmed but made no impact"
    # Neutral overrides are safe on both outcomes
    if "no_stacking_support" in compound_flags:
        return "🧺", "support who forgot to stack jungle"
    if "low_kp" in compound_flags:
        return "🤷", "low kill participation"

    # Very low neutral zone (−4 … +4)
    if -4 <= score_val <= 4:
        tier = "very_low"
        bank = _pick_title_bank("win" if won else "loss", tier)
        emoji = "🎲" if won else "💀"
        phrase = random.choice(bank) if bank else "played a game"
        return emoji, phrase

    # Positive bands
    if score_val >= 50:
        tier, win_emoji, loss_emoji = "legendary", "🧨", "🧨"
    elif score_val >= 35:
        tier, win_emoji, loss_emoji = "high", "💥", "💪"
    elif score_val >= 20:
        tier, win_emoji, loss_emoji = "mid", "🔥", "😓"
    elif score_val >= 5:
        tier, win_emoji, loss_emoji = "low", "🎯", "☠️"
    # Negative bands (mirrored)
    elif score_val <= -50:
        tier, win_emoji, loss_emoji = "neg_legendary", "🎁", "🤡"
    elif score_val <= -35:
        tier, win_emoji, loss_emoji = "neg_high", "🧯", "💀"
    elif score_val <= -20:
        tier, win_emoji, loss_emoji = "neg_mid", "🫠", "☠️"
    elif score_val <= -5:
        tier, win_emoji, loss_emoji = "neg_low", "😅", "😓"
    else:
        tier, win_emoji, loss_emoji = "very_low", "🎲", "💀"

    bank = _pick_title_bank("win" if won else "loss", tier)
    emoji = win_emoji if won else loss_emoji
    phrase = random.choice(bank) if bank else "played a game"
    return emoji, phrase
