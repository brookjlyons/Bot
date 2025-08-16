# bot/runner_pkg/webhook_client.py

import time
import random
import requests
import os
from bot.throttle import throttle_webhook

# ── Debug & webhook selection ──────────────────────────────────────────────────

def _debug_level() -> int:
    """
    DEBUG_MODE:
      0 → prod (DISCORD_WEBHOOK_URL)
      1 → debug (DISCORD_WEBHOOK_URL_DEBUG)
      2 → debug + verbose dumps (read elsewhere)
    Truthy strings ('true','yes','on') map to 1.
    """
    raw = (os.getenv("DEBUG_MODE") or "0").strip().lower()
    try:
        return int(raw)
    except Exception:
        return 1 if raw in {"1", "true", "yes", "on"} else 0

DEBUG_LEVEL = _debug_level()
_DEFAULT_WEBHOOK_URL = (
    os.getenv("DISCORD_WEBHOOK_URL_DEBUG") if DEBUG_LEVEL > 0 else os.getenv("DISCORD_WEBHOOK_URL")
)
_LOGGED_DEFAULT_TARGET = False  # log destination once

# ── Global posting state ───────────────────────────────────────────────────────

_HARD_BLOCKED = False                   # Cloudflare 1015 guard
_WEBHOOK_COOLDOWN_UNTIL = 0.0           # per-bucket cooldown (monotonic)

# ── Internals ─────────────────────────────────────────────────────────────────

def _parse_retry_after(r: requests.Response) -> float:
    """Backoff seconds from headers/body; clamp to sane range."""
    try:
        xr = r.headers.get("X-RateLimit-Reset-After")
        if xr is not None:
            return max(0.5, float(xr))
    except Exception:
        pass
    ra = r.headers.get("Retry-After")
    if ra:
        try:
            return max(0.5, float(ra))
        except Exception:
            pass
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
    """Detect Cloudflare 1015 HTML block."""
    if "text/html" in (r.headers.get("Content-Type") or "").lower():
        b = (r.text or "")[:500].lower()
        return "error 1015" in b or "you are being rate limited" in b or "cloudflare" in b
    return False


def _webhook_cooldown_active() -> bool:
    return time.monotonic() < _WEBHOOK_COOLDOWN_UNTIL


def _set_webhook_cooldown(seconds: float):
    global _WEBHOOK_COOLDOWN_UNTIL
    _WEBHOOK_COOLDOWN_UNTIL = time.monotonic() + max(1.0, float(seconds))


def _add_wait_param(url: str) -> str:
    """Ensure ?wait=true so Discord returns the message JSON."""
    return url + ("&wait=true" if "?" in url else "?wait=true")


def strip_query(url: str) -> str:
    """Drop query params from webhook URL."""
    q = url.find("?")
    return url if q == -1 else url[:q]


def _ensure_webhook_url(webhook_url: str | None) -> str | None:
    """
    Resolve final webhook:
      • DEBUG_LEVEL>0 + DEBUG URL set → force debug webhook.
      • else use provided URL or default env.
    """
    global _LOGGED_DEFAULT_TARGET

    if DEBUG_LEVEL > 0:
        dbg = (os.getenv("DISCORD_WEBHOOK_URL_DEBUG") or "").strip()
        if dbg:
            if webhook_url and strip_query(webhook_url) != strip_query(dbg) and not _LOGGED_DEFAULT_TARGET:
                print("📤 Overriding provided webhook → DEBUG (DEBUG_MODE>0).")
                _LOGGED_DEFAULT_TARGET = True
            if not _LOGGED_DEFAULT_TARGET and not webhook_url:
                print("📤 Using DEBUG webhook (env).")
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
# code ∈ {"ok","rate_limited","hard_block","other_error"}

def _ok(msg_id: str | None, structured: bool):
    return (True, msg_id) if not structured else (True, msg_id, "ok", 0.0)

def _fail(code: str, backoff: float, structured: bool, msg_id: str | None = None):
    return (False, msg_id) if not structured else (False, msg_id, code, float(backoff))

# ── Public API ─────────────────────────────────────────────────────────────────

def post_to_discord_embed(
    embed: dict,
    webhook_url: str,
    want_message_id: bool = False,
    *,
    structured: bool = False,
) -> tuple[bool, str | None] | tuple[bool, str | None, str, float]:
    """
    Post one embed with safe 429/CF handling and per-webhook pacing.
    Legacy return: (ok, msg_id)
    Phase 4 (structured=True): (ok, msg_id, code, backoff)
    """
    global _HARD_BLOCKED

    webhook_url = _ensure_webhook_url(webhook_url)
    if not webhook_url:
        return _fail("other_error", 0.0, structured)

    if _webhook_cooldown_active():
        rem = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
        print(f"⏸️ Webhook cooling down — {rem:.1f}s.")
        return _fail("rate_limited", rem, structured)

    throttle_webhook(strip_query(webhook_url))
    url = _add_wait_param(webhook_url) if want_message_id else webhook_url
    payload = {"embeds": [embed]}

    try:
        r = requests.post(url, json=payload, timeout=10)

        if r.status_code == 204:
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return _ok(None, structured)

        if r.status_code == 200:
            msg_id = None
            if want_message_id:
                try:
                    msg = r.json()
                    msg_id = str(msg.get("id")) if isinstance(msg, dict) else None
                except Exception:
                    msg_id = None
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return _ok(msg_id, structured)

        if r.status_code == 429:
            backoff = _parse_retry_after(r)
            print(f"⚠️ Rate limited — retry_after={backoff:.2f}s")
            if backoff > 10:
                _set_webhook_cooldown(backoff)
                print(f"⏩ Entering global cooldown for {backoff:.2f}s.")
                return _fail("rate_limited", backoff, structured)
            time.sleep(backoff)
            throttle_webhook(strip_query(webhook_url))
            rr = requests.post(url, json=payload, timeout=10)
            if rr.status_code in (200, 204):
                msg_id = None
                if want_message_id and rr.status_code == 200:
                    try:
                        msg = rr.json()
                        msg_id = str(msg.get("id")) if isinstance(msg, dict) else None
                    except Exception:
                        msg_id = None
                time.sleep(1.0 + random.uniform(0.1, 0.6))
                return _ok(msg_id, structured)
            if _looks_like_cloudflare_1015(rr):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 on retry — aborting run.")
                return _fail("hard_block", max(15.0, backoff), structured)
            if rr.status_code == 429:
                rb = _parse_retry_after(rr)
                back = max(backoff, rb)
                _set_webhook_cooldown(back)
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
    structured: bool = False,
) -> bool | tuple[bool, str, float]:
    """
    Edit a webhook message:
      PATCH {base}/messages/{message_id} with {"embeds":[...]}
    Legacy return: bool
    Phase 4 (structured=True): (ok, code, backoff)
    """
    global _HARD_BLOCKED

    base_url = webhook_url if exact_base else _ensure_webhook_url(webhook_url)
    if not base_url:
        return False if not structured else (False, "other_error", 0.0)

    if _webhook_cooldown_active():
        rem = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
        return False if not structured else (False, "rate_limited", rem)

    throttle_webhook(strip_query(base_url))

    base = strip_query(base_url)
    url = f"{base}/messages/{message_id}"
    payload = {"embeds": [embed]}

    try:
        r = requests.patch(url, json=payload, timeout=10)
        if r.status_code in (200, 204):
            time.sleep(0.6 + random.uniform(0.05, 0.3))
            return True if not structured else (True, "ok", 0.0)

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
            if _looks_like_cloudflare_1015(rr):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 on edit retry — aborting run.")
                return False if not structured else (False, "hard_block", max(15.0, backoff))
            return False if not structured else (False, "other_error", 0.0)

        if _looks_like_cloudflare_1015(r):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 on edit — aborting run.")
            return False if not structured else (False, "hard_block", 30.0)

        print(f"⚠️ Edit failed {r.status_code}: {r.text[:300]}")
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
