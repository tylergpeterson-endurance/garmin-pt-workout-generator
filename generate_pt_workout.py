#!/usr/bin/env python3
"""
Generate a Garmin FIT workout file for knee rehab PT exercises.

Long holds (>= 5s): FLAT INTERVALS — each rep is an individual timed step
with explicit rest steps between reps. No REPEAT loops for timed exercises
(Garmin watches mishandle rest steps inside repeat loops).

Short holds (< 5s): uses rep counter with REPEAT_UNTIL_STEPS_CMPLT for sets.

Uses ExerciseTitleMessage (undocumented msg ID 264) for custom step names.
"""

import datetime
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.workout_message import WorkoutMessage
from fit_tool.profile.messages.workout_step_message import WorkoutStepMessage
from fit_tool.profile.messages.exercise_title_message import ExerciseTitleMessage
from fit_tool.profile.profile_type import (
    Sport, SubSport, Intensity, WorkoutStepDuration,
    WorkoutStepTarget, Manufacturer, FileType,
    ExerciseCategory,
)

# ── PT Exercise Definitions ──────────────────────────────────────────
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
HOLD_TIMER_THRESHOLD_SEC = 5  # >= this uses timed countdown per rep

# Tiered inter-rep recovery: shorter rest for shorter holds
LONG_HOLD_THRESHOLD_SEC = 25  # holds > this get longer recovery
REST_BETWEEN_REPS_SHORT_SEC = 5.0   # recovery for holds <= 25s
REST_BETWEEN_REPS_LONG_SEC = 10.0   # recovery for holds > 25s


def _rep_rest_for(hold_sec):
    """Return inter-rep recovery duration based on hold length."""
    if hold_sec > LONG_HOLD_THRESHOLD_SEC:
        return REST_BETWEEN_REPS_LONG_SEC
    return REST_BETWEEN_REPS_SHORT_SEC


def _add_timed_step(steps, step_index, name, duration_sec, intensity, ex_id=None, notes=""):
    """Helper to create a timed workout step."""
    step = WorkoutStepMessage()
    step.message_index = step_index
    step.workout_step_name = name
    step.intensity = intensity
    step.duration_type = WorkoutStepDuration.TIME
    step.duration_time = int(duration_sec * 1000)  # milliseconds
    step.target_type = WorkoutStepTarget.OPEN
    if ex_id is not None:
        step.exercise_category = ExerciseCategory.UNKNOWN
        step.exercise_name = ex_id
    if notes:
        step.notes = notes
    steps.append(step)
    return step_index + 1


def _build_timed_exercise(steps, step_index, ex, ex_id):
    """
    FLAT INTERVALS approach for timed holds.

    Unrolls all sets x reps into individual sequential steps:
      Hold -> Recover -> Hold -> Recover -> Hold -> [Set Rest] -> Hold -> ...

    No REPEAT loops. The watch just walks through step by step.
    Skips the inter-rep rest after the last rep of each set.
    """
    sets = ex["sets"]
    reps = ex["reps"]
    hold = ex["hold_sec"]
    step_name = f"{ex['name']} ({hold}s hold)"
    notes = ex.get("notes", "")

    rep_rest = _rep_rest_for(hold)

    for set_num in range(sets):
        for rep_num in range(reps):
            # ── Active hold ──
            step_index = _add_timed_step(
                steps, step_index, step_name, hold,
                Intensity.ACTIVE, ex_id=ex_id, notes=notes
            )
            # ── Inter-rep rest (skip after last rep of the set) ──
            if rep_num < reps - 1:
                step_index = _add_timed_step(
                    steps, step_index, "Recover", rep_rest,
                    Intensity.REST
                )

        # ── Rest between sets (skip after last set) ──
        if set_num < sets - 1:
            step_index = _add_timed_step(
                steps, step_index, "Set Rest", REST_BETWEEN_SETS_SEC,
                Intensity.REST
            )

    return step_index


def _build_rep_exercise(steps, step_index, ex, ex_id):
    """
    Rep counter approach for short holds.
    Uses REPEAT_UNTIL_STEPS_CMPLT for multiple sets (works reliably
    because the repeat contains exercise + rest with no mixed-intensity issues).
    """
    sets = ex["sets"]
    reps = ex["reps"]
    hold = ex["hold_sec"]
    step_name = f"{ex['name']} ({hold}s hold)" if hold > 0 else ex["name"]
    notes = ex.get("notes", "")

    if sets > 1:
        # Exercise step (rep counter)
        exercise_step = WorkoutStepMessage()
        exercise_step.message_index = step_index
        exercise_step.workout_step_name = step_name
        exercise_step.intensity = Intensity.ACTIVE
        exercise_step.duration_type = WorkoutStepDuration.REPS
        exercise_step.duration_reps = reps
        exercise_step.target_type = WorkoutStepTarget.OPEN
        exercise_step.exercise_category = ExerciseCategory.UNKNOWN
        exercise_step.exercise_name = ex_id
        exercise_step.notes = notes
        steps.append(exercise_step)
        first_step = step_index
        step_index += 1

        # Rest between sets
        rest = WorkoutStepMessage()
        rest.message_index = step_index
        rest.workout_step_name = "Set Rest"
        rest.intensity = Intensity.REST
        rest.duration_type = WorkoutStepDuration.TIME
        rest.duration_time = int(REST_BETWEEN_SETS_SEC * 1000)
        rest.target_type = WorkoutStepTarget.OPEN
        steps.append(rest)
        step_index += 1

        # Repeat for sets
        repeat = WorkoutStepMessage()
        repeat.message_index = step_index
        repeat.duration_type = WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT
        repeat.duration_value = first_step
        repeat.target_value = sets
        steps.append(repeat)
        step_index += 1

    else:
        # Single set — no repeat needed
        exercise_step = WorkoutStepMessage()
        exercise_step.message_index = step_index
        exercise_step.workout_step_name = step_name
        exercise_step.intensity = Intensity.ACTIVE
        exercise_step.duration_type = WorkoutStepDuration.REPS
        exercise_step.duration_reps = reps
        exercise_step.target_type = WorkoutStepTarget.OPEN
        exercise_step.exercise_category = ExerciseCategory.UNKNOWN
        exercise_step.exercise_name = ex_id
        exercise_step.notes = notes
        steps.append(exercise_step)
        step_index += 1

    return step_index


def build_workout():
    builder = FitFileBuilder(auto_define=True)

    # ── File ID ──────────────────────────────────────────────────────
    file_id = FileIdMessage()
    file_id.type = FileType.WORKOUT
    file_id.manufacturer = Manufacturer.DEVELOPMENT.value
    file_id.product = 0
    file_id.time_created = round(datetime.datetime.now().timestamp() * 1000)
    file_id.serial_number = 0x12345678
    builder.add(file_id)

    # ── Build all workout steps ──────────────────────────────────────
    workout_steps = []
    exercise_titles = []
    step_index = 0

    for ex_idx, ex in enumerate(PT_EXERCISES):
        hold = ex["hold_sec"]
        use_timer = hold >= HOLD_TIMER_THRESHOLD_SEC
        unique_ex_id = ex_idx

        step_name = f"{ex['name']} ({hold}s hold)" if hold > 0 else ex["name"]

        # ── Exercise Title (one per exercise) ────────────────────
        title = ExerciseTitleMessage()
        title.message_index = ex_idx
        title.exercise_category = ExerciseCategory.UNKNOWN
        title.exercise_name = unique_ex_id
        title.workout_step_name = step_name
        exercise_titles.append(title)

        # ── Build steps based on exercise type ───────────────────
        if use_timer:
            step_index = _build_timed_exercise(
                workout_steps, step_index, ex, unique_ex_id
            )
        else:
            step_index = _build_rep_exercise(
                workout_steps, step_index, ex, unique_ex_id
            )

        # ── Rest between exercises ───────────────────────────────
        if ex_idx < len(PT_EXERCISES) - 1:
            step_index = _add_timed_step(
                workout_steps, step_index,
                "Next Exercise", REST_BETWEEN_EXERCISES_SEC,
                Intensity.REST
            )

    # ── Workout message ──────────────────────────────────────────────
    workout = WorkoutMessage()
    workout.workout_name = "Knee Rehab PT"
    workout.sport = Sport.TRAINING
    workout.sub_sport = SubSport.STRENGTH_TRAINING
    workout.num_valid_steps = len(workout_steps)
    builder.add(workout)

    for step in workout_steps:
        builder.add(step)

    for title in exercise_titles:
        builder.add(title)

    # ── Write file ───────────────────────────────────────────────────
    fit_file = builder.build()
    output_path = "Knee_Rehab_PT.fit"
    fit_file.to_file(output_path)
    print(f"  Workout file created: {output_path}")
    print(f"   Total workout steps: {len(workout_steps)}")
    print(f"   Exercise titles: {len(exercise_titles)}")

    # ── Detailed step walkthrough ────────────────────────────────────
    # Use .value for comparisons — fit-tool stores raw ints internally
    TIME_VAL = WorkoutStepDuration.TIME.value
    REPS_VAL = WorkoutStepDuration.REPS.value
    REPEAT_VAL = WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT.value
    REST_VAL = Intensity.REST.value

    print("\n── Step-by-Step Breakdown ──")
    for i, step in enumerate(workout_steps):
        name = getattr(step, 'workout_step_name', None) or "REPEAT"
        dur_type = getattr(step, 'duration_type', None)
        # Handle both enum and raw int from fit-tool
        dur_val = dur_type.value if hasattr(dur_type, 'value') else dur_type
        intensity = getattr(step, 'intensity', None)
        int_val = intensity.value if hasattr(intensity, 'value') else intensity
        tag = "REST" if int_val == REST_VAL else "WORK"

        if dur_val == TIME_VAL:
            dur_ms = getattr(step, 'duration_time', 0)
            print(f"  [{i:2d}] [{tag:4s}] {name} — {dur_ms/1000:.0f}s")
        elif dur_val == REPS_VAL:
            reps = getattr(step, 'duration_reps', 0)
            print(f"  [{i:2d}] [{tag:4s}] {name} — {reps} reps")
        elif dur_val == REPEAT_VAL:
            back_to = getattr(step, 'duration_value', 0)
            count = getattr(step, 'target_value', 0)
            print(f"  [{i:2d}] [LOOP] REPEAT -> step {back_to}, {count}x sets")
        else:
            print(f"  [{i:2d}] [{tag:4s}] {name}")

    print("\n── Exercise Summary ──")
    for ex in PT_EXERCISES:
        mode = "INTERVALS" if ex["hold_sec"] >= HOLD_TIMER_THRESHOLD_SEC else "REPS"
        hold_note = f" x {ex['hold_sec']}s hold" if ex['hold_sec'] > 0 else ""
        print(f"  [{mode:>9s}] {ex['name']}: {ex['sets']}s x {ex['reps']}r{hold_note}")

    return output_path


if __name__ == "__main__":
    build_workout()
