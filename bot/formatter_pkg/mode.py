# bot/formatter_pkg/mode.py
# --- Game mode ID to label mapping ---
GAME_MODE_NAMES = {
    0: "Unknown",
    1: "All Pick",
    2: "Captains Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    6: "Intro",
    7: "Diretide",
    8: "Reverse Captains Mode",
    9: "Greeviling",
    10: "Tutorial",
    11: "Mid Only",
    12: "Ability Draft",
    13: "Event",
    14: "AR Deathmatch",
    15: "1v1 Mid",
    16: "Captains Draft",
    17: "Balanced Draft",
    18: "Ability All Pick",
    20: "Turbo",
    21: "Mutation",
    22: "Ranked All Pick",
    23: "Turbo",
    24: "Ranked Draft",
    25: "Ranked Random Draft"
}

# --- Raw Stratz gameModeName fallback mappings ---
RAW_MODE_LABELS = {
    "MODE_TURBO": "Turbo",
    "MODE_ALL_PICK": "All Pick",
    "ALL_PICK_RANKED": "Ranked All Pick",
    "CAPTAINS_MODE": "Captains Mode",
    "SINGLE_DRAFT": "Single Draft",
    "RANDOM_DRAFT": "Random Draft",
    "ABILITY_DRAFT": "Ability Draft",
    "CAPTAINS_DRAFT": "Captains Draft",
    # Allow raw enums without MODE_ prefix
    "TURBO": "Turbo",
    "ALL_PICK": "All Pick",
    "RANKED_ALL_PICK": "Ranked All Pick",
}

def resolve_game_mode_name(game_mode_field, raw_label_upper: str) -> str:
    """
    Mirrors the exact logic from the monolithic formatter:
    - Accepts numeric IDs or string enums for game_mode_field
    - Uses RAW_MODE_LABELS and GAME_MODE_NAMES the same way
    """
    if isinstance(game_mode_field, str) and game_mode_field:
        return (
            RAW_MODE_LABELS.get(game_mode_field.upper())
            or RAW_MODE_LABELS.get(raw_label_upper)
            or game_mode_field.replace("_", " ").title()
            or "Unknown"
        )
    else:
        return (
            RAW_MODE_LABELS.get(raw_label_upper)
            or GAME_MODE_NAMES.get(game_mode_field)
            or (raw_label_upper.replace("_", " ").title() if raw_label_upper else None)
            or "Unknown"
        )

def is_turbo_mode(game_mode_field, raw_label_upper: str) -> bool:
    """
    Exact Turbo detection parity with the original code.
    """
    return (
        game_mode_field in (20, 23, "TURBO")
        or RAW_MODE_LABELS.get(raw_label_upper) == "Turbo"
        or raw_label_upper == "MODE_TURBO"
    )
