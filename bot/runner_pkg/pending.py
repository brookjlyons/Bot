# bot/runner_pkg/pending.py
"""
Pending pass (Pass 0): upgrade or expire fallback posts.

Phase 4 adds efficient re-polling:
- Re-check spacing with deterministic ±jitter per entry.
- Track lastCheckedAt (ISO) and optional recheckWindowSec (bounded).
"""

import time
import os
import hashlib
from typing import Dict, Any

from bot.config import CONFIG
from bot.throttle import throttle
from bot.stratz import fetch_full_match
from bot.formatter import (
    format_match_embed,
    build_discord_embed,
    build_fallback_embed,
)
from .webhook_client import (
    edit_discord_message,
    webhook_cooldown_active,
    webhook_cooldown_remaining,
    is_hard_blocked,
)

from bot.runner_pkg.timeutil import now_iso, iso_to_epoch


# ---------- Bounds & defaults ----------
# Expiry: env override with sane bounds (30m–48h), default 12h.
_MIN_EXPIRY = 30 * 60
_MAX_EXPIRY = 48 * 60 * 60
_DEFAULT_EXPIRY = 12 * 60 * 60

# Re-poll spacing: default 45s with ±15s jitter (bounded overall 20–120s).
_MIN_RECHECK = 20
_MAX_RECHECK = 120
_DEFAULT_RECHECK = 45
_JITTER_RANGE = 15  # seconds


# ---------- Small helpers ----------
def _abort_if_blocked() -> bool:
    """Return True if we should end the run early (prints reason)."""
    if is_hard_blocked():
        print("🧯 Ending run early due to Cloudflare hard block.")
        return True
    if webhook_cooldown_active():
        print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
        return True
    return False


def _env_expiry_seconds() -> int:
    raw = (os.getenv("PENDING_EXPIRY_SEC") or "").strip()
    if raw.isdigit():
        try:
            v = int(raw)
            return max(_MIN_EXPIRY, min(_MAX_EXPIRY, v))
        except Exception:
            pass
    return _DEFAULT_EXPIRY


def _entry_expiry_seconds(entry: Dict[str, Any]) -> int:
    v = entry.get("expiresAfterSec")
    try:
        if isinstance(v, (int, float)):
            return max(_MIN_EXPIRY, min(_MAX_EXPIRY, int(v)))
    except Exception:
        pass
    return _env_expiry_seconds()


def _expire_pending_snapshot(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Return an 'expired' fallback embed built from stored snapshot."""
    snap = entry.get("snapshot") or {}
    expired = dict(snap)
    expired["statusNote"] = "Stats window expired — final analysis unavailable."
    return build_fallback_embed(expired)


def _normalize_pending_map(pending_map: Dict[str, Any]) -> None:
    """
    In-place cleanup & migration:
      - Drop non-dict values.
      - Ensure postedAt exists (ISO).
      - Clamp recheckWindowSec if present.
      - Migrate legacy keys to '<matchId>:<steamId>' when possible.
    """
    if not isinstance(pending_map, dict):
        return

    to_delete, to_add = [], {}

    for key, val in list(pending_map.items()):
        if not isinstance(val, dict):
            to_delete.append(key)
            continue

        # postedAt (ISO) required; accept transitional 'postedAtIso'.
        if "postedAt" not in val:
            posted = val.get("postedAtIso")
            val["postedAt"] = str(posted) if posted else now_iso()

        # Optional Phase 4 fields:
        rws = val.get("recheckWindowSec")
        try:
            if isinstance(rws, (int, float)):
                val["recheckWindowSec"] = max(_MIN_RECHECK, min(_MAX_RECHECK, int(rws)))
        except Exception:
            if "recheckWindowSec" in val:
                del val["recheckWindowSec"]

        # Legacy key migration: "<matchId>" → "<matchId>:<steamId>"
        if ":" not in str(key) and str(key).isdigit():
            try:
                steam = int((val or {}).get("steamId"))
            except Exception:
                steam = None
            if steam is not None:
                new_key = f"{int(key)}:{steam}"
                if new_key not in pending_map and new_key not in to_add:
                    to_add[new_key] = val
                    to_delete.append(key)

    for k in to_delete:
        pending_map.pop(k, None)
    pending_map.update(to_add)


def _recheck_window(entry: Dict[str, Any]) -> int:
    v = entry.get("recheckWindowSec")
    try:
        if isinstance(v, (int, float)):
            return max(_MIN_RECHECK, min(_MAX_RECHECK, int(v)))
    except Exception:
        pass
    return _DEFAULT_RECHECK


def _stable_jitter_seconds(stable_key: str) -> int:
    """
    Deterministic jitter based on a stable key (matchId:steamId).
    We hash to [−_JITTER_RANGE, +_JITTER_RANGE] and clamp final spacing.
    """
    h = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
    # Use first 8 hex chars for jitter
    try:
        base = int(h[:8], 16)
    except Exception:
        base = 0
    span = 2 * _JITTER_RANGE + 1
    # Map to [-_JITTER_RANGE, +_JITTER_RANGE]
    offset = (base % span) - _JITTER_RANGE
    return int(offset)


def _should_recheck_now(entry: Dict[str, Any], stable_key: str, now_epoch: float) -> bool:
    """
    Re-poll only if (now - lastCheckedAt) >= window + jitter.
    Missing/invalid lastCheckedAt -> allow immediate check.
    """
    last_iso = entry.get("lastCheckedAt")
    if not last_iso:
        return True
    last_epoch = iso_to_epoch(last_iso)
    if last_epoch <= 0:
        return True
    next_allowed = last_epoch + max(0, _recheck_window(entry) + _stable_jitter_seconds(stable_key))
    return now_epoch >= next_allowed


# ---------- Main ----------
def process_pending_upgrades_and_expiry(state: Dict[str, Any]) -> bool:
    """
    Pass 0: upgrade or expire pending fallback posts.
    Returns False to end the run early (hard block or webhook cooldown).
    """
    if _abort_if_blocked():
        return False

    pending_map = state.get("pending") or {}
    if not isinstance(pending_map, dict):
        state["pending"] = {}
        return True

    _normalize_pending_map(pending_map)

    keys = list(pending_map.keys())
    now_epoch = time.time()

    for key in keys:
        entry = pending_map.get(key)
        if not isinstance(entry, dict):
            pending_map.pop(key, None)
            continue

        if _abort_if_blocked():
            return False

        # Identity & validation
        steam_id = entry.get("steamId")
        match_id = entry.get("matchId")
        message_id = entry.get("messageId")
        base_url = entry.get("webhookBase") or CONFIG.get("webhook_url")
        if not (steam_id and match_id and message_id and base_url):
            pending_map.pop(key, None)
            continue

        # Expiry (always evaluated; not gated by spacing)
        posted_epoch = iso_to_epoch(entry.get("postedAt"))
        if max(0.0, now_epoch - max(0.0, posted_epoch)) >= _entry_expiry_seconds(entry):
            try:
                embed = _expire_pending_snapshot(entry)
                ok = edit_discord_message(message_id, embed, base_url, exact_base=True)
                if ok:
                    print(f"🗑️ Expired fallback for match {match_id} (steam {steam_id})")
                    pending_map.pop(key, None)
                else:
                    if _abort_if_blocked():
                        return False
                    print(f"⚠️ Failed to mark expired for match {match_id} (steam {steam_id}) — will retry later")
            except Exception as e:
                print(f"❌ Error expiring fallback for match {match_id} (steam {steam_id}): {e}")
            time.sleep(0.5)
            continue

        # Spacing / recheck control
        stable_key = f"{match_id}:{steam_id}"
        if not _should_recheck_now(entry, stable_key, now_epoch):
            continue

        # Attempt upgrade
        try:
            throttle()
            data = fetch_full_match(int(match_id))
            entry["lastCheckedAt"] = now_iso()  # record attempt regardless of outcome

            if not data or (isinstance(data, dict) and data.get("error") == "quota_exceeded"):
                time.sleep(0.2)
                continue

            players = (data.get("players") or []) if isinstance(data, dict) else []
            try:
                sid_int = int(steam_id)
            except Exception:
                sid_int = steam_id
            player = next((p for p in players if p.get("steamAccountId") == sid_int), None)
            if not player or player.get("imp") is None:
                continue

            # Preserve the original displayed player name from the pending snapshot when upgrading.
            # This keeps guild nicknames / custom labels stable between fallback and full embeds.
            snapshot = entry.get("snapshot") or {}
            player_name = snapshot.get("playerName") or player.get("name", "") or "Player"

            embed_result = format_match_embed(player, data, player.get("stats", {}) or {}, player_name)
            embed = build_discord_embed(embed_result)

            ok = edit_discord_message(message_id, embed, base_url, exact_base=True)
            if ok:
                print(f"🔁 Upgraded fallback → full embed for match {match_id} (steam {steam_id})")
                state[str(steam_id)] = match_id
                pending_map.pop(key, None)
            else:
                if _abort_if_blocked():
                    return False
                print(f"⚠️ Failed to upgrade (edit) for match {match_id} (steam {steam_id}) — will retry later")

        except Exception as e:
            print(f"❌ Error building/upgrading embed for match {match_id} (steam {steam_id}): {e}")

        time.sleep(0.5)  # be gentle to Discord & Stratz

    state["pending"] = pending_map
    return True
