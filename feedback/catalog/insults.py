"""Phrase catalog: deterministic insult replies for the Discord 'matchbot' trigger.

This module is intentionally "dumb": constants only (no RNG, no logic).
Selection is performed in server.py using a local seeded random.Random(message.id).
"""

from __future__ import annotations

MATCHBOT_INSULTS: list[str] = [
    "your gameplay is a cautionary tale with legs.",
    "I've seen smarter pathing from a lost courier.",
    "you play like you're buffering in real life.",
    "you make neutral creeps look coordinated.",
    "your map awareness called — it wants a refund.",
    "that was so bad the replay filed a restraining order.",
    "you rotate like a fridge: slowly and with effort.",
    "even the fog of war is embarrassed for you.",
    "you have the confidence of a smurf and the impact of a ward.",
    "I've seen stronger pushes from a wet noodle.",
    "your decision-making is a random number generator with a headache.",
    "your laning phase is just a cry for help with last hits.",
    "you buy items like you're speedrunning regret.",
    "you ping like it fixes problems. it doesn't.",
    "your teamfight positioning is performance art, unfortunately.",
    "you turned 'game sense' into a missing persons case.",
    "your micro is so slow it needs a loading screen.",
    "you make feeding look like a community service.",
    "that play was sponsored by poor choices.",
    "I've seen better coordination from five strangers on dial-up.",
]

__all__ = ["MATCHBOT_INSULTS"]
