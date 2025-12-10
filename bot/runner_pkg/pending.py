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
from bot.fetch import fetch_full_match
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
# Expiry: env override with FALLBACK_EXPIRY_SEC
_DEFAULT_EXPIRY = 900      # 15 minutes
_MIN_EXPIRY = 300          # 5 minutes
_MAX_EXPIRY = 3600         # 60 minutes

# Recheck window: env override with PENDING_RECHECK_SEC
_DEFAULT_RECHECK = 60      # 1 minute
_MIN_RECHECK = 20          # 20s
_MAX_RECHECK = 600         # 10 minutes


def _env_expiry_seconds() -> int:
    raw = (os.getenv("FALLBACK_EXPIRY_SEC") or "").strip()
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
    - Ensure keys are composite "<matchId>:<steamId>" where possible.
    - Drop clearly invalid / corrupt entries.
    """
    to_delete = []
    to_add: Dict[str, Any] = {}

    for key, val in list(pending_map.items()):
        if not isinstance(val, dict):
            to_delete.append(key)
            continue

        match_id = val.get("matchId") or key
        steam_id = val.get("steamId")
        if not match_id or steam_id is None:
            to_delete.append(key)
            continue

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
    Convert stable_key into a deterministic ±jitter in [0, recheckWindow).
    """
    h = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
    return int(h[:4], 16) % max(_DEFAULT_RECHECK, 1)


def _should_recheck_now(entry: Dict[str, Any], stable_key: str, now_epoch: float) -> bool:
    """
    Decide whether this entry should be re-polled now based on lastCheckedAt
    and a deterministic jitter window.
    """
    last_checked_iso = entry.get("lastCheckedAt")
    window = _recheck_window(entry)
    jitter = _stable_jitter_seconds(stable_key)

    if not last_checked_iso:
        return True  # first time

    try:
        last_checked_epoch = iso_to_epoch(last_checked_iso)
    except Exception:
        return True

    return (now_epoch - last_checked_epoch) >= max(5.0, window + jitter)


def _abort_if_blocked() -> bool:
    if is_hard_blocked():
        print("🛑 Pending pass aborted — Cloudflare hard block detected.")
        return True
    if webhook_cooldown_active():
        rem = webhook_cooldown_remaining()
        print(f"⏱️ Pending pass aborted — webhook cooldown {rem:.2f}s.")
        return True
    return False


def process_pending_upgrades_and_expiry(state: Dict[str, Any]) -> bool:
    """
    Pass 0: walk state["pending"], upgrading to full embeds when IMP is ready,
    or expiring them when the fallback window closes.

    Returns False if the run should be aborted early (hard block / cooldown).
    """
    pending_map = state.get("pending") or {}
    if not isinstance(pending_map, dict):
        state["pending"] = {}
        return True

    _normalize_pending_map(pending_map)

    now_epoch = time.time()
    expiry_sec_env = _env_expiry_seconds()

    for key, entry in list(pending_map.items()):
        if not isinstance(entry, dict):
            continue

        match_id = entry.get("matchId")
        steam_id = entry.get("steamId")
        message_id = entry.get("messageId")
        base_url = entry.get("webhookBase") or CONFIG.get("webhook_url")

        if not match_id or not steam_id or not message_id or not base_url:
            continue

        # Expiry check
        expires_after = _entry_expiry_seconds(entry) or expiry_sec_env
        try:
            posted_at_epoch = float(entry.get("postedAt") or 0.0)
        except Exception:
            posted_at_epoch = 0.0

        if posted_at_epoch > 0 and (now_epoch - posted_at_epoch) >= expires_after:
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
                print(f"❌ Error expiring pending entry for match {match_id} (steam {steam_id}): {e}")
            time.sleep(0.3)
            continue

        # Recheck spacing logic
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

            # Resolve Discord ID for this player name (matches config mapping used in players runner)
            try:
                discord_ids = CONFIG.get("discord_ids") or {}
                discord_id = discord_ids.get(player_name, "")
            except Exception:
                discord_id = ""

            ok = edit_discord_message(
                message_id,
                embed,
                base_url,
                exact_base=True,
                context={"discord_id": discord_id} if discord_id else None,
            )
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
