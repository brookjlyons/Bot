from typing import Dict, Any, List
import json

DEBUG = False  # Set to True to enable debug logging

def _safe_num(val: Any, default: float = 0.0) -> float:
    """Convert None or non-numeric values to a safe float."""
    try:
        if val is None:
            return default
        if isinstance(val, bool):
            return float(val)
        return float(val)
    except (ValueError, TypeError):
        return default

def _get_role_category(role: str, lane: str) -> str:
    role = (role or "").lower()
    lane = (lane or "").lower()
    if role in ["softsupport", "hardsupport"]:
        return "support"
    if lane in ["offlane", "safelane", "mid"]:
        return "core"
    return "unknown"

def _compute_kp(kills: Any, assists: Any, team_kills: Any) -> float:
    try:
        kills = _safe_num(kills)
        assists = _safe_num(assists)
        team_kills = _safe_num(team_kills)
        return (kills + assists) / team_kills if team_kills > 0 else 0.0
    except Exception:
        return 0.0

def _segment_phases(stats_block: Dict[str, Any], duration: Any) -> Dict[str, List[float]]:
    """
    Splits per-minute arrays into early/mid/late segments.
    Returns dict with keys: early, mid, late.
    """
    duration = _safe_num(duration, 0)
    if duration <= 0:
        return {"early": [], "mid": [], "late": []}

    total_minutes = max(1, int(duration) // 60)
    early_cut = total_minutes // 3
    mid_cut = (total_minutes * 2) // 3

    segmented = {}
    for key, arr in stats_block.items():
        if isinstance(arr, list) and arr and all(isinstance(x, (int, float)) for x in arr):
            segmented[key] = {
                "early": arr[:early_cut],
                "mid": arr[early_cut:mid_cut],
                "late": arr[mid_cut:]
            }
    return segmented

def _select_priority_feedback(role_category: str, context: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        'highlight': None,
        'lowlight': None,
        'praises': [],
        'critiques': [],
        'compound_flags': []
    }

    imp = _safe_num(context.get("imp"))
    kills = _safe_num(context.get("kills"))
    assists = _safe_num(context.get("assists"))
    deaths = _safe_num(context.get("deaths"))
    camp_stack = _safe_num(context.get("campStack"))
    level = _safe_num(context.get("level"))
    kp = _safe_num(context.get("killParticipation"))
    duration = _safe_num(context.get("durationSeconds"))
    lane = context.get("lane", "")
    role = context.get("roleBasic", "")
    intentional_feeding = bool(context.get("intentionalFeeding", False))

    ranked_stats = {
        "imp": imp,
        "kills": kills,
        "assists": assists,
        "campStack": camp_stack,
        "killParticipation": kp,
        "deaths": -deaths
    }
    result["highlight"] = max(ranked_stats, key=ranked_stats.get)
    result["lowlight"] = min(ranked_stats, key=ranked_stats.get)

    if kills >= 10: result["praises"].append("kills")
    if assists >= 15: result["praises"].append("assists")
    if imp >= 1.3: result["praises"].append("imp")
    if camp_stack >= 5: result["praises"].append("campStack")
    if kp >= 0.7: result["praises"].append("killParticipation")

    if deaths >= 10: result["critiques"].append("deaths")
    if kp < 0.3: result["critiques"].append("killParticipation")

    if role_category == "support" and camp_stack == 0:
        result['compound_flags'].append("no_stacking_support")

    if kp < 0.3 and duration > 900:
        result['compound_flags'].append("low_kp")

    if deaths >= 10 and imp < 0.2:
        result['compound_flags'].append("fed_no_impact")

    if deaths >= 5 and level < 10:
        result['compound_flags'].append("fed_early")

    if lane in ['mid', 'jungle'] and role_category == 'support':
        result['compound_flags'].append("lane_violation")

    if intentional_feeding:
        result['compound_flags'].append("intentional_feeder")

    # --- New: IMP trend analysis from timeline arrays ---
    stats_block = context.get("statsBlock", {})
    phases = _segment_phases(stats_block, duration)
    imp_pm = stats_block.get("impPerMinute", [])

    if isinstance(imp_pm, list) and imp_pm:
        if phases.get("impPerMinute"):
            early_avg = _safe_avg(phases["impPerMinute"]["early"])
            late_avg = _safe_avg(phases["impPerMinute"]["late"])
            if early_avg < 0.5 and late_avg > early_avg + 0.5:
                result["compound_flags"].append("slow_start")
            if late_avg < early_avg - 0.5:
                result["compound_flags"].append("late_game_falloff")

    return result

def _safe_avg(arr: List[float]) -> float:
    if not arr:
        return 0.0
    arr = [_safe_num(x) for x in arr]
    return sum(arr) / len(arr) if arr else 0.0

def analyze_player(player_stats: Dict[str, Any], _: Dict[str, Any], role: str, team_kills: Any) -> Dict[str, Any]:
    lane = player_stats.get("lane", "")
    role_basic = player_stats.get("roleBasic", "")
    role_category = _get_role_category(role_basic, lane)

    stats = dict(player_stats)
    stats["killParticipation"] = _compute_kp(
        stats.get("kills"),
        stats.get("assists"),
        team_kills
    )

    tags = _select_priority_feedback(role_category, stats)

    if DEBUG:
        print("🧪 NORMAL analyze_player debug:")
        print("  Role:", role_basic, "| Lane:", lane, "→", role_category)
        print("  Stats:", json.dumps(stats, indent=2))
        print("  Tags:", json.dumps(tags, indent=2))

    return {
        "deltas": {},  # placeholder for future non-turbo delta logic
        "score": _safe_num(stats.get("imp")),
        "feedback_tags": tags
    }
