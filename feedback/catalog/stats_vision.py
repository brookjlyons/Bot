# feedback/catalog/stats_vision.py
# Vision/utility/jungle support stats
# Banded phrasing per polarity:
#   Positive  → "light", "moderate", "high", "extreme"
#   Negative  → "light", "moderate", "severe", "critical"
# Authoring rule: Lines must only imply what stacking reflects (using downtime to set up camps);
#                 do not assume wards, items, or objective outcomes.

PHRASE_BOOK = {
    "campStack": {
        "positive": {
            "extreme": [
                "Relentless stacking — you juiced the jungle every minute.",
                "Top-tier stacks — your downtime always turned into value.",
                "You kept multiple camps prepped on repeat — textbook support economy.",
                "Stacks rolled in non‑stop — cores always had somewhere rich to farm.",
                "Elite habit formation — you never missed a safe stacking window."
            ],
            "high": [
                "Great stacking — you created real farm headroom.",
                "You consistently turned quiet moments into stacks.",
                "Excellent rhythm — waves → stack → reset stayed tight.",
                "Your map checks routinely ended with a fresh stack.",
                "Strong game sense — stacks appeared before anyone asked."
            ],
            "moderate": [
                "Solid stacking — you added noticeable jungle value.",
                "Good use of several downtime windows for stacks.",
                "You kept a camp or two prepped during calmer phases.",
                "Respectable habit — most rotations included a stack.",
                "You found safe moments to stack without missing fights."
            ],
            "light": [
                "Some stacks landed — add one more per cycle.",
                "Decent starts — tighten timings to catch more horn ticks.",
                "You stacked occasionally; aim for a steadier cadence.",
                "A few extra pings on the minute mark will raise totals.",
                "Small routing tweaks can fit more stacks into the loop."
            ]
        },
        "negative": {
            "critical": [
                "Zero stacking — free jungle value left untouched.",
                "No stacks all game — a core support habit was missing.",
                "You skipped every safe stacking window.",
                "Jungle prep never happened — easy gold left on the map.",
                "Absent stacking made farm routes thinner than needed."
            ],
            "severe": [
                "Very low stacks — quiet minutes weren’t converted.",
                "Stack timings were repeatedly missed.",
                "Long calm stretches passed with no jungle prep.",
                "Rotations rarely included even a single stack.",
                "Your route choices bypassed stack opportunities."
            ],
            "moderate": [
                "Below-par stacks — fit one into each calm rotation.",
                "A few missed minute marks cost easy value.",
                "You stacked rarely despite safe opportunities.",
                "Add stacking to your standard move pattern.",
                "Close to workable — just a more regular cadence needed."
            ],
            "light": [
                "Slight stacking dip — minor timing/positioning fixes.",
                "You had the idea; be a beat earlier on the pull.",
                "One extra camp per cycle would add up fast.",
                "Watch the clock: nudge toward the :53–:55 window.",
                "Tiny path adjustments will capture more stacks."
            ]
        }
    },
}
