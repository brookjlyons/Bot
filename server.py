# server.py

from flask import Flask
from threading import Thread, Lock
from bot.runner import run_bot
import traceback
import os
import asyncio
import random
from feedback.catalog.insults import MATCHBOT_INSULTS

app = Flask(__name__)
run_lock = Lock()

_discord_thread_lock = Lock()
_discord_thread_started = False


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


def _run_discord_bot_loop(token: str):
    # Runs in a background thread with its own event loop.
    try:
        import discord  # type: ignore
    except Exception as e:
        print(f"⚠️ Discord bot disabled — failed to import discord.py: {e}", flush=True)
        return

    intents = discord.Intents.default()
    # Required for reading message text (literal '@matchbot' trigger in a later session).
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
            if "matchbot" not in content.lower():
                return

            author = getattr(message, "author", None)
            channel = getattr(message, "channel", None)
            author_id = getattr(author, "id", None)
            channel_name = getattr(channel, "name", "unknown")

            print(f"🔥 matchbot trigger in #{channel_name} (author_id={author_id})", flush=True)

            try:
                seed = int(getattr(message, "id", 0) or 0)
                rng = random.Random(seed)

                if MATCHBOT_INSULTS:
                    insult = rng.choice(MATCHBOT_INSULTS)
                else:
                    insult = "no insults loaded, but I'm still judging you."

                if author_id is None:
                    await message.reply(insult)
                else:
                    await message.reply(f"<@{author_id}> {insult}")

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


def start_discord_bot_if_configured():
    global _discord_thread_started
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        print("ℹ️ Discord bot not started — DISCORD_BOT_TOKEN not set.", flush=True)
        return

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
