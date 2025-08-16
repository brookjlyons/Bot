# feedback/context.py

def evaluate_team_context(player_id, player_stats, team_stats):
    def net_impact(p):
        return p["kills"] + 0.5 * p["assists"] - 2 * p["deaths"]

    ranks = {
        "impact": [],
        "gpm": [],
        "xpm": []
    }

    for p in team_stats:
        account_id = p.get("account_id")
        if account_id is None:
            continue
        ranks["impact"].append((account_id, net_impact(p)))
        ranks["gpm"].append((account_id, p.get("gpm", 0)))
        ranks["xpm"].append((account_id, p.get("xpm", 0)))

    for key in ranks:
        ranks[key].sort(key=lambda x: x[1], reverse=True)

    def get_rank(account_id, sorted_list):
        for i, (pid, _) in enumerate(sorted_list):
            if pid == account_id:
                return i + 1
        return None

    rank_gpm = get_rank(player_id, ranks["gpm"])
    rank_xpm = get_rank(player_id, ranks["xpm"])
    rank_impact = get_rank(player_id, ranks["impact"])
    total_players = len(ranks["impact"])

    tag = "Filler"
    summary = "Performance was there, but not game-changing."

    if rank_impact == 1:
        tag = "Backpack Carrier"
        summary = "You had the highest impact on your team. Clutch."
    elif rank_gpm == 1 and rank_xpm == 1:
        tag = "Top Farmer"
        summary = "You farmed better than anyone on your team."
    elif rank_impact == total_players:
        tag = "Deadweight"
        summary = "Rough one — your stats were bottom of the team."
    elif rank_impact <= total_players // 2:
        tag = "Did Their Bit"
        summary = "Solid contribution, middle of the board."

    return {
        "tag": tag,
        "impact_rank": rank_impact,
        "gpm_rank": rank_gpm,
        "xpm_rank": rank_xpm,
        "summary_line": summary
    }
