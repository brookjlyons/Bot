# feedback/catalog/flags.py
# Behavior-based flags (compound)
COMPOUND_FLAGS = {
    "farmed_did_nothing": {
        "modes": ["NON_TURBO"],
        "lines": [
            "You farmed well, but didn’t convert it into pressure.",
            "High GPM with low impact. Work on map presence.",
            "Farm isn’t enough — your gold did nothing.",
            "You were rich, but invisible. Time to fight.",
            "Great income, little influence — turn items into moves.",
            "Gold piled up while the map stayed quiet — look to force plays.",
            "Strong farm, weak translation — connect with your team to push.",
            "Items arrived on time, but fights didn’t — initiate or join earlier.",
            "Your net worth spiked, but objectives didn’t follow.",
            "Income achieved; output missing — create pressure with your timing."
        ]
    },
    "no_stacking_support": {
        "lines": [
            "Zero stacks as support — use quiet moments to help your cores.",
            "You forgot to stack. Big value lost for your carry.",
            "Supports must stack. It's expected.",
            "Jungle economy was untouched. Missed role responsibility.",
            "Stack on the minute — it’s free efficiency for your team.",
            "Passing through triangle? Add a stack before you leave.",
            "Safe window = stack window — build the habit.",
            "Your route skipped easy stacks — fold them into rotations.",
            "A single stack each cycle compounds fast — aim for consistency.",
            "Remember: a ping at :53–:55 helps catch the timing."
        ]
    },
    "low_kp": {
        "lines": [
            "Low fight involvement — too much solo play.",
            "You missed key fights. Watch your minimap more.",
            "The team fought without you. Try shadowing your core.",
            "Your absence hurt team engagements.",
            "Rotations were late — be within TP range when fights start.",
            "Choose the nearest skirmish rather than the far wave.",
            "Sync with initiators — arrive before the first stun lands.",
            "Cut farm detours when pings begin.",
            "A screen closer to allies raises KP instantly.",
            "Match smoke timings — don’t arrive after it’s over."
        ]
    },
    "fed_no_impact": {
        "lines": [
            "Died too much with nothing to show. That’s a liability.",
            "High deaths, low contribution — rethink your fights.",
            "Feeding without pressure — brutal combo.",
            "Try to die for a reason, not just habit.",
            "Chain deaths erased your presence — stabilize before re-engaging.",
            "Walk with vision and numbers; avoid solo entries into fog.",
            "Respect burst range — adjust spacing and target selection.",
            "Reset after a rough fight — don’t double down on a losing angle.",
            "If you must trade, trade for something — time, spells, or space.",
            "Fewer risky pokes, more calculated commits."
        ]
    },
    "impact_without_farm": {
        "modes": ["NON_TURBO"],
        "lines": [
            "Great contribution with low gold — excellent support play.",
            "Low farm, big impact. Well played.",
            "You squeezed value out of little. Smart support instincts.",
            "Minimal gold, maximum presence. Impressive.",
            "You made plays without resources — high efficiency.",
            "Value from thin air — clutch timings on a budget.",
            "You showed that decisions beat items this game.",
            "Lean economy, rich impact — textbook role discipline.",
            "You prioritized presence over farm, and it paid off.",
            "Resource-light, fight-heavy — you kept the game winnable."
        ]
    },
    "fed_early": {
        "lines": [
            "Rough early game — multiple deaths put you behind.",
            "Fed early and never recovered. Be more cautious.",
            "Your lane was a disaster — bounce back next time.",
            "Early feed snowballed the enemy. Rethink lane safety.",
            "Stabilize after first death — avoid giving a second in lane.",
            "Pull the wave or reset the lane when pressure mounts.",
            "Use defensive TPs and stick with supports until level spikes.",
            "Play for safe XP until help arrives.",
            "Respect their level 3–5 power window.",
            "Trade HP for last hits only when you have cover."
        ]
    },
    "no_neutral_item": {
        "lines": [
            "You didn’t equip a neutral item — that’s free power.",
            "No neutral item found — check drops more closely.",
            "Missing neutral item all game. That’s just value lost.",
            "Neutral slots are free stats — fill them.",
            "Cycle neutrals — even a small bonus matters.",
            "Ping neutral drops so the right hero picks them up.",
            "Swap neutrals to match the fight or farm phase.",
            "Inventory check: fill the slot, always.",
            "Don’t forget tier upgrades when they drop.",
            "A minor neutral buff can swing close fights."
        ]
    },
    "hoarded_gold": {
        "lines": [
            "You sat on a lot of gold. Consider spending earlier.",
            "Gold does nothing in your pocket. Buy items sooner.",
            "Delayed purchases slowed your timing.",
            "Big savings, small impact. Spend proactively.",
            "Convert banked gold into a timing push.",
            "Shop before fights — don’t carry a fortune into death.",
            "If buyback isn’t needed, invest in impact now.",
            "Hit your component timings, then regroup to fight.",
            "Idle gold = idle power — commit to a build path.",
            "Spend to spike; spike to win the map."
        ]
    },
    "lane_violation": {
        "lines": [
            "As support, don’t take core lanes like mid or jungle.",
            "Lane assignment mismatch — don’t grief mid.",
            "Wrong lane for your role. Stick to the plan.",
            "Supports don’t need to jungle farm early. Let cores scale.",
            "Respect roles — soak XP and enable, don’t replace your core.",
            "If mid rotates, guard the tower — don’t steal waves.",
            "Share resources: hand the high-value lane to your carry.",
            "Rotate for stacks and wards instead of pushing core lanes.",
            "Hold the lane only to defend; release it when ally returns.",
            "Roles win games — align farm priority with the plan."
        ]
    },
    "intentional_feeder": {
        "lines": [
            "This game had griefing behavior. Not a good look.",
            "Multiple intentional feeds detected. Don't ruin games.",
            "Deliberate feeding ruins the experience for others.",
            "Please queue when you're ready to play.",
            "If you need a break, take one — don’t spoil the match.",
            "Reportable behavior — consider the impact on teammates.",
            "Reset before re-queueing; this wasn’t competitive play.",
            "Games are better when everyone’s trying — keep it fair."
        ]
    },
    "slow_start": {
        "modes": ["ALL"],
        "lines": [
            "Took a while to get going — early impact was low but you found your footing later.",
            "Slow out of the gate, but improved as the match went on.",
            "Early game was quiet, but you made your presence felt in the mid to late game.",
            "Lan­ing was shaky; midgame course-corrected well.",
            "You stabilized after a rough start — nice recovery.",
            "Once your spells came online, the map looked better.",
            "After minute 15 you found your rhythm — keep that entry timing earlier.",
            "Good adaptation midgame — try to accelerate that pivot next time.",
            "You needed a few items/levels — once there, impact followed.",
            "Early discipline was missing; later discipline saved the game."
        ]
    },
    "late_game_falloff": {
        "modes": ["ALL"],
        "lines": [
            "Started strong but faded late — keep momentum into the final fights.",
            "Dominated early but couldn't maintain pressure late game.",
            "Great start, but the impact dropped off in the closing stages.",
            "Tempo stalled — protect your lead into high-ground moments.",
            "Translate mid-game wins into vision and objectives before scaling hits.",
            "Reassess target focus late — switch to backliners or saves.",
            "Your hero’s window closed — force earlier objectives next time.",
            "Itemize for closing, not just for snowballing.",
            "Set up buybacks and wards to secure the last two fights.",
            "Convert picks into lanes and towers before they reset."
        ]
    }
}
