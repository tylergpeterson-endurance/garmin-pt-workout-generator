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

## Chrome Extension (One-Click from PT Wired)

If your PT uses [PT Wired](https://rspt.mobile.ptwired.com), you can skip the Python script entirely — the Chrome extension extracts exercises directly from the page and generates the FIT file in-browser.

### Install

1. Open `chrome://extensions/`
2. Enable **Developer mode** (toggle, top right)
3. Click **Load unpacked** → select the `chrome-extension/` folder from this repo
4. Pin the extension icon in your toolbar

### Use

1. Open your PT Wired exercise page in Chrome
2. Click the **PT → Garmin FIT** extension icon
3. Click **Extract Exercises** — review the list (names, sets, reps, hold times)
4. Click **Generate & Download FIT File**
5. Copy the `.fit` file to your watch:
   - **Windows:** `[GARMIN DRIVE]:\GARMIN\NewFiles\` (USB Mass Storage mode)
   - **Mac:** Use OpenMTP to copy to `GARMIN/NewFiles/`
   - **Either:** Run `python deploy.py`

### How It Works

The extension uses **pure JavaScript FIT binary generation** — no Python, no server, no native messaging. It:

1. Injects a script into the PT Wired page via `chrome.scripting.executeScript`
2. Finds exercise names (`span.text-xl.font-medium.capitalize`) and badges (`div.bg-primary-500`)
3. Parses badge text: "3 SETS", "10 REPS", "30 SECONDS HOLD", "2-3 SECONDS HOLD" (takes upper value of ranges)
4. Generates a structurally identical FIT file to `generate_pt_workout.py` — same REPEAT loops, ExerciseTitleMessage, step metadata

The JS FIT writer was validated byte-for-byte against `fit-tool` Python output (only difference: timestamp).

### Supported Badge Formats

| Badge Text | Parsed As |
|-----------|-----------|
| `3 SETS` | sets = 3 |
| `10 REPS` | reps = 10 |
| `30 SECONDS HOLD` | holdSeconds = 30 |
| `2-3 SECONDS HOLD` | holdSeconds = 3 (upper value) |
| `6-8 SECONDS HOLD` | holdSeconds = 8 (upper value) |

## Python Script (Manual Entry)

### Requirements (Python only — Chrome extension has none)

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
| `chrome-extension/` | Chrome extension — one-click FIT generation from PT Wired |
| `generate_pt_workout.py` | Python script — generates `.FIT` from a hardcoded exercise list |
| `deploy.py` | Copies the `.FIT` file to a connected Garmin watch |
| `Knee_Rehab_PT.fit` | Pre-built workout (post-surgical knee rehab) |

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
