# feedback/catalog/stats_economy.py
# Economy/efficiency stats (gated to NON_TURBO where appropriate)
# Banded phrasing: Positive → ["light","moderate","high","extreme"]
#                   Negative → ["light","moderate","severe","critical"]
# Authoring rule: Do not assume items/wards/objectives; speak to farming/XP pace only.

PHRASE_BOOK = {
    "gpm": {
        "modes": ["NON_TURBO"],
        "positive": {
            "extreme": [
                "Explosive GPM — you converted time into gold relentlessly.",
                "Top-tier farm rate — waves and camps melted on schedule.",
                "You hit power spikes fast with near-constant income.",
                "Elite efficiency — every rotation packed gold value.",
                "Your farming never stalled — the graph just climbed."
            ],
            "high": [
                "Strong GPM — routes were clean and consistent.",
                "You chained waves into camps efficiently.",
                "Great uptime — little idle time between clears.",
                "You created safe, repeatable farm cycles.",
                "Your income stayed comfortably above pace."
            ],
            "moderate": [
                "Healthy GPM — solid, steady farming throughout.",
                "You maintained respectable gold flow.",
                "Clear, if not blazing, farm patterns.",
                "Income kept you relevant across phases.",
                "You stayed close to expected farm tempo."
            ],
            "light": [
                "Decent GPM — a bit more chaining lifts it further.",
                "Some gaps between clears — tighten transitions.",
                "One extra camp per route would add up.",
                "Small optimizations in pathing raise income.",
                "Trim low-value detours to keep gold ticking."
            ]
        },
        "negative": {
            "critical": [
                "Very low GPM — farm patterns never took off.",
                "Income stalled for long stretches.",
                "Little conversion of time into gold.",
                "Routes lacked structure — gold graph stayed flat.",
                "Too few wave/camp cycles to matter."
            ],
            "severe": [
                "Low GPM — route efficiency needs work.",
                "Gaps between clears cost significant gold.",
                "You left farm on the map repeatedly.",
                "Slow transitions blunted income.",
                "Split paths reduced your gold per minute."
            ],
            "moderate": [
                "Below average GPM — smooth out your cycles.",
                "A bit too much low-value movement between camps.",
                "Missed chances to chain wave→camp reliably.",
                "Earlier pivots to safe farm would help.",
                "Shorten downtime to raise income."
            ],
            "light": [
                "Slight GPM dip — minor pathing tweaks will fix it.",
                "A few missed camps each rotation.",
                "Clear one more nearby camp before rotating.",
                "Cut small detours to keep income flowing.",
                "Tighten recall points to stay on farm tempo."
            ]
        }
    },

    "xpm": {
        "modes": ["NON_TURBO"],
        "positive": {
            "extreme": [
                "Explosive XPM — levels arrived ahead of schedule.",
                "You soaked XP constantly — spikes came early.",
                "Top-end XP pace — you were always in the action or the wave.",
                "Elite presence in XP zones — no stalls.",
                "Your level curve stayed a step above."
            ],
            "high": [
                "Great XPM — strong access to waves and skirmish XP.",
                "Consistent participation kept XP flowing.",
                "You balanced rotations without sacrificing levels.",
                "You found safe XP windows between plays.",
                "Your level timing matched game tempo well."
            ],
            "moderate": [
                "Healthy XPM — steady level progression.",
                "You kept close to expected level marks.",
                "Regular XP intake from waves and nearby fights.",
                "No major dips — progression stayed intact.",
                "You stayed in range to collect XP often."
            ],
            "light": [
                "Decent XPM — grab one more wave between moves.",
                "Small gaps in soaking nearby XP.",
                "Be a step closer to fights to catch ambient XP.",
                "Protect side-lane XP during resets.",
                "A bit more time in XP zones will pay off."
            ]
        },
        "negative": {
            "critical": [
                "Very low XPM — levels lagged far behind.",
                "Long XP droughts — progression stalled.",
                "You rarely occupied XP-rich spaces.",
                "Your curve fell out of the game’s pace.",
                "Spikes never arrived due to missing XP."
            ],
            "severe": [
                "Low XPM — not enough time in XP zones.",
                "Rotations cost too much XP opportunity.",
                "You played just out of XP range too often.",
                "Missed multiple safe waves across phases.",
                "Skirmishes happened without you in XP range."
            ],
            "moderate": [
                "Below-average XPM — secure more nearby waves.",
                "A few missed chances to soak fight XP.",
                "Shorten travel gaps between XP sources.",
                "Be closer when action breaks out.",
                "Anchor to a lane briefly to rebuild pace."
            ],
            "light": [
                "Slight XPM dip — minor positioning fixes.",
                "Stand a screen closer to pick up XP more often.",
                "Grab the nearest safe wave before rotating.",
                "Stay in XP range when plays start.",
                "Trim brief detours that drop you out of XP."
            ]
        }
    },
}
