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

    NOTE (change requested):
      • Avatars are now rendered as a LARGE image block (embed['image']) rather than a thumbnail.
        This mirrors the standalone Steam avatar webhook behavior and makes the avatar prominent.
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
        "timestamp": timestamp
    }

    # 🖼️ Optional Steam avatar as LARGE image (requested change)
    avatar_url = result.get("avatarUrl") or result.get("steamAvatarUrl")
    if avatar_url:
        embed["image"] = {"url": avatar_url}

    return embed


def build_fallback_embed(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the PENDING/SAFE fallback embed used when IMP is missing or private data blocks analysis.

    NOTE (change requested):
      • Avatars are now rendered as a LARGE image block (embed['image']) rather than a thumbnail.
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
        "timestamp": timestamp
    }

    # 🖼️ Optional Steam avatar as LARGE image (requested change)
    avatar_url = result.get("avatarUrl") or result.get("steamAvatarUrl")
    if avatar_url:
        embed["image"] = {"url": avatar_url}

    return embed
