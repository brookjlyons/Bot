# bot/runner_pkg/webhook_client.py

import time
import random
import requests
import os
from bot.throttle import throttle_webhook

# --- Debug / webhook selection -------------------------------------------------

def _debug_level() -> int:
    """
    Parse DEBUG_MODE as an integer level:
      0 = prod (post to DISCORD_WEBHOOK_URL)
      1 = debug posting only (route to DISCORD_WEBHOOK_URL_DEBUG)
      2 = debug posting + (elsewhere) payload dumps (stratz.py will gate on >=2)
    Also accepts common truthy strings ("true","yes","on") as level 1.
    """
    raw = (os.getenv("DEBUG_MODE") or "0").strip().lower()
    try:
        return int(raw)
    except Exception:
        return 1 if raw in {"1", "true", "yes", "on"} else 0

DEBUG_LEVEL = _debug_level()

# When callers don't pass a webhook_url (or when we force override in debug),
# we fall back to one of these:
_DEFAULT_WEBHOOK_URL = (
    os.getenv("DISCORD_WEBHOOK_URL_DEBUG") if DEBUG_LEVEL > 0 else os.getenv("DISCORD_WEBHOOK_URL")
)

# Log once so we know where we're posting when default/override is used
_LOGGED_DEFAULT_TARGET = False

# -------------------------------------------------------------------------------

# Global flag to stop the run if Cloudflare hard-blocks our IP
_HARD_BLOCKED = False
# Global cooldown (monotonic seconds) for Discord webhook bucket
_WEBHOOK_COOLDOWN_UNTIL = 0.0


def _parse_retry_after(response: requests.Response) -> float:
    """Parse backoff seconds from Retry-After header, JSON, or X-RateLimit-Reset-After."""
    try:
        xr = response.headers.get("X-RateLimit-Reset-After")
        if xr is not None:
            return max(0.5, float(xr))
    except Exception:
        pass

    ra = response.headers.get("Retry-After")
    if ra:
        try:
            return max(0.5, float(ra))
        except Exception:
            pass
    try:
        data = response.json()
        if isinstance(data, dict) and "retry_after" in data:
            val_f = float(data.get("retry_after"))
            # Some Discord responses use ms; heuristic guard
            if val_f > 60:
                val_f = val_f / 1000.0
            elif 0 < val_f < 0.2:
                val_f = val_f * 1000.0
            return max(0.5, min(val_f, 60.0))
    except Exception:
        pass
    return 2.0


def _looks_like_cloudflare_1015(response: requests.Response) -> bool:
    """Detect Cloudflare Error 1015 HTML block."""
    if "text/html" in (response.headers.get("Content-Type") or "").lower():
        body = (response.text or "")[:500].lower()
        return "error 1015" in body or "you are being rate limited" in body or "cloudflare" in body
    return False


def _webhook_cooldown_active() -> bool:
    return time.monotonic() < _WEBHOOK_COOLDOWN_UNTIL


def _set_webhook_cooldown(seconds: float):
    global _WEBHOOK_COOLDOWN_UNTIL
    seconds = max(1.0, float(seconds))
    _WEBHOOK_COOLDOWN_UNTIL = time.monotonic() + seconds


def _add_wait_param(url: str) -> str:
    """Ensure ?wait=true so Discord returns a JSON body (message object)."""
    return url + ("&wait=true" if "?" in url else "?wait=true")


def strip_query(url: str) -> str:
    """Return webhook base without any query params."""
    q = url.find("?")
    return url if q == -1 else url[:q]


def _ensure_webhook_url(webhook_url: str | None) -> str | None:
    """
    Resolve the webhook to use.
    • If DEBUG_LEVEL > 0 and DISCORD_WEBHOOK_URL_DEBUG is set, ALWAYS route to the debug webhook
      (even if the caller provided a different URL). This guarantees debug isolation without
      changing callers.
    • Otherwise, use the caller-provided URL if present; else fall back to DISCORD_WEBHOOK_URL.
    """
    global _LOGGED_DEFAULT_TARGET

    # Force override to DEBUG webhook if level > 0 and env present
    if DEBUG_LEVEL > 0:
        dbg = (os.getenv("DISCORD_WEBHOOK_URL_DEBUG") or "").strip()
        if dbg:
            # If caller passed a different URL, note the override once
            if webhook_url and strip_query(webhook_url) != strip_query(dbg) and not _LOGGED_DEFAULT_TARGET:
                print("📤 Overriding provided webhook → DEBUG webhook (DEBUG_MODE>0).")
                _LOGGED_DEFAULT_TARGET = True
            if not _LOGGED_DEFAULT_TARGET and not webhook_url:
                print("📤 Using DEBUG webhook (default from env).")
                _LOGGED_DEFAULT_TARGET = True
            return dbg

    # Not in debug (or no debug URL set) — use caller or prod default
    if webhook_url and webhook_url.strip():
        return webhook_url.strip()

    if not _DEFAULT_WEBHOOK_URL:
        # No usable URL — caller must provide or env must be set
        print("❌ No Discord webhook configured. Set DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL_DEBUG.")
        return None

    if not _LOGGED_DEFAULT_TARGET:
        print(f"📤 Using {'DEBUG' if DEBUG_LEVEL > 0 else 'PROD'} webhook (default from env).")
        _LOGGED_DEFAULT_TARGET = True
    return _DEFAULT_WEBHOOK_URL.strip()

# --- New: expose the resolved posting URL for callers that need to store it ----

def resolve_webhook_for_post(webhook_url: str | None) -> str | None:
    """
    Return the exact webhook URL that will be used for a POST after applying
    any DEBUG/webhook overrides. Callers can store strip_query(...) of this
    so later edits hit the correct channel even if env changes.
    """
    return _ensure_webhook_url(webhook_url)


# --- Outcome taxonomy (Phase 4) ------------------------------------------------
# code ∈ {"ok","rate_limited","hard_block","other_error"}

def _ok(msg_id: str | None, structured: bool):
    return (True, msg_id) if not structured else (True, msg_id, "ok", 0.0)

def _fail(code: str, backoff: float, structured: bool, msg_id: str | None = None):
    return (False, msg_id) if not structured else (False, msg_id, code, float(backoff))


def post_to_discord_embed(
    embed: dict,
    webhook_url: str,
    want_message_id: bool = False,
    *,
    structured: bool = False,
) -> tuple[bool, str | None] | tuple[bool, str | None, str, float]:
    """
    Post a single embed to Discord with safe handling:
      • Respect 429 with Retry-After / reset-after.
      • Detect Cloudflare 1015 HTML and mark hard-block.
      • Throttle per webhook to avoid hitting limits.
      • Global cooldown when limits are high.
    Legacy return: (success, message_id).
    Phase-4 return (when structured=True): (ok, msg_id, code, backoff).
      code: "ok" | "rate_limited" | "hard_block" | "other_error"
      backoff: seconds to wait before retrying (0.0 if none).
    """
    global _HARD_BLOCKED

    webhook_url = _ensure_webhook_url(webhook_url)
    if not webhook_url:
        return _fail("other_error", 0.0, structured)

    if _webhook_cooldown_active():
        remaining = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
        print(f"⏸️ Webhook cooling down — {remaining:.1f}s remaining. Skipping post.")
        return _fail("rate_limited", remaining, structured)

    # 🔧 Pass the base webhook URL so per-webhook pacing groups correctly
    throttle_webhook(strip_query(webhook_url))

    url = _add_wait_param(webhook_url) if want_message_id else webhook_url
    payload = {"embeds": [embed]}
    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 204:
            # No body returned (typical when wait=false). Success.
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return _ok(None, structured)

        if response.status_code == 200:
            # wait=true → JSON body; capture id if requested
            msg_id = None
            if want_message_id:
                try:
                    msg = response.json()
                    msg_id = str(msg.get("id")) if isinstance(msg, dict) else None
                except Exception:
                    msg_id = None
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return _ok(msg_id, structured)

        if response.status_code == 429:
            backoff = _parse_retry_after(response)
            print(f"⚠️ Rate limited by Discord — retry_after = {backoff:.2f}s (raw)")
            if backoff > 10:
                _set_webhook_cooldown(backoff)
                print(f"⏩ Backoff {backoff:.2f}s too long — entering global cooldown and skipping further posts.")
                return _fail("rate_limited", backoff, structured)
            time.sleep(backoff)
            throttle_webhook(strip_query(webhook_url))
            retry = requests.post(url, json=payload, timeout=10)
            if retry.status_code in (200, 204):
                msg_id = None
                if want_message_id and retry.status_code == 200:
                    try:
                        msg = retry.json()
                        msg_id = str(msg.get("id")) if isinstance(msg, dict) else None
                    except Exception:
                        msg_id = None
                time.sleep(1.0 + random.uniform(0.1, 0.6))
                return _ok(msg_id, structured)
            if _looks_like_cloudflare_1015(retry):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 encountered on retry — aborting run to cool down.")
                return _fail("hard_block", max(15.0, backoff), structured)
            if retry.status_code == 429:
                rb = _parse_retry_after(retry)
                _set_webhook_cooldown(max(backoff, rb))
                print(f"⏩ Secondary 429 — entering global cooldown for {max(backoff, rb):.2f}s.")
                return _fail("rate_limited", max(backoff, rb), structured)
            print(f"⚠️ Retry failed with status {retry.status_code}: {retry.text[:200]}")
            return _fail("other_error", 0.0, structured)

        if response.status_code in (403, 429) and _looks_like_cloudflare_1015(response):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block detected — aborting run to cool down.")
            return _fail("hard_block", 30.0, structured)

        print(f"⚠️ Discord webhook responded {response.status_code}: {response.text[:300]}")
        return _fail("other_error", 0.0, structured)

    except Exception as e:
        print(f"❌ Failed to post embed to Discord: {e}")
        return _fail("other_error", 0.0, structured)


def edit_discord_message(
    message_id: str,
    embed: dict,
    webhook_url: str,
    exact_base: bool = True,
    *,
    structured: bool = False,
) -> bool | tuple[bool, str, float]:
    """
    Edit a previously-sent webhook message by ID.
    PATCH {webhookBase}/messages/{message_id} with {"embeds":[.]}

    exact_base=True → use the passed base exactly (no debug/prod override).
    Set exact_base=False only if you intentionally want override behavior.

    Legacy return: bool
    Phase-4 return (when structured=True): (ok, code, backoff)
    """
    global _HARD_BLOCKED

    # Honor exact base by default to avoid editing the wrong channel
    base_url = webhook_url if exact_base else _ensure_webhook_url(webhook_url)
    if not base_url:
        return False if not structured else (False, "other_error", 0.0)

    if _webhook_cooldown_active():
        remaining = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
        return False if not structured else (False, "rate_limited", remaining)

    # 🔧 Pass the base webhook URL so per-webhook pacing groups correctly
    throttle_webhook(strip_query(base_url))

    base = strip_query(base_url)
    url = f"{base}/messages/{message_id}"
    payload = {"embeds": [embed]}

    try:
        response = requests.patch(url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            time.sleep(0.6 + random.uniform(0.05, 0.3))
            return True if not structured else (True, "ok", 0.0)

        if response.status_code == 429:
            backoff = _parse_retry_after(response)
            print(f"⚠️ Edit rate limited — retry_after = {backoff:.2f}s")
            if backoff > 10:
                _set_webhook_cooldown(backoff)
                return False if not structured else (False, "rate_limited", backoff)
            time.sleep(backoff)
            throttle_webhook(strip_query(base_url))
            retry = requests.patch(url, json=payload, timeout=10)
            if retry.status_code in (200, 204):
                return True if not structured else (True, "ok", 0.0)
            if _looks_like_cloudflare_1015(retry):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 encountered on edit retry — aborting run.")
                return False if not structured else (False, "hard_block", max(15.0, backoff))
            return False if not structured else (False, "other_error", 0.0)

        if _looks_like_cloudflare_1015(response):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block on edit — aborting run.")
            return False if not structured else (False, "hard_block", 30.0)

        print(f"⚠️ Edit failed {response.status_code}: {response.text[:300]}")
        return False if not structured else (False, "other_error", 0.0)

    except Exception as e:
        print(f"❌ Edit request failed: {e}")
        return False if not structured else (False, "other_error", 0.0)


# --- Small public helpers for runner/orchestrator ---

def is_hard_blocked() -> bool:
    return _HARD_BLOCKED


def webhook_cooldown_active() -> bool:
    return _webhook_cooldown_active()


def webhook_cooldown_remaining() -> float:
    return max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
