# bot/runner.py

from bot.gist_state import load_state, save_state
from bot.config import CONFIG
from bot.runner_pkg import (
    process_pending_upgrades_and_expiry,
    process_player,
    webhook_cooldown_active,
    webhook_cooldown_remaining,
    is_hard_blocked,
)
import time
import os


def _log_level() -> str:
    v = (os.getenv("GB_LOG_LEVEL") or "").strip().lower()
    return v or "info"


def _debug_enabled() -> bool:
    return _log_level() in ("debug", "trace")


def run_bot():
    print("🚀 GuildBot started")

    players = CONFIG.get("players") or {}
    try:
        players_count = len(players)
    except Exception:
        players_count = 0

    print(f"👥 Loaded {players_count} players from config.json")

    state = {}
    try:
        state = load_state()
        print("📥 Loaded state.json from GitHub Gist")
    except Exception as e:
        print(f"⚠️ Failed to load state.json from GitHub Gist ({type(e).__name__}). Starting with empty state.")

    # Pass 0: try to upgrade or expire existing fallbacks before scanning for new matches
    try:
        ok = process_pending_upgrades_and_expiry(state)
    except Exception as e:
        print(f"❌ Pending pass crashed ({type(e).__name__}). Ending run early (fail-safe).")
        ok = False

    if not ok:
        if is_hard_blocked():
            print("🧯 Ending run early due to Cloudflare hard block.")
        elif webhook_cooldown_active():
            remaining = webhook_cooldown_remaining()
            print(f"🧯 Ending run early — webhook cooling down for {remaining:.1f}s.")
        else:
            print("🧯 Ending run early to preserve API quota.")

        try:
            save_state(state)
            print("📝 Updated state.json on GitHub Gist")
        except Exception as e:
            print(f"⚠️ Failed to save state.json to GitHub Gist ({type(e).__name__}). Run ended without persisting state.")

        print("✅ GuildBot run complete.")
        return

    processed = 0
    early_exit_reason = ""

    for index, (player_name, steam_id) in enumerate(players.items(), start=1):
        if is_hard_blocked():
            early_exit_reason = "cloudflare_hard_block"
            print("🧯 Ending run early due to Cloudflare hard block.")
            break
        if webhook_cooldown_active():
            early_exit_reason = "webhook_cooldown"
            remaining = webhook_cooldown_remaining()
            print(f"🧯 Ending run early — webhook cooling down for {remaining:.1f}s.")
            break

        if _debug_enabled():
            print(f"🔍 [{index}/{players_count}] Checking {player_name} ({steam_id})...")

        last_posted_id = None
        try:
            last_posted_id = state.get(str(steam_id))
        except Exception:
            last_posted_id = None

        try:
            should_continue = process_player(player_name, steam_id, last_posted_id, state)
        except Exception as e:
            print(f"❌ process_player crashed for {player_name} ({steam_id}) ({type(e).__name__}). Ending run early (fail-safe).")
            early_exit_reason = "process_player_crash"
            break

        processed += 1

        if not should_continue:
            if is_hard_blocked():
                early_exit_reason = "cloudflare_hard_block"
                print("🧯 Ending run early due to Cloudflare hard block.")
            elif webhook_cooldown_active():
                early_exit_reason = "webhook_cooldown"
                remaining = webhook_cooldown_remaining()
                print(f"🧯 Ending run early due to webhook cooldown ({remaining:.1f}s).")
            else:
                early_exit_reason = "quota_preserve"
                print("🧯 Ending run early to preserve API quota.")
            break

        time.sleep(0.6)

    try:
        save_state(state)
        print("📝 Updated state.json on GitHub Gist")
    except Exception as e:
        print(f"⚠️ Failed to save state.json to GitHub Gist ({type(e).__name__}). Run ended without persisting state.")

    if not _debug_enabled():
        if early_exit_reason:
            print(f"ℹ️ Run summary: processed {processed}/{players_count} players (early_exit={early_exit_reason}).")
        else:
            print(f"ℹ️ Run summary: processed {processed}/{players_count} players.")

    print("✅ GuildBot run complete.")
