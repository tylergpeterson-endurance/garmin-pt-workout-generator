# Garmin PT Workout Generator

Generate Garmin `.FIT` workout files from your physical therapy exercises — with custom exercise names, rep counts, hold times, and set loops that display natively on your Garmin watch.

**Built during knee surgery recovery. Battle-tested on a Forerunner 970.**

## Why This Exists

If you've tried to create a strength/PT workout for your Garmin watch, you've probably discovered:

- **Garmin Connect's workout builder** doesn't support reps as an end condition for strength exercises — only time-based steps
- **The Garmin Connect API** has the same limitation (we tried)
- **The FIT SDK documentation** doesn't explain how to get custom exercise names to display on the watch

This project solves all of that. It generates `.FIT` workout files with:

- ✅ Custom exercise names (not "Go")
- ✅ Rep-based step completion (not timers)
- ✅ Hold time info in step names
- ✅ Set loops with rest periods
- ✅ Transition rest between exercises

## The Undocumented Stuff We Learned

Getting custom exercise names to display on a Garmin watch requires an **undocumented `ExerciseTitleMessage`** (message ID 264) in the FIT file. Here's what we found through reverse engineering:

1. **`ExerciseTitleMessage` is required** — Without it, the watch ignores `workout_step_name` and shows "Go" for every step
2. **Each exercise needs a unique `exercise_name` integer** — If all exercises share the same value, the watch maps every step to the first title
3. **Set `exercise_category` to `UNKNOWN` (65534)** — This forces the watch to use your custom text instead of trying to match a built-in exercise animation
4. **Exercise titles must come after workout steps** in the FIT file message order

None of this is in Garmin's official SDK documentation.

## Quick Start

### Requirements

```bash
pip install fit-tool
```

### 1. Edit your exercises

Open `generate_pt_workout.py` and modify the `PT_EXERCISES` list:

```python
PT_EXERCISES = [
    {"name": "Long Sitting Hamstring Stretch", "sets": 2, "reps": 3,  "hold_sec": 30, "notes": "Hold 30s each rep"},
    {"name": "Short Arc Quads (Foam Roller)",  "sets": 3, "reps": 10, "hold_sec": 2,  "notes": "Hold 2s at top"},
    # Add your exercises here...
]
```

### 2. Generate the FIT file

```bash
python generate_pt_workout.py
```

### 3. Deploy to your watch

Connect your Garmin via USB. Make sure USB mode is set to **"Garmin"** (not MTP):

> Watch: Settings → System → USB Mode → Garmin

Then run:

```bash
python deploy.py
```

Or manually copy `Knee_Rehab_PT.fit` to `[GARMIN DRIVE]:\GARMIN\NewFiles\`

### 4. Start the workout

On your watch: **Strength → Menu (hold up) → Training → Workouts → Knee Rehab PT**

## Files

| File | Purpose |
|------|---------|
| `generate_pt_workout.py` | Generates the `.FIT` workout file from your exercise list |
| `deploy.py` | Copies the `.FIT` file to a connected Garmin watch |
| `Knee_Rehab_PT.fit` | Pre-built workout (post-surgical knee rehab, 8 exercises) |

## Compatibility

Tested on **Garmin Forerunner 970**. Should work on any Garmin watch that supports strength workouts with the current FIT protocol, including Fenix 8, Epix Pro, Venu 4, and Forerunner 265/570/965 series.

## Exercise Format Reference

Each exercise in the `PT_EXERCISES` list takes these fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Exercise name displayed on watch (max ~40 chars) |
| `sets` | int | Number of sets (uses repeat loops for sets > 1) |
| `reps` | int | Reps per set (watch shows rep counter) |
| `hold_sec` | int | Hold time in seconds (appended to name on watch display) |
| `notes` | string | Additional notes (stored in FIT, visible in some apps) |

## Adjustable Timing

Rest periods are defined at the top of `generate_pt_workout.py`:

```python
REST_BETWEEN_SETS_SEC = 30.0       # Rest between sets of same exercise
REST_BETWEEN_EXERCISES_SEC = 45.0  # Rest transitioning between exercises
```

## The Journey (for the curious)

This started as "screenshot my PT exercises → get them on my Garmin watch." What we discovered:

1. **Garmin Connect API** can push workouts to the watch wirelessly, but strength workouts only support time-based steps — no reps
2. **The FIT file format** supports reps natively via `WorkoutStepDuration.REPS`, but custom step names don't display without the undocumented `ExerciseTitleMessage`
3. **The `ExerciseTitleMessage`** maps a custom string to a `(exercise_category, exercise_name)` pair — each pair must be unique across all steps
4. **USB deployment** requires the watch in "Garmin" USB mode (not MTP), which mounts it as a standard drive letter

Total development time: one very long evening of reverse engineering. Total deployment time going forward: 30 seconds.

## License

MIT — use it, fork it, recover well.
