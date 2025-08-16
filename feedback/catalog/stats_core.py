# feedback/catalog/stats_core.py
# Core, mode-agnostic stats (non-economy)
# NOTE: This file now organizes lines by INTENSITY BANDS per polarity.
#       advice.py understands both this banded shape and legacy flat lists.
#
# Band keys:
#   Positive → "extreme", "high", "moderate", "light"
#   Negative → "critical", "severe", "moderate", "light"
#
# Authoring rule: Lines must not assume information outside the stat itself.

PHRASE_BOOK = {
    "imp": {
        # Impact is a composite contribution metric. Lines may speak to fight presence,
        # timings, and momentum, but should not claim economy/vision specifics.
        "positive": {
            "extreme": [
                "Massive impact — you decided fights again and again.",
                "You swung every major engagement in your team’s favor.",
                "Game-shaping presence — you were the axis of every fight.",
                "Constantly decisive — your moves set the tempo all game.",
                "You turned skirmishes into routs with clinical timings."
            ],
            "high": [
                "High impact — you consistently shifted engagements.",
                "You showed up early and often with meaningful contributions.",
                "Reliable presence — your inputs changed outcomes.",
                "You found windows to influence every important clash.",
                "Strong reads — your entries arrived at the right moments."
            ],
            "moderate": [
                "Solid impact — you contributed in most key moments.",
                "You were present where it counted more often than not.",
                "Steady influence — not flashy, but effective.",
                "You added value across phases without big dips.",
                "You kept fights competitive with timely inputs."
            ],
            "light": [
                "Some impact — you had moments that nudged fights.",
                "You added occasional pressure, but could press more.",
                "Impact flickered — look to chain contributions together.",
                "You helped on the margins; scale that up next time.",
                "Quiet stretches reduced otherwise decent influence."
            ]
        },
        "negative": {
            "critical": [
                "Minimal impact — fights progressed without you.",
                "You rarely altered outcomes — find earlier entries.",
                "Invisible in key moments — create or join plays sooner.",
                "Fights happened on your screen, not with your hero.",
                "Windows opened and closed without your involvement."
            ],
            "severe": [
                "Low impact — late or hesitant entries cost value.",
                "Your presence didn’t move the needle enough.",
                "You hovered but didn’t commit when it mattered.",
                "Angles were off — spells landed without consequence.",
                "Impact dipped when tempo rose — tighten your timing."
            ],
            "moderate": [
                "Limited impact — you touched fights without tilting them.",
                "Quiet midgame — look for higher-value engagements.",
                "Contribution was scattered rather than focused.",
                "Reaction windows were narrow — anticipate earlier.",
                "More proactive movements would raise your influence."
            ],
            "light": [
                "A bit under-involved — add one more action per fight.",
                "Small delays blunted otherwise good ideas.",
                "You were close to the moment, but not inside it.",
                "Sharpen entry timing for cleaner follow-through.",
                "Tiny position tweaks would lift your effect."
            ]
        }
    },

    "kills": {
        # Do not infer objectives or vision; speak only to execution/pressure.
        "positive": {
            "extreme": [
                "Explosive kill pressure — you finished targets repeatedly.",
                "Relentless execution — you deleted heroes on sight.",
                "You strung together kills with ruthless efficiency.",
                "Priority targets fell as soon as you committed.",
                "You kept the kill feed tilted your way all game."
            ],
            "high": [
                "Strong finishing — you converted openings into kills.",
                "Great kill count — attempts consistently landed.",
                "Clean focus — targets went down when you committed.",
                "You punished positioning errors quickly.",
                "Your burst windows were well used."
            ],
            "moderate": [
                "Good presence — you secured kills when chances arose.",
                "Respectable finishing — you closed out fair fights.",
                "Kill pressure showed whenever setups appeared.",
                "You contributed meaningful damage to secure takedowns.",
                "Steady conversions on accessible targets."
            ],
            "light": [
                "Some finishing — look to tighten target selection.",
                "You found a few, but left some on the table.",
                "Damage spread thin — pick one and commit.",
                "Arrive half a beat earlier to seal more kills.",
                "Capitalize faster when a hero is already exposed."
            ]
        },
        "negative": {
            "critical": [
                "Almost no kill threat — targets escaped repeatedly.",
                "Kill attempts fizzled — rework focus and timing.",
                "You rarely finished anyone — commit to a single target.",
                "Pressure never turned into takedowns.",
                "No closing power — align damage with disables."
            ],
            "severe": [
                "Low kills — better target priority needed.",
                "You chipped multiple heroes without a finish.",
                "Late arrivals left you outside the takedown window.",
                "Overchasing ruined otherwise good opportunities.",
                "Damage missed stun windows too often."
            ],
            "moderate": [
                "Kill count below expectation — refine paths to fights.",
                "You pressured, but finishing touch was missing.",
                "More decisive commits would raise conversion rate.",
                "Wrong targets soaked your damage.",
                "Hesitation closed a few clear windows."
            ],
            "light": [
                "Slightly low kill output — be closer when fights start.",
                "Pick cleaner angles to secure the last bit of damage.",
                "Sync with a disable to guarantee finishes.",
                "One extra step forward turns pressure into kills.",
                "Thin margins — small timing tweaks should do it."
            ]
        }
    },

    "deaths": {
        # Positive = fewer deaths. Avoid crediting items/vision explicitly.
        "positive": {
            "extreme": [
                "Deathless — pristine survivability.",
                "You stayed alive through everything — flawless risk control.",
                "Near-perfect survival — you refused to give openings.",
                "Zero feed — you kept timers off the board.",
                "Untouchable — you slipped every punish window."
            ],
            "high": [
                "Excellent survival — you stayed relevant on map.",
                "Few deaths — disciplined positioning all game.",
                "You reset danger well before it turned into deaths.",
                "Clean exits — you lived through sticky spots.",
                "You denied streaks and avoided throw moments."
            ],
            "moderate": [
                "Solid survival — limited mistakes under pressure.",
                "Death count stayed manageable for the tempo.",
                "You rarely gave away back-to-back deaths.",
                "You lived long enough to matter in the next fight.",
                "Respectable caution around risky lanes."
            ],
            "light": [
                "Mostly safe — trim one or two avoidable picks.",
                "A couple risky moments — tidy up spacing.",
                "Greedy wave or two turned into deaths — dial that back.",
                "You survived the big ones; clean up the small ones.",
                "Slight polish on exits will pay off."
            ]
        },
        "negative": {
            "critical": [
                "Frequent deaths — you weren’t on the map enough.",
                "Chain deaths collapsed your presence.",
                "You gave away too many timers in succession.",
                "Pickoffs halted your ability to participate.",
                "Deaths came at the worst possible moments."
            ],
            "severe": [
                "High death count — reconsider spacing and paths.",
                "You were caught alone too often.",
                "Greedy pushes turned into unnecessary feeds.",
                "You re-entered danger before stabilizing.",
                "Punished repeatedly by reach you didn’t respect."
            ],
            "moderate": [
                "A bit too many deaths — tighten risk assessment.",
                "Late exits flipped winnable moments.",
                "Avoidable picks slowed your momentum.",
                "Misread threat ranges around fights.",
                "One fewer risky wave each cycle would help."
            ],
            "light": [
                "Occasional pickoffs — small map discipline fixes.",
                "Trim overstay after fights conclude.",
                "Careful with low-HP teases near visionless areas.",
                "Safer TPs would save a death or two.",
                "Minor attention lapses cost you here and there."
            ]
        }
    },

    "assists": {
        # Speak to follow-up and presence; don’t assume wards or item saves.
        "positive": {
            "extreme": [
                "Everywhere at once — huge assist presence.",
                "You connected with nearly every takedown.",
                "Constant follow-up — fights felt stacked in your favor.",
                "Your timing turned stuns into secured takedowns.",
                "You amplified allies on every skirmish."
            ],
            "high": [
                "Great assist count — you arrived on time.",
                "Reliable follow-up — your presence sealed outcomes.",
                "You chained contributions across the map.",
                "You layered control cleanly with teammates.",
                "You were there when allies needed just a bit more."
            ],
            "moderate": [
                "Steady involvement — assists came when fights brewed.",
                "You backed plays consistently without over-rotating.",
                "Good presence across multiple skirmishes.",
                "You added the exact touch to close out fights.",
                "Solid coordination with nearby allies."
            ],
            "light": [
                "Some assists — be half a step earlier to add weight.",
                "You were close; push a little deeper into fights.",
                "Small delays turned assists into near-misses.",
                "Choose the nearest skirmish and commit.",
                "A touch more decisiveness raises your assist share."
            ]
        },
        "negative": {
            "critical": [
                "Barely any assists — you weren’t part of takedowns.",
                "Skirmishes resolved without your involvement.",
                "You arrived after fights were already decided.",
                "No follow-up when allies created openings.",
                "You hovered but didn’t contribute to finishes."
            ],
            "severe": [
                "Low assist count — rotations missed their windows.",
                "Slow commits left allies short-handed.",
                "You split from action despite nearby fights.",
                "You didn’t connect to the plays being made.",
                "Your contribution came late too often."
            ],
            "moderate": [
                "Could be more present — add one more rotation cycle.",
                "You were selective to a fault — join more mid-fights.",
                "Pick a lane to shadow when the map heats up.",
                "Commit earlier when control is already there.",
                "Be available for the second skirmish, not just the first."
            ],
            "light": [
                "Slightly low involvement — minor timing tweaks.",
                "A faster TP turns these into easy assists.",
                "Shorter farm detours would catch more fights.",
                "Stand a screen closer when allies show intent.",
                "Look up from farm when pings start — just a beat sooner."
            ]
        }
    },

    "level": {
        # Keep language to XP/level pace; do not infer tomes/runes explicitly.
        "positive": {
            "extreme": [
                "Top-end levels — you stayed ahead of the curve.",
                "Excellent scaling — you hit spikes right on time.",
                "Your levels stayed a step above the field.",
                "You maintained a commanding level lead.",
                "Late-game levels arrived without delay."
            ],
            "high": [
                "Great XP pace — you kept key skills on schedule.",
                "Levels tracked the game tempo closely.",
                "You matched or beat expected level timings.",
                "You stayed comfortably within top levels.",
                "Your scaling never stalled."
            ],
            "moderate": [
                "Healthy level progression — no major dips.",
                "You kept pace even through rough patches.",
                "Steady XP flow kept abilities relevant.",
                "You stayed within a safe band of levels.",
                "No costly delays on level-based spikes."
            ],
            "light": [
                "Mostly on pace — a touch more wave XP helps.",
                "You were close to ideal level marks.",
                "Minor stalls — keep an eye on side-wave XP.",
                "Tiny XP gaps — soak nearby fights when possible.",
                "One extra safe wave per rotation lifts levels."
            ]
        },
        "negative": {
            "critical": [
                "Far behind in levels — abilities lagged the game.",
                "Severely underleveled — spikes never arrived.",
                "Large XP gap — you couldn’t access key upgrades.",
                "Your level pace fell out of contention.",
                "The floor dropped out of your scaling."
            ],
            "severe": [
                "Underleveled — you trailed important timings.",
                "XP stalls left you short in mid fights.",
                "Slow progression limited your options.",
                "Level deficits blunted your presence.",
                "You couldn’t catch up to the game’s pace."
            ],
            "moderate": [
                "A bit behind — secure safer XP windows.",
                "Missed several nearby XP opportunities.",
                "Creep XP gaps added up over time.",
                "Split decisions cost you a level or two.",
                "You hovered near XP but didn’t soak enough."
            ],
            "light": [
                "Slight dip in levels — minor routing fix.",
                "A few lost waves — tidy rotations to recover.",
                "Take safer XP when action slows.",
                "Be near skirmishes to collect ambient XP.",
                "Protect level pace during map resets."
            ]
        }
    },

    "killParticipation": {
        # Use only what KP implies: presence in takedowns, nothing about wards/econ.
        "positive": {
            "extreme": [
                "Everywhere in the action — you joined almost every takedown.",
                "Exceptional presence — you were part of nearly all kills.",
                "You mirrored the team perfectly — constant involvement.",
                "Skirmishes rarely happened without you.",
                "You lived inside the team’s fight windows."
            ],
            "high": [
                "High participation — dependable presence in fights.",
                "You were there when kills happened.",
                "Strong connection to team movements.",
                "Your rotations matched the team’s tempo well.",
                "You consistently arrived before the close."
            ],
            "moderate": [
                "Solid participation — present in many takedowns.",
                "You caught a good share of the action.",
                "Mostly in step — a few windows missed.",
                "You were around for several key picks.",
                "Decent presence with room for more."
            ],
            "light": [
                "Some involvement — add one more join per skirmish cycle.",
                "Be a touch earlier to convert more KP.",
                "Stay within reach when the map heats up.",
                "Shadow active allies to raise your share.",
                "Trim side tasks when pings start."
            ]
        },
        "negative": {
            "critical": [
                "Very low participation — most kills happened without you.",
                "You were absent from the action too often.",
                "Skirmishes concluded before you ever arrived.",
                "You seldom shared in takedowns — close the distance.",
                "Fights resolved off-camera from your hero."
            ],
            "severe": [
                "Participation dipped — late rotations cost involvement.",
                "You split from team moves during active windows.",
                "You played away from where kills formed.",
                "You didn’t connect when allies committed.",
                "Your joins were consistently a beat late."
            ],
            "moderate": [
                "Below-average participation — shorten travel decisions.",
                "You missed several makeable joins.",
                "One faster TP per cycle raises KP meaningfully.",
                "Choose the nearby skirmish instead of the far wave.",
                "Stay within a screen of the forming fight."
            ],
            "light": [
                "Slightly low KP — minor timing and pathing tweaks.",
                "You were close but just outside several takedowns.",
                "Stand nearer to active allies between waves.",
                "Cut one farm detour when the map goes live.",
                "A small speed-up on reactions will do the trick."
            ]
        }
    },
}
