"""PT exercise plan and rest-timing constants.

Single source of truth shared by the FIT generator and the Garmin Connect
uploader. Import-only — no heavy deps here so lightweight consumers
(e.g. --dry-run JSON preview) don't pull in fit_tool.

Current program: the **Lobdell 2026-07-29 prescription** — 11 exercises,
3x/wk, ALL of them every session. The source of truth is
`knowledge/injury-current.md` -> HEP in the endurance-training repo; this
file is just the generator input. Debuts Wed 2026-08-05.

Three encoding decisions, all deliberate:

1. UNILATERAL ITEMS ARE SPLIT INTO SEPARATE RIGHT/LEFT ENTRIES, RIGHT
   FIRST. The prescription is symmetric 3x10 and the standing rule is
   "RIGHT side first on every unilateral item, and do NOT invent a 4th
   right-side set." Splitting puts that ordering on the watch instead of
   in prose — the device card is the control mechanism. 11 prescribed
   exercises -> 21 entries. Same physical work, explicit sequencing.

2. LOADS LIVE IN THE STEP NAME, not just the notes. Same reason. The two
   that matter: abduction is 5 lb ON THE WORKING LEG (resolved 2026-08-04
   — the old ledger's "10 lb" named the PAIR of ankle weights), and the
   SL Goblet RDL enters at bodyweight or a LIGHT kettlebell. The retired
   bilateral RDL's 35 lb does NOT carry across: PT's control rule makes
   frontal-plane control the binding constraint, not strength.

3. ORDER IS BY EQUIPMENT BLOCK, not prescription number: floor (mat/ball/
   ankle weights) -> loaded standing (KB/DB/slideboard) -> standing
   bodyweight -> band -> balance finish. Four equipment pickups instead of
   eleven. Carried over from the DJ-008 ordering principle.
   /!\ TENSION, flagged not resolved: this puts SL Squats (high-skill,
   varus-critical) late, when form fatigues. If a frontal-plane signal
   shows up, move Block C ahead of Block B — it is a one-line reorder.

/!\ VARUS, not valgus, on every weightbearing single-leg item: knee
stacked over the MIDDLE OF THE FOOT. Never "knees out." Medial tear.
"""

PT_EXERCISES = [
    # ── Block A: FLOOR (mat, gym ball, ankle weights) ───────────────────
    {"name": "SL Bridge R (involved)",   "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Involved side first while fresh. Ham LSI 86%"},
    {"name": "SL Bridge L",              "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Symmetric 3x10 - do NOT add a 4th right set"},
    {"name": "SL Ham Curl Ball R",       "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Was bilateral, now single leg. Deficit side first"},
    {"name": "SL Ham Curl Ball L",       "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Hamstring - expect diffuse DOMS, that is adherence"},
    {"name": "Side Abduction R 5lb",     "sets": 3, "reps": 10, "hold_sec": 3,  "notes": "5 lb ankle weight on the WORKING leg. Glute med"},
    {"name": "Side Abduction L 5lb",     "sets": 3, "reps": 10, "hold_sec": 3,  "notes": "5 lb. Non-weightbearing, varus cue does not apply"},

    # ── Block B: LOADED STANDING (kettlebell, DB, slideboard) ───────────
    {"name": "SL Goblet RDL R BW-ltKB",  "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "BW or LIGHT KB. NOT the retired 35 lb. Control rule"},
    {"name": "SL Goblet RDL L BW-ltKB",  "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Load = what you control with good form. Varus cue"},
    {"name": "Goblet Squat 40lb",        "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Bilateral symmetry anchor. Held 40 lb since 7/28"},
    {"name": "Slideboard Fwd Lunge R",   "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Sagittal. Varus cue - knee over middle of foot"},
    {"name": "Slideboard Fwd Lunge L",   "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Varus cue - knee over middle of foot"},
    {"name": "DB Lateral Lunge R",       "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "FRONTAL PLANE - open PT question. Film it. Varus cue"},
    {"name": "DB Lateral Lunge L",       "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Stop on any pinpoint medial joint-line signal"},

    # ── Block C: STANDING BODYWEIGHT ────────────────────────────────────
    {"name": "SL Heel Raise R",          "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Gastroc. Also direct prep for ankle-dominant pogos"},
    {"name": "SL Heel Raise L",          "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Slow lower"},
    {"name": "SL Squat R",               "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Varus cue. Depth = what you control with good form"},
    {"name": "SL Squat L",               "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Varus cue - knee over middle of foot"},

    # ── Block D: BAND ───────────────────────────────────────────────────
    {"name": "Fire Hydrant R band",      "sets": 3, "reps": 10, "hold_sec": 2,  "notes": "Standing. 2s hold at the top"},
    {"name": "Fire Hydrant L band",      "sets": 3, "reps": 10, "hold_sec": 2,  "notes": "Non-weightbearing, varus cue does not apply"},

    # ── Block E: BALANCE FINISH ─────────────────────────────────────────
    {"name": "SL Balance R",             "sets": 2, "reps": 3,  "hold_sec": 30, "notes": "Full 2-set dose. Varus cue. 30s each rep"},
    {"name": "SL Balance L",             "sets": 2, "reps": 3,  "hold_sec": 30, "notes": "Full 2-set dose. 30s each rep"},
]

# ── Rest constants ───────────────────────────────────────────────────────
# /!\ VERIFIED 2026-08-04, and it corrected a wrong belief in the
# endurance-training backlog. Two DIFFERENT gaps exist and they are not
# interchangeable:
#   REST_BETWEEN_SETS_SEC      - inside an exercise, between sets. Has been
#                                30.0 since this file was created
#                                (2026-03-13). It was NEVER 45 s.
#   REST_BETWEEN_EXERCISES_SEC - the transition between exercises. THIS is
#                                the one that was 45 s and was cut to 10 s
#                                on 2026-07-28 (commit 3e23931). Already
#                                applied; measured saving was 1:37.
# So there is no unclaimed "45 -> 10 s" saving left. The only remaining
# duration lever in this file is REST_BETWEEN_SETS_SEC, and cutting that
# changes the training stimulus - it is a PT question, not a friction fix.
REST_BETWEEN_SETS_SEC = 30.0
REST_BETWEEN_EXERCISES_SEC = 10.0  # was 45s - too long, broke flow (Tyler, 2026-07-24)
REST_BETWEEN_REPS_SEC = 10.0
REST_BETWEEN_SHORT_REPS_SEC = 5.0
SHORT_HOLD_MAX_SEC = 10
HOLD_TIMER_THRESHOLD_SEC = 5

WORKOUT_NAME = "HEP Full 11"
