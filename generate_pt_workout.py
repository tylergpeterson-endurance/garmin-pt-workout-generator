#!/usr/bin/env python3
"""
Generate a Garmin FIT workout file for knee rehab PT exercises.
Uses ExerciseTitleMessage to display custom exercise names on watch.
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
        step_name = f"{ex['name']} ({hold}s hold)" if hold > 0 else ex["name"]

        # Each exercise gets a unique exercise_name so titles map correctly
        unique_ex_id = ex_idx

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

            title = ExerciseTitleMessage()
            title.message_index = title_index
            title.exercise_category = ExerciseCategory.UNKNOWN
            title.exercise_name = unique_ex_id
            title.workout_step_name = step_name
            exercise_titles.append(title)
            title_index += 1

            first_step_of_set = step_index
            step_index += 1

            rest_step = WorkoutStepMessage()
            rest_step.message_index = step_index
            rest_step.workout_step_name = "Rest"
            rest_step.intensity = Intensity.REST
            rest_step.duration_type = WorkoutStepDuration.TIME
            rest_step.duration_time = REST_BETWEEN_SETS_SEC * 1000
            rest_step.target_type = WorkoutStepTarget.OPEN
            workout_steps.append(rest_step)
            step_index += 1

            repeat_step = WorkoutStepMessage()
            repeat_step.message_index = step_index
            repeat_step.duration_type = WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT
            repeat_step.duration_value = first_step_of_set
            repeat_step.target_value = sets
            workout_steps.append(repeat_step)
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

            title = ExerciseTitleMessage()
            title.message_index = title_index
            title.exercise_category = ExerciseCategory.UNKNOWN
            title.exercise_name = unique_ex_id
            title.workout_step_name = step_name
            exercise_titles.append(title)
            title_index += 1

            step_index += 1

        if ex_idx < len(PT_EXERCISES) - 1:
            transition_rest = WorkoutStepMessage()
            transition_rest.message_index = step_index
            transition_rest.workout_step_name = "Next Exercise"
            transition_rest.intensity = Intensity.REST
            transition_rest.duration_type = WorkoutStepDuration.TIME
            transition_rest.duration_time = REST_BETWEEN_EXERCISES_SEC * 1000
            transition_rest.target_type = WorkoutStepTarget.OPEN
            workout_steps.append(transition_rest)
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

    # Exercise titles MUST come after workout steps
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
    for i, ex in enumerate(PT_EXERCISES):
        hold_note = f" × {ex['hold_sec']}s hold" if ex['hold_sec'] > 0 else ""
        print(f"  {i+1}. {ex['name']}: {ex['sets']}s × {ex['reps']}r{hold_note}")

    return output_path


if __name__ == "__main__":
    build_workout()
