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

# Public surface re-exported from formatter_pkg
from bot.formatter_pkg.stats_sets import NORMAL_STATS, TURBO_STATS
from bot.formatter_pkg.mode import resolve_game_mode_name, is_turbo_mode
from bot.formatter_pkg.util import normalize_hero_name, get_role, get_baseline
from bot.formatter_pkg.embed import build_discord_embed, build_fallback_embed

__all__ = [
    # constants
    "NORMAL_STATS", "TURBO_STATS",
    # main formatters
    "format_match_embed", "format_fallback_embed",
    # embed builders
    "build_discord_embed", "build_fallback_embed",
    # utilities (deprecated kept public)
    "normalize_hero_name", "get_role", "get_baseline",
]

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

    score = float(result.get("score") or 0.0)

    # Title (pass rng if supported; fall back if not)
    try:
        emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []), rng=rng)  # new preferred
    except TypeError:
        emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))  # legacy

    title = title[:1].lower() + title[1:]

    # 🔗 Steam avatar (optional)
    avatar_url = None
    try:
        # Only attempt lookup when an API key is present
        if os.getenv("STEAM_API_KEY"):
            try:
                from bot.steam_user import get_avatar_url  # local helper
            except Exception:
                # Support flat module name if placed at project root (dev convenience)
                from steam_user import get_avatar_url  # type: ignore
            steam32 = player.get("steamAccountId")
            if isinstance(steam32, int):
                avatar_url = get_avatar_url(steam32) or None
    except Exception as _e:
        # Non-fatal; just skip avatar on any error
        avatar_url = None

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": score,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": player.get("hero", {}).get("displayName") or normalize_hero_name(player.get("hero", {}).get("name", "")),
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": match.get("durationSeconds", 0),
        "isVictory": is_victory,
        "positives": advice.get("positives", [])[:3],
        "negatives": advice.get("negatives", [])[:3],
        "flags": advice.get("flags", [])[:3],
        "tips": advice.get("tips", [])[:3],
        "matchId": match.get("id"),
        "avatarUrl": avatar_url,  # ← optional
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

    # 🔗 Steam avatar (optional) for fallback too (non-breaking)
    avatar_url = None
    try:
        if os.getenv("STEAM_API_KEY"):
            try:
                from bot.steam_user import get_avatar_url
            except Exception:
                from steam_user import get_avatar_url  # type: ignore
            steam32 = player.get("steamAccountId")
            if isinstance(steam32, int):
                avatar_url = get_avatar_url(steam32) or None
    except Exception:
        avatar_url = None

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
        "avatarUrl": avatar_url,  # ← optional
    }
