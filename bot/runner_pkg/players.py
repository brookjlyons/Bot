# bot/runner_pkg/players.py

import json
import time
import os
from bot.fetch import get_latest_new_match
from bot.formatter import (
    format_match_embed,
    build_discord_embed,
    format_fallback_embed,
    build_fallback_embed,
)
from bot.config import CONFIG
from bot.throttle import throttle
from .webhook_client import (
    post_to_discord_embed,
    edit_discord_message,
    webhook_cooldown_active,
    webhook_cooldown_remaining,
    is_hard_blocked,
    strip_query,
    resolve_webhook_for_post,
)
from bot.runner_pkg.pending import process_pending_upgrades_and_expiry
from bot.runner_pkg.timeutil import now_iso


def _private_ids() -> set[int]:
    """
    Steam IDs with private match data. These players cannot be processed beyond fallback.
    Accept both env and config overrides; env wins.
    """
    out: set[int] = set()

    raw_env = (os.getenv("PRIVATE_DATA_STEAM_IDS") or "").strip()
    if raw_env:
        for part in raw_env.replace(",", " ").split():
            try:
                out.add(int(part.strip()))
            except Exception:
                pass

    try:
        cfg = CONFIG.get("private_data_steam_ids") or []
        for sid in cfg:
            try:
                out.add(int(sid))
            except Exception:
                pass
    except Exception:
        pass

    return out


def _force_fallback_for(steam_id: int) -> bool:
    """
    TEST hook: force fallback embed even if IMP is ready.
    Controlled by env FORCE_FALLBACK_STEAM_IDS: comma/space-separated list.
    """
    raw = (os.getenv("FORCE_FALLBACK_STEAM_IDS") or "").strip()
    if not raw:
        return False
    for part in raw.replace(",", " ").split():
        try:
            if int(part.strip()) == int(steam_id):
                return True
        except Exception:
            continue
    return False


def _coerce_int(v) -> int | None:
    try:
        return int(v)
    except Exception:
        return None


def process_player(player_name: str, steam_id: int, last_posted_id: int | None, state: dict) -> bool:
    """
    Process one player:
    - Determine if new match exists
    - If IMP ready: post full embed (or edit pending message)
    - If IMP not ready: post fallback + add to pending

    NOTE: runner supplies last_posted_id; we fall back to state for compatibility.
    """
    # runner passes last_posted_id for efficiency/compat; fall back to state if missing
    if last_posted_id is None:
        last_posted_id = _coerce_int(state.get(str(steam_id)))

    # 🔔 Resolve Discord ID from config (if available)
    try:
        discord_id = (CONFIG.get("discord_ids") or {}).get(player_name, "")
    except Exception:
        discord_id = ""

    # Pass 0: pending upgrades/expiry before doing any new work
    if not process_pending_upgrades_and_expiry(state):
        return False

    if is_hard_blocked():
        return False
    if webhook_cooldown_active():
        return False

    throttle()

    match_bundle = get_latest_new_match(steam_id, last_posted_id)
    if not match_bundle:
        print(f"⏩ No new match or failed to fetch for {player_name}. Skipping.")
        return True

    match_id = match_bundle["match_id"]
    match_data = match_bundle["full_data"]

    player_data = next((p for p in match_data["players"] if p.get("steamAccountId") == steam_id), None)
    if not player_data:
        print(f"❌ Player data missing in match {match_id} for {player_name}")
        return True

    # If there is a pending entry for this specific (match, player), prefer editing that message when full stats are ready
    pending_map = state.setdefault("pending", {})
    composite_key = f"{match_id}:{steam_id}"
    pending_entry = pending_map.get(composite_key)

    # 🔄 Backward-compat: migrate legacy single-key (matchId-only) entries to composite keys when they match this player
    if not pending_entry:
        legacy = pending_map.get(str(match_id))
        if legacy and legacy.get("steamId") == steam_id:
            pending_entry = legacy
            pending_map[composite_key] = legacy
            pending_map.pop(str(match_id), None)

    # --- Private-data path (no pending/upgrade tracking, custom status, no '(Pending Stats)') ---
    if steam_id in _private_ids():
        print(f"🔒 Private-data player detected for {player_name} ({steam_id}) — posting one-off fallback.")
        try:
            # Build standard fallback then mutate title/status per private-data rules
            result = format_fallback_embed(player_data, match_data, player_name)

            # Remove "(Pending Stats)" and set final status message
            result["title"] = ""  # no pending wording
            result["statusNote"] = "Public Match Data not exposed — Detailed analysis unavailable."

            embed = build_fallback_embed(result)

            resolved = resolve_webhook_for_post(CONFIG.get("webhook_url"))
            if CONFIG.get("webhook_enabled") and resolved:
                # No mention here: private-data fallback should not ping the player
                posted, _ = post_to_discord_embed(
                    embed,
                    resolved,
                    want_message_id=False,
                )
                if posted:
                    print(f"✅ Posted private-data fallback for {player_name} match {match_id}")
                    state[str(steam_id)] = match_id
                else:
                    if is_hard_blocked():
                        return False
                    if webhook_cooldown_active():
                        print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
                        return False
                    print(f"⚠️ Failed to post private-data fallback for {player_name} match {match_id}")
            else:
                print("⚠️ Webhook disabled or misconfigured — printing instead.")
                print(json.dumps(embed, indent=2))
                state[str(steam_id)] = match_id

        except Exception as e:
            print(f"❌ Error formatting or posting private-data fallback for {player_name}: {e}")
        return True

    # --- Test hook: force fallback even if IMP is ready ---
    imp_value = player_data.get("imp")
    try:
        if _force_fallback_for(steam_id) and imp_value is not None:
            imp_value = None
            print(f"🧪 TEST_FORCE_FALLBACK active — forcing fallback for match {match_id} (player {steam_id}).")
    except Exception:
        pass

    if imp_value is None:
        print(f"⏳ IMP not ready for match {match_id} (player {steam_id}). Posting minimal fallback embed.")
        try:
            result = format_fallback_embed(player_data, match_data, player_name)
            embed = build_fallback_embed(result)

            # Resolve actual posting URL and store it with the pending entry
            resolved = resolve_webhook_for_post(CONFIG.get("webhook_url"))
            if CONFIG.get("webhook_enabled") and resolved:
                # No mention here: pending fallback should not ping the player
                posted, msg_id = post_to_discord_embed(
                    embed,
                    resolved,
                    want_message_id=True,
                )
                if posted:
                    print(f"✅ Posted fallback embed for {player_name} match {match_id}")
                    pending_map[composite_key] = {
                        "steamId": steam_id,
                        "matchId": match_id,              # store explicitly for upgrade/expiry
                        "messageId": msg_id,
                        "postedAt": time.time(),          # legacy float
                        "postedAtIso": now_iso(),         # ISO
                        "recheckWindowSec": 300,          # 5 minutes
                        "webhookBase": strip_query(resolved),
                        "snapshot": result,
                    }
                    state[str(steam_id)] = match_id
                else:
                    if is_hard_blocked():
                        return False
                    if webhook_cooldown_active():
                        print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
                        return False
                    print(f"⚠️ Failed to post fallback embed for {player_name} match {match_id}")
            else:
                print("⚠️ Webhook disabled or misconfigured — printing instead.")
                print(json.dumps(embed, indent=2))
                state[str(steam_id)] = match_id
        except Exception as e:
            print(f"❌ Error formatting or posting fallback embed for {player_name}: {e}")
        return True

    print(f"🎮 {player_name} — processing match {match_id}")

    try:
        result = format_match_embed(player_data, match_data, player_data.get("stats", {}), player_name)
        embed = build_discord_embed(result)

        if pending_entry and pending_entry.get("messageId") and CONFIG.get("webhook_enabled"):
            ok = edit_discord_message(
                pending_entry["messageId"],
                embed,
                pending_entry.get("webhookBase") or CONFIG.get("webhook_url"),
                exact_base=True,  # honor stored base; do NOT override
                context={"discord_id": discord_id} if discord_id else None,
            )
            if ok:
                print(f"🔁 Upgraded fallback → full embed for {player_name} match {match_id}")
                state[str(steam_id)] = match_id
                # Remove both composite and any lingering legacy key for safety
                pending_map.pop(composite_key, None)
                pending_map.pop(str(match_id), None)
            else:
                if is_hard_blocked():
                    return False
                if webhook_cooldown_active():
                    print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
                    return False
                print(f"⚠️ Failed to upgrade fallback for {player_name} match {match_id} — will retry later")
        else:
            # Normal fresh post path
            resolved = resolve_webhook_for_post(CONFIG.get("webhook_url"))
            if CONFIG.get("webhook_enabled") and resolved:
                # ✅ Mentions only on full posts (IMP ready, no pending upgrade)
                posted, _ = post_to_discord_embed(
                    embed,
                    resolved,
                    want_message_id=False,
                    context={"discord_id": discord_id},
                )
                if posted:
                    print(f"✅ Posted embed for {player_name} match {match_id}")
                    state[str(steam_id)] = match_id
                else:
                    if is_hard_blocked():
                        return False
                    if webhook_cooldown_active():
                        print(f"🧯 Ending run early — webhook cooling down for {webhook_cooldown_remaining():.1f}s.")
                        return False
                    print(f"⚠️ Failed to post embed for {player_name} match {match_id}")
            else:
                print("⚠️ Webhook disabled or misconfigured — printing instead.")
                print(json.dumps(embed, indent=2))
                state[str(steam_id)] = match_id

    except Exception as e:
        print(f"❌ Error formatting or posting match for {player_name}: {e}")

    # ── Party & Duel (fallback-only) — do not affect main per-player pipeline ──
    try:
        party_posted = state.setdefault("partyPosted", {})
        duel_posted = state.setdefault("duelPosted", {})

        # Backward-compat: migrate legacy set/list shapes to dicts (JSON-safe) in-memory.
        try:
            if isinstance(party_posted, set):
                party_posted = {str(k): True for k in party_posted}
            elif isinstance(party_posted, list):
                party_posted = {str(k): True for k in party_posted}
            elif not isinstance(party_posted, dict):
                party_posted = {}
        except Exception:
            party_posted = {}

        try:
            if isinstance(duel_posted, set):
                duel_posted = {str(k): True for k in duel_posted}
            elif isinstance(duel_posted, list):
                duel_posted = {str(k): True for k in duel_posted}
            elif not isinstance(duel_posted, dict):
                duel_posted = {}
        except Exception:
            duel_posted = {}

        state["partyPosted"] = party_posted
        state["duelPosted"] = duel_posted

        guild_ids = set((CONFIG.get("players") or {}).keys())

        # Gather guild players in this match
        guild_players = [p for p in match_data.get("players", []) if str(p.get("steamAccountId")) in guild_ids]
        if guild_players:
            # Group by (partyId, side)
            parties: dict[tuple[str, int], list[dict]] = {}
            for p in guild_players:
                try:
                    pid = p.get("partyId")
                except Exception:
                    pid = None
                if pid is None:
                    continue
                side = 1 if p.get("isRadiant") else 0
                parties.setdefault((str(pid), side), []).append(p)

            from bot.formatter_pkg.embed import build_party_fallback_embed, build_duel_fallback_embed

            for (pid, side), members in parties.items():
                if len(members) < 2:
                    continue
                party_key = f"{match_id}:{pid}:{side}"
                if party_key in party_posted:
                    continue

                # Derive Win/Loss for the party side (best-effort) from any member payload.
                try:
                    party_is_victory = bool((members or [])[0].get("isVictory")) if members else None
                except Exception:
                    party_is_victory = None

                # Basic "guild-only" member list
                member_rows = []
                for m in members:
                    sid = str(m.get("steamAccountId") or "").strip()
                    if not sid:
                        continue
                    nick = (CONFIG.get("players") or {}).get(sid) or sid
                    hero = m.get("hero", {}) or {}
                    hero_name = hero.get("displayName") or hero.get("name") or "?"
                    k = (m.get("kills") or 0)
                    d = (m.get("deaths") or 0)
                    a = (m.get("assists") or 0)
                    member_rows.append({"steamId": sid, "nickname": nick, "hero": hero_name, "k": k, "d": d, "a": a})

                snapshot = {
                    "matchId": match_id,
                    "partyId": pid,
                    "isRadiant": side == 1,
                    "isVictory": party_is_victory,
                    "members": member_rows,
                    "memberCount": len(member_rows),
                }

                embed = build_party_fallback_embed(snapshot)

                resolved = resolve_webhook_for_post(CONFIG.get("webhook_url"))
                if CONFIG.get("webhook_enabled") and resolved:
                    posted, msg_id = post_to_discord_embed(
                        embed,
                        resolved,
                        want_message_id=True,
                    )
                    if posted:
                        base = strip_query(resolved)
                        party_pending = state.setdefault("partyPending", {})
                        party_pending[party_key] = {
                            "matchId": match_id,
                            "partyId": pid,
                            "isRadiant": 1 if side == 1 else 0,
                            "messageId": str(msg_id),
                            "webhookBase": base,
                            "postedAt": now_iso(),
                            "snapshot": {"memberCount": len(member_rows)},
                        }
                        party_posted[party_key] = True
                        print(f"👥 Party fallback posted & tracked: {party_key}")

            # Duel detection: must have at least 1 guild on each side
            radiant = [p for p in guild_players if p.get("isRadiant")]
            dire = [p for p in guild_players if not p.get("isRadiant")]
            if radiant and dire:
                duel_key = str(match_id)
                if duel_key not in duel_posted:
                    snapshot = {
                        "matchId": match_id,
                        "radiant": [{"steamId": str(p.get("steamAccountId") or "")} for p in radiant],
                        "dire": [{"steamId": str(p.get("steamAccountId") or "")} for p in dire],
                    }
                    embed = build_duel_fallback_embed(snapshot)

                    resolved = resolve_webhook_for_post(CONFIG.get("webhook_url"))
                    if CONFIG.get("webhook_enabled") and resolved:
                        posted, msg_id = post_to_discord_embed(
                            embed,
                            resolved,
                            want_message_id=True,
                        )
                        if posted:
                            base = strip_query(resolved)
                            duel_pending = state.setdefault("duelPending", {})
                            duel_pending[duel_key] = {
                                "matchId": match_id,
                                "radiantIds": [str(p.get("steamAccountId")) for p in radiant],
                                "direIds": [str(p.get("steamAccountId")) for p in dire],
                                "messageId": str(msg_id),
                                "webhookBase": base,
                                "postedAt": now_iso(),
                                "snapshot": {"radiantCount": len(radiant), "direCount": len(dire)},
                            }
                            duel_posted[duel_key] = True
                            print(f"⚔️ Duel fallback posted & tracked: {duel_key}")
    except Exception as e:
        print(f"⚠️ Party/Duel detection skipped due to error: {e}")

    return True
