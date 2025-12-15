# bot/formatter_pkg/embed.py

from typing import List, Dict, Any


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


def build_discord_embed(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the FULL match embed using the agreed contract and field order.
    (See Project Guidance Bible → GUIDELINES:EMBED_CONTRACT)

    NOTE (Phase 5):
      • Avatars render both as a LARGE image (embed['image']) and as the author icon.
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

    score = result.get("score", None)
    impact_val = "-" if score is None else f"{score:.1f}"

    positives = _ellipsis_lines(result.get("positives", []) or [])
    negatives = _ellipsis_lines(result.get("negatives", []) or [])
    flags = _ellipsis_lines(result.get("flags", []) or [])
    tips = _ellipsis_lines(result.get("tips", []) or [])

    # ⚠ Field order must match contract exactly.
    fields: List[Dict[str, Any]] = [
        {"name": "🧮 Impact", "value": impact_val, "inline": True},
        {"name": "🧭 Role", "value": str(result.get("role", "unknown")).capitalize(), "inline": True},
        {"name": "⚙️ Mode", "value": result.get("gameModeName", "Unknown"), "inline": True},
        {"name": "⏱️ Duration", "value": duration_str, "inline": True},
        {"name": "🎯 What went well", "value": positives, "inline": False},
        {"name": "🧱 What to work on", "value": negatives, "inline": False},
        {"name": "📌 Flagged behavior", "value": flags, "inline": False},
        {"name": "🗺️ Tips", "value": tips, "inline": False},
    ]

    embed: Dict[str, Any] = {
        "title": title,
        "description": "",
        "fields": fields,
        "footer": {
            "text": f"Match ID: {result.get('matchId', '-')}"
        },
        "timestamp": timestamp,
        # author.name is part of our contract; icon_url added below if avatar present
        "author": {"name": str(result.get("playerName", "Player"))},
    }

    # 🖼️ Optional Steam avatar as LARGE image + author icon
    avatar_url = result.get("avatarUrl") or result.get("steamAvatarUrl")
    if avatar_url:
        embed["image"] = {"url": avatar_url}
        embed["author"]["icon_url"] = avatar_url

    return embed


def build_fallback_embed(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the PENDING/SAFE fallback embed used when IMP is missing or private data blocks analysis.

    NOTE (Phase 5):
      • Avatars render both as a LARGE image and as the author icon.
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
        {"name": "⚙️ Mode", "value": result.get("gameModeName", "Unknown"), "inline": True},
        {"name": "⏱️ Duration", "value": duration_str, "inline": True},
        {"name": "🧭 Role", "value": str(result.get("role", "unknown")).capitalize(), "inline": True},
        {"name": "📊 Basic Stats", "value": result.get("basicStats", "-"), "inline": False},
        {"name": "⚠️ Status", "value": result.get("statusNote", "-"), "inline": False},
    ]

    embed: Dict[str, Any] = {
        "title": title,
        "description": "",
        "fields": fields,
        "footer": {
            "text": f"Match ID: {result.get('matchId', '-')}"
        },
        "timestamp": timestamp,
        "author": {"name": str(result.get("playerName", "Player"))},
    }

    # 🖼️ Optional Steam avatar as LARGE image + author icon
    avatar_url = result.get("avatarUrl") or result.get("steamAvatarUrl")
    if avatar_url:
        embed["image"] = {"url": avatar_url}
        embed["author"]["icon_url"] = avatar_url

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


def build_party_fallback_embed(
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

    # Resolve member display names:
    # Prefer guild nickname via CONFIG['players'][steam32], else fall back to Steam name fields, else steam32 id.
    try:
        from bot.config import CONFIG
    except Exception:
        CONFIG = {}

    lines: list[str] = []
    for p in (members_sorted or []):
        sid = p.get("steamAccountId")
        sid_str = str(sid) if sid is not None else ""

        name = ""
        try:
            nickname = (CONFIG.get("players") or {}).get(str(int(sid))) if sid is not None else None
            if isinstance(nickname, str) and nickname.strip():
                name = nickname.strip()
        except Exception:
            pass

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
            name = sid_str.strip() or "-"

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

    return {
        "title": title,
        "description": "",
        "fields": [
            {"name": "⚙️ Mode", "value": mode_label, "inline": True},
            {"name": "⏱️ Duration", "value": dur_label, "inline": True},
            {"name": "👥 Stack", "value": stack_label, "inline": True},
            {"name": "🧑‍🤝‍🧑 Members", "value": members_val, "inline": False},
            {
                "name": "⚠️ Status",
                "value": "Impact score not yet processed by Stratz — detailed analysis will appear later.",
                "inline": False,
            },
        ],
        "footer": {"text": f"Match ID: {match_id}"},
        "timestamp": timestamp,
    }


def build_duel_fallback_embed(match_id: int, radiant: list[dict], dire: list[dict]) -> dict:
    """Build a simple fallback embed for a detected guild duel (Phase 2a)."""
    from datetime import datetime, timezone

    r_ids = [str(p.get("steamAccountId") or "") for p in (radiant or []) if str(p.get("steamAccountId") or "").strip()]
    d_ids = [str(p.get("steamAccountId") or "") for p in (dire or []) if str(p.get("steamAccountId") or "").strip()]

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    return {
        "title": "⚔️ Guild Duel Detected",
        "description": "",
        "fields": [
            {"name": "Radiant", "value": "\n".join(r_ids) if r_ids else "-", "inline": True},
            {"name": "Dire", "value": "\n".join(d_ids) if d_ids else "-", "inline": True},
        ],
        "footer": {"text": f"Match ID: {match_id}"},
        "timestamp": timestamp,
    }
