# feedback/catalog/impact.py

from __future__ import annotations

from typing import Dict


_EXPLANATIONS: Dict[int, str] = {
    -40: "-40: Catastrophic impact — you were a walking win-condition… for the enemy.",
    -39: "-39: Utterly brutal — every decision seemed to make things worse.",
    -38: "-38: Nightmare fuel — the map would’ve improved if you were AFK.",
    -37: "-37: Pure sabotage vibes — your team fought 4v6 all game.",
    -36: "-36: Horrendous — you gave away momentum like it was free.",
    -35: "-35: Trainwreck — you weren’t in the game, you were in the way.",
    -34: "-34: Deeply awful — the enemy got rich off your existence.",
    -33: "-33: Painful — you delivered more value to their team than yours.",
    -32: "-32: Ugly — you kept showing up at the worst possible moments.",
    -31: "-31: Grim — you made losing easier than winning.",
    -30: "-30: Very bad — you were consistently a step behind and a death ahead.",
    -29: "-29: Rough — you took fights that shouldn’t exist.",
    -28: "-28: Bad — you bled gold and tempo across the map.",
    -27: "-27: Really poor — you were present, but mostly as a donation.",
    -26: "-26: Miserable — you turned small problems into big ones.",
    -25: "-25: Low impact in the worst way — you fed pressure to the enemy.",
    -24: "-24: Weak showing — you helped them more than you helped you.",
    -23: "-23: Not good — your moves created openings for the other side.",
    -22: "-22: Struggling — you kept losing trades that mattered.",
    -21: "-21: Pretty bad — you were a liability more often than not.",
    -20: "-20: Below par — you weren’t the only problem, but you were definitely one.",
    -19: "-19: Underwhelming — you didn’t stabilize anything when it mattered.",
    -18: "-18: Poor — you missed windows and paid for it.",
    -17: "-17: Subpar — you didn’t convert time into value.",
    -16: "-16: Off it — you were late to fights and early to die.",
    -15: "-15: Not great — you gave away too much for too little.",
    -14: "-14: Sloppy — your impact came with a big price tag.",
    -13: "-13: Shaky — you weren’t useless, but you weren’t helpful either.",
    -12: "-12: Weak — you had moments, but mostly didn’t move the needle.",
    -11: "-11: Low value — you existed on the map without controlling it.",
    -10: "-10: Mildly negative — you cost more than you contributed.",
    -9: "-9: A bit harmful — you gave the enemy some easy wins.",
    -8: "-8: Slightly bad — your presence didn’t improve the game.",
    -7: "-7: Not ideal — you struggled to make anything stick.",
    -6: "-6: Small negative — you didn’t pull your weight this one.",
    -5: "-5: Just below neutral — you were close to fine, but not quite.",
    -4: "-4: Slight negative — you didn’t help much, and you hurt a little.",
    -3: "-3: Minor drag — you were mostly irrelevant with a couple mistakes.",
    -2: "-2: Almost neutral — a few missteps, not much else.",
    -1: "-1: Near zero — basically no real contribution either way.",
    0: "0: Perfectly neutral — you did exactly nothing: didn’t help, didn’t hurt.",
    1: "1: Barely positive — you existed, and that’s technically something.",
    2: "2: Slight help — a couple small things went your team’s way.",
    3: "3: Minor contribution — you added a little more than you took.",
    4: "4: Small positive — not flashy, but not useless.",
    5: "5: Just above neutral — you helped a bit more than you harmed.",
    6: "6: Light impact — you started to matter in small ways.",
    7: "7: Decent — you made a few plays that actually counted.",
    8: "8: Solid — you weren’t carrying, but you were contributing.",
    9: "9: Good — you were more useful than the average body on the map.",
    10: "10: Strong — you consistently did something productive.",
    11: "11: Pretty good — you showed up and it mattered.",
    12: "12: Very decent — you made the game easier for your team.",
    13: "13: Helpful — your decisions more often improved the situation.",
    14: "14: Good value — you turned your time into meaningful impact.",
    15: "15: Strong value — you were reliably doing the right things.",
    16: "16: Really good — you were a net advantage across the game.",
    17: "17: High impact — you created pressure instead of absorbing it.",
    18: "18: Very impactful — you made things happen, not just reacted.",
    19: "19: Great — you were a genuine force in this match.",
    20: "20: Excellent — you were a major reason your team had a chance.",
    21: "21: Big impact — you were shaping fights and map control.",
    22: "22: Huge help — your contributions were obvious and repeatable.",
    23: "23: Very strong — you consistently swung moments your way.",
    24: "24: Massive — you were driving the pace, not following it.",
    25: "25: Dominant — you were a problem the enemy couldn’t ignore.",
    26: "26: Scary good — your plays created real win conditions.",
    27: "27: Crushing — you kept converting advantages into more advantages.",
    28: "28: Monster game — you were dictating how the map was played.",
    29: "29: Absurdly strong — you made the enemy feel outnumbered.",
    30: "30: Ridiculous impact — you were everywhere and it all mattered.",
    31: "31: Outrageous — you turned the match into your personal project.",
    32: "32: Insane — the enemy’s best option was “avoid you.”",
    33: "33: Completely dominant — you were winning multiple lanes at once.",
    34: "34: Disgusting — you were stacking advantages like it was scripted.",
    35: "35: Unreal — you were the reason the game had a storyline.",
    36: "36: Legendary — every move you made changed the game state.",
    37: "37: Godlike — you were smothering them with pressure.",
    38: "38: Absolutely cracked — you made pro-level choices all match.",
    39: "39: Holy hell — you weren’t playing Dota, you were running it.",
    40: "40: Peak performance — this was a carry job people complain about in all-chat.",
}

_LOW_BLANKET = "<= -41: Absolute disaster — if you weren’t intentionally feeding, Dota might not be for you."
_HIGH_BLANKET = ">= +41: Unhinged carry job — were you smurfing, against bots, or secretly a retired pro?"


def impact_explanation_line(score_int: int) -> str:
    """
    Return the single-line impact explanation for a whole-integer IMP score.

    Rules:
    - Unique line for every integer score from -40 to +40 (inclusive)
    - Blanket line for <= -41 and >= +41
    - No mode branching, no economy logic, deterministic only
    """
    if score_int <= -41:
        return _LOW_BLANKET
    if score_int >= 41:
        return _HIGH_BLANKET
    return _EXPLANATIONS.get(score_int, f"{score_int}: Unknown impact score (no catalog line).")

