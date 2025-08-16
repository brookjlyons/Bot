from feedback.engine import analyze_player as normal_analyze
from feedback.engine_turbo import analyze_player as turbo_analyze

def test_engine_normal():
    sample_stats = {"kills": 8, "deaths": 3, "assists": 12, "imp": 1.2, "gpm": 510, "xpm": 600, "level": 18, "campStack": 2}
    baseline = {"kills": 6, "deaths": 5, "assists": 10, "imp": 1.0, "gpm": 450, "xpm": 500, "level": 17, "campStack": 1}
    result = normal_analyze(sample_stats, baseline, "core", team_kills=30)
    print(result)

def test_engine_turbo():
    sample_stats = {"kills": 4, "deaths": 6, "assists": 5, "imp": 0.5, "campStack": 0, "level": 12}
    baseline = {"kills": 5, "deaths": 4, "assists": 7, "imp": 0.7, "campStack": 1, "level": 13}
    result = turbo_analyze(sample_stats, baseline, "softsupport", team_kills=25)
    print(result)
