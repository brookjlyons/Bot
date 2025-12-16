# server.py

from flask import Flask
from flask import jsonify
from threading import Thread, Lock
from bot.runner import run_bot
import traceback
import os
import time

from bot.runner_pkg.discord_gateway import start_discord_gateway_if_configured
import bot.runner_pkg.discord_gateway as discord_gateway


app = Flask(__name__)
run_lock = Lock()

run_started_at = None
last_run_finished_at = None


def safe_run_bot():
    global run_started_at, last_run_finished_at
    try:
        run_bot()
    except Exception:
        print("❌ Bot run crashed:", flush=True)
        traceback.print_exc()
    finally:
        last_run_finished_at = time.time()
        run_started_at = None
        try:
            run_lock.release()
        except Exception:
            pass


@app.route("/")
def index():
    return (
        "✅ GuildBot Flask server is running. "
        "Try /run to trigger a full match check. "
        "Use /health for keepalive."
    )


@app.route("/health")
def health():
    now = time.time()
    running = run_started_at is not None
    run_age = int(now - run_started_at) if running else 0

    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    discord_configured = bool(token)

    discord_started = bool(getattr(discord_gateway, "_discord_thread_started", False))
    t = getattr(discord_gateway, "_discord_thread", None)
    discord_thread_alive = bool(t is not None and getattr(t, "is_alive", None) and t.is_alive())

    payload = {
        "ok": True,
        "run_in_progress": running,
        "run_age_seconds": run_age,
        "discord_configured": discord_configured,
        "discord_started": discord_started,
        "discord_thread_alive": discord_thread_alive,
    }
    return jsonify(payload), 200


@app.route("/run")
def run():
    global run_started_at
    try:
        acquired = run_lock.acquire(blocking=False)
        if not acquired:
            return "🛑 GuildBot is already running; skipped.", 200

        run_started_at = time.time()

        t = Thread(target=safe_run_bot, daemon=True)
        t.start()
        return "✅ GuildBot run triggered. Check logs for progress.", 200
    except Exception as e:
        try:
            run_started_at = None
            run_lock.release()
        except Exception:
            pass
        print(f"❌ Error starting GuildBot thread: {e}", flush=True)
        return f"❌ Error: {str(e)}", 500


# Process boot hook: start Discord gateway once per process (idempotent).
start_discord_gateway_if_configured()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
