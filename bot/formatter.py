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
from bot.formatter_pkg.embed import build_discord_embed, build_fallback_embed, build_party_fallback_embed, build_duel_fallback_embed, build_party_full_embed

__all__ = [
    # constants
    "NORMAL_STATS", "TURBO_STATS",
    # main formatters
    "format_match_embed", "format_fallback_embed", "format_party_full_embed",
    # embed builders
    "build_discord_embed", "build_fallback_embed", "build_party_fallback_embed", "build_duel_fallback_embed", "build_party_full_embed",
    # utilities (deprecated kept public)
    "normalize_hero_name", "get_role", "get_baseline",
]


_AVATAR_BASE_URL = "https://raw.githubusercontent.com/brookjlyons/Bot/refs/heads/main/data/avatars/"
_AVATAR_DEFAULT_URL = f"{_AVATAR_BASE_URL}default.jpg"

_HERO_BANNER_BASE_URL = "https://raw.githubusercontent.com/brookjlyons/Bot/refs/heads/main/data/hero_banners/"


_OBFUSCATE_STEAM32 = 48165461

_ZERO_WIDTH_CHARS = (
    "\u200B",  # ZERO WIDTH SPACE
    "\u200C",  # ZERO WIDTH NON-JOINER
    "\u200D",  # ZERO WIDTH JOINER
    "\u2060",  # WORD JOINER
)

_HOMOGLYPH_MAP = {
    "i": ("i", "\u0456"),  # Latin i, Cyrillic і
    "K": ("K", "\u039A"),  # Latin K, Greek Κ
    "g": ("g", "\u0261"),  # g, Latin script g
}


def _maybe_obfuscate_player_name(player_name: str, steam32: Any, rng: random.Random) -> str:
    """
    Lightweight, deterministic nickname obfuscation (Unicode) for a single player.
    Purpose: break naive copy/paste name matching while rendering identically in Discord.
    """
    try:
        sid = int(steam32)
    except Exception:
        sid = 0

    if sid != _OBFUSCATE_STEAM32:
        return str(player_name or "Player")

    name = str(player_name or "Player")

    chars: list[str] = []
    for ch in name:
        # Optional homoglyph substitution (stable under rng)
        try:
            alts = _HOMOGLYPH_MAP.get(ch)
            if alts:
                ch = rng.choice(alts)
        except Exception:
            pass

        chars.append(ch)

        # Optional zero-width insertion after characters
        try:
            if rng.random() < 0.4:
                chars.append(rng.choice(_ZERO_WIDTH_CHARS))
        except Exception:
            pass

    # Optional leading/trailing invisibles (extra salt)
    try:
        if rng.random() < 0.3:
            chars.insert(0, rng.choice(_ZERO_WIDTH_CHARS))
    except Exception:
        pass
    try:
        if rng.random() < 0.3:
            chars.append(rng.choice(_ZERO_WIDTH_CHARS))
    except Exception:
        pass

    return "".join(chars)


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


def _hero_banner_filename(hero_name: Any) -> str:
    """
    Convert a hero name into the banner filename convention used in data/hero_banners:
      - Title Case words joined by underscores
      - spaces/hyphens/underscores normalized
      - apostrophes removed
    Examples:
      "Abaddon" -> "Abaddon"
      "Anti-Mage" -> "Anti_Mage"
      "Nature's Prophet" -> "Natures_Prophet"
      "npc_dota_hero_keeper_of_the_light" -> "Keeper_Of_The_Light"
    """
    raw = str(hero_name or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith("npc_dota_hero_"):
        raw = raw[len("npc_dota_hero_"):]
    raw = raw.replace("-", " ").replace("_", " ")
    raw = raw.replace("’", "").replace("'", "")
    parts = [p for p in raw.split() if p.strip()]
    if not parts:
        return ""
    return "_".join([p[:1].upper() + p[1:].lower() if p else "" for p in parts])


def _hero_banner_url(hero_name: Any) -> str:
    """
    Deterministically derive a public hero banner URL.
    Always returns a non-empty URL string (never None).
    """
    fname = _hero_banner_filename(hero_name)
    if not fname:
        return ""
    return f"{_HERO_BANNER_BASE_URL}{fname}.jpg"


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

    player_name = _maybe_obfuscate_player_name(player_name, player.get("steamAccountId"), rng)

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

    hero_display = player.get("hero", {}).get("displayName")
    hero_fallback = normalize_hero_name(player.get("hero", {}).get("name", ""))
    hero_name = hero_display or hero_fallback
    hero_banner_url = _hero_banner_url(hero_display or player.get("hero", {}).get("name", "") or hero_name)

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
        "hero": hero_name,
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
        "heroBannerUrl": hero_banner_url,
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

    hero_display = player.get("hero", {}).get("displayName")
    hero_fallback = normalize_hero_name(player.get("hero", {}).get("name", ""))
    hero_name = hero_display or hero_fallback
    hero_banner_url = _hero_banner_url(hero_display or player.get("hero", {}).get("name", "") or hero_name)

    seed_str = f"{match.get('id')}:{player.get('steamAccountId')}"
    seed_hex = hashlib.md5(seed_str.encode()).hexdigest()
    rng = random.Random(int(seed_hex, 16))
    player_name = _maybe_obfuscate_player_name(player_name, player.get("steamAccountId"), rng)

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": None,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": hero_name,
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": duration,
        "isVictory": is_victory,
        "basicStats": basic_stats,
        "statusNote": status_note,
        "matchId": match.get("id"),
        "avatarUrl": avatar_url,
        "heroBannerUrl": hero_banner_url,
    }


def format_party_full_embed(
    match: dict,
    members: list[dict],
    *,
    is_victory: bool | None = None,
) -> dict:
    """
    Build the formatter result dict for a FULL party match embed.
    Assumes IMP is present for ALL members.
    No summary generation in this phase.
    """

    def _safe_float(x: Any) -> float:
        try:
            f = float(x)
        except Exception:
            return 0.0
        if f != f:
            return 0.0
        return f

    def _safe_int(x: Any, default: int = 0) -> int:
        try:
            return int(x)
        except Exception:
            try:
                return int(float(x))
            except Exception:
                return default

    def _hero_name_from_player(p: dict) -> str:
        try:
            hv = p.get("heroName") or p.get("heroDisplayName") or p.get("hero")
            if isinstance(hv, str) and hv.strip():
                return hv.strip()
            if isinstance(hv, dict):
                dn = hv.get("displayName") or hv.get("name")
                if isinstance(dn, str) and dn.strip():
                    return dn.strip()
        except Exception:
            pass
        try:
            hero_obj = p.get("hero") or {}
            if isinstance(hero_obj, dict):
                dn = hero_obj.get("displayName") or ""
                if isinstance(dn, str) and dn.strip():
                    return dn.strip()
                nm = hero_obj.get("name") or ""
                if isinstance(nm, str) and nm.strip():
                    return normalize_hero_name(nm)
        except Exception:
            pass
        return ""

    def _member_key(p: dict):
        imp = _safe_float(p.get("imp"))
        sid = _safe_int(p.get("steamAccountId"), 0)
        return (-imp, sid)

    members_sorted = sorted(list(members or []), key=_member_key)

    member_lines: list[str] = []
    impact_vals: list[int] = []

    for p in members_sorted:
        imp_int = int(round(_safe_float(p.get("imp"))))
        impact_vals.append(imp_int)

        name = ""
        try:
            for key in ("playerName", "name", "steamName", "personaName", "personaname"):
                v = p.get(key)
                if isinstance(v, str) and v.strip():
                    name = v.strip()
                    break
        except Exception:
            pass
        if not name:
            try:
                steam_acct = p.get("steamAccount") or {}
                v = steam_acct.get("name")
                if isinstance(v, str) and v.strip():
                    name = v.strip()
            except Exception:
                pass
        if not name:
            name = str(p.get("steamAccountId") or "Unknown")

        try:
            k = int(p.get("kills") or 0)
        except Exception:
            k = 0
        try:
            d = int(p.get("deaths") or 0)
        except Exception:
            d = 0
        try:
            a = int(p.get("assists") or 0)
        except Exception:
            a = 0

        line1 = f"{name} — {k}/{d}/{a} — IMP {imp_int:+d}"
        line2 = f"↳ {impact_explanation_line(imp_int)}"
        member_lines.append(f"{line1}\n{line2}")

    avg_imp = int(round(sum(impact_vals) / len(impact_vals))) if impact_vals else 0

    top = members_sorted[0] if members_sorted else {}
    avatar_url = _avatar_url_from_steam32(top.get("steamAccountId"))

    top_hero = _hero_name_from_player(top)
    hero_banner_url = _hero_banner_url(top_hero)

    game_mode_field = match.get("gameMode")
    raw_label = (match.get("gameModeName") or "").upper()
    game_mode_name = resolve_game_mode_name(game_mode_field, raw_label)

    return {
        "matchId": match.get("id"),
        "isVictory": is_victory,
        "gameModeName": game_mode_name,
        "durationSeconds": match.get("durationSeconds", 0),
        "stackSize": len(members_sorted),
        "partyImpactAvgInt": avg_imp,
        "partyImpactLine": impact_explanation_line(avg_imp),
        "membersLines": member_lines,
        "avatarUrl": avatar_url,
        "heroBannerUrl": hero_banner_url,
    }
