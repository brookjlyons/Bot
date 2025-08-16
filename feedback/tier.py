# feedback/tier.py

def calculate_performance_score(player_stats, hero_baseline, roles, is_turbo=False):
    def get_role_weight(stat, roles):
        ROLE_WEIGHTS = {
            "kills":      {"carry": 1.2, "mid": 1.3, "offlane": 1.0, "support": 0.6},
            "deaths":     {"carry": -2.0, "mid": -2.0, "offlane": -1.8, "support": -1.0},
            "assists":    {"carry": 0.4, "mid": 0.7, "offlane": 1.0, "support": 1.5},
            "gpm":        {"carry": 1.5, "mid": 1.3, "offlane": 1.0, "support": 0.4},
            "xpm":        {"carry": 1.0, "mid": 1.2, "offlane": 1.0, "support": 0.6},
            "last_hits":  {"carry": 1.3, "mid": 1.0, "offlane": 0.7, "support": 0.3},
            "denies":     {"carry": 0.5, "mid": 0.8, "offlane": 0.6, "support": 0.1}
        }
        weights = []
        for role in roles:
            for stat_type, values in ROLE_WEIGHTS.items():
                if stat == stat_type and role in values:
                    weights.append(values[role])
        return max(weights) if weights else 0

    deltas = {}
    weights = {}
    total_score = 0.0
    count = 0

    for stat in ["kills", "deaths", "assists", "gpm", "xpm", "last_hits", "denies"]:
        if is_turbo and stat in ("gpm", "xpm"):
            continue

        player_val = player_stats.get(stat, 0)
        baseline_val = hero_baseline.get(stat, 0)
        delta = (player_val - baseline_val) / (baseline_val or 1)
        delta = max(min(delta, 3.0), -3.0)

        deltas[stat] = delta
        weight = get_role_weight(stat, roles)
        weights[stat] = weight

        if weight != 0:
            total_score += delta * weight
            count += 1

    avg_score = total_score / count if count else 0.0

    if avg_score >= 2.0:
        tier = "Excellent"
    elif avg_score >= 0.5:
        tier = "Solid"
    elif avg_score > -0.5:
        tier = "Neutral"
    else:
        tier = "Underperformed"

    return {
        "score": round(avg_score, 2),
        "tier": tier,
        "deltas": deltas,
        "weights": weights
    }
