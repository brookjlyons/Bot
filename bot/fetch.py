# bot/fetch.py

from __future__ import annotations

from typing import TypedDict, Literal, Optional, Union, Any

from bot.stratz import fetch_latest_match, fetch_full_match

# ---- Types & constants (documentation + static checking) --------------------

class QuotaError(TypedDict):
    error: Literal["quota_exceeded"]


class LatestMatchBundle(TypedDict):
    match_id: int
    full_data: dict


ReturnType = Union[LatestMatchBundle, QuotaError, None]

QUOTA_SIGNAL: QuotaError = {"error": "quota_exceeded"}


def _is_quota(obj: Any) -> bool:
    """True if an upstream call signalled a quota limit."""
    return isinstance(obj, dict) and obj.get("error") == "quota_exceeded"


def _extract_match_id(latest: Any) -> Optional[int]:
    """
    Extract an integer match_id from various shapes:
      - {"match_id": int}
      - int (defensive: in case upstream changes shape)
    """
    if latest is None:
        return None
    if isinstance(latest, dict):
        mid = latest.get("match_id")
        return int(mid) if isinstance(mid, (int, str)) and str(mid).isdigit() else None
    if isinstance(latest, int):
        return latest
    # last-ditch: attempt str-to-int if it looks numeric
    try:
        return int(latest) if str(latest).isdigit() else None
    except Exception:
        return None


def get_latest_new_match(steam_id: int, last_posted_id: str | None) -> ReturnType:
    """
    Fetch and compare most recent match for a player. If it's new, return full data.
    Otherwise, return None to skip. Detects quota exhaustion and returns signal.
    """
    try:
        if not isinstance(steam_id, int):
            print(f"⚠️ steam_id should be int, got {type(steam_id).__name__} -> {steam_id}")

        latest = fetch_latest_match(steam_id)

        if _is_quota(latest):
            print(f"🛑 Quota exceeded while fetching latest match for {steam_id}")
            return QUOTA_SIGNAL

        match_id = _extract_match_id(latest)
        if match_id is None:
            print(f"⚠️ No latest match found for {steam_id}")
            return None

        last_posted_norm = "" if last_posted_id is None else str(last_posted_id)
        if str(match_id) == last_posted_norm:
            print(f"⏩ Match {match_id} already posted for {steam_id}")
            return None

        full_data = fetch_full_match(match_id)

        if _is_quota(full_data):
            print(f"🛑 Quota exceeded while fetching full data for match {match_id}")
            return QUOTA_SIGNAL

        if not full_data or not isinstance(full_data, dict):
            shape = type(full_data).__name__
            print(f"⚠️ Failed to fetch full match data for match {match_id} (got {shape})")
            return None

        return {
            "match_id": match_id,
            "full_data": full_data,
        }

    except Exception as e:
        print(f"❌ Error in get_latest_new_match for {steam_id}: {type(e).__name__}: {e}")
        return None
