"""PT exercise plan and rest-timing constants.

Single source of truth shared by the FIT generator and the Garmin Connect
uploader. Import-only — no heavy deps here so lightweight consumers
(e.g. --dry-run JSON preview) don't pull in fit_tool.
"""

PT_EXERCISES = [
    {"name": "Long Sitting Hamstring Stretch", "sets": 2, "reps": 3,  "hold_sec": 30, "notes": "Hold 30s each rep"},
    {"name": "Seated Calf Stretch (Belt)",     "sets": 1, "reps": 3,  "hold_sec": 30, "notes": "Hold 30s each rep"},
    {"name": "Short Arc Quads (Foam Roller)",  "sets": 3, "reps": 10, "hold_sec": 2,  "notes": "Hold 2s at top"},
    {"name": "Long Arc Quad",                  "sets": 3, "reps": 10, "hold_sec": 2,  "notes": "Hold 2s at top"},
    {"name": "Ankle Plantarflexion w/ Band",   "sets": 3, "reps": 10, "hold_sec": 3,  "notes": "Hold 2-3s each rep"},
    {"name": "Prone TKE",                      "sets": 2, "reps": 3,  "hold_sec": 20, "notes": "Hold 15-30s each rep"},
    {"name": "Standing Hip Abduction (Band)",  "sets": 3, "reps": 10, "hold_sec": 3,  "notes": "Hold 2-3s each rep"},
    {"name": "Standing Glute Squeeze",         "sets": 2, "reps": 5,  "hold_sec": 7,  "notes": "Hold 6-8s each rep"},
]

REST_BETWEEN_SETS_SEC = 30.0
REST_BETWEEN_EXERCISES_SEC = 45.0
REST_BETWEEN_REPS_SEC = 10.0
REST_BETWEEN_SHORT_REPS_SEC = 5.0
SHORT_HOLD_MAX_SEC = 10
HOLD_TIMER_THRESHOLD_SEC = 5

WORKOUT_NAME = "Knee Rehab PT"
