#!/usr/bin/env python3
"""
Generate a Garmin FIT workout file for knee rehab PT exercises.

Long holds (>= 5s): each rep is a timed countdown step in a repeat loop.
Short holds (< 5s): uses rep counter with hold info in the name.

Uses ExerciseTitleMessage (undocumented) for custom step names.
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
REST_BETWEEN_REPS_SEC = 10.0  # brief rest between timed hold reps
HOLD_TIMER_THRESHOLD_SEC = 5  # >= this uses timed countdown per rep


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
    title_index = 0

    for ex_idx, ex in enumerate(PT_EXERCISES):
        sets = ex["sets"]
        reps = ex["reps"]
        hold = ex["hold_sec"]
        use_timer = hold >= HOLD_TIMER_THRESHOLD_SEC

        step_name = f"{ex['name']} ({hold}s hold)" if hold > 0 else ex["name"]
        unique_ex_id = ex_idx

        # ── Exercise Title (one per exercise) ────────────────────
        title = ExerciseTitleMessage()
        title.message_index = title_index
        title.exercise_category = ExerciseCategory.UNKNOWN
        title.exercise_name = unique_ex_id
        title.workout_step_name = step_name
        exercise_titles.append(title)
        title_index += 1

        if use_timer:
            # ── TIMED REPS: each rep is a countdown step ─────────
            # Can't nest repeats in FIT, so unroll sets manually
            for set_num in range(sets):
                # Timed step for one rep
                timed_step = WorkoutStepMessage()
                timed_step.message_index = step_index
                timed_step.workout_step_name = step_name
                timed_step.intensity = Intensity.ACTIVE
                timed_step.duration_type = WorkoutStepDuration.TIME
                timed_step.duration_time = hold * 1000  # milliseconds
                timed_step.target_type = WorkoutStepTarget.OPEN
                timed_step.exercise_category = ExerciseCategory.UNKNOWN
                timed_step.exercise_name = unique_ex_id
                timed_step.notes = ex.get("notes", "")
                workout_steps.append(timed_step)
                rep_step_index = step_index
                step_index += 1

                # Brief rest between reps
                rep_rest = WorkoutStepMessage()
                rep_rest.message_index = step_index
                rep_rest.workout_step_name = "Recover"
                rep_rest.intensity = Intensity.REST
                rep_rest.duration_type = WorkoutStepDuration.TIME
                rep_rest.duration_time = REST_BETWEEN_REPS_SEC * 1000
                rep_rest.target_type = WorkoutStepTarget.OPEN
                workout_steps.append(rep_rest)
                step_index += 1

                # Repeat for number of reps
                if reps > 1:
                    repeat_reps = WorkoutStepMessage()
                    repeat_reps.message_index = step_index
                    repeat_reps.duration_type = WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT
                    repeat_reps.duration_value = rep_step_index
                    repeat_reps.target_value = reps
                    workout_steps.append(repeat_reps)
                    step_index += 1

                # Rest between sets (not after last set)
                if set_num < sets - 1:
                    rest = WorkoutStepMessage()
                    rest.message_index = step_index
                    rest.workout_step_name = "Rest"
                    rest.intensity = Intensity.REST
                    rest.duration_type = WorkoutStepDuration.TIME
                    rest.duration_time = REST_BETWEEN_SETS_SEC * 1000
                    rest.target_type = WorkoutStepTarget.OPEN
                    workout_steps.append(rest)
                    step_index += 1

        else:
            # ── REP COUNTER: short holds, count reps ─────────────
            if sets > 1:
                exercise_step = WorkoutStepMessage()
                exercise_step.message_index = step_index
                exercise_step.workout_step_name = step_name
                exercise_step.intensity = Intensity.ACTIVE
                exercise_step.duration_type = WorkoutStepDuration.REPS
                exercise_step.duration_reps = reps
                exercise_step.target_type = WorkoutStepTarget.OPEN
                exercise_step.exercise_category = ExerciseCategory.UNKNOWN
                exercise_step.exercise_name = unique_ex_id
                exercise_step.notes = ex.get("notes", "")
                workout_steps.append(exercise_step)
                first_step_of_set = step_index
                step_index += 1

                rest = WorkoutStepMessage()
                rest.message_index = step_index
                rest.workout_step_name = "Rest"
                rest.intensity = Intensity.REST
                rest.duration_type = WorkoutStepDuration.TIME
                rest.duration_time = REST_BETWEEN_SETS_SEC * 1000
                rest.target_type = WorkoutStepTarget.OPEN
                workout_steps.append(rest)
                step_index += 1

                repeat = WorkoutStepMessage()
                repeat.message_index = step_index
                repeat.duration_type = WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT
                repeat.duration_value = first_step_of_set
                repeat.target_value = sets
                workout_steps.append(repeat)
                step_index += 1

            else:
                exercise_step = WorkoutStepMessage()
                exercise_step.message_index = step_index
                exercise_step.workout_step_name = step_name
                exercise_step.intensity = Intensity.ACTIVE
                exercise_step.duration_type = WorkoutStepDuration.REPS
                exercise_step.duration_reps = reps
                exercise_step.target_type = WorkoutStepTarget.OPEN
                exercise_step.exercise_category = ExerciseCategory.UNKNOWN
                exercise_step.exercise_name = unique_ex_id
                exercise_step.notes = ex.get("notes", "")
                workout_steps.append(exercise_step)
                step_index += 1

        # ── Rest between exercises ───────────────────────────────
        if ex_idx < len(PT_EXERCISES) - 1:
            transition = WorkoutStepMessage()
            transition.message_index = step_index
            transition.workout_step_name = "Next Exercise"
            transition.intensity = Intensity.REST
            transition.duration_type = WorkoutStepDuration.TIME
            transition.duration_time = REST_BETWEEN_EXERCISES_SEC * 1000
            transition.target_type = WorkoutStepTarget.OPEN
            workout_steps.append(transition)
            step_index += 1

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
    output_path = "/home/claude/Knee_Rehab_PT.fit"
    fit_file.to_file(output_path)
    print(f"✅ Workout file created: {output_path}")
    print(f"   Workout steps: {len(workout_steps)}")
    print(f"   Exercise titles: {len(exercise_titles)}")

    print("\n── Workout Summary ──")
    for ex in PT_EXERCISES:
        mode = "TIMER" if ex["hold_sec"] >= HOLD_TIMER_THRESHOLD_SEC else "REPS"
        hold_note = f" × {ex['hold_sec']}s hold" if ex['hold_sec'] > 0 else ""
        print(f"  [{mode}] {ex['name']}: {ex['sets']}s × {ex['reps']}r{hold_note}")

    return output_path


if __name__ == "__main__":
    build_workout()
