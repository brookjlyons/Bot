# --- Utility: Normalize hero name from full name string ---
def normalize_hero_name(raw_name: str) -> str:
    if not raw_name:
        return "unknown"
    if raw_name.startswith("npc_dota_hero_"):
        return raw_name.replace("npc_dota_hero_", "").lower()
    return raw_name.lower()

# --- Deprecated fallback functions (kept for API compatibility) ---
def get_role(hero_name: str) -> str:
    return "unknown"

def get_baseline(hero_name: str, mode: str) -> dict | None:
    return None

# --- Discord mention helper (Step 4) ---
def build_discord_mention(discord_id: str | None) -> str | None:
    """
    Safely convert a Discord ID into a mention string (<@ID>).

    Returns None when:
    - discord_id is None
    - discord_id is empty/whitespace
    - discord_id contains non-digit characters

    This MUST NOT raise exceptions, and MUST NOT modify embed logic.
    """
    if not discord_id:
        return None

    discord_id = str(discord_id).strip()
    if not discord_id or not discord_id.isdigit():
        return None

    return f"<@{discord_id}>"
