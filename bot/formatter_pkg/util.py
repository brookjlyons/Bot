# bot/formatter_pkg/util.py
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
