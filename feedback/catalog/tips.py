# feedback/catalog/tips.py
# Situational tip lines — expanded with multiple variants per band
# Authoring rules:
# - 3–5 lines per band for variety
# - Lines stay relevant to the stat only; no assumptions about other stats
# - Language varies subtly to avoid obvious repetition

TIP_LINES = {
    "campStack": {
        "modes": ["ALL"],
        "text": {
            "light": [
                "Try to stack during quiet moments — it adds up quickly.",
                "One extra camp each rotation can snowball team economy.",
                "Watch the clock for :53–:55 pulls to sneak in more stacks."
            ],
            "moderate": [
                "Look for more stacking windows in your rotations.",
                "You’re stacking occasionally — aim for a steadier rhythm.",
                "Include a stack when rotating through your jungle."
            ],
            "high": [
                "You’re stacking well — keep routing to hit every minute mark.",
                "Strong stacking habits — maintain the minute-mark discipline.",
                "Make sure your stacks are timed so allies can clear them quickly."
            ],
            "extreme": [
                "Your stacking game is elite — keep anchoring team economy.",
                "Flawless stacking — you’re feeding your cores efficiently.",
                "Keep chaining those stacks — you’re driving the farm curve."
            ]
        }
    },
    "deaths": {
        "modes": ["ALL"],
        "text": {
            "light": [
                "Tighten map awareness to avoid unnecessary deaths.",
                "Play a touch safer when vision is low.",
                "Choose fights you can finish without overextending."
            ],
            "moderate": [
                "Use your minimap more aggressively to avoid blind deaths.",
                "Track enemy positions before committing to fights.",
                "Avoid venturing alone into dark areas of the map."
            ],
            "severe": [
                "High death count — play around vision and allies for safety.",
                "Group up more to avoid being picked off.",
                "Slow the pace — give yourself time to farm and reset."
            ],
            "critical": [
                "Deaths are crippling your impact — reset positioning habits.",
                "Stop dying alone — coordinate with teammates before pushing.",
                "Rethink risky moves — every death shifts momentum."
            ]
        }
    },
    "killParticipation": {
        "modes": ["ALL"],
        "text": {
            "light": [
                "Stay closer to your team during skirmishes.",
                "Rotate earlier when fights are brewing.",
                "Be ready to TP to fights that break out."
            ],
            "moderate": [
                "Link up for more fights to boost kill participation.",
                "Coordinate smoke ganks to join in on picks.",
                "Sync rotations with your initiators."
            ],
            "high": [
                "Strong presence in fights — keep syncing with initiators.",
                "Excellent participation — maintain map presence.",
                "Stay proactive — force plays while ahead."
            ],
            "extreme": [
                "You’re in almost every kill — perfect teamfight presence.",
                "Relentless participation — you’re everywhere.",
                "Your map sense keeps you in every fight — keep it up."
            ]
        }
    },
    "gpm": {
        "modes": ["NON_TURBO"],
        "text": {
            "light": [
                "Push lanes before jungling to get more out of rotations.",
                "Clear enemy jungle when safe for bonus gold.",
                "Stack camps for yourself when passing through."
            ],
            "moderate": [
                "Balance lane farm and jungle clears to lift GPM.",
                "Chain farm routes without downtime.",
                "Avoid idle time between waves and camps."
            ],
            "high": [
                "Great farming pace — keep map pressure high between clears.",
                "Maintain ward coverage to farm aggressive zones.",
                "Use hero power spikes to farm enemy territory safely."
            ],
            "extreme": [
                "Elite GPM — you’re setting the game’s economy tempo.",
                "You’re farming at pro-level speed — keep up the pressure.",
                "Your farm rate is choking enemy space — finish the game."
            ]
        }
    },
    "assists": {
        "modes": ["ALL"],
        "text": {
            "light": [
                "Buy items that reward teamplay — glimmers, greaves, etc.",
                "Join fights a bit earlier to help secure kills.",
                "Position to follow up on ally initiations."
            ],
            "moderate": [
                "Join fights earlier to boost assist count.",
                "Rotate to pressure lanes where allies are fighting.",
                "Look for easy teleports into ongoing fights."
            ],
            "high": [
                "Excellent assist rate — you’re enabling fights well.",
                "Great support presence — your allies rely on you.",
                "You’re in sync with your team — keep enabling plays."
            ],
            "extreme": [
                "You’re everywhere — your assists are driving team success.",
                "Perfect presence — every fight has your impact.",
                "You’re a force multiplier in every engagement."
            ]
        }
    },
    "xpm": {
        "modes": ["NON_TURBO"],
        "text": {
            "light": [
                "Look for tomes, XP runes, and split-pushing to boost levels.",
                "Farm safe jungle camps while moving between objectives.",
                "Don’t miss lane creeps while rotating."
            ],
            "moderate": [
                "Catch more waves between objectives to lift XPM.",
                "Soak XP from fights even if you can’t secure kills.",
                "Rotate into lanes with free farm when possible."
            ],
            "high": [
                "Strong XP gain — maintain wave control between fights.",
                "Great lane coverage — you’re staying ahead in levels.",
                "Control jungle and lane XP to pressure enemy cores."
            ],
            "extreme": [
                "Top-tier XPM — you’re outpacing the field in levels.",
                "You’re maxing out XP — push the tempo with your lead.",
                "Use your level advantage to force winning fights."
            ]
        }
    },
    "kills": {
        "modes": ["ALL"],
        "text": {
            "light": [
                "Think about kill angles before fights — who can you burst?",
                "Work with teammates to finish low-HP targets.",
                "Position to secure kills without overextending."
            ],
            "moderate": [
                "Set up fights where you can finish targets reliably.",
                "Coordinate disables to secure high-value kills.",
                "Prioritise fragile enemy cores in fights."
            ],
            "high": [
                "Strong kill count — keep snowballing with good target picks.",
                "You’re converting fights into kills — keep the chain going.",
                "Force fights where your damage output is decisive."
            ],
            "extreme": [
                "You’re leading the slaughter — control the map with pressure.",
                "Dominant kill leader — keep denying enemy space.",
                "Turn your kill lead into objectives and map control."
            ]
        }
    },
    "level": {
        "modes": ["ALL"],
        "text": {
            "light": [
                "XP isn’t just from kills — soak waves, jungle, and fight.",
                "Don’t miss lane XP when rotating.",
                "Farm neutral camps if no waves are nearby."
            ],
            "moderate": [
                "Keep lane presence and join fights to raise your level.",
                "Split push safely for extra XP.",
                "Stay active around objectives to soak fight XP."
            ],
            "high": [
                "You’re ahead in XP — press advantage before enemies catch up.",
                "Control key areas to deny enemy farm and XP.",
                "Convert your XP lead into fight wins."
            ],
            "extreme": [
                "Max level dominance — close out the game before it stalls.",
                "Your level lead makes you untouchable — force fights.",
                "End the game while your XP advantage is overwhelming."
            ]
        }
    }
}
