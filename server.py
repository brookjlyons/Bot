# server.py

from flask import Flask
from threading import Thread, Lock
from bot.runner import run_bot
import traceback
import os
import asyncio
import random
import re
from feedback.catalog.insults import MATCHBOT_INSULTS

app = Flask(__name__)
run_lock = Lock()

_discord_thread_lock = Lock()
_discord_thread_started = False


def safe_run_bot():
    try:
        if run_lock.locked():
            print("🛑 GuildBot is already running; skipping /run trigger.", flush=True)
            return

        with run_lock:
            print("🚀 /run trigger received — starting bot run...", flush=True)
            run_bot()
            print("✅ Bot run complete.", flush=True)

    except Exception:
        print("❌ Bot run crashed:", flush=True)
        traceback.print_exc()


def _run_discord_bot_loop(token: str) -> None:
    """
    Run the Discord gateway bot in its own thread.
    We do NOT tie this to the Flask request lifecycle.
    """
    try:
        import discord  # local import so requirements without discord.py won't crash import-time
    except Exception as e:
        print(f"⚠️ discord.py not available: {e}", flush=True)
        return

    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        try:
            user = getattr(client, "user", None)
            print(f"🤖 Discord bot connected as {user}", flush=True)
        except Exception:
            print("🤖 Discord bot connected.", flush=True)

    @client.event
    async def on_message(message):
        try:
            # Ignore the bot's own messages (avoid reply loops).
            if getattr(message, "author", None) and getattr(client, "user", None):
                if message.author.id == client.user.id:
                    return

            content = getattr(message, "content", "") or ""
            content_l = content.lower()

            has_matchbot = re.search(r"\bmatchbot\b", content_l) is not None
            has_insult = re.search(r"\binsult\b", content_l) is not None
            has_me = re.search(r"\bme\b", content_l) is not None

            # Require BOTH "matchbot" and "insult" anywhere in the message.
            if not (has_matchbot and has_insult):
                return

            # Targeting rule: requires either the word "me" or a real @mention.
            # If both exist, "me" wins.
            target_user = None
            if has_me:
                target_user = getattr(message, "author", None)
            else:
                mentions = getattr(message, "mentions", None) or []
                bot_user = getattr(client, "user", None)
                bot_id = getattr(bot_user, "id", None)
                mentions = [u for u in mentions if u is not None and getattr(u, "id", None) != bot_id]
                if mentions:
                    target_user = mentions[0]

            if target_user is None:
                return

            channel = getattr(message, "channel", None)
            target_id = getattr(target_user, "id", None)
            channel_name = getattr(channel, "name", "unknown")

            print(f"🔥 matchbot insult trigger in #{channel_name} (target_id={target_id})", flush=True)

            try:
                seed = int(getattr(message, "id", 0) or 0)
                rng = random.Random(seed)

                if MATCHBOT_INSULTS:
                    insult = rng.choice(MATCHBOT_INSULTS)
                else:
                    insult = "no insults loaded, but I'm still judging you."

                if target_id is None:
                    await message.reply(insult)
                else:
                    await message.reply(f"<@{target_id}> {insult}")

            except Exception as e:
                print(f"⚠️ matchbot reply failed: {e}", flush=True)

        except Exception as e:
            print(f"⚠️ Discord on_message handler error: {e}", flush=True)

    async def runner():
        try:
            await client.start(token)
        except Exception as e:
            print(f"❌ Discord bot stopped (start failed): {e}", flush=True)

    try:
        asyncio.run(runner())
    except Exception as e:
        print(f"❌ Discord bot thread crashed: {e}", flush=True)


def start_discord_bot_if_configured() -> None:
    """
    Starts a background Discord gateway bot if DISCORD_TOKEN is present.
    Safe to call multiple times; only starts once.
    """
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        print("ℹ️ DISCORD_TOKEN not set; Discord gateway bot not started.", flush=True)
        return

    global _discord_thread_started
    with _discord_thread_lock:
        if _discord_thread_started:
            return
        _discord_thread_started = True

    print("🔌 Starting Discord bot (gateway)...", flush=True)
    t = Thread(target=_run_discord_bot_loop, args=(token,), daemon=True)
    t.start()


@app.route("/")
def index():
    return "✅ GuildBot Flask server is running. Try /run to trigger a full match check. Use /health for keepalive."


@app.route("/health")
def health():
    return "ok", 200


@app.route("/run")
def run():
    try:
        t = Thread(target=safe_run_bot, daemon=True)
        t.start()
        return "✅ GuildBot run triggered. Check logs for progress."
    except Exception as e:
        print(f"❌ Error starting GuildBot thread: {e}", flush=True)
        return f"❌ Error: {str(e)}"


# Start the Discord gateway bot as soon as the service boots (if configured).
start_discord_bot_if_configured()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
