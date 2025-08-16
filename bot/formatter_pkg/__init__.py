# bot/formatter_pkg/__init__.py
# Re-exports to preserve the public surface from bot.formatter imports.
from .stats_sets import NORMAL_STATS, TURBO_STATS
from .mode import GAME_MODE_NAMES, RAW_MODE_LABELS, resolve_game_mode_name, is_turbo_mode
from .util import normalize_hero_name, get_role, get_baseline
from .embed import build_discord_embed, build_fallback_embed

__all__ = [
    "NORMAL_STATS", "TURBO_STATS",
    "GAME_MODE_NAMES", "RAW_MODE_LABELS",
    "resolve_game_mode_name", "is_turbo_mode",
    "normalize_hero_name", "get_role", "get_baseline",
    "build_discord_embed", "build_fallback_embed",
]
