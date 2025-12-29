# bot/formatter.py
import json
from pathlib import Path
import hashlib
import random
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from feedback.extract import extract_player_stats
from datetime import datetime
import os
from typing import Any
from feedback.catalog.impact import impact_explanation_line

# Public surface re-exported from formatter_pkg
from bot.formatter_pkg.stats_sets import NORMAL_STATS, TURBO_STATS
from bot.formatter_pkg.mode import resolve_game_mode_name, is_turbo_mode
from bot.formatter_pkg.util import normalize_hero_name, get_role, get_baseline
from bot.formatter_pkg.embed import build_discord_embed, build_fallback_embed, build_party_fallback_embed, build_duel_fallback_embed

__all__ = [
    # constants
    "NORMAL_STATS", "TURBO_STATS",
    # main formatters
    "format_match_embed", "format_fallback_embed",
    # embed builders
    "build_discord_embed", "build_fallback_embed", "build_party_fallback_embed", "build_duel_fallback_embed",
    # utilities (deprecated kept public)
    "normalize_hero_name", "get_role", "get_baseline",
]


_AVATAR_BASE_URL = "https://raw.githubusercontent.com/brooklyons/Bot/main/Bot-main/data/avatars/"
_AVATAR_DEFAULT_URL = f"{_AVATAR_BASE_URL}default.jpg"


def _avatar_url_from_steam32(steam32: Any) -> str:
    """
    Deterministically derive a public avatar URL from Steam32.
    Always returns a non-empty URL string (never None).
    """
    try:
        sid = int(steam32)
    except Exception:
        return _AVATAR_DEFAULT_URL
    if sid <= 0:
        return _AVATAR_DEFAULT_URL
    return f"{_AVATAR_BASE_URL}{sid}.jpg"


def _first3_lines(value) -> list[str]:
    """
    Normalize any advice collection into a list[str] of at most 3 items.
    - None → []
    - str  → [str] (single line)
    - list/tuple → cast each item to str, keep first 3
    Ensures no None leaks into the embed pipeline.
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value][:1]
    if isinstance(value, (list, tuple)):
        return [str(x) for x in list(value)[:3]]
    # Unexpected type: coerce to single-line string
    return [str(value)][:1]


def _notes_sentence(lines: list[str]) -> str:
    """
    Collapse a list[str] (≤3) into a single sentence.
    - [] -> ""
    - joins with a single space
    - ensures terminal punctuation (.,!,?) for clean paragraph concatenation
    """
    if not lines:
        return ""
    s = " ".join([str(x).strip() for x in lines if str(x).strip()]).strip()
    if not s:
        return ""
    if s.endswith((".", "!", "?")):
        return s
    return s + "."


def _safe_score_float(value) -> float:
    """
    Defensive float parse for IMP score.
    - None/unparseable -> 0.0
    - NaN -> 0.0
    """
    try:
        f = float(value)
    except Exception:
        return 0.0
    # NaN check: NaN != NaN
    if f != f:
        return 0.0
    return f


# --- Main match analysis entrypoint ---
def format_match_embed(player: dict, match: dict, stats_block: dict, player_name: str = "Player") -> dict:
    game_mode_field = match.get("gameMode")
    raw_label = (match.get("gameModeName") or "").upper()

    game_mode_name = resolve_game_mode_name(game_mode_field, raw_label)
    is_turbo = is_turbo_mode(game_mode_field, raw_label)
    mode = "TURBO" if is_turbo else "NON_TURBO"

    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in match.get("players", [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    stats = extract_player_stats(player, stats_block, team_kills, mode)
    stats["durationSeconds"] = match.get("durationSeconds", 0)

    # Safe-null sweep — preserve exact behavior
    for k in list(stats.keys()):
        v = stats[k]
        if v is None:
            if k in {"lane", "roleBasic"}:
                stats[k] = ""
            elif k == "statsBlock":
                stats[k] = {}
            else:
                stats[k] = 0

    engine = analyze_turbo if is_turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)

    tags = result.get("feedback_tags", {})
    is_victory = player.get("isVictory", False)

    # Deterministic RNG (local) — seeded per match:player
    seed_str = f"{match.get('id')}:{player.get('steamAccountId')}"
    seed_hex = hashlib.md5(seed_str.encode()).hexdigest()
    rng = random.Random(int(seed_hex, 16))

    # Transitional: still seed global RNG for back-compat until advice* is updated
    try:
        random.seed(seed_hex)
    except Exception:
        pass

    # Advice (pass rng if supported; fall back to legacy signature otherwise)
    try:
        advice = generate_advice(tags, stats, mode=mode, rng=rng)  # new preferred path
    except TypeError:
        advice = generate_advice(tags, stats, mode=mode)  # legacy path

    score = _safe_score_float(result.get("score") or 0.0)
    impact_score_int = int(round(score))
    impact_explanation = impact_explanation_line(impact_score_int)

    # Title (pass rng if supported; fall back if not)
    try:
        emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []), rng=rng)  # new preferred
    except TypeError:
        emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))  # legacy

    title = title[:1].lower() + title[1:]

    avatar_url = _avatar_url_from_steam32(player.get("steamAccountId"))

    positives_lines = _first3_lines(advice.get("positives"))
    negatives_lines = _first3_lines(advice.get("negatives"))
    flags_lines = _first3_lines(advice.get("flags"))
    tips_lines = _first3_lines(advice.get("tips"))

    notes_parts = [
        _notes_sentence(positives_lines),
        _notes_sentence(negatives_lines),
        _notes_sentence(flags_lines),
        _notes_sentence(tips_lines),
    ]
    notes_text = " ".join([p for p in notes_parts if p])

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": score,
        "impact_score_int": impact_score_int,
        "impact_explanation_line": impact_explanation,
        "notes_text": notes_text,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": player.get("hero", {}).get("displayName") or normalize_hero_name(player.get("hero", {}).get("name", "")),
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": match.get("durationSeconds", 0),
        "isVictory": is_victory,
        # Enforce ≤3 lines and no None using helper (embed builder will also cap)
        "positives": positives_lines,
        "negatives": negatives_lines,
        "flags": flags_lines,
        "tips": tips_lines,
        "matchId": match.get("id"),
        "avatarUrl": avatar_url,
    }


# --- Minimal fallback embed for IMP-missing matches ---
def format_fallback_embed(player: dict, match: dict, player_name: str = "Player", private_data_blocked: bool = False) -> dict:
    game_mode_field = match.get("gameMode")
    raw_label = (match.get("gameModeName") or "").upper()

    game_mode_name = resolve_game_mode_name(game_mode_field, raw_label)
    is_turbo = is_turbo_mode(game_mode_field, raw_label)
    mode = "TURBO" if is_turbo else "NON_TURBO"
    is_victory = player.get("isVictory", False)

    duration = match.get("durationSeconds", 0)
    basic_stats = f"Level {player.get('level', 0)}"
    if not is_turbo:
        basic_stats += f" • {player.get('goldPerMinute', 0)} GPM • {player.get('experiencePerMinute', 0)} XPM"
    # Turbo policy (Stage 3): do not show GPM/XPM in fallback when mode==TURBO

    if private_data_blocked:
        emoji = "🔒"
        title = ""
        status_note = "Public Match Data not exposed — Detailed analysis unavailable."
    else:
        emoji = "⏳"
        title = "(Pending Stats)"
        status_note = "Impact score not yet processed by Stratz — detailed analysis will appear later."

    avatar_url = _avatar_url_from_steam32(player.get("steamAccountId"))

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": None,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": player.get("hero", {}).get("displayName") or normalize_hero_name(player.get("hero", {}).get("name", "")),
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": duration,
        "isVictory": is_victory,
        "basicStats": basic_stats,
        "statusNote": status_note,
        "matchId": match.get("id"),
        "avatarUrl": avatar_url,
    }
