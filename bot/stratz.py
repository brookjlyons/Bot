# bot/stratz.py

import json
import os
import requests
from bot.throttle import throttle  # ✅ Enforce rate limit before each request

STRATZ_URL = "https://api.stratz.com/graphql"

def _debug_level() -> int:
    """
    Parse DEBUG_MODE as an integer level:
      0 = prod (no payload dumps)
      1 = debug posting only (no payload dumps)
      2 = debug posting + payload dumps (enable verbose Stratz JSON logging)
    Also accepts common truthy strings ("true","yes","on") as level 1.
    """
    raw = (os.getenv("DEBUG_MODE") or "0").strip().lower()
    try:
        return int(raw)
    except Exception:
        return 1 if raw in {"1", "true", "yes", "on"} else 0

# --- Shared Stratz query runner ---
def post_stratz_query(query: str, variables: dict, timeout: int = 10) -> dict | str | None:
    """
    POST a GraphQL query to Stratz and return the 'data' object on success.
    On quota exhaustion: return the string 'quota_exceeded'.
    On other failures: return None (callers handle skip/continue logic).
    """

    token = os.getenv("STRATZ_TOKEN") or os.getenv("TOKEN")
    if not token:
        print("❌ No STRATZ_TOKEN or TOKEN found in environment — cannot query Stratz.")
        return None

    headers = {
        "User-Agent": "STRATZ_API",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    throttle()  # ✅ Rate-limit per second/minute/hour caps

    try:
        response = requests.post(
            STRATZ_URL,
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=timeout
        )

        # Explicit quota handling
        if response.status_code == 429:
            print("🛑 Stratz API returned 429 Too Many Requests")
            return "quota_exceeded"

        # Cloudflare/WAF HTML challenge detection
        if response.status_code == 403 and "text/html" in response.headers.get("Content-Type", ""):
            snippet = (response.text or "")[:300].replace("\n", " ").strip()
            print(f"⚠️ HTTP 403 HTML challenge from Stratz/Cloudflare | body[:300]={snippet}")
            return None

        # Better diagnostics for any non-200
        if response.status_code != 200:
            safe_headers = {
                "status": response.status_code,
                "server": response.headers.get("server"),
                "cf-ray": response.headers.get("cf-ray"),
                "content-type": response.headers.get("Content-Type"),
                "date": response.headers.get("Date"),
            }
            snippet = (response.text or "")[:300].replace("\n", " ").strip()
            print(f"⚠️ Stratz non-200: {safe_headers} | body[:300]={snippet}")
            response.raise_for_status()

        try:
            payload = response.json()
        except Exception as je:
            print(f"❌ Failed to parse JSON from Stratz: {je}")
            text_snippet = (response.text or "")[:200].replace("\n", " ").strip()
            print(f"📎 Body[:200]={text_snippet}")
            return None

        return (payload or {}).get("data")

    except requests.HTTPError as e:
        print(f"❌ Stratz query failed: {e}")
        if "429" in str(e):
            return "quota_exceeded"
        return None
    except Exception as e:
        print(f"❌ Stratz query failed: {e}")
        if "quota" in str(e).lower():
            return "quota_exceeded"
        return None

# --- Minimal match summary: for checking most recent match ID ---
def fetch_latest_match(steam_id: int) -> dict | None:
    """
    Fetch the most recent match ID for a given Steam32 ID.
    Used for polling latest match played.
    """
    query = """
    query ($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: { take: 1 }) {
          id
        }
      }
    }
    """
    variables = {"steamId": steam_id}
    data = post_stratz_query(query, variables)

    if data == "quota_exceeded":
        return {"error": "quota_exceeded"}

    if not data or "player" not in data or not data["player"].get("matches"):
        return None

    return {"match_id": data["player"]["matches"][0]["id"]}

# --- Full match payload including extended stats and timeline ---
def fetch_full_match(match_id: int) -> dict | None:
    """
    Full match data query with extended player + stat info (v4-ready).
    """
    query = """
    query ($matchId: Long!) {
      match(id: $matchId) {
        id
        durationSeconds
        gameMode
        startDateTime
        players {
          steamAccountId
          isVictory
          isRadiant
          lane
          role
          roleBasic
          position
          partyId
          behavior
          intentionalFeeding
          kills
          deaths
          assists
          imp
          gold
          goldSpent
          networth
          goldPerMinute
          experiencePerMinute
          level
          item0Id
          item1Id
          item2Id
          item3Id
          item4Id
          item5Id
          backpack0Id
          backpack1Id
          backpack2Id
          neutral0Id
          hero {
            id
            name
            displayName
          }
          stats {
            campStack
            networthPerMinute
            experiencePerMinute
            actionsPerMinute
            heroDamagePerMinute
            towerDamagePerMinute
            killEvents { time target }
            deathEvents { time }
            assistEvents { time target }
            wards { time }
            wardDestruction { time }
            courierKills { time }
            runes { time }
          }
        }
      }
    }
    """
    variables = {"matchId": match_id}
    data = post_stratz_query(query, variables, timeout=15)

    if data == "quota_exceeded":
        return {"error": "quota_exceeded"}

    if not data:
        return None

    # Only dump verbose Stratz payloads when DEBUG_MODE >= 2
    if _debug_level() >= 2:
        print("🔎 Full match response:")
        print(json.dumps(data, indent=2))

    return data.get("match")
