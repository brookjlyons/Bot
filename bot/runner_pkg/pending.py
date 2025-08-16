# bot/runner_pkg/pending.py

import time
import os
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

# NEW: single source of truth for timestamp handling (Stage 1)
from bot.runner_pkg.timeutil import now_iso, iso_to_epoch


# --- Defaults & bounds ---
# Historical default was 24h; we now honor an env override with a default of 12h.
# Bounds protect against misconfiguration (30m–48h).
_MIN_EXPIRY = 30 * 60
_MAX_EXPIRY = 48 * 60 * 60
_DEFAULT_EXPIRY = 12 * 60 * 60


def _env_expiry_seconds() -> int:
    """Resolve expiry seconds from env with sane bounds, falling back to 12h."""
    raw = (os.getenv("PENDING_EXPIRY_SEC") or "").strip()
    if raw.isdigit():
        try:
            v = int(raw)
            return max(_MIN_EXPIRY, min(_MAX_EXPIRY, v))
        except Exception:
            pass
    return _DEFAULT_EXPIRY


def _entry_expiry_seconds(entry: Dict[str, Any]) -> int:
    """
    Determine the expiry for a specific pending entry:
      1) entry['expiresAfterSec'] if present (bounded)
      2) env PENDING_EXPIRY_SEC (bounded)
      3) legacy default (bounded)
    """
    v = entry.get("expiresAfterSec")
    try:
        if isinstance(v, (int, float)):
            return max(_MIN_EXPIRY, min(_MAX_EXPIRY, int(v)))
    except Exception:
        pass
    return _env_expiry_seconds()


def _expire_pending_snapshot(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an 'expired' version of the fallback embed from stored snapshot.

    Behavior: preserves the original fallback minimal structure but changes
    the status note to indicate expiry, leaving score=None and other fields intact.
    """
    snap = entry.get("snapshot") or {}
    expired = dict(snap)
    try:
        # Mutate snapshot-safe fields; tolerate absence gracefully.
        expired["statusNote"] = "Stats window expired — final analysis unavailable."
    except Exception:
        pass
    return build_fallback_embed(expired)


def _normalize_pending_map(pending_map: Dict[str, Any]) -> None:
    """
    In-place cleanup/migration:

    - Drop non-dict values.
    - Migrate legacy keys (matchId only) → composite "<matchId>:<steamId>" when both are present.
    - Ensure postedAt is present as ISO string; accept legacy floats during migration.
    """
    if not isinstance(pending_map, dict):
        return

    to_delete = []
    to_add: Dict[str, Dict[str, Any]] = {}

    # Pass 1: drop junk and prepare rekeys
    for key, val in list(pending_map.items()):
        if not isinstance(val, dict):
            to_delete.append(key)
            continue

        steam_id = val.get("steamId")
        match_id = val.get("matchId")

        # Ensure postedAt (ISO). Accept existing ISO or legacy epoch numbers.
        if "postedAt" not in val:
            # Prefer any transitional field that may exist
            if "postedAtIso" in val and val["postedAtIso"]:
                val["postedAt"] = str(val["postedAtIso"])
            else:
                val["postedAt"] = now_iso()

        # Migrate legacy key if needed and we have the components
        if ":" not in str(key) and steam_id is not None and match_id is not None:
            try:
                composite = f"{int(match_id)}:{int(steam_id)}"
                # Don't overwrite an existing proper key
                if composite != key and composite not in pending_map and composite not in to_add:
                    to_add[composite] = val
                    to_delete.append(key)
            except Exception:
                # If conversion fails, keep legacy key to avoid data loss
                pass

    # Apply deletions and additions
    for k in to_delete:
        pending_map.pop(k, None)
    for k, v in to_add.items():
        pending_map[k] = v


def process_pending_upgrades_and_expiry(state: Dict[str, Any]) -> bool:
    """
    Pass 0: try to upgrade or expire any pending fallback messages.

    Returns:
        False → signal the run should end early (e.g., Cloudflare hard block or webhook cooldown).
        True  → continue with player processing.
    """
    # Early global aborts
    if is_hard_blocked():
        print("🧯 Ending run early due to Cloudflare hard block.")
        return False
    if webhook_cooldown_active():
        print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
        return False

    pending_map = (state.get("pending") or {})
    if not isinstance(pending_map, dict):
        # Ensure correct shape for subsequent runs
        state["pending"] = {}
        return True

    # One-time normalization/migration
    _normalize_pending_map(pending_map)

    # Work on a snapshot of keys to be robust against in-loop mutations
    keys = list(pending_map.keys())
    now_epoch = time.time()

    for key in keys:
        entry = pending_map.get(key)
        if not isinstance(entry, dict):
            # Clean up unexpected shapes
            pending_map.pop(key, None)
            continue

        # Global early aborts (checked frequently to avoid useless work)
        if is_hard_blocked():
            print("🧯 Ending run early due to Cloudflare hard block.")
            return False
        if webhook_cooldown_active():
            print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
            return False

        # Resolve identity
        steam_id = entry.get("steamId")
        match_id = entry.get("matchId")
        message_id = entry.get("messageId")
        base_url = entry.get("webhookBase") or CONFIG.get("webhook_url")

        # Basic validation
        if not (steam_id and match_id and message_id and base_url):
            # If critical data is missing, drop this entry to prevent permanent dangling state.
            pending_map.pop(key, None)
            continue

        # Expiry logic (ISO/epoch tolerant)
        posted_epoch = iso_to_epoch(entry.get("postedAt"))
        expiry_sec = _entry_expiry_seconds(entry)
        elapsed = max(0.0, now_epoch - max(0.0, posted_epoch))

        if elapsed >= expiry_sec:
            # Expire in place
            try:
                embed = _expire_pending_snapshot(entry)
                ok = edit_discord_message(message_id, embed, base_url, exact_base=True)
                if ok:
                    print(f"🗑️ Expired fallback for match {match_id} (steam {steam_id}) after {int(elapsed)}s")
                    pending_map.pop(key, None)
                else:
                    # Respect global abort signals if they flipped during edit attempt
                    if is_hard_blocked():
                        print("🧯 Ending run early due to Cloudflare hard block.")
                        return False
                    if webhook_cooldown_active():
                        print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
                        return False
                    print(f"⚠️ Failed to mark expired for match {match_id} (steam {steam_id}) — will retry later")
            except Exception as e:
                print(f"❌ Error expiring fallback for match {match_id} (steam {steam_id}): {e}")
            # Be gentle between webhook edits
            time.sleep(0.5)
            continue

        # Try to upgrade to full embed if stats are ready
        try:
            throttle()  # pace Stratz
            data = fetch_full_match(int(match_id))
            if not data or isinstance(data, dict) and data.get("error") == "quota_exceeded":
                # Nothing to do now; try later
                time.sleep(0.2)
                continue

            # Locate player slice
            players = (data.get("players") or []) if isinstance(data, dict) else []
            player = None
            try:
                sid_int = int(steam_id)
            except Exception:
                sid_int = steam_id
            for p in players:
                if p.get("steamAccountId") == sid_int:
                    player = p
                    break

            if not player:
                # Can't upgrade without the player slice; try next time
                continue

            # If IMP is still missing, keep waiting
            if player.get("imp") is None:
                continue

            # Build full embed
            embed_result = format_match_embed(player, data, player.get("stats", {}) or {}, player.get("name", "") or "")
            embed = build_discord_embed(embed_result)

            ok = edit_discord_message(message_id, embed, base_url, exact_base=True)
            if ok:
                print(f"🔁 Upgraded fallback → full embed for match {match_id} (steam {steam_id})")
                # Record last posted match for the player and clear pending
                state[str(steam_id)] = match_id
                pending_map.pop(key, None)
            else:
                if is_hard_blocked():
                    print("🧯 Ending run early due to Cloudflare hard block.")
                    return False
                if webhook_cooldown_active():
                    print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
                    return False
                print(f"⚠️ Failed to upgrade (edit) for match {match_id} (steam {steam_id}) — will retry later")

        except Exception as e:
            print(f"❌ Error building/upgrading embed for match {match_id} (steam {steam_id}): {e}")

        # Pace between items to be gentle on Discord + Stratz
        time.sleep(0.5)

    # Ensure normalized map is written back
    state["pending"] = pending_map
    return True
