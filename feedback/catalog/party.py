"""
Party & Guild Duel phrase catalog.

This module is a pure phrase bank for group commentary:
- Per-player lines based on role label + IMP tier.
- Overall party/duel lines based on scenario key.
- Private-data lines for players with hidden stats.

No logic and no RNG in this file.
Selection and seeding are handled in feedback/advice_pkg/party.py
using a local random.Random(f"{matchId}:party:{partyId}") etc,
as per the Party Matches & Guild Duels plan.
"""

# Per-player commentary lines.
#
# Keys:
#   Top level: role label ("hard_carry", "strong", "ride_along", "fed", "hero_loss").
#   Second level: IMP tier ("legendary", "high", "mid", "low", "very_low", "negative", "neg_legendary").
#
# Advice code will:
#   - Decide the label + tier for each player.
#   - Pick one line from the appropriate list.
#   - Format {name}, {hero}, {k}, {d}, {a}, {imp}.
PLAYER_LINES = {
    "hard_carry": {
        "legendary": [
            "{name} hard-carried this one on {hero}: {k}/{d}/{a} with IMP {imp} — the rest of the stack was basically support staff.",
            "{name} put the whole lobby in their backpack on {hero}: {k}/{d}/{a}, IMP {imp}. Everyone else just punched the ticket.",
        ],
        "high": [
            "{name} did the heavy lifting on {hero}: {k}/{d}/{a}, IMP {imp}. Without that game, this party looks a lot rougher.",
        ],
    },
    "strong": {
        "mid": [
            "{name} pulled their weight on {hero}: {k}/{d}/{a}, IMP {imp}. Solid party member, no free rides here.",
        ],
    },
    "ride_along": {
        "very_low": [
            "{name} queued for a guided tour on {hero}: {k}/{d}/{a}, IMP {imp}. The rest of the stack did the driving.",
        ],
    },
    "fed": {
        "negative": [
            "{name} had a rough one on {hero}: {k}/{d}/{a}, IMP {imp}. Every party needs someone to test the enemy damage numbers.",
        ],
    },
    "hero_loss": {
        "high": [
            "{name} tried to drag a doomed team over the line on {hero}: {k}/{d}/{a}, IMP {imp}. Hero performance, bad outcome.",
        ],
    },
}

# Overall group commentary lines.
#
# Keys:
#   "party_win"        – party stack won their game.
#   "party_loss"       – party stack lost their game.
#   "duel_radiant_win" – Radiant guild side won the duel.
#   "duel_dire_win"    – Dire guild side won the duel.
#   "duel_close"       – duel was close / hard-fought.
#
# Advice code will:
#   - Decide which key applies based on win/loss and IMP gap.
#   - Pick one line and format any placeholders as needed.
OVERALL_LINES = {
    "party_win": [
        "Stack diff: the party walked away with the win and some boosted IMP.",
        "The stack paid off — coordinated chaos, good IMP, and a clean party win.",
    ],
    "party_loss": [
        "Sometimes the party is there for shared trauma: tough loss, but at least everyone fed together.",
        "The stack couldn’t quite convert this one — party queue, party pain.",
    ],
    "duel_radiant_win": [
        "Radiant guild squad takes the duel — bragging rights secured until the next rematch.",
    ],
    "duel_dire_win": [
        "Dire guild crew wins the civil war — Radiant will be hearing about this in voice chat for a while.",
    ],
    "duel_close": [
        "Guild duel came down to the wire — nobody walks away quiet after a game that close.",
    ],
}

# Private-data commentary lines.
#
# Used when a guild player’s IMP is hidden (match data private) but others have visible IMP.
#
# Advice code will:
#   - Detect isPrivate.
#   - Pick from these lines instead of PLAYER_LINES.
#   - Format {name} as usual.
PRIVATE_LINES = [
    "{name} has match data set to private, so IMP stays hidden — only K/D/A is visible.",
    "{name} keeps their stats private, so we can’t see impact, just the scoreboard.",
]

__all__ = [
    "PLAYER_LINES",
    "OVERALL_LINES",
    "PRIVATE_LINES",
]

