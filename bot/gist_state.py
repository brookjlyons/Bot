# bot/gist_state.py

import requests
import os
import json

GIST_ID = "2a6cdb57dcdbd69d7468f612a31691f9"
GIST_FILENAME = "state.json"
GITHUB_TOKEN = os.getenv("GIST_TOKEN")

def load_state():
    """Fetches the current state.json from GitHub Gist"""
    res = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    })
    res.raise_for_status()
    gist = res.json()

    print("🧪 Gist file keys:", list(gist["files"].keys()))

    if GIST_FILENAME not in gist["files"]:
        print(f"❌ Gist file {GIST_FILENAME} not found. Returning empty dict.")
        return {}

    content = gist["files"][GIST_FILENAME]["content"]
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
        f"https://api.github.com/gists/{GIST_ID}",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        },
        json=payload
    )

    if res.status_code == 200:
        updated_content = res.json()["files"][GIST_FILENAME]["content"]
        print(f"✅ Gist successfully patched. New content:\n{updated_content}")
    else:
        print(f"❌ Gist PATCH failed: {res.status_code} - {res.text}")

    res.raise_for_status()
    return True
