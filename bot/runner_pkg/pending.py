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
# Expiry: env override with FALLBACK_EXPIRY_SEC
_DEFAULT_EXPIRY = 10800   # 3 hours
_MIN_EXPIRY = 300          # 5 minutes
_MAX_EXPIRY = 10800       # 3 hours

# Recheck window: env override with PENDING_RECHECK_SEC
_DEFAULT_RECHECK = 300     # 5 minutes
_MIN_RECHECK = 60          # 60s
_MAX_RECHECK = 3600        # 60 minutes

# Pending re-poll cap per run: env override with PENDING_MAX_CHECKS_PER_RUN
_DEFAULT_MAX_CHECKS_PER_RUN = 8
_MIN_MAX_CHECKS_PER_RUN = 1
_MAX_MAX_CHECKS_PER_RUN = 50


def _env_expiry_seconds() -> int:
    raw = (os.getenv("FALLBACK_EXPIRY_SEC") or "").strip()
    if raw.isdigit():
        try:
            v = int(raw)
            return max(_MIN_EXPIRY, min(_MAX_EXPIRY, v))
        except Exception:
            pass
    return _DEFAULT_EXPIRY


def _env_max_checks_per_run() -> int:
    raw = (os.getenv("PENDING_MAX_CHECKS_PER_RUN") or "").strip()
    if raw.isdigit():
        try:
            v = int(raw)
            return max(_MIN_MAX_CHECKS_PER_RUN, min(_MAX_MAX_CHECKS_PER_RUN, v))
        except Exception:
            pass
    return _DEFAULT_MAX_CHECKS_PER_RUN


def _entry_expiry_seconds(entry: Dict[str, Any]) -> int:
    v = entry.get("expiresAfterSec")
    try:
        if isinstance(v, (int, float)):
            return max(_MIN_EXPIRY, min(_MAX_EXPIRY, int(v)))
    except Exception:
        pass
    return _env_expiry_seconds()


def _posted_at_epoch(entry: Dict[str, Any]) -> float:
    v = entry.get("postedAt")
    try:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str) and v.strip():
            vv = v.strip()
            if vv.replace(".", "", 1).isdigit():
                return float(vv)
            return float(iso_to_epoch(vv))
    except Exception:
        pass
    return 0.0


def _expire_pending_snapshot(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Return an 'expired' fallback embed built from stored snapshot."""
    snap = entry.get("snapshot") or {}
    expired = dict(snap)
    expired["statusNote"] = "Stats window expired — final analysis unavailable."
    return build_fallback_embed(expired)


def _build_party_upgrade_embed(match_id: int, party_id: str, is_radiant: int, members: list[dict]) -> dict:
    """Build a simple 'upgraded' embed for party stacks once IMP is available (Phase 2b)."""
    from datetime import datetime, timezone

    side = "Radiant" if int(is_radiant) == 1 else "Dire"
    lines = []
    for p in sorted((members or []), key=lambda x: str(x.get("steamAccountId") or "")):
        sid = str(p.get("steamAccountId") or "").strip()
        if not sid:
            continue
        nick = (CONFIG.get("players") or {}).get(sid) or sid
        imp = p.get("imp")
        try:
            imp_str = "-" if imp is None else f"{float(imp):.1f}"
        except Exception:
            imp_str = "-"
        lines.append(f"{nick} ({sid}) — IMP {imp_str}")

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    return {
        "title": f"👥 Party Stack — {side} (Upgraded)",
        "description": "",
        "fields": [
            {"name": "Party ID", "value": str(party_id), "inline": True},
            {"name": "Members", "value": "\n".join(lines) if lines else "-", "inline": False},
        ],
        "footer": {"text": f"Match ID: {match_id}"},
        "timestamp": timestamp,
    }


def _build_party_expired_embed(match_id: int, party_id: str, is_radiant: int, snapshot: Dict[str, Any]) -> dict:
    from datetime import datetime, timezone

    side = "Radiant" if int(is_radiant) == 1 else "Dire"
    count = (snapshot or {}).get("memberCount")
    count_str = str(count) if isinstance(count, (int, float)) else "-"
    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    return {
        "title": f"👥 Party Stack — {side} (Expired)",
        "description": "",
        "fields": [
            {"name": "Party ID", "value": str(party_id), "inline": True},
            {"name": "Members", "value": f"{count_str} member(s) (details unavailable)", "inline": False},
            {"name": "⚠️ Status", "value": "Stats window expired — final analysis unavailable.", "inline": False},
        ],
        "footer": {"text": f"Match ID: {match_id}"},
        "timestamp": timestamp,
    }


def _build_duel_upgrade_embed(match_id: int, radiant: list[dict], dire: list[dict]) -> dict:
    """Build a simple 'upgraded' embed for duels once IMP is available (Phase 2b)."""
    from datetime import datetime, timezone

    def _lines(side_players: list[dict]) -> list[str]:
        out = []
        for p in sorted((side_players or []), key=lambda x: str(x.get("steamAccountId") or "")):
            sid = str(p.get("steamAccountId") or "").strip()
            if not sid:
                continue
            nick = (CONFIG.get("players") or {}).get(sid) or sid
            imp = p.get("imp")
            try:
                imp_str = "-" if imp is None else f"{float(imp):.1f}"
            except Exception:
                imp_str = "-"
            out.append(f"{nick} ({sid}) — IMP {imp_str}")
        return out

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    r_lines = _lines(radiant)
    d_lines = _lines(dire)

    return {
        "title": "⚔️ Guild Duel (Upgraded)",
        "description": "",
        "fields": [
            {"name": "Radiant", "value": "\n".join(r_lines) if r_lines else "-", "inline": True},
            {"name": "Dire", "value": "\n".join(d_lines) if d_lines else "-", "inline": True},
        ],
        "footer": {"text": f"Match ID: {match_id}"},
        "timestamp": timestamp,
    }


def _build_duel_expired_embed(match_id: int, snapshot: Dict[str, Any]) -> dict:
    from datetime import datetime, timezone

    rc = (snapshot or {}).get("radiantCount")
    dc = (snapshot or {}).get("direCount")
    rc_s = str(rc) if isinstance(rc, (int, float)) else "-"
    dc_s = str(dc) if isinstance(dc, (int, float)) else "-"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    return {
        "title": "⚔️ Guild Duel (Expired)",
        "description": "",
        "fields": [
            {"name": "Radiant", "value": f"{rc_s} member(s) (details unavailable)", "inline": True},
            {"name": "Dire", "value": f"{dc_s} member(s) (details unavailable)", "inline": True},
            {"name": "⚠️ Status", "value": "Stats window expired — final analysis unavailable.", "inline": False},
        ],
        "footer": {"text": f"Match ID: {match_id}"},
        "timestamp": timestamp,
    }


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
    Deterministic jitter helper (Phase 4).

    Phase 4 originally added ±jitter to spread load across runs.
    Current policy: fixed cadence (no jitter). Return 0.
    """
    _ = stable_key
    return 0


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
    max_checks_per_run = _env_max_checks_per_run()
    checks_used = 0

    for key, entry in sorted(list(pending_map.items()), key=lambda kv: _posted_at_epoch(kv[1])):
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
        posted_at_epoch = _posted_at_epoch(entry)

        if posted_at_epoch > 0 and (now_epoch - posted_at_epoch) >= expires_after:
            try:
                embed = _expire_pending_snapshot(entry)
                ok, code, _ = edit_discord_message(message_id, embed, base_url, exact_base=True, structured=True)
                if ok:
                    print(f"🗑️ Expired fallback for match {match_id} (steam {steam_id})")
                    pending_map.pop(key, None)
                else:
                    if code == "not_found":
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
            if checks_used >= max_checks_per_run:
                continue

            throttle()
            data = fetch_full_match(int(match_id))
            checks_used += 1
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

            ok, code, _ = edit_discord_message(
                message_id,
                embed,
                base_url,
                exact_base=True,
                context={"discord_id": discord_id} if discord_id else None,
                structured=True,
            )
            if ok:
                print(f"🔁 Upgraded fallback → full embed for match {match_id} (steam {steam_id})")
                state[str(steam_id)] = match_id
                pending_map.pop(key, None)
            else:
                if code == "not_found":
                    pending_map.pop(key, None)
                else:
                    if _abort_if_blocked():
                        return False
                    print(f"⚠️ Failed to upgrade (edit) for match {match_id} (steam {steam_id}) — will retry later")

        except Exception as e:
            print(f"❌ Error building/upgrading embed for match {match_id} (steam {steam_id}): {e}")

        time.sleep(0.5)  # be gentle to Discord & Stratz

    # ---- Party pending upgrades/expiry (Phase 2b) ----
    party_pending_map = state.get("partyPending") or {}
    if isinstance(party_pending_map, dict) and party_pending_map:
        for key, entry in sorted(list(party_pending_map.items()), key=lambda kv: _posted_at_epoch(kv[1])):
            if not isinstance(entry, dict):
                continue

            match_id = entry.get("matchId")
            party_id = entry.get("partyId")
            message_id = entry.get("messageId")
            base_url = entry.get("webhookBase") or CONFIG.get("webhook_url")

            # Parse side from key "<matchId>:<partyId>:<isRadiant>"
            is_radiant = None
            try:
                parts = str(key).split(":")
                if len(parts) >= 3 and parts[-1].strip().isdigit():
                    is_radiant = int(parts[-1].strip())
            except Exception:
                is_radiant = None
            if is_radiant is None:
                is_radiant = 1 if (entry.get("isRadiant") in (1, True, "1", "true", "True")) else 0

            if not match_id or not party_id or not message_id or not base_url:
                continue

            # Expiry check
            expires_after = _entry_expiry_seconds(entry) or expiry_sec_env
            posted_at_epoch = _posted_at_epoch(entry)

            if posted_at_epoch > 0 and (now_epoch - posted_at_epoch) >= expires_after:
                try:
                    snap = entry.get("snapshot") or {}
                    embed = _build_party_expired_embed(int(match_id), str(party_id), int(is_radiant), snap)
                    ok, code, _ = edit_discord_message(message_id, embed, base_url, exact_base=True, structured=True)
                    if ok:
                        print(f"🗑️ Expired party pending for match {match_id} (party {party_id}, side {is_radiant})")
                        party_pending_map.pop(key, None)
                    else:
                        if code == "not_found":
                            party_pending_map.pop(key, None)
                        else:
                            if _abort_if_blocked():
                                return False
                            print(f"⚠️ Failed to mark party expired for match {match_id} (party {party_id}) — will retry later")
                except Exception as e:
                    print(f"❌ Error expiring party pending entry for match {match_id} (party {party_id}): {e}")
                time.sleep(0.3)
                continue

            # Recheck spacing logic
            stable_key = f"{match_id}:{party_id}:{is_radiant}"
            if not _should_recheck_now(entry, stable_key, now_epoch):
                continue

            try:
                if checks_used >= max_checks_per_run:
                    continue

                throttle()
                data = fetch_full_match(int(match_id))
                checks_used += 1
                entry["lastCheckedAt"] = now_iso()

                if not data or (isinstance(data, dict) and data.get("error") == "quota_exceeded"):
                    time.sleep(0.2)
                    continue

                match_players = (data.get("players") or []) if isinstance(data, dict) else []
                # Locate party members by partyId + side; ignore solo/partyId missing
                members = []
                for p in match_players:
                    try:
                        if str(p.get("partyId") or "") != str(party_id):
                            continue
                        side = 1 if p.get("isRadiant") else 0
                        if int(side) != int(is_radiant):
                            continue
                        members.append(p)
                    except Exception:
                        continue

                if len(members) < 2:
                    # Party no longer looks valid; leave it pending (safe no-op)
                    continue

                # Upgrade only when all members have IMP
                if any((p.get("imp") is None) for p in members):
                    continue

                embed = _build_party_upgrade_embed(int(match_id), str(party_id), int(is_radiant), members)
                ok, code, _ = edit_discord_message(message_id, embed, base_url, exact_base=True, structured=True)
                if ok:
                    print(f"🔁 Upgraded party pending → upgraded embed for match {match_id} (party {party_id}, side {is_radiant})")
                    party_pending_map.pop(key, None)
                else:
                    if code == "not_found":
                        party_pending_map.pop(key, None)
                    else:
                        if _abort_if_blocked():
                            return False
                        print(f"⚠️ Failed to upgrade party (edit) for match {match_id} (party {party_id}) — will retry later")

            except Exception as e:
                print(f"❌ Error upgrading party pending entry for match {match_id} (party {party_id}): {e}")

            time.sleep(0.5)

        state["partyPending"] = party_pending_map

    # ---- Duel pending upgrades/expiry (Phase 2b) ----
    duel_pending_map = state.get("duelPending") or {}
    if isinstance(duel_pending_map, dict) and duel_pending_map:
        guild_ids = set((CONFIG.get("players") or {}).keys())
        for key, entry in sorted(list(duel_pending_map.items()), key=lambda kv: _posted_at_epoch(kv[1])):
            if not isinstance(entry, dict):
                continue

            match_id = entry.get("matchId") or key
            message_id = entry.get("messageId")
            base_url = entry.get("webhookBase") or CONFIG.get("webhook_url")

            if not match_id or not message_id or not base_url:
                continue

            # Expiry check
            expires_after = _entry_expiry_seconds(entry) or expiry_sec_env
            posted_at_epoch = _posted_at_epoch(entry)

            if posted_at_epoch > 0 and (now_epoch - posted_at_epoch) >= expires_after:
                try:
                    snap = entry.get("snapshot") or {}
                    embed = _build_duel_expired_embed(int(match_id), snap)
                    ok, code, _ = edit_discord_message(message_id, embed, base_url, exact_base=True, structured=True)
                    if ok:
                        print(f"🗑️ Expired duel pending for match {match_id}")
                        duel_pending_map.pop(str(key), None)
                    else:
                        if code == "not_found":
                            duel_pending_map.pop(str(key), None)
                        else:
                            if _abort_if_blocked():
                                return False
                            print(f"⚠️ Failed to mark duel expired for match {match_id} — will retry later")
                except Exception as e:
                    print(f"❌ Error expiring duel pending entry for match {match_id}: {e}")
                time.sleep(0.3)
                continue

            # Recheck spacing logic
            stable_key = f"{match_id}:duel"
            if not _should_recheck_now(entry, stable_key, now_epoch):
                continue

            try:
                if checks_used >= max_checks_per_run:
                    continue

                throttle()
                data = fetch_full_match(int(match_id))
                checks_used += 1
                entry["lastCheckedAt"] = now_iso()

                if not data or (isinstance(data, dict) and data.get("error") == "quota_exceeded"):
                    time.sleep(0.2)
                    continue

                match_players = (data.get("players") or []) if isinstance(data, dict) else []
                radiant = [p for p in match_players if p.get("isRadiant") and str(p.get("steamAccountId")) in guild_ids]
                dire = [p for p in match_players if (not p.get("isRadiant")) and str(p.get("steamAccountId")) in guild_ids]

                if not radiant or not dire:
                    continue

                if any((p.get("imp") is None) for p in radiant + dire):
                    continue

                embed = _build_duel_upgrade_embed(int(match_id), radiant, dire)
                ok, code, _ = edit_discord_message(message_id, embed, base_url, exact_base=True, structured=True)
                if ok:
                    print(f"🔁 Upgraded duel pending → upgraded embed for match {match_id}")
                    duel_pending_map.pop(str(key), None)
                else:
                    if code == "not_found":
                        duel_pending_map.pop(str(key), None)
                    else:
                        if _abort_if_blocked():
                            return False
                        print(f"⚠️ Failed to upgrade duel (edit) for match {match_id} — will retry later")

            except Exception as e:
                print(f"❌ Error upgrading duel pending entry for match {match_id}: {e}")

            time.sleep(0.5)

        state["duelPending"] = duel_pending_map

    state["pending"] = pending_map
    return True
