import time
import threading
from collections import deque

# Rolling tracker of timestamps for API calls (monotonic seconds)
api_calls = deque()
_lock = threading.Lock()

# Stratz Free Tier Limits
MAX_CALLS_PER_SECOND = 20
MAX_CALLS_PER_MINUTE = 250
MAX_CALLS_PER_HOUR = 2000
# Note: No hard limit on daily quota enforced here

# Discord webhook limits (per webhook, not per bot user)
# Ref: ~30 requests/minute hard limit per webhook, but we stay well under
discord_posts = deque()
_webhook_lock = threading.Lock()
MAX_DISCORD_POSTS_PER_MINUTE = 25  # keep a safe buffer below 30/minute
MAX_DISCORD_POSTS_PER_SECOND = 1   # small-burst gate to avoid bucket trips


def _now() -> float:
    """Monotonic time in seconds to avoid system clock jumps."""
    return time.monotonic()


def throttle():
    """
    Global, process-wide rate limiter for Stratz API calls.
    Blocks until issuing another Stratz API call would respect all caps:
      - 20 per 1 second (sliding window)
      - 250 per 60 seconds (sliding window)
      - 2000 per 3600 seconds (sliding window)
    """
    while True:
        # Compute inside a lock to keep the deque consistent under concurrency
        with _lock:
            now = _now()

            # Trim anything older than 1 hour (we only enforce up to hourly)
            cutoff_hour = now - 3600.0
            while api_calls and api_calls[0] < cutoff_hour:
                api_calls.popleft()

            sleep_for = 0.0

            # --- Per-second window (20/sec)
            threshold_1s = now - 1.0
            count_1s = 0
            earliest_1s = None
            for t in api_calls:
                if t >= threshold_1s:
                    earliest_1s = t if earliest_1s is None else earliest_1s
                    count_1s += 1
            if count_1s >= MAX_CALLS_PER_SECOND and earliest_1s is not None:
                sleep_for = max(sleep_for, (earliest_1s + 1.0) - now)

            # --- Per-minute window (250/min)
            threshold_60s = now - 60.0
            count_60s = 0
            earliest_60s = None
            for t in api_calls:
                if t >= threshold_60s:
                    earliest_60s = t if earliest_60s is None else earliest_60s
                    count_60s += 1
            if count_60s >= MAX_CALLS_PER_MINUTE and earliest_60s is not None:
                sleep_for = max(sleep_for, (earliest_60s + 60.0) - now)

            # --- Per-hour window (2000/hr)
            count_3600 = len(api_calls)  # already trimmed to last hour
            if count_3600 >= MAX_CALLS_PER_HOUR and api_calls:
                earliest_3600 = api_calls[0]
                sleep_for = max(sleep_for, (earliest_3600 + 3600.0) - now)

            if sleep_for <= 0:
                api_calls.append(now)
                return

        time.sleep(min(sleep_for + 0.005, 5.0))


def throttle_webhook(webhook_url: str | None = None):
    """
    Rate limiter for Discord webhook posts.

    NOTE: `webhook_url` is optional for backward compatibility with callers
    that invoke `throttle_webhook()` without arguments. It is **ignored**
    by this simple global limiter, which paces all webhook posts together.

    Discord enforces a hard cap of ~30 requests/minute per webhook, and small burst buckets.
    We gate both per-minute and per-second to avoid tripping long cooldowns.
    """
    while True:
        with _webhook_lock:
            now = _now()

            # Trim anything older than 60 seconds
            cutoff_minute = now - 60.0
            while discord_posts and discord_posts[0] < cutoff_minute:
                discord_posts.popleft()

            sleep_for = 0.0

            # --- Per-second window (small burst bucket)
            threshold_1s = now - 1.0
            count_1s = 0
            earliest_1s = None
            for t in discord_posts:
                if t >= threshold_1s:
                    earliest_1s = t if earliest_1s is None else earliest_1s
                    count_1s += 1
            if count_1s >= MAX_DISCORD_POSTS_PER_SECOND and earliest_1s is not None:
                sleep_for = max(sleep_for, (earliest_1s + 1.0) - now)

            # --- Per-minute window
            count_60s = len(discord_posts)
            if count_60s >= MAX_DISCORD_POSTS_PER_MINUTE and discord_posts:
                earliest_60s = discord_posts[0]
                sleep_for = max(sleep_for, (earliest_60s + 60.0) - now)

            if sleep_for <= 0:
                discord_posts.append(now)
                return

        time.sleep(min(sleep_for + 0.02, 5.0))
