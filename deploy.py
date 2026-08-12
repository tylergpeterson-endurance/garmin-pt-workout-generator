"""Deploy the generated workout FIT to a Garmin watch connected via USB.

Filename tracks pt_config.WORKOUT_NAME, so this stays in sync with whatever
generate_pt_workout.py last wrote.
"""

import shutil
import string
import os
from pathlib import Path

from pt_config import WORKOUT_NAME

FIT_FILENAME = f"{WORKOUT_NAME.replace(' ', '_')}.fit"

def find_garmin():
    """Find the Garmin device drive letter."""
    for letter in string.ascii_uppercase:
        garmin_path = Path(f"{letter}:\\GARMIN\\NewFiles")
        if garmin_path.exists():
            return garmin_path
    return None

def main():
    src = Path.home() / "Downloads" / FIT_FILENAME
    if not src.exists():
        print(f"Source not found: {src}")
        print(f"Make sure {FIT_FILENAME} is in your Downloads folder.")
        return

    dest = find_garmin()
    if dest:
        shutil.copy2(src, dest / FIT_FILENAME)
        print(f"Deployed to {dest}")
        print(f"Safely eject, then: Strength > Workouts > {WORKOUT_NAME}")
    else:
        print("Garmin drive not found.")
        print("")
        print("Check: Settings > System > USB Mode > Mass Storage")
        print("Then reconnect and try again.")

if __name__ == "__main__":
    main()
