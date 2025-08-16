import os
import json
from bot.formatter import _extract_stats, TURBO_STATS, NORMAL_STATS

# Enable debug printout from formatter.py
os.environ["DEBUG_MODE"] = "1"

def run_extraction_test(path: str, player_id: int):
    with open(path, "r") as f:
        match = json.load(f)

    match_id = match.get("id", "???")
    game_mode = str(match.get("gameMode", 0))
    players = match.get("players", [])
    player = next((p for p in players if p.get("steamAccountId") == player_id), None)

    if not player:
        print(f"❌ Player {player_id} not found in match {match_id}")
        return

    is_radiant = player.get("isRadiant", True)
    team_kills = sum(p.get("kills", 0) for p in players if p.get("isRadiant") == is_radiant)
    player["_team_kills"] = team_kills

    stat_keys = TURBO_STATS if game_mode == "23" else NORMAL_STATS
    stats_block = player.get("stats", {})

    print(f"\n📦 Testing match {match_id} — {'TURBO' if game_mode == '23' else 'NORMAL'} mode")
    stats = _extract_stats(player, stats_block, stat_keys)
    print("🧪 Extracted stats:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    run_extraction_test("tests/samples/match_normal.json", 123456789)
    run_extraction_test("tests/samples/match_turbo.json", 123456789)
