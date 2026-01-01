# bot/formatter_pkg/embed.py

from typing import List, Dict, Any


# Discord sidebar colors (24-bit RGB)
COLOR_WIN = 0x2ECC71   # green
COLOR_LOSS = 0xE74C3C  # red


def _ellipsis_lines(lines: List[str], max_lines: int = 3) -> str:
    """
    Join up to `max_lines` lines with newlines. If more items exist, append an ellipsis.
    Guarantees a non-empty string (returns "-" when no lines).
    """
    lines = [str(x).strip() for x in (lines or []) if str(x or "").strip()]
    if not lines:
        return "-"
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines] + ["…"])


def _impact_emoji(impact_score_int: Any) -> str:
    """
    Canonical IMPACT emoji tiers (locked).
    -41..-31 ⚰️
    -30..-21 💀
    -20..-11 ⚠️
    -10..-1  ❗
    0        ⚪
    +1..+10  🌱
    +11..+20 🌳
    +21..+30 🏅
    +31..+40 🏆
    +41+     👑
    """
    try:
        s = int(impact_score_int)
    except Exception:
        return "⚪"

    if s >= 41:
        return "👑"
    if s >= 31:
        return "🏆"
    if s >= 21:
        return "🏅"
    if s >= 11:
        return "🌳"
    if s >= 1:
        return "🌱"
    if s == 0:
        return "⚪"
    if s >= -10:
        return "❗"
    if s >= -20:
        return "⚠️"
    if s >= -30:
        return "💀"
    return "⚰️"


def build_discord_embed(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the FULL match embed using the agreed contract and field order.
    (See Project Guidance Bible → GUIDELINES:EMBED_CONTRACT)

    NOTE (Phase 5):
      • Avatars render as a THUMBNAIL (embed['thumbnail']).
      • Advice sections are trimmed to ≤3 lines here (and already pre-trimmed by formatter).
    """
    from datetime import datetime, timezone

    hero = result.get("hero", "unknown")
    kda = result.get("kda", "0/0/0")
    victory = "Win" if result.get("isVictory") else "Loss"
    # Title format: {emoji} {PlayerName} {title} {K/D/A} as {Hero} — Win|Loss
    title = f"{result.get('emoji', '')} {result.get('playerName', 'Player')} {result.get('title', '')} {kda} as {hero} — {victory}".strip()

    duration = int(result.get("duration") or 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    impact_score_int = result.get("impact_score_int", None)
    impact_score_int_str = "-" if impact_score_int is None else str(int(impact_score_int))
    impact_explanation_line = str(result.get("impact_explanation_line", "-") or "-")

    notes_text = str(result.get("notes_text", "") or "").strip()
    if not notes_text:
        notes_text = "-"

    impact_emoji = _impact_emoji(impact_score_int)
    impact_label = f"{impact_emoji} Impact {impact_emoji}"

    # ⚠ Field order must match contract exactly.
    fields: List[Dict[str, Any]] = [
        {"name": "Role", "value": str(result.get("role", "unknown")).capitalize(), "inline": True},
        {"name": "Mode", "value": result.get("gameModeName", "Unknown"), "inline": True},
        {"name": "Duration", "value": duration_str, "inline": True},
        {"name": "Notes", "value": notes_text, "inline": False},
    ]

    embed: Dict[str, Any] = {
        "title": title,
        "description": f"{impact_label} — {impact_score_int_str}\n{impact_explanation_line}",
        "fields": fields,
        "footer": {
            "text": f"Match ID: {result.get('matchId', '-')}"
        },
        "timestamp": timestamp,
        "color": COLOR_WIN if result.get("isVictory") else COLOR_LOSS,
    }

    # 🖼️ Optional avatar as THUMBNAIL
    avatar_url = result.get("avatarUrl") or result.get("steamAvatarUrl")
    if avatar_url:
        embed["thumbnail"] = {"url": avatar_url}

    # 🖼️ Optional hero banner as IMAGE (bottom of embed)
    hero_banner_url = result.get("heroBannerUrl")
    if hero_banner_url:
        embed["image"] = {"url": hero_banner_url}

    return embed


def build_fallback_embed(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the PENDING/SAFE fallback embed used when IMP is missing or private data blocks analysis.

    NOTE (Phase 5):
      • Avatars render as a THUMBNAIL.
    """
    from datetime import datetime, timezone

    hero = result.get("hero", "unknown")
    kda = result.get("kda", "0/0/0")
    victory = "Win" if result.get("isVictory") else "Loss"
    title = f"{result.get('emoji', '')} {result.get('playerName', 'Player')} {result.get('title', '')} {kda} as {hero} — {victory}".strip()

    duration = int(result.get("duration") or 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    fields: List[Dict[str, Any]] = [
        {"name": "Mode", "value": result.get("gameModeName", "Unknown"), "inline": True},
        {"name": "Duration", "value": duration_str, "inline": True},
        {"name": "Role", "value": str(result.get("role", "unknown")).capitalize(), "inline": True},
        {"name": "Basic Stats", "value": result.get("basicStats", "-"), "inline": False},
        {"name": "Status", "value": result.get("statusNote", "-"), "inline": False},
    ]

    embed: Dict[str, Any] = {
        "title": title,
        "description": "",
        "fields": fields,
        "footer": {
            "text": f"Match ID: {result.get('matchId', '-')}"
        },
        "timestamp": timestamp,
        "color": COLOR_WIN if result.get("isVictory") else COLOR_LOSS,
    }

    # 🖼️ Optional avatar as THUMBNAIL
    avatar_url = result.get("avatarUrl") or result.get("steamAvatarUrl")
    if avatar_url:
        embed["thumbnail"] = {"url": avatar_url}

    # 🖼️ Optional hero banner as IMAGE (bottom of embed)
    hero_banner_url = result.get("heroBannerUrl")
    if hero_banner_url:
        embed["image"] = {"url": hero_banner_url}

    return embed


def _format_duration_seconds(seconds: int) -> str:
    """Format duration seconds as M:SS or H:MM:SS (deterministic)."""
    try:
        s = int(seconds or 0)
    except Exception:
        s = 0
    if s < 0:
        s = 0
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def _human_game_mode(game_mode: Any) -> str:
    """Convert game mode token to human readable label (best-effort, no lookup tables)."""
    raw = str(game_mode or "").strip()
    if not raw:
        return "Unknown"
    return raw.replace("_", " ").strip().title()


def _steam_to_name_map() -> Dict[str, str]:
    """
    CONFIG["players"] shape:
      keys = names
      values = Steam32 IDs
    Return reverse mapping: steam32(str) -> name(str)
    """
    try:
        from bot.config import CONFIG
    except Exception:
        CONFIG = {}

    try:
        cfg_players = (CONFIG.get("players") or {})
        return {str(v): str(k) for (k, v) in cfg_players.items()}
    except Exception:
        return {}


def _build_party_fallback_embed_from_parts(
    match_id: int,
    party_id: int,
    is_radiant: int,
    members: list[dict],
    game_mode: Any | None = None,
    duration_seconds: int | None = None,
    is_victory: bool | None = None,
) -> dict:
    """Build a party pending embed with parity to individual pending match embeds."""
    from datetime import datetime, timezone

    # Prefer stable ordering: Steam32 ascending (deterministic).
    try:
        members_sorted = sorted(
            (members or []),
            key=lambda p: int(p.get("steamAccountId") or 0),
        )
    except Exception:
        members_sorted = list(members or [])

    steam_to_name = _steam_to_name_map()

    lines: list[str] = []
    for p in (members_sorted or []):
        sid = p.get("steamAccountId")
        sid_str = str(sid) if sid is not None else ""

        name = ""
        try:
            if sid is not None:
                name = steam_to_name.get(str(int(sid))) or ""
        except Exception:
            name = ""

        if not name:
            # Best-effort Steam name fallbacks from match payload variants.
            try:
                for key in ("name", "steamName", "personaName", "personaname", "playerName"):
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
            name = sid_str.strip() or "Unknown"

        # Resolve hero name (best-effort from available fields; no invented hero lists).
        hero = ""
        try:
            hv = p.get("heroName") or p.get("hero") or p.get("heroDisplayName")
            if isinstance(hv, str) and hv.strip():
                hero = hv.strip()
            elif isinstance(hv, dict):
                dn = hv.get("displayName") or hv.get("name")
                if isinstance(dn, str) and dn.strip():
                    hero = dn.strip()
        except Exception:
            pass

        if not hero:
            try:
                hid = p.get("heroId")
                if hid is not None:
                    hero = str(hid)
            except Exception:
                pass

        if not hero:
            hero = "Unknown"

        # K/D/A defaults are 0 when missing.
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

        lines.append(f"{name} — {hero} — {k} / {d} / {a}")

    members_val = "\n".join(lines) if lines else "-"

    mode_label = _human_game_mode(game_mode)
    dur_label = _format_duration_seconds(duration_seconds or 0)

    stack_n = len(members_sorted or [])
    stack_label = f"{stack_n}-stack" if stack_n > 0 else "-"

    wl = ""
    if is_victory is True:
        wl = "Win"
    elif is_victory is False:
        wl = "Loss"

    title = f"⏳ Party (Pending Stats) — {stack_label}"
    if wl:
        title = f"{title} — {wl}"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    embed = {
        "title": title,
        "description": "",
        "fields": [
            {"name": "Mode", "value": mode_label, "inline": True},
            {"name": "Duration", "value": dur_label, "inline": True},
            {"name": "Stack", "value": stack_label, "inline": True},
            {"name": "Members", "value": members_val, "inline": False},
            {
                "name": "Status",
                "value": "Impact score not yet processed by Stratz — detailed analysis will appear later.",
                "inline": False,
            },
        ],
        "footer": {"text": f"Match ID: {match_id}"},
        "timestamp": timestamp,
    }

    if is_victory is True:
        embed["color"] = COLOR_WIN
    elif is_victory is False:
        embed["color"] = COLOR_LOSS

    return embed


def build_party_fallback_embed(
    match_id: int | dict,
    party_id: int | None = None,
    is_radiant: int | None = None,
    members: list[dict] | None = None,
    game_mode: Any | None = None,
    duration_seconds: int | None = None,
    is_victory: bool | None = None,
) -> dict:
    """
    Build a party pending embed.

    Supports two call shapes:
      1) build_party_fallback_embed(match_id, party_id, is_radiant, members, ...)
      2) build_party_fallback_embed(snapshot_dict) where snapshot has:
           matchId, partyId, isRadiant, isVictory, members
    """
    if isinstance(match_id, dict):
        snap = match_id
        try:
            mid = int(snap.get("matchId") or 0)
        except Exception:
            mid = 0
        try:
            pid = int(snap.get("partyId") or 0)
        except Exception:
            pid = 0
        ir = 1 if snap.get("isRadiant") in (1, True, "1", "true", "True") else 0
        mem = snap.get("members") or []
        gm = snap.get("gameMode")
        dur = snap.get("durationSeconds")
        iv = snap.get("isVictory")
        return _build_party_fallback_embed_from_parts(
            mid,
            pid,
            ir,
            mem if isinstance(mem, list) else [],
            game_mode=gm,
            duration_seconds=dur if isinstance(dur, (int, float)) else None,
            is_victory=iv if isinstance(iv, bool) else None,
        )

    return _build_party_fallback_embed_from_parts(
        int(match_id),
        int(party_id or 0),
        int(is_radiant or 0),
        members or [],
        game_mode=game_mode,
        duration_seconds=duration_seconds,
        is_victory=is_victory,
    )


def build_party_full_embed(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the FULL party match embed (no summary yet).

    Contract (result dict):
      - matchId
      - isVictory (bool|None)
      - gameModeName (str)
      - durationSeconds (int)
      - stackSize (int)
      - partyImpactAvgInt (int)
      - partyImpactLine (str)
      - membersVal (str) OR membersLines (list[str])  (Members field content)
      - avatarUrl (optional)
      - heroBannerUrl (optional)
    """
    from datetime import datetime, timezone

    def _victory_label(v: Any) -> str:
        if v is True:
            return "Win"
        if v is False:
            return "Loss"
        return ""

    def _safe_int(x: Any, default: int = 0) -> int:
        try:
            return int(x)
        except Exception:
            try:
                return int(float(x))
            except Exception:
                return default

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    stack_n = _safe_int(result.get("stackSize"), 0)
    stack_label = f"{stack_n}-stack" if stack_n > 0 else "-"

    wl = _victory_label(result.get("isVictory"))
    title = f"PARTY MATCH — {stack_label}"
    if wl:
        title = f"{title} — {wl}"

    impact_score_int = result.get("partyImpactAvgInt", None)
    impact_score_int_str = "-" if impact_score_int is None else str(int(_safe_int(impact_score_int, 0)))
    impact_explanation_line = str(result.get("partyImpactLine", "-") or "-")

    impact_emoji = _impact_emoji(impact_score_int)
    impact_label = f"{impact_emoji} Impact {impact_emoji}"

    mode_label = str(result.get("gameModeName", "Unknown") or "Unknown")
    dur_label = _format_duration_seconds(_safe_int(result.get("durationSeconds"), 0))

    members_val = str(result.get("membersVal", "") or "").strip()
    if not members_val:
        lines = result.get("membersLines")
        if isinstance(lines, list):
            members_val = "\n".join([str(x) for x in lines if str(x or "").strip()]).strip()
    if not members_val:
        members_val = "-"

    fields: List[Dict[str, Any]] = [
        {"name": "Mode", "value": mode_label, "inline": True},
        {"name": "Duration", "value": dur_label, "inline": True},
        {"name": "Stack", "value": stack_label, "inline": True},
        {"name": "Members", "value": members_val, "inline": False},
    ]

    embed: Dict[str, Any] = {
        "title": title,
        "description": f"{impact_label} — {impact_score_int_str}\n{impact_explanation_line}",
        "fields": fields,
        "footer": {"text": f"Match ID: {result.get('matchId', '-')}"},
        "timestamp": timestamp,
    }

    if result.get("isVictory") is True:
        embed["color"] = COLOR_WIN
    elif result.get("isVictory") is False:
        embed["color"] = COLOR_LOSS

    # 🖼️ Optional avatar as THUMBNAIL
    avatar_url = result.get("avatarUrl") or result.get("steamAvatarUrl")
    if avatar_url:
        embed["thumbnail"] = {"url": avatar_url}

    # 🖼️ Optional hero banner as IMAGE (bottom of embed)
    hero_banner_url = result.get("heroBannerUrl")
    if hero_banner_url:
        embed["image"] = {"url": hero_banner_url}

    return embed


def build_duel_fallback_embed(match_id: int | dict, radiant: list[dict] | None = None, dire: list[dict] | None = None) -> dict:
    """Build a simple fallback embed for a detected guild duel (Phase 2a)."""
    from datetime import datetime, timezone

    if isinstance(match_id, dict):
        snap = match_id
        try:
            mid = int(snap.get("matchId") or 0)
        except Exception:
            mid = 0
        radiant = snap.get("radiant") or []
        dire = snap.get("dire") or []
        steam_to_name = snap.get("steamToName")
        if not isinstance(steam_to_name, dict):
            steam_to_name = _steam_to_name_map()
    else:
        mid = int(match_id)
        steam_to_name = _steam_to_name_map()

    def _names(players: list[dict]) -> list[str]:
        out: list[str] = []
        for p in (players or []):
            sid = str(p.get("steamAccountId") or "").strip()
            if not sid:
                continue
            name = ""
            try:
                name = str(steam_to_name.get(sid) or "").strip()
            except Exception:
                name = ""
            if not name:
                name = "Unknown"
            out.append(name)
        return out

    r_names = _names(radiant or [])
    d_names = _names(dire or [])

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    return {
        "title": "⚔️ Guild Duel Detected",
        "description": "",
        "fields": [
            {"name": "Radiant", "value": "\n".join(r_names) if r_names else "-", "inline": True},
            {"name": "Dire", "value": "\n".join(d_names) if d_names else "-", "inline": True},
        ],
        "footer": {"text": f"Match ID: {mid}"},
        "timestamp": timestamp,
    }
