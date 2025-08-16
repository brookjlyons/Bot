# server.py

from flask import Flask
from threading import Thread, Lock
from bot.runner import run_bot
import traceback
import os

app = Flask(__name__)
run_lock = Lock()


def safe_run_bot():
    if run_lock.locked():
        print("🛑 GuildBot is already running. Skipping.", flush=True)
        return
    with run_lock:
        try:
            print("🔐 Running GuildBot.", flush=True)
            run_bot()
            print("✅ GuildBot complete.", flush=True)
        except Exception:
            print("❌ Unhandled exception in GuildBot thread:", flush=True)
            traceback.print_exc()


@app.route("/")
def index():
    return "✅ GuildBot Flask server is running. Try /run to trigger a full match check."


@app.route("/run")
def run():
    try:
        t = Thread(target=safe_run_bot, daemon=True)
        t.start()
        return "✅ GuildBot run triggered. Check logs for progress."
    except Exception as e:
        print(f"❌ Error starting GuildBot thread: {e}", flush=True)
        return f"❌ Error: {str(e)}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
