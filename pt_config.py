"""PT exercise plan and rest-timing constants.

Single source of truth shared by the FIT generator and the Garmin Connect
uploader. Import-only — no heavy deps here so lightweight consumers
(e.g. --dry-run JSON preview) don't pull in fit_tool.

Current program: HEP **Core** tier (~30'), per DJ-008 in the
endurance-training repo — that markdown is the source of truth for the
program, this file is just the generator input. Order is deliberate:
floor block -> loaded standing block -> balance finish = three equipment
pickups instead of six.
"""

PT_EXERCISES = [
    {"name": "SL Bridges - RIGHT (involved)", "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Involved side, first while fresh. Ham LSI 80%"},
    {"name": "SL Bridges - LEFT",             "sets": 2, "reps": 10, "hold_sec": 0,  "notes": "Maintenance dose - left is the 100% reference"},
    {"name": "Hamstring Bridge on Ball",      "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Hamstring - LSI 80% deficit side"},
    {"name": "Side Lying Hip Abduction",      "sets": 3, "reps": 10, "hold_sec": 3,  "notes": "Ankle weights. Glute med - knee tracking"},
    {"name": "Goblet Squat (Kettlebell)",     "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Bilateral - the symmetry anchor"},
    {"name": "Goblet RDL",                    "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Hamstring, bilateral hinge"},
    {"name": "Slideboard Forward Lunge",      "sets": 3, "reps": 10, "hold_sec": 0,  "notes": "Sagittal only - no lateral this cycle"},
    {"name": "Single Leg Balance",            "sets": 1, "reps": 3,  "hold_sec": 30, "notes": "Hold 30s each rep"},
]

REST_BETWEEN_SETS_SEC = 30.0
REST_BETWEEN_EXERCISES_SEC = 10.0  # was 45s - too long, broke flow (Tyler, 2026-07-24)
REST_BETWEEN_REPS_SEC = 10.0
REST_BETWEEN_SHORT_REPS_SEC = 5.0
SHORT_HOLD_MAX_SEC = 10
HOLD_TIMER_THRESHOLD_SEC = 5

WORKOUT_NAME = "HEP Core"
