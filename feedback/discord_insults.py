# feedback/discord_insults.py

from __future__ import annotations

from typing import List, Optional
import random
import re

from feedback.catalog.insults import MATCHBOT_INSULTS


def build_matchbot_insult_reply(
    *,
    message_content: str,
    message_id: int,
    author_id: Optional[int],
    mention_ids: List[int],
    bot_id: Optional[int],
) -> str:
    """
    Pure logic: parse a Discord message and (optionally) return a reply string.

    Rules preserved from previous server.py:
    - Require BOTH "matchbot" and "insult" as whole words anywhere in the message.
    - Targeting requires either the word "me" OR a real @mention (excluding the bot).
      If both exist, "me" wins.
    - Deterministic insult selection seeded by message_id via local random.Random(seed).
    - Return "" when no reply should be sent.
    """
    content = (message_content or "")
    content_l = content.lower()

    has_matchbot = re.search(r"\bmatchbot\b", content_l) is not None
    has_insult = re.search(r"\binsult\b", content_l) is not None
    has_me = re.search(r"\bme\b", content_l) is not None

    # Require BOTH "matchbot" and "insult" anywhere in the message.
    if not (has_matchbot and has_insult):
        return ""

    # Targeting rule: requires either the word "me" or a real @mention.
    # If both exist, "me" wins.
    target_id: Optional[int] = None
    if has_me:
        if author_id is None:
            return ""
        target_id = author_id
    else:
        mentions = list(mention_ids or [])
        if bot_id is not None:
            mentions = [uid for uid in mentions if uid != bot_id]
        if not mentions:
            return ""
        target_id = mentions[0]

    if target_id is None:
        return ""

    seed = int(message_id or 0)
    rng = random.Random(seed)

    if MATCHBOT_INSULTS:
        insult = rng.choice(MATCHBOT_INSULTS)
    else:
        insult = "no insults loaded, but I'm still judging you."

    return f"<@{target_id}> {insult}"

