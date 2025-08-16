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


def run_bot():
    print("🚀 GuildBot started")

    players = CONFIG["players"]
    print(f"👥 Loaded {len(players)} players from config.json")

    state = load_state()
    print("📥 Loaded state.json from GitHub Gist")

    # Pass 0: try to upgrade or expire existing fallbacks before scanning for new matches
    ok = process_pending_upgrades_and_expiry(state)
    if not ok:
        if is_hard_blocked():
            print("🧯 Ending run early due to Cloudflare hard block.")
        elif webhook_cooldown_active():
            remaining = webhook_cooldown_remaining()
            print(f"🧯 Ending run early — webhook cooling down for {remaining:.1f}s.")
        else:
            print("🧯 Ending run early to preserve API quota.")
        save_state(state)
        print("📝 Updated state.json on GitHub Gist")
        print("✅ GuildBot run complete.")
        return

    for index, (player_name, steam_id) in enumerate(players.items(), start=1):
        if is_hard_blocked():
            print("🧯 Ending run early due to Cloudflare hard block.")
            break
        if webhook_cooldown_active():
            remaining = webhook_cooldown_remaining()
            print(f"🧯 Ending run early — webhook cooling down for {remaining:.1f}s.")
            break

        print(f"🔍 [{index}/{len(players)}] Checking {player_name} ({steam_id})...")
        last_posted_id = state.get(str(steam_id))
        should_continue = process_player(player_name, steam_id, last_posted_id, state)
        if not should_continue:
            if is_hard_blocked():
                print("🧯 Ending run early due to Cloudflare hard block.")
            elif webhook_cooldown_active():
                remaining = webhook_cooldown_remaining()
                print(f"🧯 Ending run early due to webhook cooldown ({remaining:.1f}s).")
            else:
                print("🧯 Ending run early to preserve API quota.")
            break
        time.sleep(0.6)

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
