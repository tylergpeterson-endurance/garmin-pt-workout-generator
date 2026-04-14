#!/usr/bin/env python3
"""Upload the PT workout to Garmin Connect as a JSON workout.

First run prompts for Garmin credentials (MFA supported via stdin).
Session token is cached to ~/.garth/ for silent subsequent runs.

The workout appears in your Connect library; schedule it to a day in
the web/app UI and it syncs wirelessly to the watch.

Uses the unofficial /workout-service/workout endpoint — Garmin's only
programmatic path for workout plans is the gated partner Training API,
so this lib may break if Garmin tightens auth.

Usage:
  python upload_to_connect.py                              # upload via garth (SSO)
  python upload_to_connect.py --dry-run                    # print JSON
  python upload_to_connect.py --console-snippet            # print browser-console JS
                                                           # to paste on connect.garmin.com
                                                           # (bypasses SSO/rate limits)
  python upload_to_connect.py --from-fit <path> [--dry-run|--console-snippet|upload]
                                                           # convert an existing .fit
                                                           # workout file to Connect JSON
"""
import getpass
import json
import sys
from pathlib import Path

from pt_config import (
    PT_EXERCISES,
    REST_BETWEEN_SETS_SEC,
    REST_BETWEEN_EXERCISES_SEC,
    REST_BETWEEN_REPS_SEC,
    REST_BETWEEN_SHORT_REPS_SEC,
    SHORT_HOLD_MAX_SEC,
    HOLD_TIMER_THRESHOLD_SEC,
    WORKOUT_NAME,
)

GARTH_HOME = Path.home() / ".garth"

# Garmin rate-limits garth's default mobile-app UA aggressively. Override
# with a recent desktop-Chrome UA (env var wins if set).
import os
DEFAULT_UA = os.environ.get(
    "GARTH_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)

STRENGTH      = {"sportTypeId": 5, "sportTypeKey": "strength_training", "displayOrder": 5}
STEP_INTERVAL = {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3}
STEP_REST     = {"stepTypeId": 5, "stepTypeKey": "rest",     "displayOrder": 5}
STEP_REPEAT   = {"stepTypeId": 6, "stepTypeKey": "repeat",   "displayOrder": 6}
END_TIME      = {"conditionTypeId": 2,  "conditionTypeKey": "time",       "displayOrder": 2,  "displayable": True}
END_REPS      = {"conditionTypeId": 10, "conditionTypeKey": "reps",       "displayOrder": 10, "displayable": True}
END_ITER      = {"conditionTypeId": 7,  "conditionTypeKey": "iterations", "displayOrder": 7,  "displayable": False}
TARGET_NONE   = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1}


class Counter:
    def __init__(self):
        self.step_order = 0
        self.child_id = 0

    def next_order(self):
        self.step_order += 1
        return self.step_order

    def next_child_id(self):
        self.child_id += 1
        return self.child_id


def active_step(c, description, *, duration_sec=None, reps=None, child_step_id=None):
    step = {
        "type": "ExecutableStepDTO",
        "stepId": None,
        "stepOrder": c.next_order(),
        "childStepId": child_step_id,
        "stepType": STEP_INTERVAL,
        "description": description,
        "targetType": TARGET_NONE,
        "category": None,
        "exerciseName": None,
    }
    if duration_sec is not None:
        step["endCondition"] = END_TIME
        step["endConditionValue"] = float(duration_sec)
    else:
        step["endCondition"] = END_REPS
        step["endConditionValue"] = float(reps)
    return step


def rest_step(c, description, duration_sec, *, child_step_id=None):
    return {
        "type": "ExecutableStepDTO",
        "stepId": None,
        "stepOrder": c.next_order(),
        "childStepId": child_step_id,
        "stepType": STEP_REST,
        "description": description,
        "targetType": TARGET_NONE,
        "endCondition": END_TIME,
        "endConditionValue": float(duration_sec),
    }


def repeat_group(c, iterations, build_children):
    """build_children(my_child_id) -> list[step]. Its children tag themselves with my_child_id."""
    my_cid = c.next_child_id()
    order = c.next_order()
    children = build_children(my_cid)
    return {
        "type": "RepeatGroupDTO",
        "stepId": None,
        "stepOrder": order,
        "childStepId": my_cid,
        "stepType": STEP_REPEAT,
        "numberOfIterations": int(iterations),
        "smartRepeat": False,
        "skipLastRestStep": False,
        "endCondition": END_ITER,
        "endConditionValue": float(iterations),
        "workoutSteps": children,
    }


def build_exercise_steps(c, ex, is_last_exercise):
    sets = ex["sets"]
    reps = ex["reps"]
    hold = ex["hold_sec"]
    use_timer = hold >= HOLD_TIMER_THRESHOLD_SEC
    label = f"{ex['name']} ({hold}s hold)" if hold > 0 else ex["name"]
    notes = ex.get("notes", "")
    desc = f"{label} — {notes}" if notes else label

    steps = []

    if use_timer:
        rep_rest_sec = REST_BETWEEN_SHORT_REPS_SEC if hold <= SHORT_HOLD_MAX_SEC else REST_BETWEEN_REPS_SEC

        def build_rep_children(rep_cid):
            return [
                active_step(c, desc, duration_sec=hold, child_step_id=rep_cid),
                rest_step(c, "Recover", rep_rest_sec, child_step_id=rep_cid),
            ]

        if sets > 1:
            def build_set_children(set_cid):
                return [
                    repeat_group(c, reps, build_rep_children),
                    rest_step(c, "Rest between sets", REST_BETWEEN_SETS_SEC, child_step_id=set_cid),
                ]
            steps.append(repeat_group(c, sets, build_set_children))
        else:
            steps.append(repeat_group(c, reps, build_rep_children))
    else:
        if sets > 1:
            def build_set_children(set_cid):
                return [
                    active_step(c, desc, reps=reps, child_step_id=set_cid),
                    rest_step(c, "Rest between sets", REST_BETWEEN_SETS_SEC, child_step_id=set_cid),
                ]
            steps.append(repeat_group(c, sets, build_set_children))
        else:
            steps.append(active_step(c, desc, reps=reps))

    if not is_last_exercise:
        steps.append(rest_step(c, "Next Exercise", REST_BETWEEN_EXERCISES_SEC))

    return steps


def build_workout_json():
    c = Counter()
    top_steps = []
    for i, ex in enumerate(PT_EXERCISES):
        top_steps.extend(build_exercise_steps(c, ex, is_last_exercise=(i == len(PT_EXERCISES) - 1)))

    return {
        "workoutName": WORKOUT_NAME,
        "description": "Generated from PT exercise plan",
        "sportType": STRENGTH,
        "estimatedDurationInSecs": 0,
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": STRENGTH,
                "workoutSteps": top_steps,
            }
        ],
    }


# ── FIT → Connect JSON conversion ──────────────────────────────────────
# FIT constants (from fit_tool.profile.profile_type)
FIT_DUR_TIME   = 0
FIT_DUR_REPEAT = 6
FIT_DUR_REPS   = 29
FIT_INT_ACTIVE = 0
FIT_INT_REST   = 1


def _fit_step_to_tree(fit_step):
    """Convert one FIT WorkoutStep to a lightweight tree node (no IDs yet)."""
    dur_type = fit_step.duration_type
    intensity = fit_step.intensity
    name = (fit_step.workout_step_name or "").strip() or "Step"

    if intensity == FIT_INT_ACTIVE:
        if dur_type == FIT_DUR_TIME:
            return {
                "kind": "executable",
                "stepType": STEP_INTERVAL,
                "endCondition": END_TIME,
                "endConditionValue": (fit_step.duration_time or 0) / 1000.0,
                "description": name,
            }
        if dur_type == FIT_DUR_REPS:
            reps = fit_step.duration_reps or fit_step.duration_value or 1
            return {
                "kind": "executable",
                "stepType": STEP_INTERVAL,
                "endCondition": END_REPS,
                "endConditionValue": float(reps),
                "description": name,
            }
    if intensity == FIT_INT_REST and dur_type == FIT_DUR_TIME:
        return {
            "kind": "executable",
            "stepType": STEP_REST,
            "endCondition": END_TIME,
            "endConditionValue": (fit_step.duration_time or 0) / 1000.0,
            "description": name,
        }
    return None  # unknown step type; caller skips


def fit_to_workout_json(fit_path):
    """Parse a FIT workout file and return Connect workout-service JSON."""
    from fit_tool.fit_file import FitFile

    fit = FitFile.from_file(fit_path)
    workout_name = None
    fit_steps = []
    for rec in fit.records:
        m = rec.message
        if m is None:
            continue
        cls = type(m).__name__
        if cls == "WorkoutMessage":
            workout_name = getattr(m, "workout_name", None)
        elif cls == "WorkoutStepMessage":
            fit_steps.append(m)

    # Pass 1: resolve FIT's flat REPEAT_UNTIL_STEPS markers into a nested tree.
    # Track the tree-position where each FIT message_index landed so a later
    # REPEAT can splice its body out.
    tree = []
    fit_idx_to_tree_pos = {}
    for fs in fit_steps:
        fit_idx_to_tree_pos[fs.message_index] = len(tree)
        if fs.duration_type == FIT_DUR_REPEAT:
            target_fit_idx = fs.duration_value
            iterations = fs.target_value or 1
            start_pos = fit_idx_to_tree_pos.get(target_fit_idx, len(tree))
            children = tree[start_pos:]
            del tree[start_pos:]
            tree.append({"kind": "repeat", "iterations": int(iterations), "children": children})
            continue
        node = _fit_step_to_tree(fs)
        if node is not None:
            tree.append(node)

    # Pass 2: assign stepOrder (sequential across whole workout) and childStepId.
    c = Counter()

    def assign(nodes, parent_cid):
        out = []
        for n in nodes:
            if n["kind"] == "repeat":
                my_cid = c.next_child_id()
                order = c.next_order()
                children = assign(n["children"], my_cid)
                out.append({
                    "type": "RepeatGroupDTO",
                    "stepId": None,
                    "stepOrder": order,
                    "childStepId": my_cid,
                    "stepType": STEP_REPEAT,
                    "numberOfIterations": int(n["iterations"]),
                    "smartRepeat": False,
                    "skipLastRestStep": False,
                    "endCondition": END_ITER,
                    "endConditionValue": float(n["iterations"]),
                    "workoutSteps": children,
                })
            else:
                step = {
                    "type": "ExecutableStepDTO",
                    "stepId": None,
                    "stepOrder": c.next_order(),
                    "childStepId": parent_cid,
                    "stepType": n["stepType"],
                    "description": n["description"],
                    "targetType": TARGET_NONE,
                    "endCondition": n["endCondition"],
                    "endConditionValue": n["endConditionValue"],
                }
                if n["stepType"] == STEP_INTERVAL:
                    step["category"] = None
                    step["exerciseName"] = None
                out.append(step)
        return out

    top_steps = assign(tree, parent_cid=None)

    return {
        "workoutName": workout_name or Path(fit_path).stem,
        "description": f"Converted from {Path(fit_path).name}",
        "sportType": STRENGTH,
        "estimatedDurationInSecs": 0,
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": STRENGTH,
                "workoutSteps": top_steps,
            }
        ],
    }


def ensure_auth():
    try:
        global garth
        import garth
        from garth.http import USER_AGENT
    except ImportError:
        sys.exit("garth not installed. Run: pip install -r requirements.txt")

    USER_AGENT["User-Agent"] = DEFAULT_UA

    if GARTH_HOME.exists():
        try:
            garth.resume(str(GARTH_HOME))
            _ = garth.client.username
            return
        except Exception as e:
            print(f"Saved session invalid ({e}); re-authenticating.")
    email = input("Garmin Connect email: ").strip()
    password = getpass.getpass("Password: ")
    garth.login(email, password)
    GARTH_HOME.mkdir(exist_ok=True)
    garth.save(str(GARTH_HOME))


CONSOLE_SNIPPET_TEMPLATE = """\
(async () => {
  const workout = __PAYLOAD__;
  try {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (!csrfMeta) {
      console.error('No <meta name="csrf-token"> on this page. Are you signed into connect.garmin.com?');
      return;
    }
    const resp = await fetch('/gc-api/workout-service/workout', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'connect-csrf-token': csrfMeta.content,
        'x-requested-with': 'XMLHttpRequest',
      },
      body: JSON.stringify(workout),
    });
    const text = await resp.text();
    let body; try { body = JSON.parse(text); } catch { body = text; }
    console.log('Status:', resp.status, resp.statusText);
    console.log('Response:', body);
    if (body && body.workoutId) {
      const url = 'https://connect.garmin.com/modern/workout/' + body.workoutId;
      console.log('%c\\u2713 Uploaded: ' + url, 'color:green;font-weight:bold');
    }
    return body;
  } catch (e) {
    console.error('Upload failed:', e);
    throw e;
  }
})();
"""


def print_console_snippet(payload):
    snippet = CONSOLE_SNIPPET_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload))
    print(snippet)


def _parse_arg(flag):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def main():
    fit_path = _parse_arg("--from-fit")
    if fit_path:
        payload = fit_to_workout_json(fit_path)
    else:
        payload = build_workout_json()

    if "--dry-run" in sys.argv:
        print(json.dumps(payload, indent=2))
        return

    if "--console-snippet" in sys.argv:
        print_console_snippet(payload)
        return

    ensure_auth()
    import garth  # now installed — imported at module scope via ensure_auth
    result = garth.connectapi("/workout-service/workout", method="POST", json=payload)
    workout_id = result.get("workoutId") if isinstance(result, dict) else None
    if workout_id:
        print(f"✅ Workout uploaded: id={workout_id}")
        print(f"   https://connect.garmin.com/modern/workout/{workout_id}")
    else:
        print("Upload response:", result)


if __name__ == "__main__":
    main()
