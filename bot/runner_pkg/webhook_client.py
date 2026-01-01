# bot/runner_pkg/webhook_client.py

import time
import random
import requests
import os
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from bot.throttle import throttle_webhook
from bot.formatter_pkg.util import build_discord_mention

# ── Debug & webhook selection ──────────────────────────────────────────────────

def _debug_level() -> int:
    """
    DEBUG_MODE:
      0 → prod (DISCORD_WEBHOOK_URL)
      1 → debug (DISCORD_WEBHOOK_URL_DEBUG)
    """
    raw = (os.getenv("DEBUG_MODE") or "0").strip().lower()
    try:
        return int(raw)
    except Exception:
        return 1 if raw in {"1", "true", "yes", "on"} else 0


DEBUG_LEVEL = _debug_level()

_DEFAULT_WEBHOOK_URL: str | None = None
_LOGGED_DEFAULT_TARGET = False
_HARD_BLOCKED = False
_WEBHOOK_COOLDOWN_UNTIL = 0.0


def _resolve_env_webhook() -> str | None:
    """
    Resolve webhook based on DEBUG_MODE:
    - DEBUG_MODE >= 1 → DISCORD_WEBHOOK_URL_DEBUG
    - else           → DISCORD_WEBHOOK_URL
    """
    if DEBUG_LEVEL > 0:
        return (os.getenv("DISCORD_WEBHOOK_URL_DEBUG") or "").strip() or None
    return (os.getenv("DISCORD_WEBHOOK_URL") or "").strip() or None


def _resolve_party_debug_webhook() -> str | None:
    """
    Resolve the dedicated party debug webhook (prod only).
    NOTE:
      - In DEBUG_MODE, DISCORD_WEBHOOK_URL_DEBUG takes precedence globally.
      - In PROD, party/duel embeds should route to DISCORD_WEBHOOK_MATCHBOT_PARTY_DEBUG when set.
    """
    return (os.getenv("DISCORD_WEBHOOK_MATCHBOT_PARTY_DEBUG") or "").strip() or None


def _is_party_or_duel_embed(embed: dict) -> bool:
    """
    Deterministic routing based on embed title produced by formatter_pkg/embed.py.
    Party pending embeds:
      title starts with "⏳ Party (Pending Stats)"
    Party full embeds:
      title starts with "👥 Party Match"
    Duel embeds:
      title == "⚔️ Guild Duel Detected"
    """
    try:
        title = str(embed.get("title") or "")
    except Exception:
        title = ""
    if not title:
        return False
    if title.startswith("⏳ Party (Pending Stats)"):
        return True
    if title.startswith("👥 Party Match"):
        return True
    if title == "⚔️ Guild Duel Detected":
        return True
    return False


def _ensure_default_webhook() -> None:
    global _DEFAULT_WEBHOOK_URL
    if _DEFAULT_WEBHOOK_URL is None:
        _DEFAULT_WEBHOOK_URL = _resolve_env_webhook()
        if not _DEFAULT_WEBHOOK_URL:
            print("⚠️ No default Discord webhook URL resolved from environment.")


_ensure_default_webhook()


def _set_webhook_cooldown(seconds: float) -> None:
    global _WEBHOOK_COOLDOWN_UNTIL
    _WEBHOOK_COOLDOWN_UNTIL = max(_WEBHOOK_COOLDOWN_UNTIL, time.monotonic() + max(0.0, seconds))


def _webhook_cooldown_active() -> bool:
    return time.monotonic() < _WEBHOOK_COOLDOWN_UNTIL


def strip_query(webhook_url: str) -> str:
    """Strip any query parameters from the webhook URL to get a stable base."""
    return webhook_url.split("?", 1)[0].strip()


def _with_wait_true(webhook_url: str) -> str:
    """
    Ensure the webhook URL includes ?wait=true, preserving any existing query parameters.
    """
    parts = urlsplit(webhook_url)
    pairs = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True) if k != "wait"]
    pairs.append(("wait", "true"))
    new_query = urlencode(pairs, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _ensure_webhook_url(webhook_url: str | None) -> str | None:
    """
    Normalise webhook URL according to the following precedence:

    1. Explicit webhook_url parameter (if non-empty).
    2. ENV default (DISCORD_WEBHOOK_URL[_DEBUG]) based on DEBUG_MODE.

    Returns the effective URL or None if nothing is configured.
    """
    global _LOGGED_DEFAULT_TARGET

    if DEBUG_LEVEL > 0:
        dbg = (os.getenv("DISCORD_WEBHOOK_URL_DEBUG") or "").strip()
        if dbg:
            if not _LOGGED_DEFAULT_TARGET:
                print("📤 Using DEBUG webhook (env override).")
                _LOGGED_DEFAULT_TARGET = True
            return dbg

    if webhook_url and webhook_url.strip():
        return webhook_url.strip()

    if not _DEFAULT_WEBHOOK_URL:
        print("❌ No Discord webhook configured. Set DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL_DEBUG.")
        return None

    if not _LOGGED_DEFAULT_TARGET:
        print(f"📤 Using {'DEBUG' if DEBUG_LEVEL > 0 else 'PROD'} webhook (env default).")
        _LOGGED_DEFAULT_TARGET = True
    return _DEFAULT_WEBHOOK_URL.strip()


def resolve_webhook_for_post(webhook_url: str | None) -> str | None:
    """Expose the exact URL used for POST (after debug override)."""
    return _ensure_webhook_url(webhook_url)

# ── Outcome taxonomy (Phase 4) ────────────────────────────────────────────────
# code ∈ {"ok","rate_limited","hard_block","not_found","other_error"}


def _ok(msg_id: str | None, structured: bool):
    return (True, msg_id) if not structured else (True, msg_id, "ok", 0.0)


def _fail(code: str, backoff: float, structured: bool):
    # Legacy fallback: just "False" when structured=False
    if not structured:
        return False, None
    return (False, None, code, backoff)


def _parse_retry_after(r: requests.Response) -> float:
    """Parse Discord retry_after (seconds; may be ms in some cases)."""
    try:
        data = r.json()
        if isinstance(data, dict) and "retry_after" in data:
            v = float(data["retry_after"])
            if v > 60:      # ms heuristic
                v /= 1000.0
            elif 0 < v < 0.2:
                v *= 1000.0
            return max(0.5, min(v, 60.0))
    except Exception:
        pass
    return 2.0


def _looks_like_cloudflare_1015(r: requests.Response) -> bool:
    """
    Heuristic: CF 1015 may return HTML or JSON with 429. We only have access
    to status + a small text snippet here, so be conservative.
    """
    if r.status_code != 429:
        return False
    text = (r.text or "").lower()
    return "cloudflare" in text and "error 1015" in text


# ── Core POST with structured outcomes ────────────────────────────────────────


def post_to_discord_embed(
    embed: dict,
    webhook_url: str,
    want_message_id: bool = False,
    *,
    context: dict | None = None,
    structured: bool = False,
) -> tuple[bool, str | None] | tuple[bool, str | None, str, float]:
    """
    Post one embed with safe 429/CF handling and per-webhook pacing.
    Legacy return: (ok, msg_id)
    Phase 4 (structured=True): (ok, msg_id, code, backoff)
    """
    global _HARD_BLOCKED

    # Route party/duel embeds to the dedicated party debug webhook (prod only).
    if DEBUG_LEVEL == 0 and _is_party_or_duel_embed(embed):
        party_dbg = _resolve_party_debug_webhook()
        if party_dbg:
            webhook_url = party_dbg

    webhook_url = _ensure_webhook_url(webhook_url)
    if not webhook_url:
        return _fail("other_error", 0.0, structured)

    if _webhook_cooldown_active():
        rem = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
        print(f"⏱️ Webhook cooldown active — {rem:.2f}s remaining.")
        return _fail("rate_limited", rem, structured)

    throttle_webhook(strip_query(webhook_url))

    content = None
    if context:
        try:
            discord_id = context.get("discord_id")
        except Exception:
            discord_id = None
        if discord_id:
            mention = build_discord_mention(discord_id)
            if mention:
                content = mention

    payload: dict = {"embeds": [embed]}
    if content:
        payload["content"] = content

    base = strip_query(webhook_url)
    url = _with_wait_true(webhook_url) if want_message_id else base

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code in (200, 204):
            msg_id = None
            if want_message_id:
                try:
                    msg = r.json()
                    msg_id = str(msg.get("id")) if isinstance(msg, dict) else None
                except Exception:
                    msg_id = None
                if not msg_id:
                    print("⚠️ want_message_id=True but no message id returned (missing ?wait=true response body).")
                    return _fail("other_error", 0.0, structured)
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return _ok(msg_id, structured)

        if r.status_code == 429:
            backoff = _parse_retry_after(r)
            print(f"⚠️ Rate limited — retry_after={backoff:.2f}s")
            if backoff > 10:
                _set_webhook_cooldown(backoff)
            time.sleep(backoff)
            throttle_webhook(strip_query(webhook_url))
            rr = requests.post(url, json=payload, timeout=10)
            if rr.status_code in (200, 204):
                msg_id = None
                if want_message_id:
                    try:
                        msg = rr.json()
                        msg_id = str(msg.get("id")) if isinstance(msg, dict) else None
                    except Exception:
                        msg_id = None
                    if not msg_id:
                        print("⚠️ want_message_id=True but no message id returned on retry (missing ?wait=true response body).")
                        return _fail("other_error", 0.0, structured)
                time.sleep(1.0 + random.uniform(0.1, 0.6))
                return _ok(msg_id, structured)
            if _looks_like_cloudflare_1015(rr):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 on retry — aborting run.")
                return _fail("hard_block", max(15.0, backoff), structured)
            if rr.status_code == 429:
                rb = _parse_retry_after(rr)
                back = max(backoff, rb)
                print(f"⏩ Secondary 429 — cooldown {back:.2f}s.")
                return _fail("rate_limited", back, structured)
            print(f"⚠️ Retry failed {rr.status_code}: {rr.text[:200]}")
            return _fail("other_error", 0.0, structured)

        if r.status_code in (403, 429) and _looks_like_cloudflare_1015(r):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block — aborting run.")
            return _fail("hard_block", 30.0, structured)

        print(f"⚠️ Webhook responded {r.status_code}: {r.text[:300]}")
        return _fail("other_error", 0.0, structured)

    except Exception as e:
        print(f"❌ Post failed: {e}")
        return _fail("other_error", 0.0, structured)


def edit_discord_message(
    message_id: str,
    embed: dict,
    webhook_url: str,
    exact_base: bool = True,
    *,
    context: dict | None = None,
    structured: bool = False,
) -> bool | tuple[bool, str, float]:
    """
    Edit a webhook message:
      PATCH {base}/messages/{message_id} with {"embeds":[...]}
    Legacy return: bool
    Phase 4 (structured=True): (ok, code, backoff)
    """
    global _HARD_BLOCKED

    # Route party/duel embeds to the dedicated party debug webhook (prod only).
    if DEBUG_LEVEL == 0 and _is_party_or_duel_embed(embed):
        party_dbg = _resolve_party_debug_webhook()
        if party_dbg:
            webhook_url = party_dbg

    webhook_url = _ensure_webhook_url(webhook_url)
    if not webhook_url:
        if not structured:
            return False
        return False, "other_error", 0.0

    if _webhook_cooldown_active():
        rem = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
        return False if not structured else (False, "rate_limited", rem)

    throttle_webhook(strip_query(webhook_url))

    base_url = webhook_url if exact_base else strip_query(webhook_url)

    base = strip_query(base_url)
    url = f"{base}/messages/{message_id}"
    content = None
    if context:
        try:
            discord_id = context.get("discord_id")
        except Exception:
            discord_id = None
        mention = build_discord_mention(discord_id) if discord_id else ""
        if mention:
            content = mention
    payload = {"embeds": [embed]}
    if content:
        payload["content"] = content

    try:
        r = requests.patch(url, json=payload, timeout=10)
        if r.status_code in (200, 204):
            time.sleep(0.6 + random.uniform(0.05, 0.3))
            return True if not structured else (True, "ok", 0.0)

        if r.status_code in (404, 410):
            return False if not structured else (False, "not_found", 0.0)

        if r.status_code == 429:
            backoff = _parse_retry_after(r)
            print(f"⚠️ Edit rate limited — retry_after={backoff:.2f}s")
            if backoff > 10:
                _set_webhook_cooldown(backoff)
                return False if not structured else (False, "rate_limited", backoff)
            time.sleep(backoff)
            throttle_webhook(strip_query(base_url))
            rr = requests.patch(url, json=payload, timeout=10)
            if rr.status_code in (200, 204):
                return True if not structured else (True, "ok", 0.0)
            if rr.status_code in (404, 410):
                return False if not structured else (False, "not_found", 0.0)
            if _looks_like_cloudflare_1015(rr):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 on edit retry — aborting run.")
                return False if not structured else (False, "hard_block", max(15.0, backoff))
            return False if not structured else (False, "other_error", 0.0)

        if r.status_code in (403, 429) and _looks_like_cloudflare_1015(r):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block on edit — aborting run.")
            return False if not structured else (False, "hard_block", 30.0)

        print(f"⚠️ Edit responded {r.status_code}: {r.text[:300]}")
        return False if not structured else (False, "other_error", 0.0)

    except Exception as e:
        print(f"❌ Edit failed: {e}")
        return False if not structured else (False, "other_error", 0.0)

# ── Runner-facing helpers ─────────────────────────────────────────────────────


def is_hard_blocked() -> bool:
    return _HARD_BLOCKED


def webhook_cooldown_active() -> bool:
    return _webhook_cooldown_active()


def webhook_cooldown_remaining() -> float:
    return max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
