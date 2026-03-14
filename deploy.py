"""Deploy Knee_Rehab_PT.fit to Garmin watch connected via USB."""

import shutil
import string
import os
from pathlib import Path

def find_garmin():
    """Find the Garmin device drive letter."""
    for letter in string.ascii_uppercase:
        garmin_path = Path(f"{letter}:\\GARMIN\\NewFiles")
        if garmin_path.exists():
            return garmin_path
    return None

def main():
    src = Path.home() / "Downloads" / "Knee_Rehab_PT.fit"
    if not src.exists():
        print(f"Source not found: {src}")
        print("Make sure Knee_Rehab_PT.fit is in your Downloads folder.")
        return

    dest = find_garmin()
    if dest:
        shutil.copy2(src, dest / "Knee_Rehab_PT.fit")
        print(f"Deployed to {dest}")
        print("Safely eject, then: Strength > Workouts > Knee Rehab PT")
    else:
        print("Garmin drive not found.")
        print("")
        print("Check: Settings > System > USB Mode > Mass Storage")
        print("Then reconnect and try again.")

if __name__ == "__main__":
    main()
