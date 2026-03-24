# PT → Garmin FIT Chrome Extension

Chrome extension that extracts PT exercises from [PT Wired](https://rspt.mobile.ptwired.com) and generates Garmin `.FIT` workout files — one click, no Python required at runtime.

## Quick Start

### Install the Extension (Developer Mode)

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (toggle, top right)
3. Click **Load unpacked** → select this `pt-wired-extension/` folder
4. Pin the extension icon in your toolbar

### Use It

1. Navigate to your PT Wired exercise page (`rspt.mobile.ptwired.com`)
2. Click the extension icon → **Extract Exercises**
3. Review the exercise list (names, sets, reps, hold times)
4. Click **Generate & Download FIT File**
5. Move the `.fit` file to your Garmin watch:
   - **Windows:** Copy to `GARMIN\NewFiles\` on the watch drive (USB Mass Storage mode)
   - **Mac:** Use OpenMTP to copy to `GARMIN/NewFiles/`
   - **Or:** Run `deploy.py` from the [garmin-pt-workout-generator](https://github.com/tylergpeterson-endurance/garmin-pt-workout-generator) repo

## Testing Without PT Wired

Open `test.html` in a browser (via a local server) to test FIT generation with sample exercises:

```bash
cd pt-wired-extension
python3 -m http.server 8080
# Open http://localhost:8080/test.html
```

## Architecture

```
pt-wired-extension/
├── manifest.json          # Chrome MV3 manifest
├── popup.html / popup.js  # Extension popup UI + controller
├── content.js             # Content script — DOM extraction on PT Wired pages
├── lib/
│   ├── fit-constants.js   # FIT protocol constants (messages, enums, config)
│   └── fit-writer.js      # Pure JS FIT binary writer (ported from fit-tool)
├── test.html              # Standalone test harness
└── icons/                 # Extension icons
```

### Key Technical Details

**FIT Binary Generation** (ported from `generate_pt_workout.py`):
- `ExerciseTitleMessage` (msg ID 264) — undocumented by Garmin, required for custom step names on-watch
- Title messages must be written **after** all WorkoutStep messages in file order
- Each exercise gets a unique `exercise_name` integer + `exercise_category = UNKNOWN (65534)`
- CRC-16 with FIT-specific polynomial for header and file checksums

**Workout Step Strategy:**
- **Timed holds (≥ 5s):** Flat intervals — each rep becomes a timed step with 10s recovery between reps. 30s rest between sets.
- **Rep-based (< 5s hold):** REPS duration type — one step per set with rep counter. 30s rest between sets.
- **Between exercises:** 45s rest step.

**DOM Extraction** (PT Wired page structure):
- Exercise names: `<span>` with classes `text-xl text-gray-800 font-medium capitalize`
- Badges: `<div class="bg-primary-500">` containing text like `"3 SETS"`, `"10 REPS"`, `"30 SECONDS HOLD"`
- Regex-based badge parser handles variations (SECONDS/SECS/S, with/without HOLD)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Not on a PT Wired page" | Make sure URL contains `ptwired.com` |
| "No exercises found" | PT Wired may have changed their DOM structure. Check `content.js` selectors. |
| FIT file doesn't load on watch | Verify file is in `GARMIN/NewFiles/`. Check watch is in USB Mass Storage ("Garmin") mode. |
| Steps don't show names on watch | Ensure `ExerciseTitleMessage` records are present (they should be — the writer handles this automatically) |

## Compatibility

- **Chrome:** Manifest V3, tested on Chrome 120+
- **Garmin:** Forerunner 970, should work on any Garmin that supports `.FIT` workout import
- **Platforms:** Windows, macOS (extension is cross-platform)
