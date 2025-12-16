# bot/runner_pkg/discord_gateway.py

from __future__ import annotations

from threading import Thread, Lock
import asyncio
import os

from feedback.discord_insults import build_matchbot_insult_reply


_discord_thread_lock = Lock()
_discord_thread_started = False
_discord_thread: Thread | None = None


def _run_discord_bot_loop(token: str) -> None:
    """
    Run the Discord gateway bot in its own thread.
    Must never crash the process.
    """
    try:
        import discord  # local import so environments without discord.py won't crash import-time
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

            author = getattr(message, "author", None)
            author_id = getattr(author, "id", None)

            mentions = getattr(message, "mentions", None) or []
            mention_ids = []
            for u in mentions:
                if u is None:
                    continue
                uid = getattr(u, "id", None)
                if uid is None:
                    continue
                mention_ids.append(uid)

            bot_user = getattr(client, "user", None)
            bot_id = getattr(bot_user, "id", None)

            message_id = getattr(message, "id", 0) or 0

            reply_text = build_matchbot_insult_reply(
                message_content=content,
                message_id=int(message_id),
                author_id=author_id,
                mention_ids=mention_ids,
                bot_id=bot_id,
            )

            if not reply_text:
                return

            channel = getattr(message, "channel", None)
            channel_name = getattr(channel, "name", "unknown")

            print(
                f"🔥 matchbot insult trigger in #{channel_name} (message_id={message_id})",
                flush=True,
            )

            try:
                await message.reply(reply_text)
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


def start_discord_gateway_if_configured() -> None:
    """
    Starts a background Discord gateway bot if DISCORD_BOT_TOKEN is present.
    Safe to call multiple times; only starts once per process.
    Never raises.
    """
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        print(
            "ℹ️ DISCORD_BOT_TOKEN not set; Discord gateway bot not started.",
            flush=True,
        )
        return

    global _discord_thread_started, _discord_thread
    with _discord_thread_lock:
        if _discord_thread_started:
            return
        _discord_thread_started = True

    print("🔌 Starting Discord bot (gateway)...", flush=True)
    t = Thread(target=_run_discord_bot_loop, args=(token,), daemon=True)
    _discord_thread = t
    t.start()

