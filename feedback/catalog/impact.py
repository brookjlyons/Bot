# feedback/catalog/impact.py

from __future__ import annotations

from typing import Dict


_EXPLANATIONS: Dict[int, str] = {
    -51: "-51: All-time catastrophe — you repeatedly transformed winning chances into historical regret.",
    -50: "-50: Legendary disaster — the enemy team could set their watch by your mistakes.",
    -49: "-49: Match-breaking negative — “punish this player” was a complete strategy.",
    -48: "-48: Unrecoverable — you created problems no amount of teamwork could solve.",
    -47: "-47: Crippling liability — when things went wrong, you were usually nearby.",
    -46: "-46: Severe negative — your decisions reliably nudged the win probability the wrong way.",
    -45: "-45: Very damaging — you invested heavily in the enemy team’s success.",
    -44: "-44: Heavily harmful — you kept giving ground and never reclaimed it.",
    -43: "-43: Extremely harmful — your errors translated cleanly into advantage for the enemy team.",
    -42: "-42: Brutal — you lost the moments that decide games, and paid interest on them.",
    -41: "-41: Disastrous — you fell behind and the game followed suit.",
    -40: "-40: Catastrophic — you were a win condition… just not for your team.",

    -39: "-39: Severely rough — each minute felt harder than the last, and not by accident.",
    -38: "-38: Very rough — you kept giving the enemy team exactly what they wanted.",
    -37: "-37: Horrid — your teammates spent more time compensating than competing.",
    -36: "-36: Extremely messy — advantage leaked out faster than it came in.",
    -35: "-35: Trainwreck — involved in everything, improving nothing.",
    -34: "-34: Deeply damaging — your presence opened doors the enemy team happily walked through.",
    -33: "-33: Painful — you handed out opportunities like party favors.",
    -32: "-32: Ugly — consistently misaligned with what the game was asking for.",
    -31: "-31: Grim — lots of effort, very little leverage.",
    -30: "-30: Very bad — behind the flow and punished for it repeatedly.",

    -29: "-29: Rough — you committed to ideas the game had already rejected.",
    -28: "-28: Bad — value went out, value did not come back.",
    -27: "-27: Really poor — present on the map, absent from the win condition.",
    -26: "-26: Miserable — manageable situations became losses on your watch.",
    -25: "-25: Strong negative — you traded resources like they were expiring.",
    -24: "-24: Weak — you created openings the enemy team reliably exploited.",
    -23: "-23: Not good — you ceded control and never really got it back.",
    -22: "-22: Struggling — consistently on the wrong side of important moments.",
    -21: "-21: Pretty bad — the negatives outpaced the positives all game long.",
    -20: "-20: Below par — not the only issue, but unmistakably part of it.",

    -19: "-19: Underwhelming — you failed to steady the game when it needed a handrail.",
    -18: "-18: Poor — missed chances, punished mistakes, no real recovery.",
    -17: "-17: Subpar — plenty of motion, not much progress.",
    -16: "-16: Off it — late to matter, early to suffer consequences.",
    -15: "-15: Not great — gave away more than you got, consistently.",
    -14: "-14: Sloppy — good intentions, expensive execution.",
    -13: "-13: Shaky — occasional usefulness, persistent uncertainty.",
    -12: "-12: Weak — a few moments, not enough influence.",
    -11: "-11: Low value — around a lot, shaping little.",
    -10: "-10: Mildly negative — a slow drain on win probability.",

    -9: "-9: Slightly harmful — just enough mistakes to matter.",
    -8: "-8: Slightly bad — nothing disastrous, nothing helpful either.",
    -7: "-7: Not ideal — pressure without payoff.",
    -6: "-6: Small negative — more drag than damage.",
    -5: "-5: Just below neutral — close, but not quite.",
    -4: "-4: Slight negative — a few avoidable costs.",
    -3: "-3: Minor drag — quiet, with some unfortunate moments.",
    -2: "-2: Nearly neutral — little downside, little upside.",
    -1: "-1: Near zero — you left very few fingerprints on the game.",
    0: "0: Neutral — the game neither thanked you nor blamed you.",

    1: "1: Barely positive — a small nudge in the right direction.",
    2: "2: Slight help — a couple things quietly went your team’s way.",
    3: "3: Minor contribution — you added a bit more than you took.",
    4: "4: Small positive — useful, if unspectacular.",
    5: "5: Just above neutral — modest help over time.",

    6: "6: Light impact — your actions started turning into value.",
    7: "7: Decent — a few plays that genuinely mattered.",
    8: "8: Solid — reliable, functional, and helpful.",
    9: "9: Good — you were doing your part, and then some.",
    10: "10: Strong — consistent, win-supporting decisions.",

    11: "11: Pretty good — you showed up when it counted.",
    12: "12: Very decent — you made the game easier for your team.",
    13: "13: Helpful — your decisions usually improved the situation.",
    14: "14: Good value — actions turned into advantage.",
    15: "15: Strong value — correct play, visible payoff.",

    16: "16: Really good — more advantage created than conceded.",
    17: "17: High impact — you pushed the game forward, not sideways.",
    18: "18: Very impactful — you forced reactions instead of waiting for them.",
    19: "19: Great — you shaped key moments in your team’s favor.",
    20: "20: Excellent — a genuine reason your team stayed winning-capable.",

    21: "21: Big impact — you repeatedly influenced how the game unfolded.",
    22: "22: Huge help — your presence clearly mattered.",
    23: "23: Very strong — important moments kept breaking your way.",
    24: "24: Massive — you set the pace instead of chasing it.",
    25: "25: Dominant — the enemy team had to play around you.",

    26: "26: Scary good — you created win conditions through steady pressure.",
    27: "27: Crushing — advantage kept compounding under your watch.",
    28: "28: Monster game — you dictated the overall flow.",
    29: "29: Absurdly strong — the enemy team struggled to respond intelligently.",
    30: "30: Ridiculous impact — you were everywhere that mattered.",

    31: "31: Outrageous — neutral moments kept turning favorable because of you.",
    32: "32: Insane — you forced bad choices without overextending.",
    33: "33: Completely dominant — multiple parts of the game bent your way.",
    34: "34: Overwhelming — your advantages stacked faster than answers appeared.",
    35: "35: Elite — consistently excellent decisions with real leverage.",

    36: "36: Exceptional — high-stakes moments kept landing in your favor.",
    37: "37: Near-perfect — disciplined, efficient, and ruthlessly effective.",
    38: "38: Masterclass — you controlled the game with intent and clarity.",
    39: "39: Match-defining — the outcome followed your decisions.",
    40: "40: Top-tier — you were the central reason win odds climbed.",

    41: "41: Dominating — the enemy team never found a clean response.",
    42: "42: Suffocating — their options disappeared minute by minute.",
    43: "43: Oppressive — you dictated terms, they reacted poorly.",
    44: "44: Unstoppable — even coordinated responses weren’t enough.",
    45: "45: Peak-level performance — about as good as this game allowed.",

    46: "46: Tournament-grade — consistently correct under pressure, with payoff.",
    47: "47: Iconic carry — the enemy team played catch-up all game.",
    48: "48: Mythic takeover — the match revolved around your decisions.",
    49: "49: Legendary carry job — win condition and safety net combined.",
    50: "50: Godlike — you controlled outcomes, not just moments.",
    51: "51: Unreal — an all-time performance; hope was the enemy team’s only plan.",
}

_LOW_BLANKET = "≤ -52: Off-the-charts negative — so damaging it exceeds the normal scale."
_HIGH_BLANKET = "≥ +52: Off-the-charts positive — so strong it exceeds the normal scale."


def impact_explanation_line(score_int: int) -> str:
    """
    Return the single-line impact explanation for a whole-integer IMP score.

    Rules:
    - Unique line for every integer score from -51 to +51 (inclusive)
    - Blanket line for <= -52 and >= +52
    - No mode branching, no economy logic, deterministic only
    """
    if score_int <= -52:
        return _LOW_BLANKET
    if score_int >= 52:
        return _HIGH_BLANKET
    return _EXPLANATIONS.get(score_int, f"{score_int}: Unknown impact score (no catalog line).")
