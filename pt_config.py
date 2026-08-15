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
   /!\ EXCEPTION (2026-08-05): SL Squat and SL Goblet RDL are ALTERNATING
   — one entry each, reps=20 (= 10/side/set), start R. The provider app
   text specifies alternation for the squat ("...then switch sides");
   Tyler extended it to the RDL (PT confirm queued in the P1 batch).
   Alternation halves continuous single-leg TUT, which protects
   form-on-the-last-set — the same rationale as their 30 s rest_sec.
   21 -> 19 entries. See endurance-training handover s42 §8.

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
    {"name": "SL Goblet RDL ALT BW-ltKB", "sets": 3, "reps": 20, "hold_sec": 0,  "notes": "START R, alternate every rep, 10/side. Light KB = control rule"},
    {"name": "Goblet Squat 40lb",        "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Bilateral symmetry anchor. Held 40 lb since 7/28"},
    {"name": "Slideboard Fwd Lunge R",   "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Sagittal. Varus cue - knee over middle of foot"},
    {"name": "Slideboard Fwd Lunge L",   "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Varus cue - knee over middle of foot"},
    {"name": "DB Lateral Lunge R",       "sets": 3, "reps": 10, "hold_sec": 0,  "rest_sec": 30, "notes": "FRONTAL PLANE - open PT question. Film it. Varus cue"},
    {"name": "DB Lateral Lunge L",       "sets": 3, "reps": 10, "hold_sec": 0,  "rest_sec": 30, "notes": "Stop on any pinpoint medial joint-line signal"},

    # ── Block C: STANDING BODYWEIGHT ────────────────────────────────────
    {"name": "SL Heel Raise R",          "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Gastroc. Also direct prep for ankle-dominant pogos"},
    {"name": "SL Heel Raise L",          "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Slow lower"},
    {"name": "SL Squat ALT start R",     "sets": 3, "reps": 20, "hold_sec": 0,  "rest_sec": 30, "notes": "Alternate every rep, 10/side. Varus cue. Depth = control"},

    # ── Block D: BAND ───────────────────────────────────────────────────
    {"name": "Fire Hydrant R band",      "sets": 3, "reps": 10, "hold_sec": 2,  "notes": "Standing. 2s hold at the top"},
    {"name": "Fire Hydrant L band",      "sets": 3, "reps": 10, "hold_sec": 2,  "notes": "Non-weightbearing, varus cue does not apply"},

    # ── Block E: BALANCE FINISH ─────────────────────────────────────────
    {"name": "SL Balance R",             "sets": 2, "reps": 3,  "hold_sec": 30, "rest_sec": 30, "notes": "Full 2-set dose. Varus cue. 30s each rep"},
    {"name": "SL Balance L",             "sets": 2, "reps": 3,  "hold_sec": 30, "rest_sec": 30, "notes": "Full 2-set dose. 30s each rep"},
]

# ── FLOOR CARD (2026-08-14) ─────────────────────────────────────────────
# Travel/short-day card: shorten-don't-zero made loadable. Supersedes the
# 2026-08-07 "HEP Floor 5", which was built from an ephemeral, uncommitted
# subset edit and carried only the RIGHT-side entries for bridges, curls
# and abduction — Tyler caught it live 2026-08-14 (had to pause the watch
# to do every left side). Three fixes, all Tyler 2026-08-14:
#   1. SYMMETRIC — every unilateral item has explicit R then L entries.
#   2. SL Heel Raise added (prescription #6; pogo-prep, travels well).
#   3. RDL + SL Squat SPLIT by side (all R sets, then all L) instead of
#      ALT-every-rep — "too complicated switching every rep." FLOOR CARD
#      ONLY: the full 11b keeps ALT (the provider-app text names it for
#      the squat). Same dose either way: 10/side/set x 3.
#      Split restores continuous single-leg TUT, which ALT existed to
#      halve -> both split items take the 30 s rest_sec, per this file's
#      own form-on-the-last-set rule. PT sanity-check of floor
#      composition + the split is queued in the P1 batch.
FLOOR_EXERCISES = [
    # ── Block A: FLOOR (mat, gym ball, ankle weights) ───────────────────
    {"name": "SL Bridge R (involved)",   "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Involved side first while fresh. Ham LSI 86%"},
    {"name": "SL Bridge L",              "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Symmetric 3x10 - do NOT add a 4th right set"},
    {"name": "SL Ham Curl Ball R",       "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Deficit side first. Ham LSI 86%"},
    {"name": "SL Ham Curl Ball L",       "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Hamstring - expect diffuse DOMS, that is adherence"},
    {"name": "Side Abduction R 5lb",     "sets": 3, "reps": 10, "hold_sec": 3,  "notes": "5 lb ankle weight on the WORKING leg. Glute med"},
    {"name": "Side Abduction L 5lb",     "sets": 3, "reps": 10, "hold_sec": 3,  "notes": "5 lb. Non-weightbearing, varus cue does not apply"},

    # ── Block B: LOADED STANDING ────────────────────────────────────────
    {"name": "SL Goblet RDL R",          "sets": 3, "reps": 10, "hold_sec": 0,  "rest_sec": 30, "notes": "SPLIT by side (floor card). Light KB = control rule. Varus cue"},
    {"name": "SL Goblet RDL L",          "sets": 3, "reps": 10, "hold_sec": 0,  "rest_sec": 30, "notes": "Varus cue - knee over middle of foot"},

    # ── Block C: STANDING BODYWEIGHT ────────────────────────────────────
    {"name": "SL Heel Raise R",          "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Gastroc. Also direct prep for ankle-dominant pogos"},
    {"name": "SL Heel Raise L",          "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Slow lower"},
    {"name": "SL Squat R",               "sets": 3, "reps": 10, "hold_sec": 0,  "rest_sec": 30, "notes": "SPLIT by side (floor card). Varus cue. Depth = control"},
    {"name": "SL Squat L",               "sets": 3, "reps": 10, "hold_sec": 0,  "rest_sec": 30, "notes": "Varus cue - knee over middle of foot"},
]

FLOOR_WORKOUT_NAME = "HEP Floor 6"  # 6 exercises, 12 entries; supersedes HEP Floor 5

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
# duration lever in this file is REST_BETWEEN_SETS_SEC - and it is the
# right one: it is 85% of all enforced rest in the card.
#
# CUT 30 -> 15 s, Tyler 2026-08-04 ("I don't know if I need that much
# recovery"). At 3x10 with bodyweight, a 5 lb ankle weight and a 40 lb
# goblet at RPE 2, rest is not shaping the adaptation - what it protects
# is FORM ON THE LAST SET. So this is not a PT question decided in
# advance; it is an in-session observation. (An earlier note here called
# it a PT question - too cautious for this load and RPE.)
#
# Four items keep 30 s via "rest_sec", because form-on-the-last-set is
# exactly the risk there: SL Squat R/L and DB Lateral Lunge R/L are where
# fatigue-driven frontal-plane collapse would show, and that IS the tear
# mechanism. SL Balance keeps 30 s for a different reason - fatigue
# corrupts a proprioceptive stimulus directly, and it costs 30 s total.
#
# WATCH SET 3 of the 15 s items on the debut. If the last set degrades -
# knee drifting outside the foot, trunk lean, a rep that needs a reset -
# put that exercise back to 30 s individually, not globally.
REST_BETWEEN_SETS_SEC = 15.0  # 30 -> 15 (Tyler, 2026-08-04). Per-exercise override: "rest_sec"
REST_BETWEEN_EXERCISES_SEC = 10.0  # was 45s - too long, broke flow (Tyler, 2026-07-24)
REST_BETWEEN_REPS_SEC = 10.0
REST_BETWEEN_SHORT_REPS_SEC = 5.0
SHORT_HOLD_MAX_SEC = 10
HOLD_TIMER_THRESHOLD_SEC = 5

WORKOUT_NAME = "HEP Full 11b"  # b = SL Squat + RDL alternating (2026-08-05)
