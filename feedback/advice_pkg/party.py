from __future__ import annotations

import logging
import random
from typing import Dict, List, Optional, Tuple

from feedback.catalog import party as party_catalog

logger = logging.getLogger(__name__)


# IMP tier thresholds from [REFERENCE:IMP_TIERS] in the Bible:
# legendary:      >= 50
# high:           35–49
# mid:            20–34
# low:            5–19
# very_low:       -4…+4
# neg_low:        -19…-5
# neg_mid:        -34…-20
# neg_high:       -49…-35
# neg_legendary:  <= -50
def _imp_tier(imp: float) -> str:
    """
    Map raw IMP to a tier label, matching Bible thresholds.

    Returns one of:
      "legendary", "high", "mid", "low", "very_low",
      "neg_low", "neg_mid", "neg_high", "neg_legendary".
    """
    if imp is None:
        # Caller should avoid calling this with None, but guard defensively.
        logger.warning("party_advice._imp_tier called with imp=None; defaulting to 'very_low'")
        return "very_low"

    if imp >= 50:
        return "legendary"
    if imp >= 35:
        return "high"
    if imp >= 20:
        return "mid"
    if imp >= 5:
        return "low"
    if imp >= -4:
        return "very_low"
    if imp >= -19:
        return "neg_low"
    if imp >= -34:
        return "neg_mid"
    if imp >= -49:
        return "neg_high"
    return "neg_legendary"


def _tier_for_catalog(imp: Optional[float]) -> str:
    """
    Convert IMP into a tier key that exists (or can reasonably map) in PLAYER_LINES.

    PLAYER_LINES in the catalog is currently sparse:
      - "legendary", "high", "mid", "very_low", "negative"
    and may grow over time. This helper keeps us resilient if the catalog
    is expanded to cover the full negative bands.

    Rules:
      - Map positive / neutral bands directly when possible.
      - All negative bands collapse to "negative" for now.
      - If we can't find a direct match in the catalog, fall back to a nearby tier.
    """
    if imp is None:
        return "very_low"

    base = _imp_tier(imp)

    # Direct matches we know the catalog uses.
    if base in ("legendary", "high", "mid", "low", "very_low"):
        return base

    # Collapse all negative bands into a single bucket for phrase selection.
    if base.startswith("neg_") or base == "negative":
        return "negative"

    # Failsafe: if we somehow get something unexpected, log and punt to very_low.
    logger.warning("party_advice._tier_for_catalog got unexpected base tier %r; using 'very_low'", base)
    return "very_low"


def _assign_labels(players: List[dict]) -> Dict[str, str]:
    """
    Assign role labels to each player with visible IMP:

    Labels:
      - "hard_carry": top IMP on winning side, high/legendary.
      - "hero_loss":  high/legendary IMP on losing side.
      - "strong":     mid/high on either side.
      - "fed":        clearly negative IMP.
      - "ride_along": very low IMP when someone else carried.
      - "private":    used by caller for players with no IMP.

    Returns:
      { steamId (str) : label (str) }
    """
    visible = [p for p in players if p.get("imp") is not None]
    labels: Dict[str, str] = {}

    if not visible:
        return labels

    # Compute basic IMP stats.
    max_imp = max(p["imp"] for p in visible)  # type: ignore[arg-type]
    min_imp = min(p["imp"] for p in visible)  # type: ignore[arg-type]

    # Identify obvious carry / hero-in-loss anchors.
    # We treat "high" and above as candidates.
    for p in visible:
        steam_id = str(p.get("steamId", ""))
        imp = float(p.get("imp", 0.0))
        won = bool(p.get("won", False))
        tier = _imp_tier(imp)

        is_top = imp == max_imp

        if won and is_top and tier in ("legendary", "high"):
            labels[steam_id] = "hard_carry"
        elif (not won) and tier in ("legendary", "high"):
            labels[steam_id] = "hero_loss"

    # Second pass: feeders and strong performers.
    for p in visible:
        steam_id = str(p.get("steamId", ""))
        if steam_id in labels:
            continue

        imp = float(p.get("imp", 0.0))
        tier = _imp_tier(imp)

        if tier in ("neg_low", "neg_mid", "neg_high", "neg_legendary"):
            labels[steam_id] = "fed"
        elif tier in ("mid", "high"):
            labels[steam_id] = "strong"

    # Third pass: ride-alongs for anyone left with very low/low impact,
    # especially when someone else had much higher IMP.
    threshold_gap = 20.0  # if max_imp is at least 20 higher, this looks like a carry + ride-along situation
    for p in visible:
        steam_id = str(p.get("steamId", ""))
        if steam_id in labels:
            continue

        imp = float(p.get("imp", 0.0))
        tier = _imp_tier(imp)

        if tier in ("very_low", "low") and (max_imp - imp) >= threshold_gap:
            labels[steam_id] = "ride_along"

    # Anything still unlabeled but visible gets a generic "strong" or "ride_along"
    # based on whether they are above or below the mid-point between max/min.
    midpoint = (max_imp + min_imp) / 2.0
    for p in visible:
        steam_id = str(p.get("steamId", ""))
        if steam_id in labels:
            continue

        imp = float(p.get("imp", 0.0))
        if imp >= midpoint:
            labels[steam_id] = "strong"
        else:
            labels[steam_id] = "ride_along"

    return labels


def _choose_player_line(
    rng: random.Random,
    player: dict,
    label: str,
) -> str:
    """
    Pick and format a per-player line for a single guild player.

    Falls back to a simple scoreboard line if no phrase is available.
    """
    name = str(player.get("name") or "Unknown")
    hero = str(player.get("hero") or "Unknown hero")
    kills = int(player.get("kills") or 0)
    deaths = int(player.get("deaths") or 0)
    assists = int(player.get("assists") or 0)
    imp_val = player.get("imp")
    is_private = bool(player.get("isPrivate", False))

    if is_private or label == "private":
        # Use PRIVATE_LINES from the catalog.
        options = party_catalog.PRIVATE_LINES or []
        if options:
            template = rng.choice(options)
            return template.format(
                name=name,
                hero=hero,
                k=kills,
                d=deaths,
                a=assists,
                imp="?",
            )

        # Fallback if catalog is unexpectedly empty.
        logger.warning("party_advice: PRIVATE_LINES is empty; falling back to generic private line")
        return f"{name} keeps their match data private, so we only see {kills}/{deaths}/{assists} on {hero}."

    # Visible IMP path.
    tier = _tier_for_catalog(imp_val)
    role_map = party_catalog.PLAYER_LINES.get(label) or {}
    lines = role_map.get(tier)

    if not lines:
        # Try a softer fallback: for negative buckets, collapse to "negative" if present.
        if tier.startswith("neg_"):
            lines = role_map.get("negative")
        if not lines:
            logger.warning(
                "party_advice: no PLAYER_LINES for label=%r, tier=%r; falling back to generic scoreboard line",
                label,
                tier,
            )
            # Hard fallback: generic but still deterministic.
            imp_str = "?" if imp_val is None else f"{imp_val:.1f}"
            return f"{name} on {hero}: {kills}/{deaths}/{assists}, IMP {imp_str}."

    template = rng.choice(lines)
    imp_str = "?" if imp_val is None else f"{imp_val:.1f}"

    return template.format(
        name=name,
        hero=hero,
        k=kills,
        d=deaths,
        a=assists,
        imp=imp_str,
    )


def _pick_overall_line(
    rng: random.Random,
    scenario_key: str,
) -> str:
    """
    Pick an overall party/duel commentary line.

    Falls back to a generic line if the catalog bucket is missing or empty.
    """
    lines = party_catalog.OVERALL_LINES.get(scenario_key) or []
    if lines:
        return rng.choice(lines)

    logger.warning("party_advice: no OVERALL_LINES for key=%r; using generic overall line", scenario_key)
    if scenario_key == "party_win":
        return "The stack pulled together for a solid party win."
    if scenario_key == "party_loss":
        return "Rough party game — at least everyone suffered together."
    if scenario_key == "duel_radiant_win":
        return "Radiant side took the guild duel."
    if scenario_key == "duel_dire_win":
        return "Dire side took the guild duel."
    if scenario_key == "duel_close":
        return "The guild duel was tight — both sides had impact."

    return "Guild game wrapped up — the details are in the scoreboard."


def _decide_duel_scenario(
    radiant_players: List[dict],
    dire_players: List[dict],
) -> str:
    """
    Decide which duel scenario key to use:
      - "duel_radiant_win"
      - "duel_dire_win"
      - "duel_close"
    """
    radiant_won = any(bool(p.get("won")) for p in radiant_players)
    dire_won = any(bool(p.get("won")) for p in dire_players)

    # Normal case: exactly one side wins.
    if radiant_won and not dire_won:
        # Later we may override to "duel_close" if IMP gap is small.
        key = "duel_radiant_win"
    elif dire_won and not radiant_won:
        key = "duel_dire_win"
    else:
        # Degenerate / unexpected case: treat as close.
        logger.warning(
            "party_advice._decide_duel_scenario unusual win state: radiant_won=%r, dire_won=%r",
            radiant_won,
            dire_won,
        )
        return "duel_close"

    # Optional IMP-gap logic to flip to "close".
    def total_imp(players: List[dict]) -> float:
        return sum(float(p.get("imp", 0.0) or 0.0) for p in players if p.get("imp") is not None)

    radiant_imp = total_imp(radiant_players)
    dire_imp = total_imp(dire_players)
    imp_gap = abs(radiant_imp - dire_imp)

    # If total IMP is very similar, treat as a close duel regardless of who technically won.
    if imp_gap <= 10.0:
        return "duel_close"

    return key


def build_party_advice(group_stats: dict) -> dict:
    """
    Build group-level advice for a stacked party game.

    Input shape (from the plan):

        {
            "matchId": int,
            "partyId": int,
            "isRadiant": bool,
            "won": bool,
            "players": [
                {
                    "steamId": str,
                    "name": str,
                    "hero": str,
                    "imp": Optional[float],
                    "kills": int,
                    "deaths": int,
                    "assists": int,
                    "isRadiant": bool,
                    "won": bool,
                    "isPrivate": bool,
                },
                ...
            ]
        }

    Returns:

        {
            "perPlayerLines": [...],  # one string per guild player, in input order
            "overallLine": "..."
        }
    """
    match_id = int(group_stats.get("matchId") or 0)
    party_id = int(group_stats.get("partyId") or 0)
    won = bool(group_stats.get("won", False))

    players: List[dict] = list(group_stats.get("players") or [])

    rng = random.Random(f"{match_id}:party:{party_id}")

    # Label visible-IMP players.
    labels_by_id = _assign_labels(players)

    per_player_lines: List[str] = []
    for p in players:
        steam_id = str(p.get("steamId", ""))
        is_private = bool(p.get("isPrivate", False))

        if is_private:
            label = "private"
        else:
            label = labels_by_id.get(steam_id, "strong")

        line = _choose_player_line(rng, p, label)
        per_player_lines.append(line)

    scenario_key = "party_win" if won else "party_loss"
    overall_line = _pick_overall_line(rng, scenario_key)

    return {
        "perPlayerLines": per_player_lines,
        "overallLine": overall_line,
    }


def build_duel_advice(duel_stats: dict) -> dict:
    """
    Build group-level advice for a guild duel (guild vs guild).

    Input shape (from the plan):

        {
            "matchId": int,
            "radiantPlayers": [...],
            "direPlayers": [...],
        }

    Each player entry mirrors the party players:
        steamId, name, hero, imp (or None),
        kills, deaths, assists, isRadiant, won, isPrivate.

    Returns:

        {
            "perPlayerLines": [...],  # one per guild player (Radiant first, then Dire)
            "overallLine": "..."
        }
    """
    match_id = int(duel_stats.get("matchId") or 0)
    radiant_players: List[dict] = list(duel_stats.get("radiantPlayers") or [])
    dire_players: List[dict] = list(duel_stats.get("direPlayers") or [])

    rng = random.Random(f"{match_id}:duel")

    all_players: List[dict] = radiant_players + dire_players
    labels_by_id = _assign_labels(all_players)

    per_player_lines: List[str] = []

    # Preserve grouping: Radiant players first, then Dire.
    for p in all_players:
        steam_id = str(p.get("steamId", ""))
        is_private = bool(p.get("isPrivate", False))

        if is_private:
            label = "private"
        else:
            label = labels_by_id.get(steam_id, "strong")

        line = _choose_player_line(rng, p, label)
        per_player_lines.append(line)

    scenario_key = _decide_duel_scenario(radiant_players, dire_players)
    overall_line = _pick_overall_line(rng, scenario_key)

    return {
        "perPlayerLines": per_player_lines,
        "overallLine": overall_line,
    }


__all__ = ["build_party_advice", "build_duel_advice"]

