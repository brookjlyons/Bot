# bot/gist_state.py

import requests
import os
import json
from urllib.parse import urlparse

# --- Configuration (env-driven) ---------------------------------------------
# Prefer a full Gist URL if provided (e.g., https://gist.github.com/<user>/<id> or
# https://api.github.com/gists/<id>). Fallbacks:
#   1) GIST_URL or STATE_GIST_URL (full URL)
#   2) GIST_ID (just the hex id)
#   3) legacy hardcoded ID (for backward compatibility only)
#
# Filename inside the Gist defaults to "state.json" but can be overridden.
_ENV_GIST_URL = os.getenv("GIST_URL") or os.getenv("STATE_GIST_URL") or ""
_ENV_GIST_ID = os.getenv("GIST_ID") or ""

# Back-compat: keep the previous constant only as a last resort to avoid breaking existing deploys
_LEGACY_DEFAULT_GIST_ID = "2a6cdb57dcdbd69d7468f612a31691f9"

GIST_FILENAME = os.getenv("GIST_FILENAME") or "state.json"
GITHUB_TOKEN = os.getenv("GIST_TOKEN")


def _extract_gist_id_from_url(url: str) -> str:
    """
    Supports:
      - https://gist.github.com/<user>/<id>
      - https://gist.github.com/<id>
      - https://api.github.com/gists/<id>
      - <id> (already an id)
    Returns hex-ish id or "" if not parseable.
    """
    if not url:
        return ""

    # If it's just the id, return as-is
    if "/" not in url and len(url) >= 20 and all(c in "0123456789abcdef" for c in url.lower()):
        return url

    try:
        parsed = urlparse(url)
        # api.github.com/gists/<id>
        if "api.github.com" in parsed.netloc and "/gists/" in parsed.path:
            return parsed.path.rstrip("/").split("/")[-1] or ""
        # gist.github.com/<user>/<id> or gist.github.com/<id>
        if "gist.github.com" in parsed.netloc:
            parts = [p for p in parsed.path.split("/") if p]
            if parts:
                return parts[-1]
    except Exception:
        pass
    return ""


# Resolve final GIST_ID
GIST_ID = (
    _extract_gist_id_from_url(_ENV_GIST_URL)
    or (_ENV_GIST_ID if _ENV_GIST_ID else "")
    or _LEGACY_DEFAULT_GIST_ID
)

# Precomputed API endpoint
def _gist_api_url(gist_id: str) -> str:
    return f"https://api.github.com/gists/{gist_id}"


def load_state():
    """Fetches the current state.json from GitHub Gist"""
    res = requests.get(
        _gist_api_url(GIST_ID),
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
            "Accept": "application/vnd.github+json",
        },
        timeout=15,
    )
    res.raise_for_status()
    gist = res.json()

    print("🧪 Gist file keys:", list(gist.get("files", {}).keys()))

    files = gist.get("files", {})
    if GIST_FILENAME not in files:
        print(f"❌ Gist file {GIST_FILENAME} not found. Returning empty dict.")
        return {}

    content = files[GIST_FILENAME].get("content", "")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        print("❌ Failed to decode state.json. Returning empty dict.")
        return {}

    if isinstance(parsed, dict):
        # 🔁 Migration: pending keys from legacy "<matchId>" → composite "<matchId>:<steamId>"
        # This allows multiple pending messages per match (one per player) without overwriting.
        try:
            pending = parsed.get("pending")
            if isinstance(pending, dict) and pending:
                migrated = {}
                changed = False
                for k, entry in list(pending.items()):
                    # Keep already-composite keys as-is
                    if ":" in str(k):
                        migrated[str(k)] = entry
                        continue

                    # Legacy numeric key — re-key using embedded steamId if present
                    if str(k).isdigit():
                        steam = None
                        try:
                            steam = int((entry or {}).get("steamId"))
                        except Exception:
                            steam = None

                        if steam is not None:
                            new_key = f"{int(k)}:{steam}"
                            # Only re-key if target not already present
                            if new_key not in pending and new_key not in migrated:
                                migrated[new_key] = entry
                                changed = True
                            else:
                                # If collision, keep legacy key to avoid data loss
                                migrated[str(k)] = entry
                        else:
                            # No steamId — keep legacy key
                            migrated[str(k)] = entry
                    else:
                        # Unknown key shape — keep as-is
                        migrated[str(k)] = entry

                if changed:
                    parsed["pending"] = migrated
                    print(f"🔁 Migrated pending keys → composite matchId:steamId (count={len(migrated)})")
        except Exception as e:
            print(f"⚠️ Pending migration skipped due to error: {type(e).__name__}: {e}")

        return parsed

    print(f"⚠️ state.json contained a {type(parsed).__name__}, expected dict. Overwriting.")
    return {}


def save_state(new_state):
    """Updates state.json in GitHub Gist with the provided dictionary"""
    payload = {
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(new_state, indent=2)
            }
        }
    }

    print(f"🔧 PATCH payload being sent to Gist:\n{json.dumps(payload, indent=2)}")

    res = requests.patch(
        _gist_api_url(GIST_ID),
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
            "Accept": "application/vnd.github+json",
        },
        json=payload,
        timeout=15,
    )

    if res.status_code == 200:
        updated = res.json().get("files", {}).get(GIST_FILENAME, {})
        updated_content = updated.get("content", "")
        print(f"✅ Gist successfully patched. New content:\n{updated_content}")
    else:
        print(f"❌ Gist PATCH failed: {res.status_code} - {res.text}")

    res.raise_for_status()
    return True
