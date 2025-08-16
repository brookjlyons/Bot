# feedback/catalog/titles.py
# Title phrasing banks for match performance summaries
# Notes:
# - Existing lines preserved exactly.
# - Each tier expanded to 6–8 lines.
# - Added neg_* tiers to mirror positive bands for negative IMP.
# - Keep "negative" as legacy fallback (advice.py may still reference it).

TITLE_BOOK = {
    "win": {
        "legendary": [
            # --- original ---
            "obliterated the enemy team",
            "made it a highlight reel",
            "went god mode this match",
            "was on another level entirely",
            "absolutely shredded the opposition",
            # --- additions ---
            "turned the map into a farm-to-table beatdown",
            "hard-carried like it was a ranked anxiety cure",
            "turned every fight into a personal montage"
        ],
        "high": [
            # --- original ---
            "carried the game hard",
            "dominated from start to finish",
            "was unstoppable this game",
            "put the team on their back",
            "ran the tempo and the scoreboard",
            # --- additions ---
            "steamrolled lanes and never looked back",
            "set the pace and cashed the win",
            "made their cores look two patches behind"
        ],
        "mid": [
            # --- original ---
            "turned up when it counted",
            "played a solid hand in the win",
            "showed up when the team needed it",
            "made the difference in key moments",
            "was a reliable presence all game",
            # --- additions ---
            "kept the plan tidy and the fights cleaner",
            "did the work so the scoreboard didn’t have to",
            "never flashy, always useful — textbook stuff"
        ],
        "low": [
            # --- original ---
            "got carried but did enough",
            "was along for the ride",
            "survived the win",
            "kept up — barely",
            "was present, if not impactful",
            # --- additions ---
            "held the rope while the team climbed",
            "just enough clicks to avoid the report",
            "rode the bus and validated the fare"
        ],
        "very_low": [
            # --- original ---
            "won despite doing very little",
            "contributed nearly nothing, but still won",
            "was dead weight but the team prevailed",
            "didn’t throw hard enough to lose",
            "won — but it wasn’t your doing",
            # --- additions ---
            "the ancient fell before your impact did",
            "spectated from an interesting angle",
            "queue dodged by your teammates, mid-match"
        ],
        # New mirrored negative tiers (win despite negative IMP)
        "neg_low": [
            "won in spite of your best attempts at neutrality",
            "teammates handled it — you handled the courier",
            "spilled a few fights but the squad mopped up",
            "you missed the spike, the team hit it anyway",
            "looked lost in some fights, found in the fountain",
            "got dragged across the line by a giga-carry",
            "your KDA hid while the team did crime",
            "Rosh got more support than you — still a W"
        ],
        "neg_mid": [
            "gift-wrapped a few deaths but the team returned to sender",
            "nearly speedran the throw, patched by teammates",
            "hard fed the early game; got rescued late",
            "played decoy so convincingly it almost worked",
            "every fight started 4v5 and somehow ended GG",
            "forgot the objective, remembered the victory screen",
            "lost the lane, lost the plot, won the game",
            "survived on carry life support"
        ],
        "neg_high": [
            "won while you auditioned for the other team",
            "teammates kited both the enemy and your decisions",
            "delivered rich, farm-fresh gold to the enemy core",
            "made space — for their net worth",
            "your minimap was a grey-scale documentary",
            "hard inted the script, the team rewrote the ending",
            "you were the content; they were the win",
            "if throwing was MMR, you’d be Immortal"
        ],
        "neg_legendary": [
            "got carried so hard you earned frequent flyer miles",
            "victory achieved despite your performance art",
            "the win queue-dodged your KDA",
            "ancient fell while you discovered new fountain routes",
            "enemy cores wrote you a thank-you note — and still lost",
            "a monument to negative impact — and yet, victory",
            "turned disaster into a team-building exercise (for them)",
            "you brought the content, they brought the trophy"
        ],
        # Legacy fallback; advice.py may still reference "negative"
        "negative": [
            # --- original ---
            "won despite being a liability",
            "barely functioned this match",
            "was carried kicking and screaming",
            "was an anchor, not a sail",
            "somehow won despite everything",
            # --- additions ---
            "the only thing you carried was buyback status",
            "team diff so large it covered your feed",
            "victory chose you; you did not choose victory"
        ]
    },
    "loss": {
        "legendary": [
            # --- original ---
            "put the team on their back and still lost",
            "was legendary even in defeat",
            "did everything — except win",
            "was a solo act in a tragedy",
            "outperformed everyone — but couldn’t carry harder",
            # --- additions ---
            "dragged four anchors to the finish line and tripped",
            "played the win condition solo; lobby said no",
            "MVP performance in a ‘maybe next time’"
        ],
        "high": [
            # --- original ---
            "was the only reason this was close",
            "fought hard in a losing battle",
            "did everything they could",
            "stood out despite the loss",
            "was a bright spot in a bad game",
            # --- additions ---
            "kept the graph from going off-screen",
            "made space; no one spent it",
            "top tier impact, bottom tier backup"
        ],
        "mid": [
            # --- original ---
            "had some moments, but not enough",
            "played okay, but couldn’t turn the tide",
            "couldn’t shift momentum",
            "gave some hope, but not consistently",
            "contributed, but didn’t shine",
            # --- additions ---
            "did the basics; win condition stayed locked",
            "a few picks short of a comeback",
            "serviceable play, insufficient chaos"
        ],
        "low": [
            # --- original ---
            "struggled to have impact",
            "couldn’t keep up",
            "got overwhelmed early",
            "never found their footing",
            "failed to turn up when needed",
            # --- additions ---
            "spent the spike window looking for the window",
            "right clicks were on cooldown all game",
            "pressed buyback more confidently than buttons"
        ],
        "very_low": [
            # --- original ---
            "was a major factor in the loss",
            "fed hard and helped the other team",
            "had zero presence this match",
            "actively harmed the team effort",
            "sank the game with poor play",
            # --- additions ---
            "produced highlight reels — for the enemy",
            "took tours of the map via death timer",
            "gave the enemy core a philanthropic experience"
        ],
        # New mirrored negative tiers (loss with negative IMP)
        "neg_low": [
            "impact trended red; not the worst, still costly",
            "a trickle of misplays that added up",
            "one rough decision per fight was enough",
            "never synced with the draft’s plan",
            "lost the rhythm, missed the fights",
            "minor throws at major moments",
            "low-impact rotations, high-impact consequences",
            "couldn’t convert farm into force"
        ],
        "neg_mid": [
            "several hard ints put the game on life support",
            "gave away the map one death at a time",
            "lane went south and the compass broke",
            "every objective was paid for twice",
            "your TP scroll saw more action than your hero",
            "fed momentum until the graph learned to fly",
            "picked fights; also picked the wrong ones",
            "dropped the bag and the courier"
        ],
        "neg_high": [
            "taught the enemy carry about compound interest",
            "played hot potato with a 1k gold bounty",
            "your impact was negative and highly liquid",
            "redefined ‘space creation’ for the wrong side",
            "joined fights mostly as a respawn timer",
            "turned high ground into a suggestion",
            "item timings met feeding timings",
            "the throw had a sequel"
        ],
        "neg_legendary": [
            "historic disaster — the postgame graph flinched",
            "imp so negative it pulled the map towards their ancient",
            "speedran the feeding challenge any% PB",
            "wrote a guide: ‘How to lose from even’",
            "anchored harder than Roshan",
            "impact so low it clipped through the floor",
            "queue-dodged by MMR itself",
            "co-authored the enemy’s Battle Pass progress"
        ],
        # Legacy fallback; advice.py may still reference "negative"
        "negative": [
            # --- original ---
            "griefed their way to a loss",
            "made every mistake imaginable",
            "dragged the whole team down",
            "looked completely lost out there",
            "barely contributed to anything all game",
            # --- additions ---
            "fed like it was charity week",
            "your minimap was a black-and-white film",
            "provided the enemy with full-service coaching"
        ]
    }
}
